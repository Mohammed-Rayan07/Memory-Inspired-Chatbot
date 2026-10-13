"""Build the final project report (docx) from results/results.json.  Run:  python report/build_report.py"""
import json
from pathlib import Path
from docx_helpers import Doc

ROOT = Path(__file__).resolve().parents[1]
R = json.load(open(ROOT / "results" / "results.json"))
FIG = ROOT / "report" / "figures"
M = R["main"]
SW, RG, MI = "Sliding window", "Plain RAG (FIFO)", "Memory-inspired"
f3 = lambda x: f"{x:.3f}"
f2 = lambda x: f"{x:.2f}"
ci = lambda v: f"[{v['ci'][0]:.3f}, {v['ci'][1]:.3f}]"
D = Doc()

# ============================================================================ title page
D.p("", after=60)
D.p("IT 207 Human Intelligence", bold=True, align="center", size=14)
D.p("Course Project Report", align="center", size=13, after=30)
D.p("A Memory-Inspired Chatbot:", bold=True, align="center", size=24, after=0)
D.p("Working Memory, Long-Term Memory and Forgetting for Dialogue", bold=True, align="center", size=17, after=40)
D.p("Human intelligence concept: working and long-term memory (Atkinson-Shiffrin, Baddeley, Tulving, ACT-R)", align="center", italic=True, after=2)
D.p("AI implementation: retrieval-augmented generation and memory modules", align="center", italic=True, after=40)
D.p("**Team members**", align="center", after=2)
D.p("[Team member 1: name, roll number]", align="center", after=0)
D.p("[Team member 2: name, roll number]", align="center", after=0)
D.p("[Team member 3: name, roll number]", align="center", after=30)
D.p("Instructor: [name]        Date: October 2026", align="center", after=40)
D.p("Source code, data-generation scripts, results and this report: repository *Memory-Inspired-Chatbot*", align="center", size=10)
D.pagebreak()

# ============================================================================ abstract
D.h("Abstract", 1)
D.p(f"Chatbots built on language models forget: once a fact leaves the context window, it is gone, and storing every turn "
    f"forever is neither cheap nor private. Human memory solves a similar problem with a capacity-limited working memory, "
    f"a long-term store split into episodic and semantic parts, selective attention, rehearsal and forgetting. "
    f"This project builds a **memory-inspired chatbot** whose dialogue memory follows that organisation: an attention gate "
    f"scores each utterance, a seven-item working memory buffers recent turns and counts rehearsals, and displaced items are "
    f"encoded into an episodic store (what was said) and a semantic store (slot = value facts, with updating). Every trace "
    f"carries an ACT-R base-level activation that decays with time and grows with rehearsal; when a memory budget is exceeded, "
    f"the least-activated trace is forgotten. Retrieval combines BM25 relevance with activation. The system is *inspired by* human "
    f"memory, not a model of it, and its parameters are borrowed from the literature rather than fitted to human data.", align="justify")
D.p(f"We evaluate it on a synthetic multi-session persona benchmark (a development split used for tuning and a held-out test split "
    f"with different sentence templates: {R['n_test_personas']} personas, {R['n_test_queries']} questions) and, as a real-data "
    f"check, on evidence retrieval over the LoCoMo long-conversation dataset. With a budget of 40 items (a third of the "
    f"{R['n_turns']}-turn conversation) the memory-inspired model answers **{f3(M[MI]['acc'])}** of held-out questions "
    f"correctly (95% CI {ci(M[MI])}), against {f3(M[SW]['acc'])} for a sliding window and {f3(M[RG]['acc'])} for plain "
    f"retrieval-augmented memory with FIFO eviction. The advantage holds across budgets from 12 to 40 items. It disappears when the "
    f"whole conversation fits in the window: a full-context reference scores {f3(M['Full context (ref., unbounded)']['acc'])}. "
    f"Ablations show that structured semantic memory and the attention gate account for most of the gain at moderate budgets, "
    f"and that decay matters only under tight budgets. A working-memory buffer gave no measurable benefit in this task. "
    f"With gold fact extraction the model reaches {f3(R['oracle']['40'][MI]['acc'])}, showing that on unseen phrasings the "
    f"rule-based perception layer, not the memory architecture, is the main bottleneck. On LoCoMo, at fixed budgets the "
    f"model retrieves more gold evidence than FIFO retrieval, but with unbounded storage plain BM25 is better. "
    f"We discuss privacy (user-controlled deletion, refusal to answer about third parties), bias, over-claiming, and limitations.", align="justify")
D.p("**Keywords:** human memory; working memory; episodic and semantic memory; forgetting; ACT-R; retrieval-augmented generation; "
    "conversational agents; long-term dialogue; cognitive-inspired AI.")
D.pagebreak()

D.h("Contents", 1)
D.bullets(["Chapter 1: Introduction", "Chapter 2: Human Intelligence Theory", "Chapter 3: Literature Review",
           "Chapter 4: Proposed Methodology", "Chapter 5: Implementation", "Chapter 6: Results and Evaluation",
           "Chapter 7: Ethics, Conclusion and Future Work", "References", "Appendix A: Parameters and reproduction",
           "Appendix B: Individual contribution statement", "Appendix C: Use of AI assistance"])
D.pagebreak()

# ============================================================================ Chapter 1
D.h("Chapter 1: Introduction", 1)
D.h("1.1 Problem statement", 2)
D.p("A conversational assistant that meets the same person on Monday, Wednesday and the following week should remember that the "
    "person lives in Toronto (not Lisbon, where they lived before), is a nurse, and has a parrot, without being reminded and without "
    "storing every sentence ever exchanged. Language-model chatbots are stateless between calls and have a finite context window. "
    "The two usual workarounds are to keep the most recent turns (a sliding window) or to store everything and retrieve by similarity "
    "(retrieval-augmented generation, RAG). The first forgets old facts abruptly. The second grows without bound, retrieves "
    "topically similar but irrelevant text, and treats a stale statement and its later correction as equally valid.", align="justify")
D.p("**Research question.** Can a dialogue memory organised after human memory (attention, a capacity-limited working memory, "
    "episodic and semantic long-term stores, rehearsal, decay and updating) recall personal facts more reliably than a window or a "
    "plain RAG memory of the same size, and which of its components are responsible for any gain?", align="justify")
D.h("1.2 Motivation and real-world application", 2)
D.p("Long-term personalisation matters in companion and coaching chatbots, tutoring systems, customer-support agents and "
    "accessibility tools, where continuity across sessions is part of usefulness. It also raises privacy questions: remembering "
    "indefinitely is itself a risk. Human memory is a useful design reference because it is selective, bounded and adaptive. "
    "It keeps what is repeated and personally relevant, lets the rest fade, and revises beliefs when circumstances change.", align="justify")
D.h("1.3 Project objectives", 2)
D.p("The objectives follow the course framework (project brief, Section 1):")
D.table(["Course objective", "How this project addresses it"], [
    ["1. Explain and apply theories of human intelligence", "Chapter 2 applies multi-store, working-memory, episodic/semantic and ACT-R activation theory to a design problem."],
    ["2. Analyse cognitive processes (perception, attention, memory, reasoning, learning, decision-making)", "Perception, attention, working memory, long-term memory, forgetting and rehearsal are analysed and mapped to components (Table 2)."],
    ["3. Develop an AI model inspired by human intelligence", "A working Python prototype with interactive CLI (Chapters 4-5)."],
    ["4. Evaluate with appropriate metrics and experiments", "Held-out benchmark, three baselines, ablations, oracle analysis, budget sweep, latency and a real-data run (Chapter 6)."],
    ["5. Discuss limitations, ethics and societal impact", "Chapter 7, plus honest negative results in Chapter 6."],
], "Mapping of course objectives to the project.", widths=[2.6, 3.9])
D.h("1.4 Scope and expected outcomes", 2)
D.bullets([
    "**In scope:** memory for *personal facts and episodes disclosed by the user* across multiple sessions; transparent memory inspection and deletion; controlled comparison under a memory budget.",
    "**Out of scope:** open-ended fluent generation (replies are templated; the contribution is the memory, not the language model); speech; multi-user deployment; any measurement of a person's intelligence or cognitive state.",
    "**Expected outcomes:** (i) working prototype, (ii) evidence on when and why cognitively inspired memory helps, (iii) an honest account of where it does not.",
])
D.p("**Important caveat from the project brief.** A computational proxy is not a validated psychological measurement. This system "
    "does not measure anyone's intelligence or memory, and it does not claim to reproduce the biological brain. Human memory is used as "
    "design inspiration, and every claim of improvement in this report is backed by an experiment.", align="justify")
