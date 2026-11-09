import json
import os
import requests
from .core import ROOT


class Ollama:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")

    def generate(self, question):
        facts = json.loads((ROOT / "data/faqs.json").read_text(encoding="utf-8"))
        # Structured output references approved text; never promote free-form model output
        # into a shared cache. Unknown questions get a human-support fallback.
        prompt = ("Classify this e-commerce question against the approved FAQ list. "
                  "Return JSON with faq_id equal to the matching id, or null if unknown, "
                  "personal, negated, or outside these policies. Do not invent policy.\n"
                  + json.dumps(facts) + "\nQuestion: " + question)
        r = requests.post(self.url + "/api/generate", json={"model":self.model,
            "prompt":prompt,"format":"json","stream":False,
            "options":{"temperature":0,"num_predict":64}}, timeout=120)
        r.raise_for_status()
        body = r.json()
        try:
            id = json.loads(body["response"]).get("faq_id")
        except (ValueError, AttributeError):
            id = None
        match = next((f for f in facts if f["id"] == id), None)
        tokens = body.get("prompt_eval_count", 0) + body.get("eval_count", 0)
        return (match["answer"], tokens, True) if match else (
            "I cannot confirm that from our published policies. Please contact support.", tokens, False)
