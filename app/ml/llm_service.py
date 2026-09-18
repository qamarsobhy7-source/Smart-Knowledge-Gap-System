"""
LLM Service — Gemini + RAG Assistant (new google-genai SDK).

Uses the new google-genai SDK with gemini-3.6-flash model.
Requires GEMINI_API_KEY environment variable.
"""

import os

from .rag_engine import retrieve


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

_client = None
_types = None

SYSTEM_INSTRUCTION = (
    "You are a helpful AI study assistant for the "
    "Smart Knowledge Gap & Personalized Learning System. "
    "You help students understand concepts in Mathematics, "
    "Physics, and Computer Science by explaining them clearly.\n\n"
    "IMPORTANT RULES:\n"
    "1. ALWAYS answer using the provided context.\n"
    "2. If the context does not contain the answer, say so honestly.\n"
    "3. NEVER invent facts, formulas, or definitions.\n"
    "4. Keep answers concise (3-5 sentences) unless asked for detail.\n"
    "5. Use examples when helpful.\n"
    "6. Be encouraging and supportive.\n"
    "7. If the student made a mistake, explain WHY it is wrong.\n\n"
    "Student subject: {subject_name}\n"
    "Student level: {level}"
)


def _load_client():
    """Lazy-load the new google-genai client."""
    global _client, _types

    if _client is not None:
        return _client

    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    _client = genai.Client(api_key=GEMINI_API_KEY)
    _types = types
    return _client


def is_available():
    """Return True if the LLM service is configured."""
    return bool(GEMINI_API_KEY) and _load_client() is not None


def build_context(retrieved_docs):
    """Format retrieved documents into a context block."""
    if not retrieved_docs:
        return "No relevant context found."

    parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        doc_type = doc["metadata"].get("type", "content")
        concept = doc["metadata"].get("concept_name", "")
        text = doc["text"]
        parts.append(f"[{i}] ({doc_type} - {concept})\n{text}\n")

    return "\n".join(parts)


# ============================================================
# FALLBACK MODEL STRATEGY
# ============================================================
FALLBACK_MODELS = [
    "gemini-flash-latest",        # Always points to the newest stable flash
    "gemini-3.8-flash",           # Latest
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",      # Fast fallback
    "gemini-flash-lite-latest",   # Lite latest
]


def _generate_with_fallback(prompt, max_retries=2):
    """
    Try to generate content, trying multiple models in order.

    If a model is overloaded (503) or unavailable (404), tries the
    next model in the list. Also retries with delay on 503.
    """
    import time

    last_error = None

    for model_name in FALLBACK_MODELS:
        for attempt in range(max_retries):
            try:
                response = _client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=_types.GenerateContentConfig(
                        temperature=0.4,
                        top_p=0.95,
                        max_output_tokens=800,
                    ),
                )
                return response
            except Exception as exc:
                err_str = str(exc)
                last_error = exc

                # Model not found → try next model
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break

                # Server overloaded → short retry
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(2 + attempt * 2)
                    continue

                # Other errors → try next model
                break

    # All models failed
    raise last_error if last_error else RuntimeError("All fallback models failed.")


def chat(
    message,
    conversation_history=None,
    subject_name="",
    level="",
    top_k=5,
):
    """Send a message to the assistant using RAG + Gemini."""
    if not is_available():
        return {
            "answer": None,
            "sources": [],
            "error": "LLM not configured. Set GEMINI_API_KEY.",
        }

    # 1. Retrieve relevant documents
    retrieved = retrieve(message, top_k=top_k)

    # 2. Build context
    context = build_context(retrieved)

    # 3. Build the prompt
    system = SYSTEM_INSTRUCTION.format(
        subject_name=subject_name or "general studies",
        level=level or "beginner",
    )

    history_text = ""
    if conversation_history:
        for turn in conversation_history[-4:]:
            role = "Student" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "")
            history_text += f"{role}: {content}\n"

    prompt = (
        f"{system}\n\n"
        f"=== CONTEXT FROM THE LEARNING SYSTEM ===\n"
        f"{context}\n"
        f"=== END OF CONTEXT ===\n\n"
        f"{history_text}Student: {message}\n\nAssistant:"
    )

    # 4. Call the model (with fallback)
    try:
        response = _generate_with_fallback(prompt)
        answer = (response.text or "").strip()
    except Exception as exc:
        return {
            "answer": None,
            "sources": retrieved,
            "error": f"LLM call failed: {exc}",
        }

    return {
        "answer": answer,
        "sources": retrieved,
        "error": None,
    }


def quick_explanation(concept_name, mastery, gap_level):
    """Generate a short explanation for struggling students."""
    if not is_available():
        return None

    prompt = (
        f"A student just scored {mastery:.1f}% on the concept "
        f"\"{concept_name}\" (status: {gap_level}).\n\n"
        "Write a short, encouraging 2-sentence explanation of:\n"
        "1. What this concept is about\n"
        "2. What they should focus on to improve\n\n"
        "Keep it simple and motivating."
    )

    try:
        response = _generate_with_fallback(prompt)
        return (response.text or "").strip()
    except Exception:
        return None