D.h("1.5 Contributions and report organisation", 2)
D.bullets([
    "A cognitively organised dialogue memory with attention gating, working memory with rehearsal, episodic and semantic stores, activation-based forgetting, and fact updating.",
    "A reproducible benchmark generator with gold evidence, third-party distractors, updates, unanswerable questions and one-off episodic details, with separate development and held-out templates.",
    "A controlled evaluation including an oracle-perception analysis that separates memory quality from fact-extraction quality, and an evidence-retrieval run on LoCoMo.",
    "Transparency and user-control features (/memory, /forget) and a discussion of their ethical role.",
])
D.p("Chapter 2 presents the theory; Chapter 3 reviews related work; Chapter 4 specifies the method; Chapter 5 describes the "
    "implementation; Chapter 6 reports experiments; Chapter 7 covers ethics, conclusions and future work.")
D.pagebreak()

# ============================================================================ Chapter 2
D.h("Chapter 2: Human Intelligence Theory", 1)
D.p("Intelligence includes the ability to learn from experience and use it later, so memory is a core component of it. "
    "This chapter summarises the theories that shape the design. The brief lists P-FIT (Jung & Haier, 2007) as an example of a "
    "distributed-processing theory. We mention it only as context: it proposes that individual differences in reasoning relate to an "
    "integrated parieto-frontal network, which motivates thinking in terms of cooperating modules rather than a single store. "
    "The theories used directly are below.", align="justify")
D.h("2.1 Multi-store model and working memory", 2)
D.p("Atkinson and Shiffrin (1968) described memory as a flow from a sensory register through a short-term store to a long-term store, "
    "with control processes such as attention and rehearsal deciding what is transferred. Baddeley and Hitch (1974) replaced the unitary "
    "short-term store with *working memory*, a limited-capacity system for holding and manipulating information, and Baddeley (2000) added "
    "an *episodic buffer* that binds information from several sources into a coherent episode. Capacity is limited. Miller (1956) "
    "proposed roughly seven plus or minus two chunks, and Cowan (2001) argued that the core limit is closer to four.", align="justify")
D.h("2.2 Episodic and semantic long-term memory", 2)
D.p("Tulving (1972) distinguished *episodic* memory (specific, time-stamped events: \"last weekend I visited Kyoto\") from *semantic* "
    "memory (general facts abstracted from experience: \"Priya lives in Toronto\"). Complementary-learning-systems theory "
    "(McClelland, McNaughton & O'Reilly, 1995) proposes that fast-learning hippocampal traces of episodes are gradually consolidated into "
    "slower-changing neocortical knowledge. These two ideas motivate keeping both raw utterances and extracted facts.", align="justify")
D.h("2.3 Forgetting, rehearsal and rational analysis of memory", 2)
D.p("Ebbinghaus (1885/1913) showed that retention falls rapidly then slowly with time and that repetition slows the loss. "
    "Anderson and Schooler (1991) argued that this pattern is rational: the probability that an item will be needed again follows the "
    "same recency, frequency and spacing statistics as human memory performance. In ACT-R (Anderson et al., 2004) this is "
    "formalised as the **base-level activation** of a memory chunk,", align="justify")
D.p("B_i = ln( Σ_j (t_now − t_j)^(−d) ),   d ≈ 0.5,", align="center", italic=True)
D.p("where t_j are the times at which the chunk was encoded or retrieved. Activation drops as a power law with elapsed time and "
    "rises with each rehearsal (Figure 1). Retrieval succeeds when activation exceeds a threshold. We reuse this equation, with its "
    "conventional decay value, as the forgetting mechanism.", align="justify")
D.figure(FIG / "fig2_decay_rehearsal.png", "(a) Power-law decay of activation for three decay exponents; (b) rehearsal re-strengthens a trace. Computed from the same function the system uses.", 6.4)
D.h("2.4 Attention", 2)
D.p("Selective attention determines which inputs reach working memory and later long-term memory at all. People encode self-relevant and "
    "distinctive information far better than idle chatter. We implement a crude analogue: a salience score favouring personal "
    "statements over questions and filler, and a gate below which an utterance is not encoded into long-term memory.", align="justify")
D.h("2.5 From theory to AI: mapping", 2)
D.table(["Cognitive concept", "Source", "AI component in this project", "Fidelity"], [
    ["Selective attention", "Atkinson & Shiffrin 1968", "Salience score + attention gate", "Loose analogy: hand-written heuristic, not learned"],
    ["Working memory (capacity ~7)", "Baddeley & Hitch 1974; Miller 1956; Cowan 2001", "Buffer of the 7 most active recent turns; displacement; rehearsal counting", "Capacity borrowed; no phonological/visuospatial subsystems"],
    ["Rehearsal / transfer to LTM", "Atkinson & Shiffrin 1968", "Items displaced from the buffer are encoded; repeated facts add activation times", "Simplified"],
    ["Episodic memory", "Tulving 1972", "Store of raw utterances with timestamps, BM25 retrieval", "Text only; no spatial or emotional context"],
    ["Semantic memory", "Tulving 1972; McClelland et al. 1995", "Slot = value fact store; newest value supersedes old", "Rule-based extraction; closed set of 10 slots"],
    ["Forgetting & rehearsal", "Ebbinghaus 1885; Anderson & Schooler 1991; ACT-R", "Base-level activation; lowest-activation trace evicted over budget", "Equation borrowed; parameters not fitted to humans"],
    ["Retrieval", "ACT-R", "BM25 relevance + activation; threshold for recall failure", "Lexical relevance only"],
], "Mapping from human cognitive processes to AI components (the design contract of the system).", widths=[1.35, 1.5, 2.3, 1.55], size=8.5)
D.h("2.6 What this theory does and does not justify", 2)
D.bullets([
    "It justifies *design choices* (two stores, activation-based forgetting, rehearsal), not a claim that the system works like a brain.",
    "ACT-R parameters are population-level defaults for laboratory tasks. Using them in a text chatbot is an assumption we test with sensitivity analysis (Section 6.6), not a result we inherit.",
    "A theory-inspired architecture is not automatically better. Chapter 6 tests each component by ablation, and some components turn out not to help.",
])
D.pagebreak()

# ============================================================================ Chapter 3
D.h("Chapter 3: Literature Review", 1)
D.h("3.1 Memory for conversational agents", 2)
D.p("**Retrieval-augmented generation.** Lewis et al. (2020) combine a pretrained generator (parametric memory) with a retriever over "
    "a document index (non-parametric memory) for knowledge-intensive tasks. This is the dominant template for giving a language model access "
    "to information outside its weights, and we use its retrieve-then-read structure as the baseline (\"plain RAG\"). It was designed for "
    "open-domain question answering over a static corpus, not for a growing, self-referential dialogue history, and it has no notion of forgetting or updating.", align="justify")
D.p("**Long contexts are not a full solution.** Liu et al. (2024) show that language-model accuracy depends on *where* the relevant "
    "information sits in a long input. It is best at the beginning or end and degrades in the middle, even for models built for long "
    "contexts. They note the resemblance to primacy and recency effects in human memory. A bigger window alone is therefore not the same as "
    "a memory.", align="justify")
