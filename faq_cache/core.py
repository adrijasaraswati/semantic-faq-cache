import json
import re
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
ROOT = Path(__file__).resolve().parents[1]
NEGATION = re.compile(r"\b(not|no|never|nahi|nahin|mat|don't|cannot|can't)\b|नहीं|मत", re.I)
PRIVATE = re.compile(r"\b\d{4,}\b|[\w.+-]+@[\w.-]+\.[a-z]+|\b(order\s*(id|number|#)|my name|mera naam|customer name|my address is|my phone|account number)\b", re.I)


def safe_to_cache(question, answer):
    # Fail closed: learned answers require the provider's explicit public scope too.
    return not PRIVATE.search(question + " " + answer)


def negation_mismatch(a, b):
    return bool(NEGATION.search(a)) != bool(NEGATION.search(b))


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL)

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype("float32")


@dataclass
class Entry:
    id: str
    question: str
    answer: str
    expires_at: float


class Cache:
    """Process-local FAISS index. Lock covers concurrent lookup and insertion."""
    def __init__(self, embedder, ttl_days=7, seed=True, clock=time.time):
        self.embedder, self.ttl_days, self.clock = embedder, ttl_days, clock
        self.entries = []
        self.index = None
        self.lock = threading.RLock()
        if seed:
            for row in json.loads((ROOT / "data/faqs.json").read_text(encoding="utf-8")):
                self.add(row["id"], row["question"], row["answer"])

    def add(self, id, question, answer, vector=None):
        if not safe_to_cache(question, answer):
            return False
        vector = self.embedder.encode([question]) if vector is None else vector
        with self.lock:
            if self.index is None:
                self.index = faiss.IndexFlatIP(vector.shape[1])
            self.index.add(vector)
            self.entries.append(Entry(id, question, answer, self.clock() + self.ttl_days * 86400))
        return True

    def lookup(self, question, threshold, vector=None):
        if PRIVATE.search(question):
            return None, 0.0, "private"
        vector = self.embedder.encode([question]) if vector is None else vector
        with self.lock:
            if self.index is None:
                return None, 0.0, "empty"
            scores, ids = self.index.search(vector, len(self.entries))
            best = float(scores[0][0])
            reason = "below_threshold"
            for score, idx in zip(scores[0], ids[0]):
                if score < threshold:
                    break
                entry = self.entries[int(idx)]
                if entry.expires_at <= self.clock():
                    reason = "expired"
                    continue
                if negation_mismatch(question, entry.question):
                    reason = "negation_guard"
                    continue
                return entry, float(score), "hit"
            return None, best, reason


class Bot:
    def __init__(self, cache, llm, threshold=.75, log_path="runtime/requests.jsonl"):
        self.cache, self.llm, self.threshold = cache, llm, threshold
        self.log_path = Path(log_path)

    def ask(self, question):
        start = time.perf_counter()
        entry, score, reason = self.cache.lookup(question, self.threshold)
        tokens = 0
        if entry:
            answer = entry.answer
        else:
            answer, tokens, public = self.llm.generate(question)
            # Reject arbitrary generated text unless explicitly marked public.
            if public and not NEGATION.search(question):
                self.cache.add("learned", question, answer)
        result = {"answer": answer, "hit": entry is not None, "similarity": score,
                  "reason": reason, "latency_ms": (time.perf_counter()-start)*1000,
                  "tokens_used": tokens}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Private inputs and generated responses never enter logs.
        event = {k:v for k,v in result.items() if k != "answer"}
        event["question"] = "[REDACTED]" if PRIVATE.search(question) else question
        event["timestamp"] = time.time()
        with self.cache.lock, self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False)+"\n")
        return result
