"""DEV templates: used only for developing the system and tuning hyper-parameters."""
POOLS = {
    "name": ["Priya", "Marco", "Aisha", "Liam", "Sofia", "Noah", "Mei", "Omar", "Elena", "Kofi", "Hana", "Lucas"],
    "city": ["Lisbon", "Toronto", "Nairobi", "San Diego", "Osaka", "Berlin", "Austin", "Cairo", "Oslo", "Lima", "Hanoi", "Perth"],
    "job": ["nurse", "teacher", "carpenter", "journalist", "architect", "chef", "pilot", "dentist", "electrician", "librarian", "translator", "farmer"],
    "pet": ["dog", "cat", "parrot", "rabbit", "hamster", "turtle", "goldfish", "horse", "lizard", "ferret", "canary", "hedgehog"],
    "food": ["pasta", "sushi", "tacos", "biryani", "falafel", "ramen", "lasagna", "dumplings", "paella", "curry", "pancakes", "risotto"],
    "color": ["teal", "crimson", "orange", "purple", "yellow", "green", "navy", "pink", "maroon", "turquoise", "violet", "amber"],
    "hobby": ["hiking", "painting", "chess", "gardening", "photography", "cycling", "knitting", "surfing", "baking", "climbing", "sailing", "pottery"],
    "music": ["jazz", "techno", "classical", "reggae", "folk", "blues", "metal", "country", "opera", "salsa", "punk", "ambient"],
    "drink": ["green tea", "espresso", "orange juice", "hot chocolate", "coconut water", "lemonade", "black coffee", "chai", "milk", "kombucha", "mint tea", "cold brew"],
    "birthday": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}
STATE = {
    "name": ["My name is {v}.", "Hi, I'm {v}.", "People call me {v}."],
    "city": ["I live in {v}.", "I'm based in {v} these days.", "I moved to {v} recently."],
    "job": ["I work as a {v}.", "I'm a {v} by profession.", "My job is being a {v}."],
    "pet": ["I have a pet {v}.", "My pet is a {v}.", "I own a {v} at home."],
    "food": ["My favorite food is {v}.", "{V} is my favorite food.", "I'm really into {v}, it's my favorite food."],
    "color": ["My favorite color is {v}.", "{V} is my favorite color.", "I'm really into {v}, it's my favorite color."],
    "hobby": ["My hobby is {v}.", "I enjoy {v} in my free time.", "In my free time, I love {v}."],
    "music": ["I listen to a lot of {v} music.", "My favorite music genre is {v}.", "I listen to mostly {v} music."],
    "drink": ["I usually drink {v} in the morning.", "My go-to drink is {v}.", "My favorite drink is {v}."],
    "birthday": ["My birthday is in {v}.", "I was born in {v}.", "My birthday is in {v}, by the way."],
}
UPDATE = {
    "city": ["Actually, I moved to {v} last month.", "Big news: I live in {v} now."],
    "job": ["Actually, I work as a {v} now.", "I changed careers and work as a {v}."],
    "food": ["Actually, my favorite food is now {v}.", "{V} is my favorite food these days."],
    "color": ["Actually, my favorite color is now {v}.", "{V} is my favorite color these days."],
    "hobby": ["My hobby is {v} now.", "Lately my hobby is {v}."],
    "music": ["Actually, I listen to mostly {v} music now.", "My favorite music genre is {v} these days."],
    "drink": ["Actually, my go-to drink is {v} now.", "My favorite drink is {v} now."],
    "pet": ["Actually, I have a pet {v} now.", "We adopted a {v} last week; my pet is a {v} now."],
}
OTHER = {  # distractors about third parties: must NOT be returned for "my ..." questions
    "city": ["My sister lives in {v}.", "My friend Dana moved to {v}."],
    "job": ["My brother works as a {v}.", "My neighbor works as a {v}."],
    "pet": ["My cousin has a pet {v}.", "My friend Tom has a pet {v}."],
    "food": ["My friend Anna's favorite food is {v}.", "My mom's favorite food is {v}."],
    "color": ["My friend Anna's favorite color is {v}.", "My dad's favorite color is {v}."],
    "hobby": ["My roommate's hobby is {v}.", "My colleague's hobby is {v}."],
    "music": ["My sister listens to a lot of {v} music.", "My boss's favorite music genre is {v}."],
    "drink": ["My brother's go-to drink is {v}.", "My friend Mia's favorite drink is {v}."],
    "birthday": ["My mom's birthday is in {v}.", "My friend Sam was born in {v}."],
}
QUERY = {
    "name": ["What is my name?", "Who am I?"],
    "city": ["Where do I live?", "Which city do I live in?"],
    "job": ["What is my job?", "What do I do for a living?"],
    "pet": ["Do I have a pet?", "What is my pet?"],
    "food": ["What is my favorite food?", "What food do I like?"],
    "color": ["What is my favorite color?", "Which color do I like?"],
    "hobby": ["What is my hobby?", "What do I enjoy in my free time?"],
    "music": ["What is my favorite music genre?", "What kind of music do I like?"],
    "drink": ["What is my favorite drink?", "What do I usually drink?"],
    "birthday": ["When is my birthday?", "Which month was I born?"],
}
# Chit-chat; several lines deliberately overlap lexically with slot words (retrieval noise).
FILLER = [
    "The weather is lovely today.", "I'm so tired after this week.", "Did you see the news this morning?",
    "The food at that new cafeteria was awful.", "What is your favorite color, by the way?",
    "The city was really crowded this weekend.", "My job has been stressful lately.",
    "Do you think pets are good for children?", "I read an article about music and memory.",
    "Traffic was terrible on my way home.", "The color of the sky was incredible at sunset.",
    "I need to buy some groceries soon.", "Honestly, Mondays are the worst.", "That show everyone talks about is overrated.",
    "I forgot my umbrella again.", "Do you know any good podcasts?", "Weekend plans are still undecided.",
    "People say drinking water is healthy.", "My phone battery dies so quickly.", "The birthday party downtown was loud.",
    "I should probably go to sleep earlier.", "It's been raining all week.", "The hobby shop closed down last year.",
    "Do you like winter or summer?", "I can't decide what to cook tonight.", "That meeting could have been an email.",
    "The pet store near the station has a sale.", "My internet connection keeps dropping.", "I went for a short walk after dinner.",
    "Let's talk about something fun.", "The new phone update is annoying.", "Is it true that coffee is bad for you?",
    "I love how quiet the library is.", "The gym was packed today.", "My neighbor's music was loud last night.",
]
EPISODIC = [  # (statement, question, value pool): one-off episode details, not stable user facts
    ("For lunch today I had {v}.", "What did I have for lunch today?", ["a tuna sandwich", "lentil soup", "a caesar salad", "fried rice", "a burrito"]),
    ("Last night I watched {v}.", "What did I watch last night?", ["Inception", "Casablanca", "Parasite", "Amelie", "Gladiator"]),
    ("Last weekend I visited {v}.", "Where did I go last weekend?", ["Prague", "Kyoto", "Seville", "Banff", "Dubrovnik"]),
]