D.p("**Multi-session dialogue.** Xu, Szlam and Weston (2022) released the Multi-Session Chat dataset and found that models trained on "
    "short conversations perform poorly across sessions, while retrieval-augmented methods and methods that summarise and recall earlier "
    "conversations do better. Maharana et al. (2024) built LoCoMo, with conversations averaging about 600 turns over up to 32 "
    "sessions, and found that long-context models and RAG help but remain well below human performance. Wu et al. (2025) introduced "
    "LongMemEval, with 500 questions testing information extraction, multi-session reasoning, temporal reasoning, *knowledge updates* and "
    "*abstention*, and reported roughly a 30% accuracy drop for commercial assistants and long-context models when memory must persist "
    "across sustained interaction. Knowledge updates and abstention are exactly the two phenomena our benchmark isolates (question types *update* and *unanswerable*).", align="justify")
D.h("3.2 Cognitively inspired memory systems", 2)
D.p("**MemGPT** (Packer et al., 2023) borrows the idea of virtual memory from operating systems: the model moves information between a "
    "limited main context and external storage tiers through function calls, with interrupts for control flow, and is evaluated on document "
    "analysis and multi-session chat. Memory management decisions are delegated to the language model. "
    "**Generative Agents** (Park et al., 2023) store an agent's experiences in a memory stream, retrieve them using recency, importance and "
    "relevance, and add reflection, and an ablation shows these components matter for the believability of agent behaviour. "
    "**MemoryBank** (Zhong et al., 2024) is the closest to our work: it updates memory following the Ebbinghaus forgetting curve, so that memories "
    "fade or strengthen with time and significance, and demonstrates it in the SiliconFriend companion chatbot, with evaluation combining "
    "qualitative analysis of real user dialogues and quantitative analysis of simulated dialogues.", align="justify")
D.table(["Work", "Mechanism", "Strength", "Limitation relevant here"], [
    ["RAG (Lewis et al. 2020)", "Dense retrieval over a document index", "Simple, strong for QA over a corpus", "No forgetting or updating; assumes a static corpus"],
    ["Lost in the Middle (Liu et al. 2024)", "Analysis of long-context use", "Shows position effects", "A diagnosis, not a memory design"],
    ["MSC (Xu et al. 2022)", "Dataset; retrieval/summary baselines", "Multi-session data", "Short histories; models end-to-end"],
    ["MemGPT (Packer et al. 2023)", "LLM-managed tiered context", "Flexible, general", "Memory policy is implicit in LLM behaviour; hard to ablate"],
    ["Generative Agents (Park et al. 2023)", "Memory stream, recency/importance/relevance retrieval, reflection", "Rich agent behaviour", "Evaluated on believability, not recall under budget"],
    ["MemoryBank (Zhong et al. 2024)", "Ebbinghaus-style updating of stored memories", "Closest cognitive analogue", "Evaluation entangles memory with LLM quality; few component ablations"],
    ["LoCoMo (Maharana et al. 2024); LongMemEval (Wu et al. 2025)", "Benchmarks", "Realistic, include updates and abstention (LongMemEval)", "Need an LLM reader; expensive to run; no component-level view"],
], "Summary of related work and the gap.", widths=[1.5, 1.8, 1.4, 1.8], size=8.5)
D.h("3.3 Research gap and what is new here", 2)
D.p("Existing cognitive-style memories are mostly evaluated end-to-end with a large language model, which entangles memory quality with "
    "language ability, and rarely compare against baselines *at the same memory budget* or ablate individual cognitive components. "
    "We do not claim novelty for any individual mechanism: activation-based decay, importance weighting and tiered memory all "
    "appear in earlier systems. Our contribution is methodological and empirical:", align="justify")
D.bullets([
    "a **modular** design in which each cognitive component (attention gate, working memory, semantic store, decay, supersession) can be switched off, so its contribution is measured rather than assumed;",
    "a **budget-matched** comparison, because the claimed benefit of selective memory is operating with bounded storage;",
    "an **oracle-perception** analysis that separates how well facts are *extracted* from how well they are *remembered*;",
    "a benchmark with **held-out phrasing** and a **real-data** retrieval check, and honest reporting of where the design does not help.",
])
D.p("**Datasets considered.** LoCoMo (Maharana et al., 2024) was downloaded from the authors' public repository and used for retrieval "
    f"evaluation ({R['locomo_stats']['convs']} conversations, {R['locomo_stats']['turns']} turns on average, {R['locomo_stats']['qa']} questions "
    "of categories 1-4 with annotated evidence turns). MSC and LongMemEval were not used (not downloaded in this environment) and are listed as future work.", align="justify")
D.pagebreak()

# ============================================================================ Chapter 4
D.h("Chapter 4: Proposed Methodology", 1)
D.h("4.1 System architecture", 2)
D.p("Figure 2 shows the pipeline. Each user utterance is perceived (facts extracted, salience scored), enters working memory, and when "
    "displaced is encoded into long-term memory, where episodic and semantic traces compete for a limited budget according to their activation. "
    "Questions are answered by consulting working memory, the semantic store and, if needed, the episodic store; if nothing supports an "
    "answer the system says it does not know.", align="justify")
D.figure(FIG / "fig1_architecture.png", "Architecture of the memory-inspired chatbot and its mapping to human memory components.", 6.5)
D.h("4.2 Perception and attention", 2)
D.p("**Fact extraction.** A rule-based extractor identifies statements about ten personal slots (name, city, job, pet, favourite food, favourite colour, hobby, "
    "music genre, drink, birthday month) using regular expressions, and attributes each fact to the *user* or to a *third party* "
    "(\"my sister lives in Rome\"). Questions are never treated as facts. A companion parser maps questions (\"Where do I live?\") to slots. "
    "This layer is deliberately transparent and offline. An LLM could replace it without changing the memory architecture (Chapter 7).", align="justify")
D.p("**Salience (attention).** Each utterance receives a score s in [0, 1]:", align="justify")
D.table(["Condition", "Salience s"], [
    ["States a fact about the user", "1.0"], ["States a fact about a third party", "0.6"], ["A question", "0.1"],
    ["Otherwise", "0.1 + 0.2 (first-person) + 0.2 (contains a digit) + 0.2 (named entity, excluding 'I') + 0.1 (more than 8 words), capped at 0.9"],
], "Heuristic salience score.", widths=[2.8, 3.7])
D.p("Utterances with s below the attention gate (default 0.35) are kept in working memory but never encoded into long-term memory.", align="justify")
D.h("4.3 Working memory", 2)
D.p("Working memory is a buffer of at most 7 items (Miller, 1956). Each item has an activation  ln Σ (now − t)^(−1) + s  computed from its entry and "
    "refresh times. When a new item arrives and the buffer is full, the least active item is displaced and *encoded into long-term memory*. "
    "If a fact is restated while an earlier statement is still in the buffer, that item's refresh count increases (maintenance rehearsal), "
    "so repeated information enters long-term memory with a stronger trace.", align="justify")
D.h("4.4 Long-term memory: encoding, updating and consolidation", 2)
D.bullets([
    "**Episodic trace:** the raw utterance, its time(s) and its salience. Used for retrieval by similarity and for episodic questions (\"What did I eat at noon?\").",
    "**Semantic trace:** a (subject, slot, value) fact. If the same value is stated again, its list of activation times is extended (consolidation by repetition). If a *different* value is stated for the same slot, the older trace is marked *superseded* and becomes the first candidate for forgetting (knowledge updating).",
])
D.h("4.5 Activation and forgetting", 2)
D.p("Every long-term trace i has activation B_i = ln Σ_j (now − t_j)^(−d), with d = 0.5 for episodic traces and d = 0.25 for semantic traces, "
    "reflecting slower loss of consolidated knowledge. The total number of items held (working memory + long-term traces) is the "
    "**memory footprint**; when it exceeds the **budget** the trace with the lowest priority  B_i + w·s_i  (w = 1; superseded traces receive a penalty of 10) "
    "is forgotten. An optional retrieval threshold τ makes traces below it unrecallable.", align="justify")
