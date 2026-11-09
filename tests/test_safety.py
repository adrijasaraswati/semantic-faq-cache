import json
import numpy as np
import pytest
from faq_cache.core import Cache, Bot, ROOT, negation_mismatch, safe_to_cache


class FakeEmbedder:
    def encode(self, texts):
        return np.array([[1.,0.] for _ in texts], dtype="float32")


@pytest.mark.parametrize("a,b", [("refund","no refund"),("refund milega","refund nahi milega"),("cancel","do not cancel")])
def test_negation(a,b):
    assert negation_mismatch(a,b)


def test_ttl():
    now=[0.]
    cache=Cache(FakeEmbedder(),ttl_days=1,seed=False,clock=lambda:now[0])
    cache.add("a","refund","public answer")
    assert cache.lookup("refund",.9)[0]
    now[0]=86400
    assert cache.lookup("refund",.9)[2]=="expired"


@pytest.mark.parametrize("q,a", [("order ID 123456","shipped"),("hello","My name is John"),("hello","a@example.com")])
def test_private(q,a):
    assert not safe_to_cache(q,a)


def test_miss_hit_tokens_and_log(tmp_path):
    class LLM:
        calls=0
        def generate(self,q):
            self.calls+=1
            return "public answer",42,True
    llm=LLM()
    bot=Bot(Cache(FakeEmbedder(),seed=False),llm,log_path=tmp_path/"events.jsonl")
    assert bot.ask("refund time")["tokens_used"]==42
    assert bot.ask("refund timeline")["hit"]
    assert llm.calls==1
    assert len((tmp_path/"events.jsonl").read_text().splitlines())==2


def test_dataset_contract():
    faqs=json.loads((ROOT/"data/faqs.json").read_text(encoding="utf-8"))
    cases=json.loads((ROOT/"data/questions.json").read_text(encoding="utf-8"))
    assert len(faqs)==30 and len(cases)==100
    assert sum(c["expected"] is None for c in cases)==40
    assert len({c["question"] for c in cases})==100
    assert all(c["expected"] in {f["id"] for f in faqs} for c in cases if c["expected"])


def test_guard_skips_high_similarity():
    cache=Cache(FakeEmbedder(),seed=False)
    cache.add("a","refund","public answer")
    assert cache.lookup("no refund",.9)[2]=="negation_guard"


def test_private_log_redacted(tmp_path):
    class LLM:
        def generate(self,q): return "private result",1,False
    path=tmp_path/"log"
    Bot(Cache(FakeEmbedder(),seed=False),LLM(),log_path=path).ask("order ID 123456")
    assert "123456" not in path.read_text()
