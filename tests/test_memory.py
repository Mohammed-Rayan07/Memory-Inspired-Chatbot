from memchat.baselines import PlainRAG, SlidingWindow
from memchat.dialogue import ChatSession
from memchat.memory import MemConfig, MemoryChatbot, base_level


def feed(bot, lines, dt=30.0):
    t = 0.0
    for i, l in enumerate(lines):
        t += dt
        bot.observe(l, t, i)
    return t


def test_recall_and_update():
    bot = MemoryChatbot(MemConfig(wm_capacity=2))
    t = feed(bot, ["I live in Lisbon.", "Nice day.", "Cool.", "Fine.", "Big news: I live in Toronto now.", "Ok.", "Yes.", "No."])
    assert bot.answer("Where do I live?", t + 100).value == "Toronto"


def test_other_person_and_unanswerable():
    bot = MemoryChatbot(MemConfig(wm_capacity=2))
    t = feed(bot, ["My sister lives in Rome.", "a", "b", "c", "d"])
    assert bot.answer("Where do I live?", t).value is None


def test_budget_respected_and_facts_survive():
    bot = MemoryChatbot(MemConfig(budget=15, wm_capacity=3))
    lines = ["My favorite color is teal."] + [f"The weather is number {i} today." for i in range(80)]
    t = feed(bot, lines)
    assert bot.footprint() <= 15
    assert bot.answer("What is my favorite color?", t).value == "teal"


def test_baselines_forget_under_budget():
    lines = ["My favorite color is teal."] + [f"Chit chat number {i}." for i in range(30)]
    w, r = SlidingWindow(10), PlainRAG(10)
    for i, l in enumerate(lines):
        w.observe(l, i, i); r.observe(l, i, i)
    assert w.answer("What is my favorite color?").value is None
    assert r.answer("What is my favorite color?").value is None


def test_decay_and_rehearsal():
    assert base_level([0.0], 100.0, 0.5) > base_level([0.0], 10000.0, 0.5)
    assert base_level([0.0, 90.0], 100.0, 0.5) > base_level([0.0], 100.0, 0.5)


def test_forget_command():
    s = ChatSession(MemConfig(wm_capacity=2))
    for l in ["I live in Lisbon.", "a.", "b.", "c.", "d."]:
        s.say(l)
    assert "Lisbon" in s.say("Where do I live?")
    s.say("/forget city")
    assert "don't know" in s.say("Where do I live?")


def test_recall_rehearses_at_query_time():
    bot = MemoryChatbot(MemConfig(wm_capacity=1))
    bot.observe("My name is Priya.", 10.0, 1)
    bot.observe("Fine.", 40.0, 2)
    bot.observe("Okay.", 70.0, 3)
    bot.answer("What is my name?", 5000.0, learn=True)
    sem = next(t for t in bot.ltm.values() if t.kind == "semantic")
    assert sem.times[-1] == 5000.0
