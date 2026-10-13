"""Tiny text utilities and an incremental BM25 index (no external dependencies)."""
from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS = frozenset(
    """a an the is are was were be been am do does did i me my mine you your it its of to in on at for with
    and or but so that this these those what which who whom whose when where why how can could would should
    will shall have has had tell about again by from as if then than there here any some""".split()
)

_TOKEN = re.compile(r"[a-z0-9]+")


def stem(tok: str) -> str:
    """Very light suffix stripping (enough to match 'lives'/'live', 'colors'/'color')."""
    for suf in ("ing", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            return tok[: -len(suf)]
    return tok


def tokenize(text: str, keep_stop: bool = False) -> list[str]:
    toks = _TOKEN.findall(text.lower().replace("'s", ""))
    if not keep_stop:
        toks = [t for t in toks if t not in STOPWORDS]
    return [stem(t) for t in toks]


class BM25Index:
    """Incremental Okapi-BM25 over small document collections (supports removal)."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs: dict[int, Counter] = {}
        self.lens: dict[int, int] = {}
        self.df: Counter = Counter()
        self.total_len = 0

    def add(self, doc_id: int, tokens: list[str]) -> None:
        tf = Counter(tokens)
        self.docs[doc_id] = tf
        self.lens[doc_id] = len(tokens)
        self.total_len += len(tokens)
        for t in tf:
            self.df[t] += 1

    def remove(self, doc_id: int) -> None:
        tf = self.docs.pop(doc_id, None)
        if tf is None:
            return
        self.total_len -= self.lens.pop(doc_id)
        for t in tf:
            self.df[t] -= 1
            if self.df[t] <= 0:
                del self.df[t]

    def score(self, query_tokens: list[str], candidates=None) -> dict[int, float]:
        n = len(self.docs)
        if n == 0:
            return {}
        avg = self.total_len / n
        ids = self.docs.keys() if candidates is None else [c for c in candidates if c in self.docs]
        out: dict[int, float] = {}
        for d in ids:
            tf, dl, s = self.docs[d], self.lens[d], 0.0
            for q in set(query_tokens):
                f = tf.get(q, 0)
                if not f:
                    continue
                idf = math.log(1 + (n - self.df[q] + 0.5) / (self.df[q] + 0.5))
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / max(avg, 1e-9)))
            if s > 0:
                out[d] = s
        return out

    def __len__(self) -> int:
        return len(self.docs)
