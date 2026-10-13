# Viva preparation: be ready to defend every choice yourself

**One-sentence pitch:** We built a chatbot memory organised like human memory (attention, working memory, episodic/semantic long-term memory, decay and rehearsal) and showed it recalls more than a sliding window or plain RAG *when memory is limited*.

## Likely questions and honest answers
1. **Which theory, and why?** Atkinson-Shiffrin (stores + control processes), Baddeley (working memory), Tulving (episodic vs semantic), ACT-R/Ebbinghaus (decay + rehearsal). Each maps to a component (report Table 2). Mention P-FIT only as context.
2. **Is this how the brain works?** No. Inspired by, not a model of. ACT-R's decay d = 0.5 is borrowed and not fitted; we tested sensitivity (Fig 8 in report).
3. **Why does it beat the baselines?** Mostly compact semantic facts that survive eviction + an attention gate that keeps chit-chat out. Ablations: semantic memory -0.10, attention -0.10 at B=40, decay -0.05 only at B=20.
4. **When does it NOT win?** When the whole conversation fits (window 0.754 vs 0.676 at B=120); unbounded BM25 beats it on LoCoMo; episodic detail is lost to the gate.
5. **Did working memory help?** No (negative result). It's there for theory fidelity and rehearsal counting; this task doesn't reward it.
6. **Isn't the benchmark circular (you wrote data and extractor)?** Partly. Mitigations: held-out templates written after the first extractor commit (recall drops 1.00 on dev -> 0.73 on test), oracle-perception run to separate memory from perception, and LoCoMo (real data, not ours).
7. **Why 0.673 and not higher?** Perception: extractor recall 0.73 and question parser 79% on unseen phrasing. With gold perception 0.903.
8. **Why hallucinations (17%)?** Unrecognised question phrasings fall back to the nearest utterance instead of abstaining. Fix: relevance threshold (not tuned on test).
9. **No LLM?** Deliberate: keeps memory measurable and offline. LLM extractor/reader is the main future work.
10. **How did you avoid tuning on test?** Hyper-parameters only on dev seeds 1000-1029. Be precise about the history: the extractor was NOT frozen at c95a2ee. Before the first test run we generalised patterns using dev errors and fixed a salience bug; after it, only third-party question handling changed (accuracies verified identical). Test extractor P/R: 0.94/0.63 at c95a2ee vs 0.96/0.73 final. We wrote both templates and patterns, so test is held out from tuning, not from our knowledge: hence LoCoMo and the oracle run.
11. **Ethics?** /memory transparency, /forget deletion, bounded retention, refuses to discuss third parties; gaps: third-party text stored until evicted, no encryption, English-only, heuristic salience.
12. **What is the budget unit?** Items (working + long-term traces); sliding window/RAG get the same number of turns.
13. **Explain the activation equation.** B = ln Σ (now - t_j)^-d: sum over encoding/rehearsal times; power-law decay, more rehearsals raise it; lowest B (+ salience) is evicted.

## Know your code
`memchat/memory.py` (observe -> WM -> _encode -> _enforce_budget; answer -> _answer_slot / retrieve), `experiments/run.py` (evaluate, metrics), `experiments/benchmark.py` (generator).
