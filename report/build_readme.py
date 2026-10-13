"""Generate README.md with every number taken from results/results.json.  Run: python report/build_readme.py"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
R = json.load(open(ROOT / "results" / "results.json"))
M = R["main"]; SW, RG, MI = "Sliding window", "Plain RAG (FIFO)", "Memory-inspired"
f = lambda x: f"{x:.3f}"
sweep_rows = "\n".join(f"| {b} | " + " | ".join(f(R['sweep'][b][n]['acc']) for n in (SW, RG, MI)) + " |" for b in sorted(R['sweep'], key=int))
A = R["ablation"]
abl_rows = "\n".join(f"| {k} | {f(A['20'][k]['acc'])} | {f(A['40'][k]['acc'])} |" for k in A["40"])
L = R["locomo"]
loc_rows = "\n".join(f"| {'unbounded' if k == 'None' else k} | {f(L[k]['BM25 (FIFO)']['recall']['5'])} | {f(L[k]['Memory-inspired']['recall']['5'])} |" for k in ("50", "100", "200", "None"))
O = R["oracle"]
txt = f"""# Memory-Inspired Chatbot

**IT 207 Human Intelligence: course project, Team 11**

| Team member | Roll no. |
|---|---|
| Yuvaraj S | 251AI050 |
| Abhinav Karthik Rao | 251AI003 |
| Mohammed Rayan | 251AI025 |
| Mohammed Ayyoub | 251AI026 |
| Jayant Nenmeli | 251AI022 |

> A chatbot memory organised after human memory: **attention, working memory, episodic and semantic long-term memory, rehearsal, decay and forgetting**.
> It is *inspired by* human memory. It does not model the brain, and its parameters are borrowed from the literature, not fitted to human data.

---

## 1. What is this project? (plain-language summary)

Ordinary chatbots have a memory problem. Either they only see the last few messages and forget everything older, or they store every message forever and then struggle to find the right one. Human memory works differently. We pay attention to what matters, hold a few things in mind briefly, move important facts into long-term memory, let trivia fade, strengthen things we repeat or recall, and update our beliefs when something changes ("I moved to Toronto" replaces "I live in Lisbon").

This project builds a chatbot memory that follows those ideas and then **measures honestly** whether it works better than simpler memories when the amount of memory is limited.

The chatbot remembers personal facts and events that a user tells it across several conversations, for example name, city, job, pet, favourite food, and a one-off "last weekend I visited Kyoto". It can answer questions about them days later, it knows when a fact has been updated, it says "I don't know" when it was never told something, and it lets the user **see** and **delete** what it remembers.

**What it is not:** it is not a large language model, and its replies are simple templates. The goal is to study and measure the *memory*, not to produce fluent conversation. It does not measure anyone's intelligence or memory.

## 2. How it works

![Architecture](report/figures/fig1_architecture.png)

| Human memory concept | Component in the code | Where |
|---|---|---|
| Selective attention | A *salience* score for each message plus an *attention gate* (default 0.35). Messages below it are never stored long-term. | `memchat/memory.py` (`salience_of`) |
| Working memory (about 7 items) | A buffer of the 7 most active recent messages. When it is full, the least active item is displaced and encoded into long-term memory. Restating a fact while it is still in the buffer counts as rehearsal. | `MemoryChatbot.observe` |
| Episodic memory | Raw messages with timestamps, retrieved by BM25 text similarity plus activation. | `MemoryChatbot.retrieve` |
| Semantic memory | Extracted `slot = value` facts (for example `city = Toronto`). A new value for the same slot *supersedes* the old one. | `MemoryChatbot._encode` |
| Forgetting and rehearsal | ACT-R base-level activation `B = ln Σ (now − t_j)^(−d)`: it decays with time and grows with each rehearsal or recall. When the memory budget is exceeded, the lowest-priority trace is deleted. | `base_level`, `_enforce_budget` |
| Perception | A transparent, rule-based extractor that finds facts in sentences and understands questions. It attributes facts to the user or to a third party. | `memchat/extract.py` |
| Privacy and user control | `/memory` shows what is stored, `/forget` deletes it, and the bot refuses to answer questions about other people. | `memchat/dialogue.py` |

