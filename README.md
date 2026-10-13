# Memory-Inspired Chatbot

IT 207 Human Intelligence course project. A dialogue memory organised after human memory:
**attention gate → working memory (7 items) → episodic + semantic long-term memory → ACT-R activation, rehearsal and forgetting under a memory budget**.
Inspired by human memory; it does not model the brain and its parameters are borrowed, not fitted.

## Headline results (held-out test, budget = 40 items of a 120-turn conversation)
| System | Accuracy |
|---|---|
| Stateless | 0.167 |
| Sliding window | 0.435 |
| Plain RAG (FIFO) | 0.348 |
| **Memory-inspired** | **0.673** (95% CI 0.652-0.696) |

With gold fact extraction the memory model reaches 0.903 (perception is the bottleneck on unseen phrasing).
The advantage holds when memory is scarce; with unlimited memory, keeping everything is as good or better. Working memory gave no benefit; semantic memory and the attention gate matter most. See `report/` for the full analysis.

## Quick start
```bash
pip install numpy matplotlib pytest python-docx python-pptx
python -m pytest -q                      # 27 tests
python chat.py                           # interactive: /memory  /forget <slot|all>  /skip <hours>  /quit
python chat.py --demo                    # scripted multi-session demo
python experiments/run_all.py            # all experiments -> results/results.json (~2 min)
python experiments/make_figures.py       # figures -> report/figures/
python report/build_report.py            # report (.docx); python report/build_slides.py for slides
# real-data run needs LoCoMo:
mkdir -p data && curl -o data/locomo10.json https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json
```

## Layout
- `memchat/` core library (`memory.py` memory model, `extract.py` perception, `baselines.py`, `dialogue.py`, `text.py` BM25)
- `experiments/` benchmark generator, **dev** (`templates_dev.py`) and **held-out test** (`templates_test.py`) templates, harness, LoCoMo run
- `tests/`, `results/` (results.json, demo transcript), `report/` (report, slides, figures), `docs/` (viva notes)

## Evaluation protocol
Hyper-parameters were examined only on dev personas (seeds 1000-1029, dev templates). All reported numbers use test personas (seeds 2000-2099) with differently phrased templates written after the extractor/memory code was committed (c95a2ee). Only bug fixes were made afterwards; held-out accuracies were verified unchanged.

## Limitations
Synthetic templated benchmark, rule-based perception and reader (no LLM), no human evaluation, budget counted in items. Not a measure of anyone's intelligence or memory.

Data: LoCoMo (Maharana et al., ACL 2024), downloaded from github.com/snap-research/locomo (not redistributed here).
