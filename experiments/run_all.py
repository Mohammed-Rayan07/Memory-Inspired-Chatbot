"""Run every experiment on the HELD-OUT test set and write results/results.json (+ figures via make_figures.py)."""
import json, sys, time
from pathlib import Path
from run import *
import locomo

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)
R = {}
B0 = 40
BUDGETS = [12, 16, 20, 30, 40, 60, 80, 120]


def summ(recs):
    p, r, f = prf(recs)
    return dict(acc=acc(recs), ci=boot_ci(recs), fact=acc(recs, "fact"), update=acc(recs, "update"),
                unanswerable=acc(recs, "unanswerable"), episodic=acc(recs, "episodic"), precision=p, recall=r, f1=f,
                halluc=halluc(recs), ms=float(np.mean([x["ms"] for x in recs])), size=float(np.mean([x["size"] for x in recs])),
                n=len(recs))


dev = make_convs(DEV_SEEDS, DEV)
test = make_convs(TEST_SEEDS, TEST)
R["n_test_personas"], R["n_test_queries"] = len(test), sum(len(c.queries) for c in test)
R["n_turns"] = len(test[0].turns)
ep, er, ef, *_ = extractor_prf(dev); R["extractor_dev"] = dict(p=ep, r=er, f1=ef)
ep, er, ef, tp, fp, fn = extractor_prf(test); R["extractor_test"] = dict(p=ep, r=er, f1=ef, tp=tp, fp=fp, fn=fn)

R['query_cov_dev'], R['query_cov_test'] = query_coverage(dev), query_coverage(test)

# ---- E1 main comparison at B0 (+ references) ------------------------------------------------------------
main = {}
recs_main = {}
sysmap = dict(systems(B0))
sysmap["Plain RAG k=10 (FIFO)"] = lambda: PlainRAG(B0, k=10)
sysmap["Full context (ref., unbounded)"] = lambda: SlidingWindow(10**9)
sysmap["Plain RAG (ref., unbounded)"] = lambda: PlainRAG(None)
sysmap["Plain RAG k=10 (ref., unbounded)"] = lambda: PlainRAG(None, k=10)
sysmap["Memory-inspired (ref., unbounded)"] = lambda: MemoryChatbot(MemConfig(budget=None))
for name, f in sysmap.items():
    recs_main[name] = evaluate(f, test)
    main[name] = summ(recs_main[name])
    print(name, round(main[name]["acc"], 3), flush=True)
R["main"] = main
R["diff_vs_window"] = paired_diff_ci(recs_main["Memory-inspired"], recs_main["Sliding window"])
R["diff_vs_rag"] = paired_diff_ci(recs_main["Memory-inspired"], recs_main["Plain RAG (FIFO)"])
R["diff_vs_rag10"] = paired_diff_ci(recs_main["Memory-inspired"], recs_main["Plain RAG k=10 (FIFO)"])

# ---- E2 budget sweep -------------------------------------------------------------------------------------
sweep = {}
for B in BUDGETS:
    row = {}
    for name in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired"):
        recs = evaluate(systems(B)[name], test)
        row[name] = dict(acc=acc(recs), ci=boot_ci(recs, n=300), fact=acc(recs, "fact"), update=acc(recs, "update"),
                         unanswerable=acc(recs, "unanswerable"), episodic=acc(recs, "episodic"))
    sweep[B] = row
    print("budget", B, {k: round(v["acc"], 3) for k, v in row.items()}, flush=True)
R["sweep"] = sweep

# ---- E3 ablations ----------------------------------------------------------------------------------------
abl = {}
variants = {"Full model": {}, "- attention gate": dict(use_attention=False), "- semantic memory": dict(use_semantic=False),
            "- decay (no recency)": dict(use_decay=False), "- supersession": dict(use_supersede=False),
            "- working memory": dict(use_wm=False)}
for B in (20, 40):
    abl[B] = {}
    base = evaluate(lambda: MemoryChatbot(MemConfig(budget=B)), test)
    for vn, kw in variants.items():
        recs = base if not kw else evaluate(lambda kw=kw: MemoryChatbot(MemConfig(budget=B, **kw)), test)
        d = paired_diff_ci(recs, base) if kw else (0, 0, 0)
        abl[B][vn] = dict(acc=acc(recs), fact=acc(recs, "fact"), update=acc(recs, "update"), unanswerable=acc(recs, "unanswerable"),
                          episodic=acc(recs, "episodic"), diff=d)
R["ablation"] = abl