D.h("4.6 Retrieval and answering", 2)
D.numbered([
    "Parse the question. If it asks about a third party, decline (\"I only keep track of facts about you\").",
    "For a slot question: collect candidate values from working memory and from non-superseded, sufficiently active semantic traces; return the value with the most recent statement time.",
    "If there is no candidate: retrieve the top-k = 3 episodic traces by  score = BM25_norm + 0.35·σ(B_i)  (Robertson & Zaragoza, 2009 for BM25), run the same extractor on them and read the most recent matching fact.",
    "If still nothing: answer \"I don't know\". This abstention is what the *unanswerable* questions test.",
    "For non-slot questions: return the top-1 retrieved episodic utterance.",
])
D.h("4.7 Data", 2)
D.p("**Synthetic persona benchmark.** Each persona has 5 sessions of 24 turns (120 turns). Turns are 30 s apart inside a session; sessions are "
    "6 hours to 3 days apart; questions are asked one hour after the last turn. A persona states 7 slot facts one to three times each "
    "(in different sessions), updates 2 of them later, mentions 4 facts about third parties (distractors), tells 3 one-off episodic details "
    "(lunch, film, trip) and chats in the remaining turns. The chit-chat deliberately shares words with slot questions (\"The food at that "
    "new cafeteria was awful\") to create retrieval noise. At the end the system answers 12 questions:", align="justify")
D.table(["Question type", "Per persona", "What it tests", "Correct if"], [
    ["fact", "5", "Recall of a stable fact stated 1-3 times", "Value equals gold"],
    ["update", "2", "Latest value after a correction", "Value equals the *latest* value"],
    ["unanswerable", "2", "Abstention; third-party facts must not leak", "System says it doesn't know"],
    ["episodic", "3", "Recall of one-off chit-chat detail (counterweight to selective encoding)", "Gold detail is in the returned utterance"],
], "Benchmark question types.", widths=[1.1, 0.9, 2.9, 1.6])
D.p("**Dev/test separation and an honest account of the process.** Templates for sentences and questions are in two files. The *development* templates were used to build the "
    "system and tune hyper-parameters (30 personas, seeds 1000-1029). The *test* templates use different phrasings, include forms the extractor does not cover, and were never used for "
    f"tuning (100 personas, seeds 2000-2099, {R['n_test_queries']} questions). The order of events matters and is as follows. (1) The extractor and memory code were first committed in c95a2ee. "
    "(2) The test templates were then written. (3) *Before the first test-set run* we changed the code again: several extractor patterns were generalised to fix errors seen on "
    "*development* data (third-person frames such as \"my neighbor works as a ...\", \"is now\", a trailing \"these days\"), and a salience bug was fixed (the pronoun \"I\" was counted as a named entity). "
    "(4) After the first test run, the only change was refusal/keyword handling for third-party *questions* (motivated by the demo), and we re-ran everything to confirm that all held-out accuracies were identical. "
    "The extractor was therefore *not* frozen at c95a2ee. Its test-set precision/recall was 0.94/0.63 (F1 0.75) at c95a2ee and is 0.96/0.73 (F1 0.83) in the final version "
    "(development: 0.99/0.91 and 1.00/1.00). Moreover, the same team (with AI assistance) wrote both the test templates and the patterns, so the test split is held out from *tuning*, not from the authors' knowledge of the extractor. "
    "This is why the LoCoMo run, whose data we did not write, and the oracle-perception analysis matter. Gold labels exist for every fact statement, so extractor precision and recall are measured directly.", align="justify")
D.p("**LoCoMo.** For each conversation we feed all turns in order with their real session timestamps, then for each question retrieve the top-k "
    "turns and compare them with the annotated evidence turn identifiers (evidence recall@k). No language model is involved. Adversarial "
    "(unanswerable) questions are excluded.", align="justify")
D.h("4.8 Systems compared", 2)
D.table(["System", "Description", "Memory limit"], [
    ["Stateless", "No memory; answers \"I don't know\" (lower bound)", "0"],
    ["Sliding window", "Keeps the last B turns; reads facts from them (proxy for a context-limited model)", "B turns"],
    ["Plain RAG (FIFO)", "Stores every turn, BM25 top-3, oldest turn evicted over budget", "B turns"],
    ["Plain RAG k = 10", "Same with 10 retrieved turns (stronger retrieval)", "B turns"],
    ["Memory-inspired (proposed)", "Chapter 4 system", "B items (working + long-term)"],
    ["References (not budget-matched)", "Full context; plain RAG unbounded; memory-inspired unbounded", "none"],
], "Systems. All systems use the same fact extractor and the same rule-based reader, so differences come from what is remembered and retrieved.", widths=[1.6, 3.7, 1.2])
D.h("4.9 Metrics and protocol", 2)
D.bullets([
    "**Accuracy** (primary): fraction of questions answered correctly, overall and per type; 95% confidence intervals by cluster bootstrap over personas (1,000 resamples), and paired bootstrap differences between systems.",
    "**Precision / recall / F1** over answerable questions: precision = correct among answered; recall = correct among all answerable; plus **hallucination rate** on unanswerable questions.",
    "**Evidence grounding**: share of correct answers whose cited turn is a gold evidence turn.",
    "**Extractor** precision/recall/F1 against gold facts, and **query-understanding coverage**.",
    "**Latency** (ms per question), **memory footprint**, scaling with conversation length.",
    "**Evidence recall@k** on LoCoMo.",
])
D.h("4.10 Tools and parameters", 2)
D.p("Python 3.13, NumPy, matplotlib (figures), pytest, python-docx (this report). The core library has no machine-learning dependency. "
    "All default parameters are in Appendix A. They come from the cognitive literature (d = 0.5; capacity 7) or were chosen once as "
    "reasonable round values; a small grid on the development split changed mean accuracy by under one point (0.794 default vs. 0.803 best), so literature defaults were kept.", align="justify")
D.pagebreak()

# ============================================================================ Chapter 5
D.h("Chapter 5: Implementation", 1)
D.h("5.1 Code organisation", 2)
D.table(["Path", "Role"], [
    ["memchat/text.py", "Tokeniser, light stemmer, incremental BM25 index with removal"],
    ["memchat/extract.py", "Rule-based fact extraction and question understanding"],
    ["memchat/memory.py", "Working memory, episodic/semantic stores, activation, forgetting, retrieval, answering, /memory view, /forget"],
    ["memchat/baselines.py", "Stateless, sliding-window and plain-RAG baselines (same interface)"],
    ["memchat/dialogue.py", "Chat session: acknowledgements, recall, commands, simulated clock"],
    ["chat.py", "Interactive CLI and scripted demo"],
    ["experiments/", "Benchmark generator, dev/test templates, harness, all experiments, LoCoMo run, figure script"],
    ["tests/", "27 unit tests (extractor edge cases, update, abstention, budget, decay, deletion)"],
    ["results/", "results.json (all numbers in this report), demo transcript"],
    ["report/", "Report and slide generators, figures"],
], "Repository layout.", widths=[1.8, 4.7])
D.h("5.2 Core mechanism (excerpt)", 2)
D.code('''def base_level(times, now, d):                      # ACT-R base-level activation
    return math.log(sum(max(now - t, 1.0) ** (-d) for t in times))

def _priority(self, tr):                            # forgetting priority
    p = self.activation(tr) + self.cfg.w_sal * tr.salience
    return p - 10.0 if tr.superseded else p

def _enforce_budget(self):                          # evict least-active traces
    while self.size() > self.cfg.budget and self.ltm:
        self._drop(min(self.ltm.values(), key=self._priority).id)''')
D.h("5.3 Interactive prototype and transparency commands", 2)
D.p("`python chat.py` starts an interactive session. `/memory` shows working-memory items with activation, every semantic trace with its "
    "activation and superseded flag, and the number of episodic traces. `/forget <slot|all>` deletes memories on request. `/skip <hours>` "
    "advances a simulated clock so that sessions and decay can be demonstrated without waiting. `python chat.py --demo` runs the scripted conversation below.", align="justify")
demo = (ROOT / "results" / "demo_transcript.txt").read_text().strip().split("\n")
D.p("**Demo transcript** (excerpt; full file in results/demo_transcript.txt). Note the update (Lisbon replaced by Toronto), abstention "
    "(favourite colour never stated), refusal to answer about a third party, an episodic recall, and deletion.", align="justify")
