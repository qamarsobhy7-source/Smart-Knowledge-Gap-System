"""
RAG Engine — Retrieval-Augmented Generation.

Builds a searchable vector store from the project's own content:
    - concept definitions
    - learning content (explanation, key points, examples)
    - practice questions
    - prerequisites

Then retrieves the most relevant chunks for any student query.

This grounds LLM answers in the project's actual content
(no hallucination).
"""

from typing import TypeVar, Generic

try:
    import chromadb
    from chromadb import Documents, EmbeddingFunction, Embeddings
    from sentence_transformers import SentenceTransformer
    _RAG_LIBS_AVAILABLE = True
except ImportError:
    chromadb = None
    SentenceTransformer = None
    _RAG_LIBS_AVAILABLE = False

    # Fallback placeholders that are safe to use as base classes
    Documents = TypeVar("Documents")

    class Embeddings(list):
        pass

    class EmbeddingFunction(Generic[Documents]):
        """Fallback base class when chromadb is not installed."""

        def __call__(self, input):
            raise NotImplementedError(
                "RAG libraries are not installed."
            )
import os
from pathlib import Path


import pandas as pd




BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = BASE_DIR / "models" / "vector_db"

COLLECTION_NAME = "skg_content"


# ============================================================
# EMBEDDING MODEL
# ============================================================
_embedder = None


def get_embedder():
    """Lazy-load the sentence transformer model."""
    global _embedder
    if not _RAG_LIBS_AVAILABLE:
        return None
    if _embedder is None:
        _embedder = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu",
        )
    return _embedder


class SentenceTransformerEF(EmbeddingFunction[Documents]):
    """
    ChromaDB-compatible embedding function using sentence-transformers.

    ChromaDB 1.5+ requires:
        - a CLASS that inherits from EmbeddingFunction
        - __call__(self, input) with the parameter named exactly 'input'
    """

    def __call__(self, input: Documents) -> Embeddings:
        embedder = get_embedder()
        return embedder.encode(
            list(input),
            show_progress_bar=False,
        ).tolist()