# ---- E3b oracle perception (isolates memory from perception) -----------------------------------------------
orc = {}
for B in (20, 40):
    orc[B] = {}
    for name in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired"):
        rr = evaluate(systems(B)[name], test, oracle=True)
        orc[B][name] = dict(acc=acc(rr), ci=boot_ci(rr, n=300), fact=acc(rr, "fact"), update=acc(rr, "update"),
                            unanswerable=acc(rr, "unanswerable"), episodic=acc(rr, "episodic"))
    print("oracle", B, {k: round(v["acc"], 3) for k, v in orc[B].items()}, flush=True)
R["oracle"] = orc

# ---- E4 breakdowns + error taxonomy (B0) --------------------------------------------------------------------
def bins(recs):
    edges = [(0, 20), (20, 40), (40, 80), (80, 121)]
    out = {}
    for lo, hi in edges:
        r = [x for x in recs if x["dist"] is not None and x["qtype"] in ("fact", "update") and lo <= x["dist"] < hi]
        out[f"{lo}-{hi-1 if hi<121 else 120}"] = (float(np.mean([x["ok"] for x in r])) if r else None, len(r))
    return out
R["by_distance"] = {n: bins(recs_main[n]) for n in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired")}
R["by_mentions"] = {n: {m: float(np.mean([x["ok"] for x in recs_main[n] if x["qtype"] == "fact" and x["mentions"] == m] or [np.nan]))
                        for m in (1, 2, 3)} for n in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired")}
R["errors"] = {n: {e: sum(1 for x in recs_main[n] if x["err"] == e) for e in ("wrong_value", "false_unknown", "hallucination")}
               for n in ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired")}
R["routes"] = {r: sum(1 for x in recs_main["Memory-inspired"] if x["route"] == r) for r in ("wm", "semantic", "episodic", "none")}
R["grounded"] = {n: float(np.mean([x["grounded"] for x in recs_main[n] if x["grounded"] is not None])) for n in
                 ("Sliding window", "Plain RAG (FIFO)", "Memory-inspired")}

# ---- E5 latency / scalability --------------------------------------------------------------------------
scal = {}
for ns in (5, 20, 50):
    cs = [benchmark.generate(5000 + i, TEST, n_sessions=ns, n_facts=7, n_updates=2) for i in range(6)]
    row = {}
    for name, f in {"Plain RAG (unbounded)": lambda: PlainRAG(None), "Memory-inspired (B=40)": lambda: MemoryChatbot(MemConfig(budget=40)),
                    "Memory-inspired (unbounded)": lambda: MemoryChatbot(MemConfig())}.items():
        recs, t0 = [], time.perf_counter()
        nt = 0
        for i, c in enumerate(cs):
            recs += run_system(f, c, i); nt += len(c.turns)
        row[name] = dict(ms=float(np.mean([x["ms"] for x in recs])), size=float(np.mean([x["size"] for x in recs])), acc=acc(recs),
                         total_s=time.perf_counter() - t0, turns=nt // len(cs))
    scal[ns * 24] = row
    print("scal", ns * 24, {k: (round(v["ms"], 2), round(v["acc"], 2)) for k, v in row.items()}, flush=True)
R["scalability"] = scal

# ---- E6 sensitivity (gate x d_epi) on test at B=24 -----------------------------------------------------------
sens = {}
for gate in (0.0, 0.25, 0.35, 0.5, 0.7):
    for d in (0.3, 0.5, 0.7):
        sens[f"{gate}|{d}"] = acc(evaluate(lambda g=gate, d=d: MemoryChatbot(MemConfig(budget=24, gate=g, d_epi=d)), test))
R["sensitivity"] = sens
for wm in (0, 4, 7, 12):
    R.setdefault("wm_capacity", {})[wm] = acc(evaluate(lambda wm=wm: MemoryChatbot(MemConfig(budget=24, wm_capacity=max(wm, 1), use_wm=wm > 0)), test))

# ---- E7 LoCoMo evidence recall -------------------------------------------------------------------------------
lc = locomo.load()
loc = {}
for B in (50, 100, 200, None):
    for name, f in {"BM25 (FIFO)": lambda B=B: PlainRAG(B, k=10), "Sliding window": lambda B=B: SlidingWindow(B or 10**9),
                    "Memory-inspired": lambda B=B: MemoryChatbot(MemConfig(budget=B, k=10, use_semantic=False))}.items():
        if B is None and name == "Sliding window":
            continue
        rec, cat, foot, n = locomo.run(f, lc)
        loc.setdefault(str(B), {})[name] = dict(recall=rec, cat=cat, foot=foot, n=n)
        print("locomo", B, name, {k: round(v, 3) for k, v in rec.items()}, flush=True)
R["locomo"] = loc
R["locomo_stats"] = dict(convs=len(lc), turns=int(np.mean([len(t) for t, _ in lc])), qa=sum(len(q) for _, q in lc))

json.dump(R, open(OUT / "results.json", "w"), indent=1, default=float)
print("saved", OUT / "results.json")