keep = [l for l in demo if not l.startswith("you> /memory") and not l.startswith("  ") and not l.startswith("Long-term") and not l.startswith("Working memory")]
D.code("\n".join(keep[14:]))
D.h("5.4 Testing", 2)
D.p("The 27 unit tests cover: extraction of user vs. third-party facts (including a bug where \"it's\" was mistaken for a possessive name), question "
    "understanding, recall after an update, refusal to leak third-party facts, budget enforcement while retaining important facts, "
    "baselines forgetting under the same budget, monotonic decay and rehearsal gain, and the /forget command. All pass (`python -m pytest -q`).", align="justify")
D.h("5.5 Reproducibility", 2)
D.code('''pip install numpy matplotlib pytest python-docx python-pptx
python -m pytest -q
python experiments/run_all.py        # all experiments -> results/results.json (about 2 minutes)
python experiments/make_figures.py   # figures
python report/build_report.py        # this report
# LoCoMo: curl -o data/locomo10.json https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json''')
D.p("All random choices are seeded; the benchmark generator and all numbers are deterministic (only wall-clock latencies vary between runs).", align="justify")
D.pagebreak()

# ============================================================================ Chapter 6
D.h("Chapter 6: Results and Evaluation", 1)
D.p(f"All results below are on the held-out test split ({R['n_test_personas']} personas, {R['n_test_queries']} questions, "
    f"{R['n_turns']}-turn conversations) unless stated otherwise. Confidence intervals are 95% cluster-bootstrap intervals over personas.", align="justify")
D.h("6.1 Main comparison at a budget of 40 items", 2)
order = ["Stateless", SW, RG, "Plain RAG k=10 (FIFO)", MI]
rows, rows2 = [], []
for n in order:
    v = M[n]
    nm = ("**" + n + "**") if n == MI else n
    rows.append([nm, f"{f3(v['acc'])} {ci(v)}", f2(v["fact"]), f2(v["update"]), f2(v["unanswerable"]), f2(v["episodic"])])
    rows2.append([nm, f2(v["precision"]), f2(v["recall"]), f2(v["f1"]), f2(v["halluc"]), f"{v['size']:.0f}", f"{v['ms']:.2f}"])
D.table(["System", "Accuracy [95% CI]", "Fact", "Update", "Unanswerable", "Episodic"], rows,
        "Accuracy at a budget of 40 items, overall and by question type.", size=9, widths=[1.9, 1.7, .55, .6, 1.0, .75])
D.table(["System", "Precision", "Recall", "F1", "Halluc. rate", "Items held", "ms / question"], rows2,
        "Precision/recall/F1 over answerable questions, hallucination rate on unanswerable questions, mean memory footprint and latency (budget = 40).", size=9, widths=[1.9, .75, .65, .5, .85, .8, .95])
refs_rows = []
for n in ("Full context (ref., unbounded)", "Plain RAG (ref., unbounded)", "Plain RAG k=10 (ref., unbounded)", "Memory-inspired (ref., unbounded)"):
    v = M[n]; refs_rows.append([n, f"{f3(v['acc'])} {ci(v)}", f2(v["fact"]), f2(v["update"]), f2(v["unanswerable"]), f2(v["episodic"]), f"{v['size']:.0f}"])
D.table(["Reference (no budget)", "Accuracy [95% CI]", "Fact", "Update", "Unans.", "Episodic", "Items"], refs_rows,
        "Unbounded references show what each system achieves when memory is not limited.", size=8.5, widths=[2.3, 1.4, .5, .6, .5, .6, .5])
D.figure(FIG / "fig4_by_type.png", "Accuracy by question type at a budget of 40 items.", 5.6)
dw, dr = R["diff_vs_window"], R["diff_vs_rag"]
D.p(f"The memory-inspired model is the most accurate budget-matched system: **{f3(M[MI]['acc'])}** against {f3(M[SW]['acc'])} (sliding window) and "
    f"{f3(M[RG]['acc'])} (plain RAG). The paired accuracy differences are +{dw[0]:.3f} (95% CI {dw[1]:.3f} to {dw[2]:.3f}) over the window and "
    f"+{dr[0]:.3f} ({dr[1]:.3f} to {dr[2]:.3f}) over RAG. Raising RAG's retrieval depth from 3 to 10 turns changes little ({f3(M['Plain RAG k=10 (FIFO)']['acc'])}), "
    f"so the weakness of RAG here is mainly that FIFO eviction discards old facts, not shallow retrieval. All systems abstain correctly on most "
    f"unanswerable questions, but not all: the memory model's hallucination rate is {f2(M[MI]['halluc'])} against {f2(M[SW]['halluc'])} for the baselines (Section 6.5).", align="justify")
D.p(f"Three observations temper this result. (1) The unbounded references are informative: a full-context reader scores "
    f"{f3(M['Full context (ref., unbounded)']['acc'])}, higher than the memory-inspired model, because it keeps every episodic detail "
    f"(episodic accuracy {f2(M['Full context (ref., unbounded)']['episodic'])} vs. {f2(M[MI]['episodic'])}). Selective memory trades detail for compactness: "
    f"it holds about {M[MI]['size']:.0f} items instead of {M['Full context (ref., unbounded)']['size']:.0f}. (2) Fact accuracy of {f2(M[MI]['fact'])} is capped by "
    f"perception on unseen phrasings (Section 6.4). (3) Plain RAG with unlimited storage reaches only {f2(M['Plain RAG (ref., unbounded)']['update'])} on update questions "
    f"(overall {f3(M['Plain RAG (ref., unbounded)']['acc'])}), because its top-3 retrieval often returns the old statement or noise instead of the newest value. "
    f"Structured updating is what the semantic store provides.", align="justify")

D.h("6.2 Effect of the memory budget", 2)
Bs = sorted(int(b) for b in R["sweep"])
D.table(["Budget"] + [str(b) for b in Bs], [[n] + [f3(R["sweep"][str(b)][n]["acc"]) for b in Bs] for n in (SW, RG, MI)],
        "Accuracy vs. memory budget (conversation length = 120 turns).", size=8.5)
D.figure(FIG / "fig3_budget_sweep.png", "Accuracy vs. memory budget with 95% CIs (shaded).", 5.0)
D.p(f"The memory-inspired model leads at every budget up to 40 items, by 0.19 to 0.24 absolute at budgets 12-40. Its curve then plateaus at "
    f"{f3(R['sweep']['60'][MI]['acc'])} because it has already retained everything it will encode "
    f"(the gate discards low-salience episodic detail and perception misses some facts), whereas the window and RAG keep improving as budget grows. "
    f"At a budget of 120, where the whole conversation fits, the sliding window is better ({f3(R['sweep']['120'][SW]['acc'])} vs. {f3(R['sweep']['120'][MI]['acc'])}). "
    f"The honest conclusion is therefore narrow: **cognitively inspired selective memory helps when memory is scarce relative to the conversation; it does not beat simply keeping everything when everything fits.**", align="justify")

D.h("6.3 Ablation study", 2)
A20, A40 = R["ablation"]["20"], R["ablation"]["40"]
rows = []
for k in A40:
    d20, d40 = A20[k]["diff"], A40[k]["diff"]
    rows.append([k, f3(A20[k]["acc"]), "-" if k == "Full model" else f"{d20[0]:+.3f} [{d20[1]:+.3f}, {d20[2]:+.3f}]",
                 f3(A40[k]["acc"]), "-" if k == "Full model" else f"{d40[0]:+.3f} [{d40[1]:+.3f}, {d40[2]:+.3f}]"])
D.table(["Variant", "Acc. (B=20)", "Δ vs full [95% CI]", "Acc. (B=40)", "Δ vs full [95% CI]"], rows,
        "Ablations of the memory-inspired model (paired cluster bootstrap).", size=8.5, widths=[1.7, .8, 1.5, .8, 1.5])