**How a question is answered:** (1) if it is about a third party, decline; (2) look for the fact in working memory and the semantic store, newest statement wins; (3) otherwise search episodic memory and read the most recent matching fact; (4) otherwise say "I don't know".

## 3. Repository layout

```
chat.py                 interactive chatbot and scripted demo
memchat/
  text.py               tokenizer and incremental BM25 index
  extract.py            fact extraction and question understanding (rule-based)
  memory.py             the memory model (working, episodic, semantic, activation, forgetting)
  baselines.py          Stateless, Sliding-window and Plain-RAG baselines (same interface)
  dialogue.py           chat session: replies, /memory, /forget, /skip
experiments/
  benchmark.py          synthetic multi-session persona benchmark with gold evidence
  templates_dev.py      sentence templates used for development and tuning
  templates_test.py     different, held-out templates used for all reported results
  run.py                evaluation harness and metrics (accuracy, P/R/F1, bootstrap CIs, oracle mode)
  locomo.py             real-data evidence-retrieval experiment on LoCoMo
  run_all.py            runs every experiment -> results/results.json
  make_figures.py       draws all figures -> report/figures/
tests/                  28 unit tests
results/                results.json (every number in the report) and demo_transcript.txt
report/                 final report (docx and pdf), slides (pptx and pdf), figures, generator scripts
docs/VIVA_PREP.md       likely viva questions with honest answers
requirements.txt
```

## 4. Installation

Requires **Python 3.10 or newer**. The chatbot itself (`chat.py`, `memchat/`) uses only the Python standard library; NumPy and matplotlib are needed for the experiments and figures, python-docx and python-pptx only to rebuild the report and slides.

```bash
git clone <this repository> && cd Memory-Inspired-Chatbot
pip install -r requirements.txt
python -m pytest -q          # expect: 28 passed
```

## 5. Using the chatbot

```bash
python chat.py --demo        # scripted three-session conversation with simulated days passing
python chat.py               # interactive
python chat.py --budget 30   # interactive with a hard memory limit of 30 items
```

| Command | What it does |
|---|---|
| `/memory` | Shows working-memory items, every stored fact with its activation, whether it was superseded, and the memory footprint |
| `/forget <slot>` | Deletes everything about one slot: `name`, `city`, `job`, `pet`, `food`, `color`, `hobby`, `music`, `drink`, `birthday` |
| `/forget all` | Deletes all memory |
| `/skip <hours>` | Advances a simulated clock so you can watch decay and sessions without waiting |
| `/quit` | Exit |
| "What do you remember about me?" | Lists the facts it currently holds |

**Example**

```
you> Hi, I'm Priya.                      bot> Got it. I'll remember your name is Priya.
you> I live in Lisbon.                   bot> Got it. I'll remember that you live in Lisbon.
you> /skip 72
you> Big news: I live in Toronto now.    bot> Got it. I'll remember that you live in Toronto.
you> Where do I live?                    bot> You live in Toronto.
you> What is my favorite color?          bot> I don't know — you haven't told me that.
you> Where does my sister live?          bot> I only keep track of facts about you, not about other people.
```

**What it understands:** simple statements such as "I live in Paris", "My favorite food is ramen", "I work as a nurse", "My birthday is in March", and matching questions. Unusual phrasings are missed, which is the main limitation (see Section 9). The full demo transcript is in `results/demo_transcript.txt`.

## 6. Reproducing the experiments

```bash
python experiments/run_all.py       # about 1-2 minutes; downloads LoCoMo automatically; writes results/results.json
python experiments/make_figures.py  # figures -> report/figures/
python report/build_report.py       # report (docx); python report/build_slides.py for slides
python report/build_readme.py       # regenerate this README from results.json
```

Everything is seeded and deterministic (only wall-clock latencies vary between runs). A fresh clone reproduces the committed results exactly.

