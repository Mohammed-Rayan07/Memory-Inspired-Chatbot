"""Thin dialogue layer on top of the memory model (acknowledgements, recall, transparency, user control)."""
from __future__ import annotations

import itertools

from .extract import SLOT_LABEL, SLOTS, extract_facts, is_question, is_recall_request, question_slot
from .memory import MemConfig, MemoryChatbot, render

_GENERIC = itertools.cycle(["I see.", "Tell me more.", "Interesting, noted.", "Got it."])


class ChatSession:
    """One user, one persistent memory. `clock` is simulated time in seconds so sessions/days can be skipped."""

    def __init__(self, cfg: MemConfig | None = None):
        self.bot = MemoryChatbot(cfg or MemConfig())
        self.clock = 0.0
        self.turn = 0

    def skip(self, hours: float) -> None:
        self.clock += hours * 3600

    def say(self, text: str, dt: float = 30.0) -> str:
        self.clock += dt
        self.turn += 1
        t = text.strip()
        if t.startswith("/"):
            return self.command(t)
        if is_recall_request(t):
            reply = self.bot.summary()
        elif is_question(t):
            ans = self.bot.answer(t, self.clock, learn=True)       # retrieval strengthens the recalled trace
            slot, _ = question_slot(t)
            if ans.value is None:
                reply = ans.text if slot else "I don't remember anything about that."
            elif slot:
                reply = ans.text
            else:
                reply = f'You told me: "{ans.text}"'
        else:
            facts = [f for f in extract_facts(t) if f.subject == "user"]
            reply = ("Got it. " + " ".join(render(f.slot, f.value).replace("Your", "I'll remember your", 1)
                                           if render(f.slot, f.value).startswith("Your") else
                                           render(f.slot, f.value).replace("You ", "I'll remember that you ", 1)
                                           for f in facts)) if facts else next(_GENERIC)
        self.bot.observe(t, self.clock, self.turn)
        return reply

    # ------------------------------------------------------------------ commands
    def command(self, cmd: str) -> str:
        parts = cmd.split()
        name = parts[0].lower()
        if name == "/memory":
            v = self.bot.view()
            lines = [f"Working memory ({len(v['working'])}/{self.bot.cfg.wm_capacity}):"]
            lines += [f"  [{a:+.2f}] {tx}" for tx, a in v["working"]] or ["  (empty)"]
            lines.append("Long-term semantic memory (subject.slot = value, activation):")
            lines += [f"  {s}.{sl} = {val}   B={a:+.2f}{'  [superseded]' if sup else ''}" for s, sl, val, a, sup in v["semantic"]] or ["  (empty)"]
            lines.append(f"Long-term episodic traces: {v['episodic']}   total footprint: {self.bot.footprint()}")
            return "\n".join(lines)
        if name == "/forget":
            arg = parts[1].lower() if len(parts) > 1 else ""
            if arg == "all":
                return f"Forgot everything ({self.bot.forget(everything=True)} items removed)."
            if arg in SLOTS:
                return f"Forgot your {SLOT_LABEL[arg]} ({self.bot.forget(slot=arg)} items removed)."
            return "Usage: /forget <" + "|".join(SLOTS) + "|all>"
        if name == "/skip":
            h = float(parts[1]) if len(parts) > 1 else 24
            self.skip(h)
            return f"(time passes: {h:g} hours)"
        return "Commands: /memory  /forget <slot|all>  /skip <hours>  /quit"
