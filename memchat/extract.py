"""Rule-based 'perception' layer: fact extraction from utterances and question understanding.

This is deliberately transparent and offline.  In the live demo an LLM can replace it
(see `llm.py`); the memory architecture itself is independent of how facts are extracted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

SLOTS = ["name", "city", "job", "pet", "food", "color", "hobby", "music", "drink", "birthday"]

SLOT_LABEL = {
    "name": "name", "city": "city", "job": "job", "pet": "pet", "food": "favorite food",
    "color": "favorite color", "hobby": "hobby", "music": "favorite music", "drink": "favorite drink",
    "birthday": "birthday month",
}

PETS = ("dog cat parrot rabbit hamster turtle goldfish horse lizard ferret canary guinea pig snake "
        "tortoise cockatiel hedgehog").split()
MONTHS = ("January February March April May June July August September October November December").split()

OTHER = r"(?:friend|sister|brother|mother|mom|father|dad|cousin|colleague|neighbou?r|boss|roommate|uncle|aunt)"
OTHER_RE = re.compile(rf"(?i:\bmy {OTHER}\b|\b(?:he|she|they) )|(?-i:\b[A-Z][a-z]+'s\s+(?:favou?rite|hobby|birthday|job|pet|dog|cat)\b)")
_PROPER = r"(?-i:([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?))"
_WORDS = r"([a-z]+(?: [a-z]+)?)"
_V = r"(?:favou?rite)"

# slot -> list of (compiled regex, group index).  Case-insensitive except where noted.
_PAT: dict[str, list[re.Pattern]] = {
    "name": [
        re.compile(rf"\b(?:my name is|call me|people call me|i(?:'m| am) called|name's)\s+{_PROPER}", re.I),
        re.compile(rf"\b(?:hi|hello|hey)[, ]+i(?:'m| am)\s+{_PROPER}", re.I),
    ],
    "city": [
        re.compile(rf"\b(?:i|we)(?: now| currently)?\s+(?:live|lives|reside|am based|'m based|moved|relocated)\s+(?:in|to)\s+{_PROPER}", re.I),
        re.compile(rf"\bi(?:'m| am) based in\s+{_PROPER}", re.I),
        re.compile(rf"\b(?:lives|moved|relocated) (?:in|to)\s+{_PROPER}", re.I),
        re.compile(rf"\bmy (?:home ?town|city) is\s+{_PROPER}", re.I),
    ],
    "job": [
        re.compile(rf"\b(?:work|works) as (?:an?|the) {_WORDS}\b", re.I),
        re.compile(rf"\bi(?:'m| am) (?:an?|the) {_WORDS} by (?:profession|trade)", re.I),
        re.compile(rf"\bmy (?:job|profession|occupation) is (?:being )?(?:an?|the)? ?{_WORDS}\b", re.I),
    ],
    "pet": [
        re.compile(rf"\b(?:i|we) (?:have|own|adopted|got) (?:an?|the) (?:pet )?({'|'.join(PETS)})\b", re.I),
        re.compile(rf"\bmy pet is (?:an?|the) ({'|'.join(PETS)})\b", re.I),
        re.compile(rf"\b(?:has|owns) (?:an?|the) (?:pet )?({'|'.join(PETS)})\b", re.I),
    ],
    "food": [
        re.compile(rf"\b(?:into|love|obsessed with) {_WORDS},? (?:it's|it is) (?:my|his|her) {_V} (?:food|dish|meal)", re.I),
        re.compile(rf"\b{_V} (?:food|dish|meal) is(?: now)? {_WORDS}\b", re.I),
        re.compile(rf"\b{_WORDS} is (?:my|his|her) {_V} (?:food|dish|meal)", re.I),
    ],
    "color": [
        re.compile(rf"\b(?:into|love|obsessed with) {_WORDS},? (?:it's|it is) (?:my|his|her) {_V} colou?r", re.I),
        re.compile(rf"\b{_V} colou?r is(?: now)? {_WORDS}\b", re.I),
        re.compile(rf"\b{_WORDS} is (?:my|his|her) {_V} colou?r", re.I),
    ],
    "hobby": [
        re.compile(rf"\b(?:my|his|her|\w+'s) hobby is(?: now)? {_WORDS}\b", re.I),
        re.compile(rf"\bin (?:my|his|her) free time,? (?:i|he|she) (?:enjoys?|loves?|likes? to|likes?) {_WORDS}\b", re.I),
        re.compile(rf"\bi (?:enjoy|love) {_WORDS} in my free time", re.I),
    ],
    "music": [
        re.compile(rf"\b(?:i listen|listens) to (?:a lot of |mostly )?{_WORDS} music", re.I),
        re.compile(rf"\b{_V} (?:music|genre|music genre) is(?: now)? {_WORDS}\b", re.I),
    ],
    "drink": [
        re.compile(rf"\bi usually drink {_WORDS} in the morning", re.I),
        re.compile(rf"\b(?:my )?go-to drink is {_WORDS}\b", re.I),
        re.compile(rf"\b{_V} drink is(?: now)? {_WORDS}\b", re.I),
    ],
    "birthday": [
        re.compile(rf"\b(?:my|his|her|\w+'s) birthday is in ({'|'.join(MONTHS)})", re.I),
        re.compile(rf"\bwas born in ({'|'.join(MONTHS)})", re.I),
    ],
}

_TRAIL = re.compile(r"\b(?:and|but|because|so|too|these|lately|now|recently|a lot|very much|at|in|with|for|on|from|since)\b.*$")


@dataclass(frozen=True)
class Fact:
    slot: str
    value: str
    subject: str  # 'user' or 'other'

    def key(self) -> tuple[str, str]:
        return (self.slot, self.subject)


def _clean(slot: str, v: str) -> str:
    v = _TRAIL.sub("", v.strip()).strip()
    v = v.title() if slot in ("city", "name", "birthday") else v.lower()
    return v


def is_question(text: str) -> bool:
    t = text.strip().lower()
    return t.endswith("?") or bool(re.match(r"^(what|where|who|when|which|do|does|did|can|could|tell me|remind me)\b", t))


def extract_facts(text: str) -> list[Fact]:
    """Return personal facts stated in `text` (empty for questions)."""
    if is_question(text):
        return []
    subject = "other" if OTHER_RE.search(text) and not re.search(r"\bmy name\b", text, re.I) else "user"
    # a first-person marker overrides the 'other' guess only when no third party is named
    facts: list[Fact] = []
    for slot, pats in _PAT.items():
        for p in pats:
            m = p.search(text)
            if m:
                v = _clean(slot, m.group(1))
                if v:
                    facts.append(Fact(slot, v, subject))
                break
    return facts


# --------------------------------------------------------------------------- questions
_Q = {
    "name": r"\b(?:my name|who am i|what am i called|what do you call me)\b",
    "city": r"\b(?:where do i live|where am i (?:based|from living)|my (?:city|home ?town)|which city do i live|where i live)\b",
    "job": r"\b(?:my (?:job|profession|occupation)|what do i do for (?:a living|work)|what do i do professionally|do for a living)\b",
    "pet": r"\b(?:my pet|do i have a pet|what pet|which pet|what animal do i)\b",
    "food": rf"\bmy {_V} (?:food|dish|meal)|what (?:food|dish) do i (?:like|love)|what do i like to eat\b",
    "color": rf"\bmy {_V} colou?r|which colou?r do i (?:like|love)|what colou?r do i (?:like|love)\b",
    "hobby": r"\b(?:my hobby|what do i (?:enjoy|do) in my free time|what are my hobbies|how do i spend my free time)\b",
    "music": rf"\b(?:my {_V} (?:music|genre)|what (?:kind of )?music do i (?:like|listen)|which music do i)\b",
    "drink": rf"\b(?:my {_V} drink|what do i (?:usually )?drink|my go-to drink)\b",
    "birthday": r"\b(?:my birthday|when was i born|which month was i born|what month is my birthday)\b",
}
_Q = {k: re.compile(v, re.I) for k, v in _Q.items()}


_KW = {k: re.compile(v, re.I) for k, v in {
    "color": r"colou?r", "food": r"food|dish|eat", "city": r"\blive|city|home ?town", "job": r"job|work|profession",
    "pet": r"\bpet", "hobby": r"hobby|free time", "music": r"music|genre", "drink": r"drink", "birthday": r"birthday|born",
    "name": r"\bname"}.items()}


def question_slot(text: str) -> tuple[str | None, str]:
    """Return (slot, subject) a question asks about, or (None, 'user')."""
    if not is_question(text):
        return None, "user"
    subject = "other" if re.search(rf"\bmy {OTHER}", text, re.I) else "user"
    if subject == "other":      # third-party questions: map by keyword (the system will decline to answer them)
        for slot, rx in _KW.items():
            if rx.search(text):
                return slot, subject
        return None, subject
    for slot, rx in _Q.items():
        if rx.search(text):
            return slot, subject
    return None, subject


def is_recall_request(text: str) -> bool:
    return bool(re.search(r"\b(what do you (?:know|remember) about me|what have i told you|summari[sz]e what you know)\b", text, re.I))