### Evaluation design
* **Synthetic persona benchmark.** Each persona has 5 sessions of 24 turns ({R['n_turns']} turns) spread over days. It states 7 facts (1-3 times each), updates 2 of them, mentions 4 facts about *other* people (distractors), tells 3 one-off episodes, and chats, with filler that deliberately shares words with the questions. At the end it is asked 12 questions: *fact*, *update* (latest value), *unanswerable* (must say "I don't know"), and *episodic* (one-off detail).
* **Development vs. held-out test.** Hyper-parameters were examined only on 30 development personas (seeds 1000-1029, `templates_dev.py`). Every reported number comes from {R['n_test_personas']} test personas ({R['n_test_queries']} questions, seeds 2000-2099) using differently phrased templates (`templates_test.py`).
* **Baselines**, all given the same memory budget and the same fact extractor and reader: *Stateless* (no memory), *Sliding window* (last B turns), *Plain RAG* (store everything, BM25 top-3, oldest evicted). Unbounded references are also reported.
* **Real data.** LoCoMo (Maharana et al., ACL 2024): {R['locomo_stats']['qa']} questions over {R['locomo_stats']['convs']} conversations (about {R['locomo_stats']['turns']} turns each), measuring whether the gold evidence turns are retrieved (recall@k). No language model is involved.
* **Metrics.** Accuracy with 95% cluster-bootstrap confidence intervals, precision/recall/F1, hallucination rate, evidence grounding, latency, memory footprint, ablations, oracle analysis, sensitivity analysis.

## 7. Results

### Main comparison (memory budget = 40 items of a 120-turn conversation, held-out test)

| System | Accuracy | Fact | Update | Unanswerable | Episodic |
|---|---|---|---|---|---|
""" + "\n".join(f"| {'**'+n+'**' if n == MI else n} | {f(M[n]['acc'])} | {M[n]['fact']:.2f} | {M[n]['update']:.2f} | {M[n]['unanswerable']:.2f} | {M[n]['episodic']:.2f} |" for n in ("Stateless", SW, RG, "Plain RAG k=10 (FIFO)", MI)) + f"""

The memory-inspired model scores **{f(M[MI]['acc'])}** (95% CI {M[MI]['ci'][0]:.3f}-{M[MI]['ci'][1]:.3f}), a paired gain of +{R['diff_vs_window'][0]:.2f} over the sliding window and +{R['diff_vs_rag'][0]:.2f} over plain RAG (confidence intervals exclude zero). Unbounded references: full context {f(M['Full context (ref., unbounded)']['acc'])}, plain RAG {f(M['Plain RAG (ref., unbounded)']['acc'])}.

![By question type](report/figures/fig4_by_type.png)

### Effect of the memory budget (accuracy)

| Budget (items) | Sliding window | Plain RAG (FIFO) | Memory-inspired |
|---|---|---|---|
{sweep_rows}

![Budget sweep](report/figures/fig3_budget_sweep.png)

The advantage is clear when memory is scarce. When the whole conversation fits (budget 120), the sliding window wins. **The honest claim is that selective, cognitively organised memory helps under scarcity. It does not beat simply keeping everything when everything fits.**

### Ablations (accuracy of the memory model with one component removed)

| Variant | Budget 20 | Budget 40 |
|---|---|---|
{abl_rows}

Semantic memory and the attention gate matter most. Decay matters only when memory is tight. Supersession has a small effect. **Working memory gave no benefit and slightly hurt at budget 20.** We report this negative result rather than hide it.

### Perception vs. memory (oracle analysis)

On unseen phrasings the rule-based extractor has precision {R['extractor_test']['p']:.2f} but recall only {R['extractor_test']['r']:.2f} (dev: 1.00/1.00), and the question parser understands {R['query_cov_test']*100:.0f}% of held-out questions. With *gold* fact extraction supplied to every system, accuracy at budget 40 is **{f(O['40'][MI]['acc'])}** (memory-inspired) vs. {f(O['40'][SW]['acc'])} (window) and {f(O['40'][RG]['acc'])} (RAG). The memory architecture is stronger than the headline suggests, and the hand-written perception layer is the main bottleneck.

