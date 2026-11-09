"""Frozen-cache retrieval sweep; optional real end-to-end Ollama benchmark."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import statistics
import time
from dataclasses import asdict
from .core import Cache, Embedder, MODEL, ROOT, Bot, negation_mismatch
from .llm import Ollama


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="Run 100 uncached + cached Ollama requests (can take minutes)")
    args = parser.parse_args()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    cases = json.loads((ROOT/"data/questions.json").read_text(encoding="utf-8"))
    embedder = Embedder()
    cache = Cache(embedder)
    embedder.encode(["warm up"])
    # Each query is embedded individually; latency includes embedding and FAISS.
    timings, vectors = [], []
    for row in cases:
        start = time.perf_counter()
        vectors.append(embedder.encode([row["question"]]))
        timings.append((time.perf_counter()-start)*1000)
    sweep, predictions = [], []
    for threshold in [.75,.80,.85,.90,.95]:
        hits = false_hits = 0
        latencies = []
        for i, row in enumerate(cases):
            start = time.perf_counter()
            entry, score, reason = cache.lookup(row["question"], threshold, vectors[i])
            latency = timings[i] + (time.perf_counter()-start)*1000
            latencies.append(latency)
            hits += bool(entry)
            wrong = bool(entry and entry.id != row["expected"])
            false_hits += wrong
            predictions.append({**row,"threshold":threshold,"predicted":entry.id if entry else None,
                "similarity":score,"reason":reason,"false_hit":wrong,"latency_ms":latency})
        sweep.append(dict(threshold=threshold,hits=hits,hit_rate_pct=hits,
            false_hits=false_hits,llm_calls=100-hits,mean_lookup_ms=statistics.mean(latencies)))
    eligible = [r for r in sweep if r["false_hits"]==0]
    chosen = max(eligible, key=lambda r:(r["hits"], r["threshold"])) if eligible else None
    # Guard examples are explicit contrast pairs, not claimed to be universally solved.
    pairs = [("I want a refund", "I do not want a refund"),
             ("Refund chahiye", "Refund nahi chahiye"),
             ("Cancel the order", "Do not cancel the order")]
    guards = [dict(cached=a,query=b,blocked=negation_mismatch(a,b),
                   similarity=float(embedder.encode([a])[0] @ embedder.encode([b])[0])) for a,b in pairs]
    report = dict(model=MODEL,python=platform.python_version(),platform=platform.platform(),
        packages={p:importlib.metadata.version(p) for p in ["sentence-transformers","faiss-cpu","torch","numpy"]},
        dataset_sha256=hashlib.sha256((ROOT/"data/questions.json").read_bytes()).hexdigest(),
        protocol="100 individual warm CPU embeddings; fixed 30 FAQ cache; no test-time writes; retrieval only",
        sweep=sweep,chosen=chosen,negation_examples=guards)
    if args.llm and chosen:
        llm = Ollama()
        baseline, cached = [], []
        for row in cases:
            start=time.perf_counter()
            llm.generate(row["question"])
            baseline.append((time.perf_counter()-start)*1000)
        # Freeze writes so this measures exactly the same cache population as the sweep.
        class FrozenCache(Cache):
            def add(self,*a,**kw):
                return super().add(*a,**kw) if not getattr(self,"frozen",False) else False
        fc=FrozenCache(embedder)
        fc.frozen=True
        bot=Bot(fc,llm,chosen["threshold"],"runtime/benchmark.jsonl")
        for row in cases:
            cached.append(bot.ask(row["question"])["latency_ms"])
        report["end_to_end"] = dict(baseline_ms=statistics.mean(baseline),cached_ms=statistics.mean(cached),
            reduction_pct=100*(1-statistics.mean(cached)/statistics.mean(baseline)))
    (out/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    (out/"predictions.json").write_text(json.dumps(predictions,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    table="| Threshold | Hit rate | False hits | LLM calls needed | Mean embed + lookup ms |\n|---|---|---|---|---|\n"
    table += "\n".join(f'| {r["threshold"]:.2f} | {r["hits"]}% | {r["false_hits"]} | {r["llm_calls"]} | {r["mean_lookup_ms"]:.2f} |' for r in sweep)
    (out/"thresholds.md").write_text(table+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
