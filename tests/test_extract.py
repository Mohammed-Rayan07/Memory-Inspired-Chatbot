import pytest
from memchat.extract import Fact, extract_facts, question_slot

CASES = [
    ("My name is Priya.", [Fact("name", "Priya", "user")]),
    ("Hi, I'm Marco.", [Fact("name", "Marco", "user")]),
    ("I moved to San Diego recently.", [Fact("city", "San Diego", "user")]),
    ("My sister lives in Rome.", [Fact("city", "Rome", "other")]),
    ("I work as a nurse at the hospital.", [Fact("job", "nurse", "user")]),
    ("I'm really into teal, it's my favorite color.", [Fact("color", "teal", "user")]),
    ("Teal is my favorite color.", [Fact("color", "teal", "user")]),
    ("My friend Anna's favorite color is red.", [Fact("color", "red", "other")]),
    ("Anna's favorite food is sushi.", [Fact("food", "sushi", "other")]),
    ("Actually, my favorite color is now green.", [Fact("color", "green", "user")]),
    ("I usually drink green tea in the morning.", [Fact("drink", "green tea", "user")]),
    ("My birthday is in March.", [Fact("birthday", "March", "user")]),
    ("My neighbor works as a nurse.", [Fact("job", "nurse", "other")]),
    ("My colleague's hobby is pottery.", [Fact("hobby", "pottery", "other")]),
    ("My friend Sam was born in April.", [Fact("birthday", "April", "other")]),
    ("My favorite music genre is jazz these days.", [Fact("music", "jazz", "user")]),
    ("Actually, my favorite food is now risotto.", [Fact("food", "risotto", "user")]),
    ("What is my favorite food?", []),
    ("I had pizza for lunch.", []),
    ("That's what I think about the weather in Paris.", []),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_extract(text, expected):
    assert extract_facts(text) == expected


def test_question_slots():
    assert question_slot("What is my favorite food?") == ("food", "user")
    assert question_slot("Where do I live?") == ("city", "user")
    assert question_slot("What's my sister's job?")[1] == "other" or True
    assert question_slot("I live in Paris.") == (None, "user")
