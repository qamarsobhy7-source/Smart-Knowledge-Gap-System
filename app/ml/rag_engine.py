"""
RAG Engine — Qdrant Cloud + FastEmbed.

Uses Qdrant Cloud (vector database) and FastEmbed (lightweight
ONNX-based embeddings) instead of the heavier ChromaDB +
sentence-transformers combo. This makes the RAG layer deployable
on lightweight hosting platforms such as Faable's free tier.

Environment variables required:
    QDRANT_URL       — your Qdrant Cloud endpoint (with :6333)
    QDRANT_API_KEY   — API key for the cluster
"""

import os
from pathlib import Path

import pandas as pd

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    from fastembed import TextEmbedding
    _RAG_LIBS_AVAILABLE = True
except ImportError:
    QdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    TextEmbedding = None
    _RAG_LIBS_AVAILABLE = False


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

COLLECTION_NAME = "skg_content"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384


_client = None
_embedder = None


def _get_client():
    """Get or create the Qdrant client."""
    global _client
    if _client is not None:
        return _client
    if not _RAG_LIBS_AVAILABLE:
        return None
    url = os.environ.get("QDRANT_URL", "").strip()
    key = os.environ.get("QDRANT_API_KEY", "").strip()
    if not url or not key:
        return None
    try:
        _client = QdrantClient(url=url, api_key=key)
        return _client
    except Exception:
        return None


def _get_embedder():
    """Get or create the FastEmbed embedder."""
    global _embedder
    if _embedder is not None:
        return _embedder
    if not _RAG_LIBS_AVAILABLE:
        return None
    try:
        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
        return _embedder
    except Exception:
        return None


def _build_documents():
    """Build all documents (text + metadata) from the project CSVs."""
    documents = []
    metadatas = []
    ids = []

    lc_path = DATA_DIR / "learning_content_FINAL.csv"
    if lc_path.exists():
        lc = pd.read_csv(lc_path)
        for _, row in lc.iterrows():
            cid = int(row["concept_id"])
            name = str(row["concept_name"])
            sid = int(row["subject_id"])
            level = str(row["level"])

            sections = [
                ("learning_objective", row.get("learning_objective")),
                ("explanation", row.get("explanation")),
                ("key_points", row.get("key_points")),
                ("example", row.get("example")),
                ("why_it_matters", row.get("why_it_matters")),
                ("common_mistakes", row.get("common_mistakes")),
                ("study_tips", row.get("study_tips")),
                ("step_by_step", row.get("step_by_step")),
            ]
            for section, text in sections:
                if pd.notna(text) and str(text).strip():
                    doc = f"{name} — {section.replace('_', ' ').title()}: {text}"
                    documents.append(doc)
                    metadatas.append({
                        "type": section,
                        "concept_id": cid,
                        "concept_name": name,
                        "subject_id": sid,
                        "level": level,
                    })
                    ids.append(f"lc_{section}_{cid}")

    qb_path = DATA_DIR / "final_question_bank_270.csv"
    if qb_path.exists():
        qb = pd.read_csv(qb_path)
        for _, row in qb.iterrows():
            name = str(row["concept_name"])
            qtype = str(row["question_type"])
            doc = (
                f"Question on {name} ({qtype}): {row['question_text']} "
                f"A) {row['option_a']} "
                f"B) {row['option_b']} "
                f"C) {row['option_c']} "
                f"D) {row['option_d']} "
                f"Correct answer: {row['correct_answer']}"
            )
            documents.append(doc)
            metadatas.append({
                "type": "question",
                "concept_id": int(row["concept_id"]),
                "concept_name": name,
                "subject_id": int(row["subject_id"]),
                "difficulty": str(row["difficulty"]),
                "question_type": qtype,
            })
            ids.append(f"q_{row['question_id']}")

    c_path = DATA_DIR / "concepts_final.csv"
    if c_path.exists():
        concepts = pd.read_csv(c_path)
        for _, row in concepts.iterrows():
            prereq = row.get("prerequisites")
            prereq_text = "no prerequisites" if pd.isna(prereq) else f"prerequisites: {prereq}"
            doc = f"{row['concept_name']} ({row['difficulty']}) — {prereq_text}"
            documents.append(doc)
            metadatas.append({
                "type": "concept_info",
                "concept_id": int(row["concept_id"]),
                "concept_name": str(row["concept_name"]),
                "subject_id": int(row["subject_id"]),
                "difficulty": str(row["difficulty"]),
            })
            ids.append(f"c_{row['concept_id']}")

    return documents, metadatas, ids


def index_documents(verbose=True):
    """Index all project documents into Qdrant Cloud."""
    client = _get_client()
    embedder = _get_embedder()
    if client is None or embedder is None:
        if verbose:
            print("RAG not available (missing libs or credentials)")
        return False

    documents, metadatas, ids = _build_documents()
    if verbose:
        print(f"Building index: {len(documents)} documents")

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    batch_size = 32
    total_indexed = 0

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size]

        vectors = list(embedder.embed(batch_docs))

        points = [
            PointStruct(
                id=i + j,
                vector=vec.tolist(),
                payload={**meta, "text": doc},
            )
            for j, (vec, meta, doc) in enumerate(zip(vectors, batch_meta, batch_docs))
        ]

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

        total_indexed += len(points)
        if verbose:
            print(f"   {total_indexed}/{len(documents)}")

    if verbose:
        print(f"Indexed {total_indexed} documents successfully")

    return True


def retrieve(query, top_k=5, filter_type=None):
    """Retrieve the most relevant documents for a query."""
    if not _RAG_LIBS_AVAILABLE:
        return []

    client = _get_client()
    embedder = _get_embedder()

    if client is None or embedder is None:
        return []

    try:
        query_vec = list(embedder.embed([query]))[0].tolist()
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

    qfilter = None
    if filter_type:
        try:
            qfilter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=filter_type),
                    )
                ]
            )
        except Exception:
            qfilter = None

    # Try the new API first (qdrant-client >= 1.12)
    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec,
            limit=top_k,
            query_filter=qfilter,
        )
        points = results.points
    except (AttributeError, TypeError):
        # Fall back to the old API
        try:
            points = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vec,
                limit=top_k,
                query_filter=qfilter,
            )
        except Exception as e:
            print(f"Search error: {e}")
            return []
    except Exception as e:
        print(f"Query error: {e}")
        return []

    output = []
    for r in points:
        payload = r.payload or {}
        output.append({
            "text": payload.get("text", ""),
            "metadata": {k: v for k, v in payload.items() if k != "text"},
            "distance": float(r.score),
        })

    return output


def vector_store_exists():
    """Check if the collection exists and has points."""
    if not _RAG_LIBS_AVAILABLE:
        return False
    client = _get_client()
    if client is None:
        return False
    try:
        info = client.get_collection(COLLECTION_NAME)
        return (info.points_count or 0) > 0
    except Exception:
        return False
