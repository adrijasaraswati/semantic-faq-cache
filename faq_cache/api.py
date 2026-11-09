import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from requests import RequestException
from .core import Bot, Cache, Embedder
from .llm import Ollama


@asynccontextmanager
async def lifespan(app):
    app.state.bot = Bot(Cache(Embedder(), ttl_days=float(os.getenv("CACHE_TTL_DAYS", "7"))),
                        Ollama(), threshold=float(os.getenv("CACHE_THRESHOLD", ".75")))
    yield


app = FastAPI(title="Semantic FAQ Cache", lifespan=lifespan)


class Question(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


@app.get("/health")
def health():
    return {"status":"ok"}


@app.post("/ask")
def ask(body: Question):
    try:
        return app.state.bot.ask(body.question)
    except RequestException as exc:
        raise HTTPException(503, "LLM unavailable. Start Ollama and pull the configured model.") from exc


@app.get("/", response_class=HTMLResponse)
def home():
    return '''<!doctype html><html><meta name="viewport" content="width=device-width"><title>Semantic FAQ Cache</title>
    <style>body{font:18px system-ui;max-width:800px;margin:10vh auto;padding:24px;background:#101c2d;color:#e8f0fc}input,button{font:inherit;padding:14px;border-radius:8px}input{width:65%}pre{white-space:pre-wrap;line-height:1.7}small{color:#99bbdd}</style>
    <small>PYTHON · MULTILINGUAL EMBEDDINGS · FAISS · OLLAMA</small><h1>Answers that remember meaning.</h1>
    <p>Ask about our demo store's returns, shipping, or payments.</p><form id="f"><input id="q" required placeholder="How long does a refund take?"><button>Ask</button></form><pre id="out" aria-live="polite"></pre>
    <script>f.onsubmit=async e=>{e.preventDefault();out.textContent='Looking up…';try{let r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q.value})});let d=await r.json();out.textContent=r.ok?d.answer+'\\n\\n'+(d.hit?'CACHE HIT':'LLM MISS')+' · '+d.latency_ms.toFixed(1)+' ms · similarity '+d.similarity.toFixed(3)+' · '+d.tokens_used+' tokens':d.detail}catch(e){out.textContent='Connection failed'}}</script></html>'''
