#!/usr/bin/env python3
"""Interactive memory-inspired chatbot.   python chat.py            (interactive)
                                          python chat.py --demo     (scripted multi-session demo)"""
import argparse
import sys
from pathlib import Path

from memchat.dialogue import ChatSession
from memchat.memory import MemConfig

DEMO = [
    "Hi, I'm Priya.", "I live in Lisbon.", "I work as a nurse.", "I have a pet parrot.", "The weather is lovely today.",
    "My sister lives in Rome.", "My favorite food is ramen.", "/skip 30",
    "Good morning! Did you see the news?", "Last weekend I visited Kyoto.", "I enjoy painting in my free time.", "/skip 48",
    "Big news: I live in Toronto now.", "/skip 72",
    "What is my name?", "Where do I live?", "What is my job?", "Where does my sister live?", "What is my favorite color?",
    "What is my favorite food?", "Where did I go last weekend?", "What do you remember about me?", "/memory",
    "/forget city", "Where do I live?",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--budget", type=int, default=None, help="max memory items (None = unbounded)")
    ap.add_argument("--out", default=None, help="write transcript to this file")
    a = ap.parse_args()
    s = ChatSession(MemConfig(budget=a.budget))
    log = []
    if a.demo:
        for line in DEMO:
            r = s.say(line)
            log += [f"you> {line}", f"bot> {r}"]
        text = "\n".join(log)
        print(text)
        if a.out:
            Path(a.out).write_text(text + "\n")
        return
    print("Memory-inspired chatbot. Commands: /memory /forget <slot|all> /skip <hours> /quit")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line in ("/quit", "/exit"):
            break
        if line:
            print("bot>", s.say(line))


if __name__ == "__main__":
    main()
