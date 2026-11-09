"""Cold-cache three-question demo against a real local Ollama model."""
import json
from .core import Bot, Cache, Embedder, ROOT
from .llm import Ollama


def main():
    metrics=ROOT/"results/metrics.json"
    threshold=.75
    if metrics.exists():
        chosen=json.loads(metrics.read_text()).get("chosen")
        if chosen: threshold=chosen["threshold"]
    bot=Bot(Cache(Embedder(), seed=False), Ollama(), threshold)
    rows=[]
    for q in ["How long does a refund take?", "How long will a refund take?", "How long does the refund take?"]:
        result=bot.ask(q)
        rows.append(dict(question=q,**result))
        print(json.dumps(rows[-1],ensure_ascii=False,indent=2))
    if [r["hit"] for r in rows] != [False,True,True]:
        raise RuntimeError("Demo did not yield miss/hit/hit. Inspect actual results; do not claim success.")
    (ROOT/"results/demo.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")


if __name__=="__main__": main()