### Real data: LoCoMo evidence recall@5

| Budget (turns) | BM25 + FIFO eviction | Memory-inspired (episodic only) |
|---|---|---|
{loc_rows}

At every fixed budget the memory model retrieves more gold evidence. With unbounded storage, plain BM25 is better. Recall is low at small budgets because most evidence turns have been forgotten.

Also in the report: error analysis, accuracy vs. temporal distance, repetition effects, sensitivity to the gate and decay, working-memory capacity, latency and scaling.

## 8. Ethics and responsible use
* **Privacy:** retention is bounded, `/memory` is fully transparent, `/forget` deletes on request, and the bot does not answer about third parties.
* **Gaps:** third-party statements are still stored as raw text until forgotten or evicted; memory is not encrypted at rest; there is no user authentication or multi-user separation.
* **Bias:** the extractor expects English and capitalised Latin-script names; the salience heuristic decides what counts as important.
* **No over-claiming:** this is a computational proxy, not a measurement of intelligence, and it does not diagnose anything.

## 9. Limitations
Synthetic, templated benchmark (held-out templates reduce but do not remove this circularity); rule-based perception and replies (no language model, no human evaluation); memory budget counted in items, not tokens; borrowed ACT-R parameters; heuristic salience; working memory did not help in this task.

**Honest note on the test split.** The test templates were written after the first commit (c95a2ee), but the extractor was *not* frozen at that commit. Before the first test run, patterns were generalised using development-set errors and a salience bug was fixed. Afterwards only third-party question handling changed, and all held-out accuracies were verified identical. Extractor test precision/recall was 0.94/0.63 at c95a2ee and is 0.96/0.73 now. The same team wrote the test templates and the patterns, so the test set is held out from *tuning*, not from our knowledge of the extractor. LoCoMo (data we did not write) and the oracle analysis guard against this.

## 10. Future work
Replace the extractor and reader with a language model; use embeddings instead of BM25; learned salience; fit decay parameters; evaluate on LongMemEval and Multi-Session Chat; consolidation by summarisation; privacy engineering (consent, encryption, per-user stores).

## 11. Deliverables for the course
| Course deliverable | File |
|---|---|
| Final report (7 chapters, references, appendices) | `report/Memory_Inspired_Chatbot_Report.pdf` (editable `.docx`) |
| Presentation slides | `report/Memory_Inspired_Chatbot_Slides.pptx` (and `.pdf`) |
| Architecture diagram | `report/figures/fig1_architecture.png` |
| Source code | `memchat/`, `chat.py`, `experiments/` |
| Dataset / source information | Synthetic generator in `experiments/benchmark.py`; LoCoMo from github.com/snap-research/locomo (downloaded automatically, not redistributed) |
| Experimental results | `results/results.json`, `report/figures/` |
| Tests | `tests/` (28 tests) |
| Viva preparation | `docs/VIVA_PREP.md` |

## 12. References (main)
Atkinson & Shiffrin (1968); Baddeley & Hitch (1974); Baddeley (2000); Miller (1956); Cowan (2001); Tulving (1972); Ebbinghaus (1885); Anderson & Schooler (1991); Anderson et al. (2004, ACT-R); McClelland, McNaughton & O'Reilly (1995); Jung & Haier (2007, P-FIT); Lewis et al. (2020, RAG); Liu et al. (2024, *Lost in the Middle*); Xu, Szlam & Weston (2022, MSC); Maharana et al. (2024, LoCoMo); Wu et al. (2025, LongMemEval); Packer et al. (2023, MemGPT); Park et al. (2023, Generative Agents); Zhong et al. (2024, MemoryBank); Robertson & Zaragoza (2009, BM25). Full citations are in the report.

## 13. Use of AI assistance
The code, experiments and draft report were developed with the help of an AI coding assistant (Claude Code). The team is responsible for understanding, verifying and defending all content.
"""
(ROOT / "README.md").write_text(txt)
print("README lines:", txt.count("\n"))
