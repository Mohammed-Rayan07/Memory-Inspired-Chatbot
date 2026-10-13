"""Memory-inspired dialogue memory.

Architecture (loosely after Atkinson & Shiffrin 1968, Baddeley 2000, Tulving 1972, ACT-R):

    utterance -> attention (salience) -> working memory (capacity-limited, rehearsal counting)
              -> long-term memory:  episodic traces (what was said)  +  semantic traces (slot=value facts)
    retrieval  = relevance (BM25) + ACT-R base-level activation;  forgetting = lowest activation evicted.

The architecture is *inspired by* human memory; parameters (decay exponents, WM capacity) are borrowed from the
cognitive literature as plausible defaults and are NOT fitted to human data.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, replace

from .extract import SLOT_LABEL, Fact, extract_facts, is_question, question_slot
from .text import BM25Index, tokenize

# --------------------------------------------------------------------------- shared answer type


@dataclass
class Answer:
    value: str | None          # extracted answer for slot questions (None = "I don't know")
    text: str                  # natural-language reply
    route: str = "none"        # wm | semantic | episodic | window | none
    evidence: list = field(default_factory=list)   # turn ids supporting the answer


def unknown() -> Answer:
    return Answer(None, "I don't know — you haven't told me that.", "none")


def render(slot: str, value: str) -> str:
    return {
        "name": f"Your name is {value}.", "city": f"You live in {value}.", "job": f"You work as a {value}.",
        "pet": f"You have a pet {value}.", "birthday": f"Your birthday is in {value}.",
    }.get(slot, f"Your {SLOT_LABEL[slot]} is {value}.")


def read_slot(slot: str, subject: str, texts: list[tuple[str, float, object]]) -> Answer | None:
    """Reader shared by all systems: from retrieved (text, time, turn_id) pick the most recent matching fact."""
    best = None
    for text, t, tid in texts:
        for f in extract_facts(text):
            if f.slot == slot and f.subject == subject and (best is None or t >= best[0]):
                best = (t, f.value, tid)
    if best is None:
        return None
    return Answer(best[1], render(slot, best[1]), "episodic", [best[2]])


def best_snippet(texts: list[tuple[str, float, object]]) -> Answer:
    if not texts:
        return unknown()
    text, _, tid = texts[0]
    return Answer(text, text, "episodic", [tid])


# --------------------------------------------------------------------------- memory model


def base_level(times: list[float], now: float, d: float) -> float:
    """ACT-R base-level activation  B = ln( sum_j (now - t_j)^-d )."""
    if d <= 0:
        return math.log(len(times))
    return math.log(sum(max(now - t, 1.0) ** (-d) for t in times))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(x, 30), -30)))


@dataclass
class MemConfig:
    budget: int | None = None        # max items held across working + long-term memory (None = unbounded)
    wm_capacity: int = 7             # Miller 1956 (7 +/- 2); Cowan 2001 argues for ~4
    d_epi: float = 0.5               # episodic decay exponent (ACT-R default 0.5)
    d_sem: float = 0.25              # semantic traces decay more slowly (systems consolidation)
    tau: float = -math.inf           # retrieval threshold on activation (below => cannot be recalled)
    gate: float = 0.35               # attention gate: min salience to be encoded into LTM
    w_sal: float = 1.0               # weight of salience in the eviction priority
    w_act: float = 0.35              # weight of activation in retrieval score
    k: int = 3                       # episodic items passed to the reader
    use_attention: bool = True
    use_semantic: bool = True
    use_decay: bool = True
    use_supersede: bool = True
    use_wm: bool = True


@dataclass
class Trace:
    id: int
    kind: str                        # 'episodic' | 'semantic'
    text: str
    times: list[float]
    salience: float
    turn: object = None
    slot: str | None = None
    value: str | None = None
    subject: str = "user"
    superseded: bool = False


@dataclass
class WMItem:
    text: str
    t: float
    facts: list[Fact]
    salience: float
    turn: object
    refreshes: list[float] = field(default_factory=list)


_FIRST = re.compile(r"\b(i|i'm|i've|my|me|we)\b", re.I)


def salience_of(text: str, facts: list[Fact]) -> float:
    """Heuristic 'attention' score: personal facts > self-relevant/informative statements > chit-chat/questions."""
    if any(f.subject == "user" for f in facts):
        return 1.0
    if facts:
        return 0.6
    if is_question(text):
        return 0.1
    toks = text.split()
    s = 0.1
    s += 0.2 if _FIRST.search(text) else 0
    s += 0.2 if any(c.isdigit() for c in text) else 0
    s += 0.2 if any(w[:1].isupper() and not re.match(r"I(?:'\w+)?$", w) for w in toks[1:]) else 0  # named entities (not "I")
    s += 0.1 if len(toks) > 8 else 0
    return min(s, 0.9)


class MemoryChatbot:
    """Working memory + episodic/semantic long-term memory with decay, rehearsal and supersession."""

    name = "Memory-inspired"

    def __init__(self, cfg: MemConfig | None = None):
        self.cfg = cfg or MemConfig()
        self.wm: list[WMItem] = []
        self.ltm: dict[int, Trace] = {}
        self.index = BM25Index()
        self._next = 0
        self.now = 0.0

    # ------------------------------------------------------------------ encoding
    def observe(self, text: str, t: float, turn_id=None) -> None:
        self.now = t
        facts = extract_facts(text)
        item = WMItem(text, t, facts, salience_of(text, facts), turn_id)
        if not self.cfg.use_wm:
            self._encode(item)
            self._enforce_budget()
            return
        # rehearsal: restating a fact still in working memory refreshes it (Atkinson-Shiffrin maintenance rehearsal)
        for old in self.wm:
            if any(f in old.facts for f in facts):
                old.refreshes.append(t)
        self.wm.append(item)
        while len(self.wm) > self.cfg.wm_capacity:
            victim = min(self.wm, key=lambda w: self._wm_activation(w, t))
            self.wm.remove(victim)
            self._encode(victim)
        self._enforce_budget()

    def _wm_activation(self, w: WMItem, now: float) -> float:
        return base_level([w.t] + w.refreshes, now, 1.0) + w.salience

    def _new(self, **kw) -> Trace:
        tr = Trace(id=self._next, **kw)
        self._next += 1
        self.ltm[tr.id] = tr
        return tr

    def _encode(self, w: WMItem) -> None:
        """Transfer a displaced working-memory item to long-term memory (gated by attention)."""
        if self.cfg.use_attention and w.salience < self.cfg.gate:
            return
        times = [w.t] + w.refreshes
        tr = self._new(kind="episodic", text=w.text, times=times, salience=w.salience, turn=w.turn)
        self.index.add(tr.id, tokenize(w.text))
        if not self.cfg.use_semantic:
            return
        for f in w.facts:
            same = [s for s in self.ltm.values()
                    if s.kind == "semantic" and s.slot == f.slot and s.subject == f.subject and not s.superseded]
            match = next((s for s in same if s.value == f.value), None)
            if match:                       # rehearsal of a known fact
                match.times.extend(times)
                match.turn = w.turn
                continue
            if self.cfg.use_supersede:      # updating: the newest value replaces the old one
                for s in same:
                    s.superseded = True
            self._new(kind="semantic", text=f"{f.subject}.{f.slot}={f.value}", times=list(times), salience=1.0,
                      turn=w.turn, slot=f.slot, value=f.value, subject=f.subject)

    # ------------------------------------------------------------------ activation & forgetting
    def activation(self, tr: Trace, now: float | None = None) -> float:
        now = self.now if now is None else now
        d = self.cfg.d_sem if tr.kind == "semantic" else self.cfg.d_epi
        return base_level(tr.times, now, d if self.cfg.use_decay else 0.0)

    def _priority(self, tr: Trace) -> float:
        p = self.activation(tr) + self.cfg.w_sal * tr.salience
        return p - 10.0 if tr.superseded else p

    def size(self) -> int:
        return len(self.wm) + len(self.ltm)

    def _enforce_budget(self) -> None:
        b = self.cfg.budget
        if b is None:
            return
        while self.size() > b and self.ltm:
            victim = min(self.ltm.values(), key=self._priority)
            self._drop(victim.id)

    def _drop(self, tid: int) -> None:
        self.ltm.pop(tid, None)
        self.index.remove(tid)

    def footprint(self) -> int:
        return self.size()

    # ------------------------------------------------------------------ retrieval
    def retrieve(self, query: str, now: float, k: int | None = None) -> list[Trace]:
        """Episodic retrieval: BM25 relevance blended with ACT-R activation; items below tau are unrecallable."""
        k = k or self.cfg.k
        qt = tokenize(query)
        cands = [i for i, tr in self.ltm.items() if tr.kind == "episodic" and self.activation(tr, now) >= self.cfg.tau]
        sc = self.index.score(qt, cands)
        if not sc:
            return []
        mx = max(sc.values())
        ranked = sorted(sc, key=lambda i: -(sc[i] / mx + self.cfg.w_act * sigmoid(self.activation(self.ltm[i], now))))
        return [self.ltm[i] for i in ranked[:k]]

    def retrieve_ids(self, query: str, now: float, k: int) -> list:
        wm = [w for w in self.wm]
        items = [(w.turn, self._wm_rel(query, w)) for w in wm]
        items = [(tid, r) for tid, r in items if r > 0]
        ltm = self.retrieve(query, now, k)
        out = [tr.turn for tr in ltm]
        for tid, _ in sorted(items, key=lambda x: -x[1]):
            if tid not in out:
                out.append(tid)
        return out[:k]

    def _wm_rel(self, query: str, w: WMItem) -> float:
        return len(set(tokenize(query)) & set(tokenize(w.text)))

    # ------------------------------------------------------------------ answering
    def answer(self, query: str, now: float | None = None, learn: bool = False) -> Answer:
        now = self.now if now is None else now
        slot, subject = question_slot(query)
        if slot:
            ans = self._answer_slot(query, slot, subject, now)
        else:
            hits = self.retrieve(query, now)
            wm_hits = [(w.text, w.t, w.turn) for w in self.wm if self._wm_rel(query, w) >= 2]
            texts = [(h.text, h.times[-1], h.turn) for h in hits]
            ans = best_snippet(texts if texts else wm_hits[:1])
        if learn and ans.value is not None:
            self._rehearse(ans)
        return ans

    def _answer_slot(self, query: str, slot: str, subject: str, now: float) -> Answer:
        if subject != "user":      # privacy by design: the assistant only answers about the user themself
            return Answer(None, "I only keep track of facts about you, not about other people.", "none")
        cands: list[tuple[float, str, str, object]] = []   # (time of statement, value, route, turn)
        for w in self.wm:
            for f in w.facts:
                if f.slot == slot and f.subject == subject:
                    cands.append(((w.refreshes[-1] if w.refreshes else w.t), f.value, "wm", w.turn))
        for tr in self.ltm.values():
            if (tr.kind == "semantic" and tr.slot == slot and tr.subject == subject and not tr.superseded
                    and self.activation(tr, now) >= self.cfg.tau):
                cands.append((tr.times[-1], tr.value, "semantic", tr.turn))
        if cands:
            _, value, route, turn = max(cands, key=lambda c: c[0])
            return Answer(value, render(slot, value), route, [turn])
        hits = self.retrieve(query, now)
        texts = [(h.text, h.times[-1], h.turn) for h in hits]
        return read_slot(slot, subject, texts) or unknown()

    def _rehearse(self, ans: Answer) -> None:
        for tr in self.ltm.values():
            if tr.turn in ans.evidence:
                tr.times.append(self.now)

    # ------------------------------------------------------------------ transparency & user control
    def view(self) -> dict:
        """Snapshot for the /memory command (explainability)."""
        return {
            "working": [(w.text, round(self._wm_activation(w, self.now), 2)) for w in self.wm],
            "semantic": [(t.subject, t.slot, t.value, round(self.activation(t), 2), t.superseded)
                         for t in self.ltm.values() if t.kind == "semantic"],
            "episodic": len([t for t in self.ltm.values() if t.kind == "episodic"]),
        }

    def forget(self, slot: str | None = None, everything: bool = False) -> int:
        """User-controlled deletion (right to be forgotten). Returns number of items removed."""
        n = 0
        if everything:
            n = self.size()
            self.wm.clear()
            for tid in list(self.ltm):
                self._drop(tid)
            return n
        for tid, tr in list(self.ltm.items()):
            hit = tr.slot == slot or (tr.kind == "episodic" and any(f.slot == slot for f in extract_facts(tr.text)))
            if slot and hit:
                self._drop(tid)
                n += 1
        before = len(self.wm)
        self.wm = [w for w in self.wm if not any(f.slot == slot for f in w.facts)]
        return n + before - len(self.wm)

    def summary(self) -> str:
        facts = {}
        for w in self.wm:
            for f in w.facts:
                if f.subject == "user":
                    facts[f.slot] = f.value
        live = sorted((t for t in self.ltm.values() if t.kind == "semantic" and t.subject == "user" and not t.superseded),
                      key=lambda t: t.times[-1])
        for t in live:
            facts[t.slot] = t.value
        if not facts:
            return "I don't have any personal facts about you yet."
        return "Here is what I remember: " + "; ".join(f"{SLOT_LABEL[s]}: {v}" for s, v in facts.items()) + "."