D.figure(FIG / "fig5_ablation.png", "Ablation results at budgets 20 and 40.", 6.3)
D.bullets([
    f"**Semantic memory** is the single most important component at both budgets (Δ {A20['- semantic memory']['diff'][0]:+.3f} and {A40['- semantic memory']['diff'][0]:+.3f}). Compact (slot = value) traces survive eviction and answer directly. Without them the model only has noisy episodic retrieval, though at B=20 it then does better on episodic detail ({f2(A20['- semantic memory']['episodic'])} vs. {f2(A20['Full model']['episodic'])}).",
    f"**Attention gate** matters at budget 40 (Δ {A40['- attention gate']['diff'][0]:+.3f}), where it keeps filler out of the store, and not at budget 20 (Δ {A20['- attention gate']['diff'][0]:+.3f}, interval includes zero at that budget), where there is little room for anything but facts.",
    f"**Decay (recency)** matters only when memory is tight (Δ {A20['- decay (no recency)']['diff'][0]:+.3f} at B=20) and is indistinguishable from zero at B=40 (Δ {A40['- decay (no recency)']['diff'][0]:+.3f}, CI {A40['- decay (no recency)']['diff'][1]:+.3f} to {A40['- decay (no recency)']['diff'][2]:+.3f}). It decides which traces to evict, and eviction is rare at B=40.",
    f"**Supersession** has a small effect (Δ about {A40['- supersession']['diff'][0]:+.3f}). The newest-statement rule already selects the right value, and supersession mainly changes what is evicted first.",
    f"**Working memory** gave **no benefit** and slightly *hurt* at B=20: removing it changes accuracy by {A20['- working memory']['diff'][0]:+.3f} (95% CI {A20['- working memory']['diff'][1]:+.3f} to {A20['- working memory']['diff'][2]:+.3f}) at B=20 and {A40['- working memory']['diff'][0]:+.3f} at B=40 (CI includes zero). Its seven slots count against the budget. The buffer exists for dialogue coherence and rehearsal counting, neither of which this end-of-conversation recall task rewards. We keep it because it is part of the theory-faithful design and report this as a negative result.",
])

D.h("6.4 Perception versus memory: oracle analysis", 2)
D.p(f"Fact accuracy is limited by fact extraction as much as by memory. On development templates, the extractor attains precision/recall of "
    f"{f2(R['extractor_dev']['p'])}/{f2(R['extractor_dev']['r'])} (as expected: the patterns were written against them). On the held-out test templates, precision is "
    f"{f2(R['extractor_test']['p'])} but recall only **{f2(R['extractor_test']['r'])}** (F1 {f2(R['extractor_test']['f1'])}; {R['extractor_test']['fn']} of "
    f"{R['extractor_test']['tp'] + R['extractor_test']['fn']} gold facts missed), and the question parser recognises {R['query_cov_test']*100:.0f}% of held-out slot questions "
    f"(100% on development). All misses are first-person facts in unseen phrasings (e.g., \"Home for me is Lisbon\", \"I could eat curry every day\"). "
    f"The 53 false positives come from one template (\"Nothing beats curry; it is my favorite dish\") where the pattern captures the pronoun *it*.", align="justify")
orc = R["oracle"]
D.table(["System", "B=20 rule-based", "B=20 oracle", "B=40 rule-based", "B=40 oracle"],
        [[n, f3(R["sweep"]["20"][n]["acc"]), f3(orc["20"][n]["acc"]), f3(R["sweep"]["40"][n]["acc"]), f3(orc["40"][n]["acc"])] for n in (SW, RG, MI)],
        "Accuracy with rule-based perception vs. oracle perception (gold facts and gold question slots supplied to all systems).", size=9)
D.figure(FIG / "fig6_oracle.png", "Isolating memory from perception.", 5.2)
D.p(f"With perfect perception the memory-inspired model reaches {f3(orc['40'][MI]['acc'])} at B=40 against {f3(orc['40'][SW]['acc'])} (window) and "
    f"{f3(orc['40'][RG]['acc'])} (RAG), and its fact and update accuracy become {f2(orc['40'][MI]['fact'])} and {f2(orc['40'][MI]['update'])}. The advantage of the *memory architecture* is therefore larger than the headline "
    f"numbers suggest, and the main weakness is the hand-written perception layer, not the memory. This supports replacing it with a learned extractor.", align="justify")

D.h("6.5 Error analysis", 2)
E = R["errors"]
D.table(["System", "Wrong value", "False \"don't know\"", "Hallucination (unanswerable)"],
        [[n, E[n]["wrong_value"], E[n]["false_unknown"], E[n]["hallucination"]] for n in (SW, RG, MI)],
        f"Error counts at B=40 ({R['n_test_queries']} questions per system).", size=9)
D.bullets([
    f"**False \"don't know\"** dominates the baselines ({E[SW]['false_unknown']} and {E[RG]['false_unknown']}): the fact was evicted or never retrieved. The memory model has about half as many ({E[MI]['false_unknown']}), mostly caused by perception misses (the fact was never extracted).",
    "**Hallucinations (33 for the memory model, 26 for each baseline)** are not memory errors but largely a parser limitation: held-out phrasings such as \"What is my main hobby?\" or \"Which music genre do I like?\" are not recognised as slot questions, so the system falls back to returning the closest utterance. For the memory model the 33 cases were hobby 11, music 11, food 8 and city 3 questions, all via this episodic fallback. Examples we inspected: \"The old hobby store on Main Street is gone\" (hobby), a friend's favourite music genre (music) and \"I have a canary at home\" (city). The system should abstain when no slot is recognised and the best match is weak. A relevance threshold on this fallback is a straightforward improvement we did not tune on test data.",
    f"**Wrong values** ({E[MI]['wrong_value']} for the memory model) occur mostly when a stale value is the only one remaining (the update statement was not extracted).",
])
D.figure(FIG / "fig7_distance.png", "Accuracy (fact + update questions) vs. number of turns since the last supporting statement.", 4.8)
bd = R["by_distance"]
D.p(f"Recall of the baselines collapses once the supporting statement is more than 40 turns old (window {bd[SW]['40-79'][0]:.2f} and {bd[SW]['80-120'][0]:.2f} for 40-79 and 80-120 turns), because it has left the budget. "
    f"The memory-inspired model degrades gracefully ({bd[MI]['0-19'][0]:.2f}, {bd[MI]['20-39'][0]:.2f}, {bd[MI]['40-79'][0]:.2f}, {bd[MI]['80-120'][0]:.2f}), "
    f"because personal facts have high salience and slowly decaying semantic traces. Repetition helps all systems, and the model most: fact accuracy for facts stated once, twice and three times is "
    f"{R['by_mentions'][MI]['1']:.2f}, {R['by_mentions'][MI]['2']:.2f} and {R['by_mentions'][MI]['3']:.2f} (window: {R['by_mentions'][SW]['1']:.2f}, {R['by_mentions'][SW]['2']:.2f}, {R['by_mentions'][SW]['3']:.2f}), consistent with rehearsal strengthening traces. "
    f"Of the memory model's answers, {R['routes']['wm']} came from working memory, {R['routes']['semantic']} from the semantic store, {R['routes']['episodic']} from episodic retrieval and {R['routes']['none']} were abstentions; "
    f"{R['grounded'][MI]*100:.0f}% of its answerable-question answers cite a gold evidence turn (window {R['grounded'][SW]*100:.0f}%, RAG {R['grounded'][RG]*100:.0f}%).", align="justify")

