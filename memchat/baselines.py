"""Baseline memory systems sharing the same interface and the same reader as the proposed model."""
from __future__ import annotations

from collections import deque

from .extract import question_slot
from .memory import Answer, best_snippet, read_slot, unknown
from .text import BM25Index, tokenize


class Stateless:
    """No memory at all: every turn is independent (lower bound)."""
    name = "Stateless"

    def observe(self, text, t, turn_id=None): pass
    def answer(self, query, now=None, learn=False): return unknown()
    def footprint(self): return 0
    def retrieve_ids(self, query, now, k): return []


class SlidingWindow:
    """Fixed-size context window of the most recent turns (proxy for a context-limited LLM)."""

    def __init__(self, size: int):
        self.size = size
        self.buf: deque = deque(maxlen=size)
        self.name = f"Sliding window"

    def observe(self, text, t, turn_id=None): self.buf.append((text, t, turn_id))
    def footprint(self): return len(self.buf)

    def answer(self, query, now=None, learn=False) -> Answer:
        slot, subject = question_slot(query)
        if slot:
            return read_slot(slot, subject, list(self.buf)) or unknown()
        idx = BM25Index()
        items = list(self.buf)
        for i, (tx, _, _) in enumerate(items):
            idx.add(i, tokenize(tx))
        sc = idx.score(tokenize(query))
        top = sorted(sc, key=lambda i: -sc[i])[:1]
        return best_snippet([items[i] for i in top])

    def retrieve_ids(self, query, now, k):
        idx = BM25Index()
        items = list(self.buf)
        for i, (tx, _, _) in enumerate(items):
            idx.add(i, tokenize(tx))
        sc = idx.score(tokenize(query))
        return [items[i][2] for i in sorted(sc, key=lambda i: -sc[i])[:k]]


class PlainRAG:
    """Standard retrieval-augmented memory: store every turn, BM25 top-k, FIFO eviction under a budget."""

    def __init__(self, budget: int | None = None, k: int = 3):
        self.budget, self.k = budget, k
        self.items: dict[int, tuple] = {}
        self.index = BM25Index()
        self._n = 0
        self.name = "Plain RAG" if budget is None else "Plain RAG (FIFO)"

    def observe(self, text, t, turn_id=None):
        self.items[self._n] = (text, t, turn_id)
        self.index.add(self._n, tokenize(text))
        self._n += 1
        while self.budget is not None and len(self.items) > self.budget:
            old = min(self.items)
            self.items.pop(old)
            self.index.remove(old)

    def footprint(self): return len(self.items)

    def _top(self, query, k):
        sc = self.index.score(tokenize(query))
        return [self.items[i] for i in sorted(sc, key=lambda i: -sc[i])[:k]]

    def answer(self, query, now=None, learn=False) -> Answer:
        slot, subject = question_slot(query)
        hits = self._top(query, self.k)
        if slot:
            return read_slot(slot, subject, hits) or unknown()
        return best_snippet(hits)

    def retrieve_ids(self, query, now, k):
        return [h[2] for h in self._top(query, k)]
