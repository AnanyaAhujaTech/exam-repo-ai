import requests
import hashlib
import json
import re
import os
import time
import copy
from typing import List, Dict, Tuple


# ========================= CONFIG =========================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

CACHE_FILE = "cache/ai_cache.json"
os.makedirs("cache", exist_ok=True)

MAX_SUBPARTS_PER_BATCH = 4


# ======================= CACHING LAYER =====================

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# ===================== HELPERS =====================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def sha256_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode()).hexdigest()


# ======================= OLLAMA =======================

def ollama_generate(prompt: str) -> Tuple[str, float]:

    start = time.time()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()

        latency = time.time() - start

        return response.json().get("response", "").strip(), latency

    except Exception as e:
        return "", 0.0


# ================== PROMPTS ==================

def build_question_prompt(question_text: str) -> str:
    return f"""
Extract:
- 3–5 technical keywords
- confidence per keyword
- 1–3 syllabus topics

Return JSON only:

{{
  "question": {{
    "tags": [],
    "confidence": {{}},
    "syllabus_topics": []
  }}
}}

Question:
{question_text}
"""


def build_subpart_prompt(question_text: str, subparts: List[Dict]) -> str:

    prompt = f"""
Analyze subparts.

Return JSON:

{{
  "subparts": {{
    "a": {{
      "tags": [],
      "confidence": {{}},
      "syllabus_topics": []
    }}
  }}
}}

Context:
{question_text}

"""

    for sp in subparts:
        prompt += f"{sp['subpart_id']}) {sp['text']}\n"

    return prompt


# ====================== MAIN ======================

def enrich_exam_json(exam_json: dict) -> Tuple[dict, dict]:

    cache = load_cache()

    enriched = copy.deepcopy(exam_json)  # 🔥 FIXED

    total_llm_calls = 0
    total_llm_time = 0.0

    for question in enriched.get("questions", []):

        q_text = question.get("question_text", "")
        q_hash = sha256_hash(q_text)

        question["question_hash"] = q_hash

        subparts = question.get("subparts", [])

        # -------- QUESTION --------

        if q_hash in cache:
            question.update(cache[q_hash])

        else:
            prompt = build_question_prompt(q_text)
            raw_output, latency = ollama_generate(prompt)

            total_llm_calls += 1
            total_llm_time += latency

            try:
                result = json.loads(raw_output)
                q_data = result.get("question", {})
            except:
                q_data = {}

            meta = {
                "ai_tags": q_data.get("tags", []),
                "ai_confidence": q_data.get("confidence", {}),
                "syllabus_topics": q_data.get("syllabus_topics", [])
            }

            question.update(meta)
            cache[q_hash] = meta

        # -------- SUBPARTS --------

        uncached = []

        for sp in subparts:

            sp_text = sp.get("text", "")
            sp_hash = sha256_hash(sp_text)

            sp["subquestion_hash"] = sp_hash

            if sp_hash in cache:
                sp.update(cache[sp_hash])
            else:
                uncached.append(sp)

        for i in range(0, len(uncached), MAX_SUBPARTS_PER_BATCH):

            batch = uncached[i:i + MAX_SUBPARTS_PER_BATCH]

            prompt = build_subpart_prompt(q_text, batch)
            raw_output, latency = ollama_generate(prompt)

            total_llm_calls += 1
            total_llm_time += latency

            try:
                result = json.loads(raw_output)
                sub_res = result.get("subparts", {})
            except:
                sub_res = {}

            for sp in batch:

                sp_id = sp.get("subpart_id")
                sp_hash = sp.get("subquestion_hash")

                data = sub_res.get(sp_id, {})

                meta = {
                    "ai_tags": data.get("tags", []),
                    "ai_confidence": data.get("confidence", {}),
                    "syllabus_topics": data.get("syllabus_topics", [])
                }

                sp.update(meta)
                cache[sp_hash] = meta

    save_cache(cache)

    metrics = {
        "llm_calls": total_llm_calls,
        "total_time": round(total_llm_time, 3)
    }

    return enriched, metrics