# ============================================================
# DOCUMENT BUILDER
# ============================================================
def _build_documents():
    """
    Build all documents to index into the vector store.

    Each document = one chunk of text + metadata.
    """
    documents = []
    metadatas = []
    ids = []

    # ---- 1. Learning Content (richest source) ----
    lc_path = DATA_DIR / "learning_content_FINAL.csv"
    if lc_path.exists():
        lc = pd.read_csv(lc_path)

        for _, row in lc.iterrows():
            concept_id = int(row["concept_id"])
            concept_name = str(row["concept_name"])
            subject_id = int(row["subject_id"])
            level = str(row["level"])

            # Overview
            if pd.notna(row.get("learning_objective")):
                documents.append(f"{concept_name}: {row['learning_objective']}")
                metadatas.append({
                    "type": "learning_objective",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_obj_{concept_id}")

            # Explanation
            if pd.notna(row.get("explanation")):
                documents.append(f"{concept_name} — Explanation: {row['explanation']}")
                metadatas.append({
                    "type": "explanation",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_exp_{concept_id}")

            # Key points
            if pd.notna(row.get("key_points")):
                documents.append(f"{concept_name} — Key Points: {row['key_points']}")
                metadatas.append({
                    "type": "key_points",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_kp_{concept_id}")

            # Examples
            if pd.notna(row.get("example")):
                documents.append(f"{concept_name} — Example: {row['example']}")
                metadatas.append({
                    "type": "example",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_ex_{concept_id}")

            # Why it matters
            if pd.notna(row.get("why_it_matters")):
                documents.append(f"{concept_name} — Why it matters: {row['why_it_matters']}")
                metadatas.append({
                    "type": "why_it_matters",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_wim_{concept_id}")

            # Common mistakes
            if pd.notna(row.get("common_mistakes")):
                documents.append(f"{concept_name} — Common Mistakes: {row['common_mistakes']}")
                metadatas.append({
                    "type": "common_mistakes",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_cm_{concept_id}")

            # Study tips
            if pd.notna(row.get("study_tips")):
                documents.append(f"{concept_name} — Study Tips: {row['study_tips']}")
                metadatas.append({
                    "type": "study_tips",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_st_{concept_id}")

            # Step by step
            if pd.notna(row.get("step_by_step")):
                documents.append(f"{concept_name} — Step by Step: {row['step_by_step']}")
                metadatas.append({
                    "type": "step_by_step",
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "subject_id": subject_id,
                    "level": level,
                })
                ids.append(f"lc_sbs_{concept_id}")

    # ---- 2. Question Bank (each question as a doc) ----
    qb_path = DATA_DIR / "final_question_bank_270.csv"
    if qb_path.exists():
        qb = pd.read_csv(qb_path)

        for _, row in qb.iterrows():
            concept_name = str(row["concept_name"])
            question_type = str(row["question_type"])

            # Options text
            options_text = (
                f"A) {row['option_a']}\n"
                f"B) {row['option_b']}\n"
                f"C) {row['option_c']}\n"
                f"D) {row['option_d']}"
            )

            doc = (
                f"Question on {concept_name} ({question_type}): "
                f"{row['question_text']}\n"
                f"Options:\n{options_text}\n"
                f"Correct answer: {row['correct_answer']}"
            )

            documents.append(doc)
            metadatas.append({
                "type": "question",
                "concept_id": int(row["concept_id"]),
                "concept_name": concept_name,
                "subject_id": int(row["subject_id"]),
                "difficulty": str(row["difficulty"]),
                "question_type": question_type,
            })
            ids.append(f"q_{row['question_id']}")

    # ---- 3. Concepts (with prerequisites) ----
    concepts_path = DATA_DIR / "concepts_final.csv"
    if concepts_path.exists():
        concepts = pd.read_csv(concepts_path)

        for _, row in concepts.iterrows():
            prereq = row.get("prerequisites")
            prereq_text = (
                "no prerequisites" if pd.isna(prereq) else f"prerequisites: {prereq}"
            )
            doc = (
                f"{row['concept_name']} "
                f"({row['difficulty']}) — {prereq_text}"
            )
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


# ============================================================
# VECTOR STORE BUILDER
# ============================================================
def build_vector_store(verbose=True):
    """
    Build (or rebuild) the ChromaDB vector store from
    the project's content.
    """
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

    # Delete existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    ef = SentenceTransformerEF()

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    documents, metadatas, ids = _build_documents()

    if verbose:
        print(f"📚 Building vector store with {len(documents)} documents...")

    # Insert in batches
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            ids=ids[i:i + batch_size],
        )

    if verbose:
        print(f"✅ Vector store built: {collection.count()} documents")
        print(f"   📁 Path: {VECTOR_DB_DIR}")

    return collection


# ============================================================
# RETRIEVER
# ============================================================
_client = None
_collection = None


def get_collection():
    """Get the existing collection (lazy)."""
    global _client, _collection

    if _collection is None:
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

        ef = SentenceTransformerEF()

        try:
            _collection = _client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=ef,
            )
        except Exception:
            return None

    return _collection


def retrieve(query, top_k=5, filter_type=None):
    """
    Retrieve the most relevant documents for a query.

    Args:
        query: str — the search query
        top_k: int — number of documents
        filter_type: optional — filter by metadata type
                     ("explanation", "example", "question", ...)

    Returns:
        List of dicts: {text, metadata, distance}
    """
    collection = get_collection()
    if collection is None:
        return []

    where = {"type": filter_type} if filter_type else None

    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )
    except Exception:
        return []

    output = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for doc, meta, dist in zip(docs, metas, dists):
            output.append({
                "text": doc,
                "metadata": meta,
                "distance": float(dist),
            })

    return output


def vector_store_exists():
    """Check if the vector store exists on disk."""
    return VECTOR_DB_DIR.exists() and any(VECTOR_DB_DIR.iterdir()) if VECTOR_DB_DIR.exists() else False