D.h("6.6 Sensitivity to hyper-parameters", 2)
D.figure(FIG / "fig10_sensitivity.png", "Test accuracy at budget 24 for different attention-gate thresholds and episodic decay exponents.", 3.6)
S = R["sensitivity"]
D.p(f"Accuracy is stable (about {min(S[k] for k in S if k.split('|')[0] in ('0.25','0.35','0.5') and k.split('|')[1] in ('0.5','0.7')):.2f}-{max(S.values()):.2f}) for gates 0.25-0.5 and d between 0.5 and 0.7, i.e. around the "
    f"literature value, which is reassuring since these values were not fitted. It collapses when the gate is too strict (0.7: {S['0.7|0.5']:.2f}, because personal statements without a fact "
    f"pattern are discarded) or when there is no gate and decay is slow (gate 0, d = 0.3: {S['0.0|0.3']:.2f}). "
    f"The default (gate 0.35, d = 0.5) was not the best test configuration (best {max(S.values()):.2f} vs. {S['0.35|0.5']:.2f}), and we did not re-tune on test data. "
    f"Varying working-memory capacity at budget 24 gives {', '.join(f'{k}: {v:.3f}' for k, v in R['wm_capacity'].items())} (0 = no buffer): larger buffers slightly hurt because they consume budget, and "
    f"Cowan's smaller capacity of about four chunks is as good as seven.", align="justify")

D.h("6.7 Efficiency and scaling", 2)
D.figure(FIG / "fig8_scalability.png", "Query latency and memory footprint as the conversation grows (6 personas per length).", 5.8)
sc = R["scalability"]
D.p(f"Plain RAG's footprint equals the conversation length and its per-question time grows with it ({sc['120']['Plain RAG (unbounded)']['ms']:.2f} ms at 120 turns to "
    f"{sc['1200']['Plain RAG (unbounded)']['ms']:.2f} ms at 1,200 turns), while the budgeted memory model stays at 40 items with flat latency "
    f"({sc['1200']['Memory-inspired (B=40)']['ms']:.2f} ms). Its unbounded variant grows more slowly than the conversation ({sc['1200']['Memory-inspired (unbounded)']['size']:.0f} items for 1,200 turns). "
    f"The cost is on the ingestion side: processing a whole conversation took {sc['1200']['Memory-inspired (B=40)']['total_s']:.2f} s versus {sc['1200']['Plain RAG (unbounded)']['total_s']:.2f} s for RAG because every turn "
    f"triggers extraction, activation computation and an eviction scan. These timings use a small pure-Python implementation on one machine and a lexical index; accuracy at the longer lengths "
    f"is based on only six personas and should not be over-interpreted.", align="justify")

D.h("6.8 Real data: LoCoMo evidence retrieval", 2)
L = R["locomo"]
rows = []
for key, lab in (("50", "50"), ("100", "100"), ("200", "200"), ("None", "unbounded")):
    for nm, show in (("BM25 (FIFO)", "BM25 + FIFO"), ("Memory-inspired", "Memory-inspired (episodic only)")):
        r = L[key][nm]
        rows.append([lab, show, f3(r["recall"]["1"]), f3(r["recall"]["3"]), f3(r["recall"]["5"]), f3(r["recall"]["10"]), f"{r['foot']:.0f}"])
D.table(["Budget (turns)", "System", "R@1", "R@3", "R@5", "R@10", "Items"], rows,
        f"Evidence recall@k on LoCoMo ({R['locomo_stats']['qa']} questions of categories 1-4, {R['locomo_stats']['convs']} conversations averaging {R['locomo_stats']['turns']} turns). The semantic store is disabled here (slots do not apply to LoCoMo).", size=8.5)
D.figure(FIG / "fig9_locomo.png", "LoCoMo evidence recall@5 vs. budget.", 4.8)
D.p(f"At every fixed budget the memory-inspired episodic memory retrieves more gold evidence than BM25 with FIFO eviction (recall@5 {L['50']['Memory-inspired']['recall']['5']:.3f} vs. {L['50']['BM25 (FIFO)']['recall']['5']:.3f} at 50 turns; "
    f"{L['100']['Memory-inspired']['recall']['5']:.3f} vs. {L['100']['BM25 (FIFO)']['recall']['5']:.3f} at 100; {L['200']['Memory-inspired']['recall']['5']:.3f} vs. {L['200']['BM25 (FIFO)']['recall']['5']:.3f} at 200), "
    f"because salience and activation keep informative turns rather than just the newest. This is on real, human-reviewed dialogue that we did not write and, "
    f"in contrast to the synthetic benchmark, is not shaped to favour the model. Absolute recall is low under tight budgets simply because most evidence turns have been "
    f"forgotten. With unbounded storage, plain BM25 is better (recall@5 {L['None']['BM25 (FIFO)']['recall']['5']:.3f} vs. {L['None']['Memory-inspired']['recall']['5']:.3f}): the gate and eviction cost a little recall when nothing "
    f"needs to be forgotten. Evidence recall measures retrieval only, not whether a reader would answer correctly.", align="justify")

D.h("6.9 Were the objectives achieved? Threats to validity", 2)
D.table(["Objective", "Evidence", "Verdict"], [
    ["Prototype inspired by human memory", "Working, episodic, semantic, forgetting, rehearsal implemented; CLI with /memory, /forget", "Achieved"],
    ["Beats equal-budget baselines", f"+{dw[0]:.2f} over window, +{dr[0]:.2f} over RAG at B=40 (CIs exclude 0); LoCoMo recall higher at fixed budgets", "Achieved under bounded memory"],
    ["Cognitive components each contribute", "Semantic memory, attention gate (B=40) and decay (B=20) do; supersession slightly; working memory does not", "Partly achieved (reported honestly)"],
    ["Beats keeping everything", "Full context scores higher when it fits; unbounded BM25 better on LoCoMo", "Not achieved, and not claimed"],
], "Objective check.", widths=[1.8, 3.4, 1.3], size=9)
D.bullets([
    "**Synthetic, templated language.** The benchmark is generated by us from templates. Held-out templates reduce but do not remove this circularity, and real conversations are far more varied. LoCoMo is the guard against this, but it tests retrieval only.",
    "**Rule-based perception and reader.** Results measure memory, not conversational ability. Replies are templated; no language model is evaluated.",
    "**Budget in items, not tokens.** Items differ in size; this favours compact semantic traces.",
    "**Borrowed parameters.** ACT-R values are not fitted to human data. Our sensitivity analysis shows robustness, not psychological validity.",
    "**Heuristic salience.** The attention gate favours capitalised entities, digits and first-person statements, which may over-retain some content (e.g. place names) and under-retain others.",
    "**One benchmark family, 100 personas.** Intervals reflect sampling over personas but not over benchmark designs.",
])
D.pagebreak()

# ============================================================================ Chapter 7
D.h("Chapter 7: Ethics, Conclusion and Future Work", 1)
D.h("7.1 Privacy", 2)
D.p("A memory-inspired chatbot deliberately accumulates personal information, which makes privacy central rather than incidental. The design includes "
    "four mitigations and is open about their limits. (1) **Bounded retention:** forgetting is a feature, since a budget limits what is kept and "
    "low-salience chit-chat is never encoded. (2) **Transparency:** `/memory` shows exactly what is stored, with activations. (3) **User control:** `/forget <slot|all>` deletes memories on request "
    "(an operational analogue of the right to erasure). (4) **Purpose limitation by design:** the assistant declines to answer about third parties. "
    "Limits: third-party statements are still stored as raw episodic text until forgotten or evicted (users could be asked for consent or such text could be dropped); "
    "memory is held in process, not encrypted at rest; there is no authentication or multi-user separation. A production system would need all three, plus retention policies and data-protection compliance.", align="justify")
D.h("7.2 Bias and fairness", 2)
D.bullets([
    "**Names and places:** the extractor expects capitalised Latin-script proper nouns and English sentence patterns. Users who write in other languages or scripts, use lowercase, or have unusual names receive worse memory. Our benchmark used a small, multicultural name list but only English.",
    "**Salience heuristic** encodes assumptions about what is important (first-person statements, entities). Content that matters to a user but does not match these cues is forgotten first.",
    "**Fact schema:** ten predefined slots reflect the designers' view of what is worth remembering about a person.",
    "A real deployment should audit recall quality across languages, dialects and user groups, which this project did not do.",
])
D.h("7.3 Over-claiming and anthropomorphism", 2)
D.p("As the brief warns, a computational proxy is not a psychological measurement. The system does not measure or diagnose anyone's memory or intelligence. "
    "It also does not model the brain: ACT-R decay is applied as an engineering heuristic. A system that says \"I remember you\" can invite users to over-trust or "
    "over-disclose, so the interface states plainly what is kept and lets users inspect and delete it. Finally, the headline result is conditional: better than "
    "equal-size baselines under scarcity, not better than keeping everything.", align="justify")
