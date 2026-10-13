"""Synthetic multi-session persona benchmark with gold evidence.

Each persona discloses personal facts across several sessions (separated by hours/days), interleaved with chit-chat
that deliberately overlaps lexically with slot words, third-party distractors, fact updates and one-off episodic
details.  At the end, the system is asked questions of four types:
  fact         - recall a stable personal fact (stated 1-3 times)
  update       - recall the *latest* value of a fact that changed
  unanswerable - ask about a slot the user never stated (third parties may have stated it): must say "don't know"
  episodic     - recall a one-off episode detail from chit-chat (counter-weight: favours raw-text memory)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

TURN_DT = 30.0            # seconds between turns inside a session
SESSION_GAP = (6 * 3600, 3 * 86400)


@dataclass
class Query:
    text: str
    qtype: str
    expected: str | None
    slot: str | None
    evidence: list            # gold turn ids
    last_mention: int         # turn index of the (latest) supporting statement (-1 for unanswerable)
    n_mentions: int = 0


@dataclass
class Conversation:
    turns: list = field(default_factory=list)      # (turn_id, text, t)
    queries: list = field(default_factory=list)
    end_time: float = 0.0
    gold: dict = field(default_factory=dict)       # turn index -> (slot, value, subject) gold fact


def _norm(slot: str, v: str) -> str:
    return v.title() if slot in ("city", "name", "birthday") else v.lower()


def _fmt(tpl: str, v: str, n: str = "") -> str:
    return tpl.format(v=v, V=v[:1].upper() + v[1:], n=n)


def generate(seed: int, T, n_sessions: int = 5, per_session: int = 24, n_facts: int = 7, n_updates: int = 2,
             n_other: int = 4, n_episodic: int = 3, n_unans: int = 2) -> Conversation:
    rng = random.Random(seed)
    slots = list(T.POOLS)
    disclosed = rng.sample(slots, n_facts)
    values = {s: rng.choice(T.POOLS[s]) for s in disclosed}
    upd_slots = rng.sample([s for s in disclosed if s in T.UPDATE], min(n_updates, len([s for s in disclosed if s in T.UPDATE])))
    unans_pool = [s for s in slots if s not in disclosed]
    unans = rng.sample(unans_pool, min(n_unans, len(unans_pool)))
    other_slots = [s for s in unans if s in T.OTHER] + rng.sample([s for s in T.OTHER if s not in unans], max(0, n_other - len(unans)))
    n_total = n_sessions * per_session

    # lay out events on a slot grid: (turn_index) -> (text, tag)
    events: dict[int, tuple] = {}
    free = list(range(n_total))
    rng.shuffle(free)

    gold: dict = {}

    def place(text, tag, lo=0, hi=None, fact=None):
        hi = n_total if hi is None else hi
        for i in free:
            if lo <= i < hi and i not in events:
                events[i] = (text, tag)
                if fact:
                    gold[i] = fact
                return i
        raise RuntimeError("no free slot")

    mentions: dict[str, list] = {s: [] for s in disclosed}
    sess_len = per_session
    for s in disclosed:
        k = rng.choice([1, 1, 2, 3])
        sess = sorted(rng.sample(range(n_sessions - 1 if s in upd_slots else n_sessions), min(k, n_sessions - (1 if s in upd_slots else 0))))
        for si in sess:
            idx = place(_fmt(rng.choice(T.STATE[s]), values[s]), ("fact", s), si * sess_len, (si + 1) * sess_len,
                        (s, _norm(s, values[s]), "user"))
            mentions[s].append(idx)
    final_vals = dict(values)
    last_upd: dict[str, int] = {}
    for s in upd_slots:
        new = rng.choice([v for v in T.POOLS[s] if v != values[s]])
        final_vals[s] = new
        last_upd[s] = place(_fmt(rng.choice(T.UPDATE[s]), new), ("update", s), max(max(mentions[s]) + 1, (n_sessions - 2) * sess_len),
                            None, (s, _norm(s, new), "user"))
    for s in other_slots:
        ov = rng.choice(T.POOLS[s])
        place(_fmt(rng.choice(T.OTHER[s]), ov), ("other", s), fact=(s, _norm(s, ov), "other"))
    epi = rng.sample(T.EPISODIC, min(n_episodic, len(T.EPISODIC)))
    epi_idx = []
    for st, q, pool in epi:
        v = rng.choice(pool)
        epi_idx.append((place(_fmt(st, v), ("episodic", q)), q, v))
    # fill the rest with chit-chat
    fillers = list(T.FILLER)
    for i in range(n_total):
        if i not in events:
            events[i] = (rng.choice(fillers), ("filler", None))

    conv = Conversation(gold=gold)
    t = 0.0
    for i in range(n_total):
        if i % per_session == 0 and i > 0:
            t += rng.uniform(*SESSION_GAP)
        else:
            t += TURN_DT
        conv.turns.append((i, events[i][0], t))
    conv.end_time = t + 3600

    qs = []
    for s in disclosed:
        if s in upd_slots:
            qs.append(Query(rng.choice(T.QUERY[s]), "update", final_vals[s], s, [last_upd[s]], last_upd[s], 1))
        else:
            qs.append(Query(rng.choice(T.QUERY[s]), "fact", values[s], s, list(mentions[s]), max(mentions[s]), len(mentions[s])))
    for s in unans:
        qs.append(Query(rng.choice(T.QUERY[s]), "unanswerable", None, s, [], -1))
    for idx, q, v in epi_idx:
        qs.append(Query(q, "episodic", v, None, [idx], idx, 1))
    rng.shuffle(qs)
    conv.queries = qs
    return conv
