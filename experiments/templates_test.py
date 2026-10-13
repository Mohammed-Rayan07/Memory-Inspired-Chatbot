"""HELD-OUT TEST templates.  Written AFTER the extractor/system were frozen (commit c95a2ee) and never used for tuning.
Phrasings differ from the dev set; some are deliberately NOT covered by the rule-based extractor, so the benchmark
measures robustness of perception as well as memory."""
from templates_dev import POOLS  # same value vocabularies, different sentence frames

STATE = {
    "name": ["You can call me {v}.", "Hello there! I'm {v}.", "The name's {v}, nice to meet you."],
    "city": ["These days I reside in {v}.", "I live in {v}, and I like it.", "Home for me is {v}."],
    "job": ["I work as an {v}.", "Professionally, I'm a {v}.", "I'm employed as a {v}."],
    "pet": ["I have a {v} at home.", "My pet is a {v}, and I adore it.", "We keep a {v} in our house."],
    "food": ["My favorite food is {v}, hands down.", "Nothing beats {v}; it is my favorite dish.", "I could eat {v} every day."],
    "color": ["My favorite color is {v}.", "Honestly, {v} is my favorite color.", "I just love the color {v}."],
    "hobby": ["My hobby is {v}, and I do it weekly.", "I enjoy {v} in my free time, mostly on Sundays.", "I spend my weekends on {v}."],
    "music": ["I listen to a lot of {v} music while working.", "My favorite music genre is {v}.", "{V} is the music I put on."],
    "drink": ["My go-to drink is {v}.", "I usually drink {v} in the morning, every day.", "I can't start my day without {v}."],
    "birthday": ["My birthday is in {v}.", "I was born in {v}, a long time ago.", "Every {v} I get another year older."],
}
UPDATE = {
    "city": ["Update: I now live in {v}.", "I relocated to {v} last month."],
    "job": ["I work as a {v} now, after a career switch.", "New role: I work as a {v}."],
    "food": ["My favorite food is now {v}.", "These days my favorite food is {v}."],
    "color": ["My favorite color is now {v}.", "I changed my mind; my favorite color is {v}."],
    "hobby": ["My hobby is {v} these days.", "I took up {v}; it's my hobby now."],
    "music": ["I listen to a lot of {v} music these days.", "My favorite music genre is {v} now."],
    "drink": ["My go-to drink is {v} now.", "My favorite drink is {v} these days."],
    "pet": ["I have a {v} at home now.", "My pet is a {v} now."],
}
OTHER = {
    "city": ["My brother lives in {v}.", "My cousin Rita relocated to {v}."],
    "job": ["My sister works as a {v}.", "My boss works as a {v}."],
    "pet": ["My neighbor has a pet {v}.", "My uncle owns a {v}."],
    "food": ["My friend Leo's favorite food is {v}.", "My dad's favorite food is {v}."],
    "color": ["My friend Leo's favorite color is {v}.", "My mom's favorite color is {v}."],
    "hobby": ["My cousin's hobby is {v}.", "My friend Zoe's hobby is {v}."],
    "music": ["My dad listens to a lot of {v} music.", "My friend Leo's favorite music genre is {v}."],
    "drink": ["My sister's go-to drink is {v}.", "My uncle's favorite drink is {v}."],
    "birthday": ["My dad's birthday is in {v}.", "My cousin was born in {v}."],
}
QUERY = {
    "name": ["Can you remind me of my name?", "What am I called?"],
    "city": ["Where is my home city?", "Where do I live these days?"],
    "job": ["What do I do for work?", "What is my occupation?"],
    "pet": ["Which pet do I have?", "What is my pet again?"],
    "food": ["Which food do I love most?", "What is my favorite dish?"],
    "color": ["What color do I like best?", "What is my favorite colour?"],
    "hobby": ["What is my main hobby?", "How do I spend my free time?"],
    "music": ["Which music genre do I like?", "What music do I listen to?"],
    "drink": ["What is my go-to drink?", "What do I drink in the morning?"],
    "birthday": ["What month is my birthday?", "When was I born?"],
}
FILLER = [
    "Sorry, I was away for a bit.", "It's freezing outside right now.", "Anyway, how's your day going?",
    "The soup at the canteen was a letdown.", "Do you have a favorite color yourself?", "Our city has a lot of construction going on.",
    "My work week has been exhausting.", "Are animals good companions for kids?", "I saw a documentary about songs and the brain.",
    "The commute was awful again.", "The colors in that painting were stunning.", "I have to go shopping later.",
    "Ugh, I can't stand early meetings.", "That series is really overhyped.", "I left my keys at the office.",
    "Know any good audiobooks?", "I haven't planned this weekend yet.", "Doctors say hydration matters.",
    "My laptop is getting slow.", "A birthday cake in the office is always nice.", "I ought to go to bed on time.",
    "It poured the whole afternoon.", "The old hobby store on Main Street is gone.", "Are you more of a summer person?",
    "I don't know what to make for dinner.", "That call dragged on forever.", "The pet shop by the park is having a promotion.",
    "My wifi is unreliable today.", "I took a stroll after supper.", "Let's switch topics.", "This app update is irritating.",
    "Is caffeine really that bad?", "I enjoy how calm the reading room is.", "The gym was crowded again.", "The music next door was loud.",
]
EPISODIC = [
    ("Today at noon I ate {v}.", "What did I eat at noon today?", ["a tuna sandwich", "lentil soup", "a caesar salad", "fried rice", "a burrito"]),
    ("Yesterday evening I saw the film {v}.", "Which film did I see yesterday evening?", ["Inception", "Casablanca", "Parasite", "Amelie", "Gladiator"]),
    ("Over the weekend I traveled to {v}.", "Where did I travel over the weekend?", ["Prague", "Kyoto", "Seville", "Banff", "Dubrovnik"]),
]
