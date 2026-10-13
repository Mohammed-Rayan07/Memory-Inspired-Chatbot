"""Real-data retrieval experiment on LoCoMo (Maharana et al., ACL 2024): evidence recall@k, no LLM involved."""
from __future__ import annotations

import json, re
from datetime import datetime
from pathlib import Path

import numpy as np

PATH = Path(__file__).resolve().parents[1] / "data" / "locomo10.json"
CATS = {1: "multi-hop", 2: "temporal", 3: "open-domain", 4: "single-hop"}


def _ts(s: str) -> float:
    return datetime.strptime(s.strip(), "%I:%M %p on %d %B, %Y").timestamp()


def load():
    data = json.load(open(PATH))
    convs = []
    for e in data:
        c = e["conversation"]
        turns = []
        for k in sorted((k for k in c if re.fullmatch(r"session_\d+", k)), key=lambda k: int(k.split("_")[1])):
            t0 = _ts(c[k + "_date_time"])
            for j, m in enumerate(c[k]):
                turns.append((m["dia_id"], f'{m["speaker"]}: {m["text"]}', t0 + 30 * j))
        qa = []
        for q in e["qa"]:
            if q["category"] not in CATS:
                continue
            ev = [x for ev in q.get("evidence", []) for x in re.findall(r"D\d+:\d+", ev)]
            if ev:
                qa.append((q["question"], ev, q["category"]))
        convs.append((turns, qa))
    return convs


def run(factory, convs, ks=(1, 3, 5, 10)):
    """Returns {k: mean evidence recall}, per-category recall@5, and mean footprint."""
    rec = {k: [] for k in ks}
    bycat: dict[int, list] = {c: [] for c in CATS}
    foot = []
    for turns, qa in convs:
        s = factory()
        for tid, text, t in turns:
            s.observe(text, t, tid)
        foot.append(s.footprint())
        end = turns[-1][2] + 3600
        valid = {tid for tid, _, _ in turns}
        for q, ev, cat in qa:
            ev = [e for e in ev if e in valid]
            if not ev:
                continue
            ids = s.retrieve_ids(q, end, max(ks))
            for k in ks:
                rec[k].append(len(set(ids[:k]) & set(ev)) / len(ev))
            bycat[cat].append(len(set(ids[:5]) & set(ev)) / len(ev))
    return ({k: float(np.mean(v)) for k, v in rec.items()}, {CATS[c]: float(np.mean(v)) for c, v in bycat.items() if v},
            float(np.mean(foot)), len(rec[ks[0]]))
