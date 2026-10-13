"""Evaluation harness: run systems on benchmark conversations and compute metrics."""
from __future__ import annotations

import sys, time, copy, json, random
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np

import benchmark
import templates_dev as DEV
import templates_test as TEST
from memchat.baselines import PlainRAG, SlidingWindow, Stateless
from memchat.extract import extract_facts
from memchat.memory import MemConfig, MemoryChatbot

DEV_SEEDS = list(range(1000, 1030))
TEST_SEEDS = list(range(2000, 2100))


def make_convs(seeds, T, **kw):
    return [benchmark.generate(s, T, **kw) for s in seeds]


def norm(s): return (s or "").strip().lower()


def run_system(factory, conv, pid=0):
    """Feed the conversation, then ask all queries (no learning side-effects). Returns per-query records."""
    sys_ = factory()
    for tid, text, t in conv.turns:
        sys_.observe(text, t, tid)
    recs = []
    n_turns = len(conv.turns)
    for q in conv.queries:
        t0 = time.perf_counter()
        a = sys_.answer(q.text, conv.end_time, learn=False)
        dt = (time.perf_counter() - t0) * 1000
        if q.qtype == "unanswerable":
            ok = a.value is None
        elif q.qtype == "episodic":
            ok = a.value is not None and norm(q.expected) in norm(a.text)
        else:
            ok = a.value is not None and norm(a.value) == norm(q.expected)
        answered = a.value is not None
        grounded = bool(set(a.evidence) & set(q.evidence)) if q.evidence else None
        if q.qtype == "unanswerable":
            err = "hallucination" if answered else None
        elif ok:
            err = None
        else:
            err = "wrong_value" if answered else "false_unknown"
        recs.append(dict(pid=pid, qtype=q.qtype, ok=ok, answered=answered, route=a.route, ms=dt, err=err,
                         dist=(n_turns - q.last_mention) if q.last_mention >= 0 else None,
                         mentions=q.n_mentions, grounded=grounded, size=sys_.footprint()))
    return recs


@contextmanager
def oracle_perception(conv):
    """Give every system gold fact extraction and gold question understanding (isolates memory from perception)."""
    from memchat.extract import Fact
    import memchat.memory as mm, memchat.baselines as bb
    gold = {text: ([Fact(*conv.gold[tid])] if tid in conv.gold else []) for tid, text, _ in conv.turns}
    qmap = {q.text: (q.slot, "user") for q in conv.queries}
    old = (mm.extract_facts, mm.question_slot, bb.question_slot)
    mm.extract_facts = lambda t: gold.get(t, [])
    mm.question_slot = bb.question_slot = lambda t: qmap.get(t, (None, "user"))
    try:
        yield
    finally:
        mm.extract_facts, mm.question_slot, bb.question_slot = old


def evaluate(factory, convs, oracle=False):
    if oracle:
        out = []
        for i, c in enumerate(convs):
            with oracle_perception(c):
                out += run_system(factory, c, i)
        return out
    out = []
    for i, c in enumerate(convs):
        out += run_system(factory, c, i)
    return out


def acc(recs, qtype=None):
    r = [x for x in recs if qtype is None or x["qtype"] == qtype]
    return float(np.mean([x["ok"] for x in r])) if r else float("nan")


def prf(recs):
    """Precision/recall/F1 over answerable questions (fact, update, episodic)."""
    r = [x for x in recs if x["qtype"] != "unanswerable"]
    answered = [x for x in r if x["answered"]]
    tp = sum(x["ok"] for x in answered)
    p = tp / len(answered) if answered else 0.0
    rec = tp / len(r) if r else 0.0
    f1 = 2 * p * rec / (p + rec) if p + rec else 0.0
    return p, rec, f1


def halluc(recs):
    r = [x for x in recs if x["qtype"] == "unanswerable"]
    return float(np.mean([x["answered"] for x in r])) if r else float("nan")


def boot_ci(recs, fn=acc, n=1000, seed=0):
    """Cluster bootstrap over personas."""
    rng = np.random.default_rng(seed)
    by = {}
    for x in recs:
        by.setdefault(x["pid"], []).append(x)
    pids = list(by)
    vals = []
    for _ in range(n):
        samp = [x for p in rng.choice(pids, len(pids)) for x in by[p]]
        vals.append(fn(samp))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def paired_diff_ci(recs_a, recs_b, n=2000, seed=0):
    """Cluster-bootstrap CI of acc(a) - acc(b) (same personas, same queries)."""
    rng = np.random.default_rng(seed)
    pa, pb = {}, {}
    for x in recs_a: pa.setdefault(x["pid"], []).append(x["ok"])
    for x in recs_b: pb.setdefault(x["pid"], []).append(x["ok"])
    pids = list(pa)
    d = []
    for _ in range(n):
        ch = rng.choice(pids, len(pids))
        a = np.mean([v for p in ch for v in pa[p]]); b = np.mean([v for p in ch for v in pb[p]])
        d.append(a - b)
    return float(np.mean(d)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def systems(budget, cfg_kw=None):
    cfg_kw = cfg_kw or {}
    return {
        "Stateless": lambda: Stateless(),
        "Sliding window": lambda: SlidingWindow(budget if budget else 10**9),
        "Plain RAG (FIFO)": lambda: PlainRAG(budget),
        "Memory-inspired": lambda: MemoryChatbot(MemConfig(budget=budget, **cfg_kw)),
    }


def query_coverage(convs):
    from memchat.extract import question_slot
    qs = [q for c in convs for q in c.queries if q.qtype != "episodic"]
    return float(np.mean([question_slot(q.text)[0] == q.slot for q in qs]))


def extractor_prf(convs):
    tp = fp = fn = 0
    for c in convs:
        for tid, text, _ in c.turns:
            pred = {(f.slot, f.value, f.subject) for f in extract_facts(text)}
            g = {c.gold[tid]} if tid in c.gold else set()
            tp += len(pred & g); fp += len(pred - g); fn += len(g - pred)
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    return p, r, (2 * p * r / (p + r) if p + r else 0), tp, fp, fn


if __name__ == "__main__":
    dev = make_convs(DEV_SEEDS, DEV)
    print("extractor dev  P/R/F1:", extractor_prf(dev))
    for B in (30, 40, 60):
        print("budget", B)
        for name, f in systems(B).items():
            r = evaluate(f, dev)
            print(f"  {name:18s} acc={acc(r):.3f} fact={acc(r,'fact'):.2f} upd={acc(r,'update'):.2f} "
                  f"unans={acc(r,'unanswerable'):.2f} epi={acc(r,'episodic'):.2f}")