D.h("7.4 Societal impact", 2)
D.p("Persistent memory can make assistants more useful for people who benefit from continuity (learners, patients, older adults) and, if misused, enables profiling and "
    "manipulation. Forgetting and user-visible control are therefore design requirements, not extras.", align="justify")
D.h("7.5 Limitations", 2)
D.p("The principal limitations are in Section 6.9. In short: synthetic data, rule-based perception (recall 0.73 on unseen phrasing), no generative reader, no human evaluation, "
    "borrowed parameters, an unhelpful working-memory component and an unbounded-storage ceiling that selective memory does not exceed.", align="justify")
D.h("7.6 Conclusion", 2)
D.p(f"We designed, implemented and evaluated a chatbot memory organised after human memory: attention, working memory, episodic and semantic long-term memory, "
    f"activation-based forgetting, rehearsal and updating. Under a memory budget of one third of the conversation it answered {f3(M[MI]['acc'])} of held-out questions correctly, "
    f"compared with {f3(M[SW]['acc'])} for a sliding window and {f3(M[RG]['acc'])} for plain RAG, and with perfect perception {f3(R['oracle']['40'][MI]['acc'])}. Ablations show that the gain comes mainly from "
    f"compact semantic memory and selective encoding, with decay mattering when memory is tight. Working memory did not help on this task, and the advantage disappears when the whole conversation fits in memory. "
    f"On real LoCoMo dialogue the model retrieves more evidence than FIFO retrieval at fixed budgets, but less than unbounded BM25. Theory-inspired design is therefore useful as a way to *decide what to forget*, and is not "
    f"automatically more intelligent.", align="justify")
D.h("7.7 Future work", 2)
D.bullets([
    "Replace the rule-based extractor and reader with a language model and measure end-to-end (the architecture is independent of the perception layer; the oracle experiment bounds the potential gain). Use an abstention threshold for the snippet fallback.",
    "Semantic embeddings instead of BM25; learned salience instead of heuristics; fitting decay parameters on conversation data.",
    "Evaluate on LongMemEval and Multi-Session Chat and with a real language-model reader; add human evaluation of usefulness and perceived creepiness.",
    "Consolidation by summarisation (\"sleep\" phase), reflection over memories, and spaced-rehearsal prompts for tutoring applications.",
    "Privacy engineering: consent for third-party information, encryption at rest, per-user stores, retention policies.",
])
D.pagebreak()

# ============================================================================ References
D.h("References", 1)
refs = [
    "Anderson, J. R., Bothell, D., Byrne, M. D., Douglass, S., Lebiere, C., & Qin, Y. (2004). An integrated theory of the mind. *Psychological Review, 111*(4), 1036-1060.",
    "Anderson, J. R., & Schooler, L. J. (1991). Reflections of the environment in memory. *Psychological Science, 2*(6), 396-408.",
    "Atkinson, R. C., & Shiffrin, R. M. (1968). Human memory: A proposed system and its control processes. In K. W. Spence & J. T. Spence (Eds.), *The Psychology of Learning and Motivation* (Vol. 2, pp. 89-195). Academic Press.",
    "Baddeley, A. D. (2000). The episodic buffer: a new component of working memory? *Trends in Cognitive Sciences, 4*(11), 417-423.",
    "Baddeley, A. D., & Hitch, G. (1974). Working memory. In G. H. Bower (Ed.), *The Psychology of Learning and Motivation* (Vol. 8, pp. 47-89). Academic Press.",
    "Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity. *Behavioral and Brain Sciences, 24*(1), 87-114.",
    "Ebbinghaus, H. (1913). *Memory: A Contribution to Experimental Psychology* (H. A. Ruger & C. E. Bussenius, Trans.). Teachers College, Columbia University. (Original work published 1885.)",
    "Jung, R. E., & Haier, R. J. (2007). The Parieto-Frontal Integration Theory (P-FIT) of intelligence: Converging neuroimaging evidence. *Behavioral and Brain Sciences, 30*(2), 135-154.",
    "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*.",
    "Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the middle: How language models use long contexts. *Transactions of the Association for Computational Linguistics, 12*, 157-173.",
    "Maharana, A., Lee, D.-H., Tulyakov, S., Bansal, M., Barbieri, F., & Fang, Y. (2024). Evaluating very long-term conversational memory of LLM agents. In *Proceedings of ACL 2024* (pp. 13851-13870).",
    "McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex: Insights from the successes and failures of connectionist models of learning and memory. *Psychological Review, 102*(3), 419-457.",
    "Miller, G. A. (1956). The magical number seven, plus or minus two: Some limits on our capacity for processing information. *Psychological Review, 63*(2), 81-97.",
    "Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023). MemGPT: Towards LLMs as operating systems. arXiv:2310.08560.",
    "Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of UIST '23*. ACM.",
    "Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval, 3*(4), 333-389.",
    "Tulving, E. (1972). Episodic and semantic memory. In E. Tulving & W. Donaldson (Eds.), *Organization of Memory* (pp. 381-403). Academic Press.",
    "Wu, D., Wang, H., Yu, W., Zhang, Y., Chang, K.-W., & Yu, D. (2025). LongMemEval: Benchmarking chat assistants on long-term interactive memory. In *Proceedings of ICLR 2025*. arXiv:2410.10813.",
    "Xu, J., Szlam, A., & Weston, J. (2022). Beyond goldfish memory: Long-term open-domain conversation. In *Proceedings of ACL 2022* (pp. 5180-5197).",
    "Zhong, W., Guo, L., Gao, Q., Ye, H., & Wang, Y. (2024). MemoryBank: Enhancing large language models with long-term memory. In *Proceedings of AAAI 2024*, 38(17).",
]
for r in refs:
    D.p(r, align="justify", after=3)
D.pagebreak()

# ============================================================================ Appendices
D.h("Appendix A: Parameters and reproduction", 1)
D.table(["Parameter", "Default", "Source / note"], [
    ["Working-memory capacity", "7", "Miller 1956; Cowan 2001 suggests ~4 (tested, Section 6.6)"],
    ["Episodic decay d_epi", "0.5", "ACT-R default (Anderson et al. 2004)"],
    ["Semantic decay d_sem", "0.25", "Chosen: consolidated knowledge decays more slowly (not fitted)"],
    ["Attention gate", "0.35", "Chosen once; dev-set grid showed little sensitivity"],
    ["Salience weight in eviction", "1.0", "Chosen"],
    ["Activation weight in retrieval", "0.35", "Chosen"],
    ["Retrieved episodic items k", "3", "Chosen; k = 10 tested for RAG"],
    ["Retrieval threshold τ", "none", "Optional"],
    ["Superseded-trace penalty", "10", "Evict outdated facts first"],
    ["Test seeds / dev seeds", "2000-2099 / 1000-1029", "Deterministic generator"],
], "Default parameters.", widths=[2.2, 1.2, 3.1])
D.h("Appendix B: Individual contribution statement", 1)
D.p("*(To be completed by the team before submission.)*", italic=True)
D.table(["Team member", "Contribution"], [
    ["[Name 1]", "[e.g., system design, memory module implementation, experiments]"],
    ["[Name 2]", "[e.g., literature review, benchmark design, report writing]"],
    ["[Name 3]", "[e.g., evaluation, figures, presentation, demo]"],
], "Individual contributions.", widths=[1.6, 4.9])
D.h("Appendix C: Use of AI assistance", 1)
D.p("*(Complete according to your course's policy.)* This project's code, experiments and draft report were prepared with the assistance of an AI coding assistant (Claude Code). "
    "The team is responsible for understanding, verifying and defending all content. [Describe what the team reviewed, changed or verified.]", italic=False)

D.save(ROOT / "report" / "Memory_Inspired_Chatbot_Report.docx")
print("saved report; tables:", D.nt, "figures:", D.nf)
