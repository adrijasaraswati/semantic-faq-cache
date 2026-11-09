"""Publish measured evidence into README and render a video from actual demo events."""
import json
import textwrap
from pathlib import Path

root=Path(__file__).resolve().parents[1]
m=json.loads((root/"results/metrics.json").read_text())
c=m["chosen"]
if c is None:
    raise RuntimeError("No zero-false-hit operating point; do not publish a recommended threshold")
summary=f'Cache hit rate {c["hits"]}% on 100 test questions at threshold {c["threshold"]:.2f} with {c["false_hits"]} false hits; LLM calls down {c["hits"]}% (100 to {c["llm_calls"]}).'
if "end_to_end" in m:
    e=m["end_to_end"]
    summary=f'Cache hit rate {c["hits"]}% on 100 test questions at threshold {c["threshold"]:.2f} with {c["false_hits"]} false hits; LLM calls down {c["hits"]}%; average latency down from {e["baseline_ms"]:.1f} ms to {e["cached_ms"]:.1f} ms.'
block="<!-- RESULTS START -->\n## Measured results\n\n"+summary+"\n\n"+(root/"results/thresholds.md").read_text()+f'\nWarm embed + lookup mean at the selected threshold: {c["mean_lookup_ms"]:.2f} ms. '
block+="The optional end-to-end run uses real local Ollama calls, not sleeps or simulated tokens. Hardware and package metadata are in `results/metrics.json`.\n\n"
block+="**Selection rule:** maximum hit rate subject to zero observed false hits; choose the higher threshold on ties. These are calibration-set measurements.\n\n"
block+="[Watch the measured three-question demo](results/demo.mp4). This video is rendered from `results/demo.json`; it is an event replay, not a browser screen recording.\n<!-- RESULTS END -->"
readme=root/"README.md"
text=readme.read_text(encoding="utf-8")
if "<!-- RESULTS START -->" in text:
    start=text.index("<!-- RESULTS START -->")
    end=text.index("<!-- RESULTS END -->")+len("<!-- RESULTS END -->")
    text=text[:start]+block+text[end:]
else:
    text=text.replace("## Run locally",block+"\n\n## Run locally")
readme.write_text(text,encoding="utf-8")
(root/".env.example").write_text(f'CACHE_THRESHOLD={c["threshold"]}\nCACHE_TTL_DAYS=7\nOLLAMA_MODEL=qwen2.5:0.5b\nOLLAMA_URL=http://localhost:11434\n')
demo_path=root/"results/demo.json"
if demo_path.exists():
    from PIL import Image, ImageDraw, ImageFont
    import imageio.v2 as imageio
    import numpy as np
    rows=json.loads(demo_path.read_text(encoding="utf-8"))
    try: font=ImageFont.truetype("DejaVuSans.ttf",28)
    except OSError: font=ImageFont.load_default(size=28)
    with imageio.get_writer(str(root/"results/demo.mp4"),fps=2,codec="libx264") as writer:
        for i,row in enumerate(rows):
            frame=Image.new("RGB",(1280,720),"#101c2d")
            d=ImageDraw.Draw(frame)
            lines=["SEMANTIC FAQ CACHE", "Real local Ollama + multilingual FAISS", "",
                f'Question {i+1} / 3: '+row["question"],"",
                ("CACHE HIT" if row["hit"] else "CACHE MISS -> OLLAMA"),
                f'{row["latency_ms"]:.1f} ms | similarity {row["similarity"]:.3f} | {row["tokens_used"]} tokens',""]
            lines+=textwrap.wrap(row["answer"],70)
            lines += ["", "Measured event replay - see results/demo.json"]
            for y,line in enumerate(lines): d.text((50,40+y*43),line,font=font,fill="#e8f0fc")
            for _ in range(12): writer.append_data(np.asarray(frame))
