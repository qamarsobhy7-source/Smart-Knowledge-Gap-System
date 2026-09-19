"""LLM Service - Groq + RAG Assistant."""

import json as _json
import os
import time as _time

import requests

from .rag_engine import retrieve


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

API_URL = "https://api.groq.com/openai/v1/chat/completions"

FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
]

SYSTEM_INSTRUCTION = (
    "You are a helpful AI study assistant for the "
    "Smart Knowledge Gap & Personalized Learning System. "
    "You help students understand concepts in Mathematics, "
    "Physics, and Computer Science clearly.\n\n"
    "RULES:\n"
    "1. ALWAYS answer using the provided context.\n"
    "2. If the context does not contain the answer, say so.\n"
    "3. NEVER invent facts, formulas, or definitions.\n"
    "4. Keep answers concise (3-5 sentences) unless asked for detail.\n"
    "5. Use examples when helpful.\n"
    "6. Be encouraging and supportive.\n\n"
    "Student subject: {subject_name}\n"
    "Student level: {level}"
)


def is_available():
    return bool(GROQ_API_KEY)


def _call_groq(prompt, max_retries=2, temperature=0.4, max_tokens=800):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    last_error = None

    for model in FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    API_URL, headers=headers, json=payload, timeout=45
                )

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        return ""
                    return str(choices[0].get("message", {}).get("content", "")).strip()

                if response.status_code == 404:
                    last_error = RuntimeError(f"{model}: 404")
                    break

                if response.status_code == 429:
                    last_error = RuntimeError(f"{model}: 429 Rate Limit")
                    _time.sleep(3 + attempt * 3)
                    continue

                if response.status_code >= 500:
                    last_error = RuntimeError(f"{model}: {response.status_code}")
                    _time.sleep(2)
                    continue

                last_error = RuntimeError(
                    f"{model}: {response.status_code} - {response.text[:200]}"
                )
                break

            except requests.exceptions.Timeout:
                last_error = RuntimeError(f"{model}: Timeout")
                continue
            except Exception as exc:
                last_error = exc
                break

    raise last_error if last_error else RuntimeError("All models failed.")


def build_context(retrieved_docs):
    if not retrieved_docs:
        return "No relevant context found."
    parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        doc_type = doc["metadata"].get("type", "content")
        concept = doc["metadata"].get("concept_name", "")
        doc_text = doc.get("text", "")
        parts.append(f"[{i}] ({doc_type} - {concept})\n{doc_text}\n")
    return "\n".join(parts)


def chat(message, conversation_history=None, subject_name="", level="", top_k=5):
    if not is_available():
        return {"answer": None, "sources": [], "error": "LLM not configured."}

    retrieved = retrieve(message, top_k=top_k)
    context = build_context(retrieved)

    system = SYSTEM_INSTRUCTION.format(
        subject_name=subject_name or "general studies",
        level=level or "beginner",
    )

    history_text = ""
    if conversation_history:
        for turn in conversation_history[-4:]:
            role = "Student" if turn.get("role") == "user" else "Assistant"
            history_text += f"{role}: {turn.get(chr(39)+chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(110)+chr(116)+chr(39), chr(39)+chr(39))}\n"

    prompt = (
        f"{system}\n\n"
        f"=== CONTEXT ===\n{context}\n=== END CONTEXT ===\n\n"
        f"{history_text}Student: {message}\n\nAssistant:"
    )

    try:
        answer = _call_groq(prompt)
    except Exception as exc:
        return {"answer": None, "sources": retrieved, "error": f"LLM call failed: {exc}"}

    return {"answer": answer, "sources": retrieved, "error": None}


def evaluate_feynman_explanation(concept_name, explanation, learning_objective="", key_points="", common_mistakes=""):
    if not is_available():
        return {"score": 0.0, "feedback": "AI evaluation is not available.", "strengths": "", "gaps": "", "suggestions": "", "error": "LLM not configured."}

    retrieved = retrieve(f"{concept_name} explanation {explanation[:200]}", top_k=4)
    context = "\n\n".join(doc["text"] for doc in retrieved) if retrieved else ""

    prompt = (
        f"You are an experienced teacher evaluating a student explanation of: \"{concept_name}\"\n\n"
        f"=== REFERENCE ===\n"
        f"Learning Objective: {learning_objective}\n"
        f"Key Points: {key_points}\n"
        f"Common Mistakes: {common_mistakes}\n"
        f"Context: {context}\n"
        f"=== END REFERENCE ===\n\n"
        f"=== STUDENT EXPLANATION ===\n{explanation}\n=== END ===\n\n"
        f"Evaluate on:\n"
        f"1. Conceptual Accuracy (0-40)\n"
        f"2. Clarity (0-30)\n"
        f"3. Completeness (0-30)\n\n"
        f"Respond with JSON ONLY (no markdown):\n"
        f"{{\n"
        f"  \"score\": <0-100>,\n"
        f"  \"feedback\": \"<2-3 sentences>\",\n"
        f"  \"strengths\": \"<what got right>\",\n"
        f"  \"gaps\": \"<what missing>\",\n"
        f"  \"suggestions\": \"<2-3 suggestions>\"\n"
        f"}}\n\n"
        f"Be encouraging."
    )

    try:
        raw = _call_groq(prompt, temperature=0.2, max_tokens=1000)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = _json.loads(raw)
        return {
            "score": float(result.get("score", 0)),
            "feedback": str(result.get("feedback", "")),
            "strengths": str(result.get("strengths", "")),
            "gaps": str(result.get("gaps", "")),
            "suggestions": str(result.get("suggestions", "")),
            "error": None,
        }
    except Exception as exc:
        return {"score": 0.0, "feedback": "", "strengths": "", "gaps": "", "suggestions": "", "error": f"Eval failed: {exc}"}
