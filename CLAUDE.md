# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Research Purpose

This codebase simulates multi-agent LLM couples therapy sessions to **characterize** (not mitigate) First Speaker Advantage / position bias. Sessions involve three OpenAI agents: Patient A, Patient B, and a Therapist. The primary research metrics are FAS, BRD, CAS (therapist bias), and SPDI/PCR (patient outcome position bias).

## Setup

```bash
pip install openai python-dotenv
```

Create a `.env` file with:
```
OPENAI_API_KEY=sk-your-key-here
```

Required data file (not tracked in git): `discussions/Final_therapy_discussion.json`

## Running Sessions

**Single interactive session:**
```bash
python main.py
```

**Non-interactive batch run** (edit `EXPERIMENTS`, `PATIENT_A`, `PATIENT_B`, `TOPIC_NAME` at the top of the file first):
```bash
python batch_experiment.py
```

**Evaluate position bias between a swapped pair:**
```bash
python compare/evaluate_bias.py --t1 transcripts/therapy_transcript_21.json --t2 transcripts/therapy_transcript_22.json
python compare/evaluate_bias.py --t1 T1.json --t2 T2.json --threshold 2
```

## Architecture

```
main.py (orchestrator)
  ├── data_loader.py          load_all_assets() → personas, prompts, therapy plans, baseline PANAS
  ├── user_interface.py       CLI menus for topic / temperature / structure / first speaker / persona
  ├── session_setup.py        setup_session_parameters(), initialize_session_state()
  ├── conversation_engine.py  generate_agent_turn() [OpenAI API], decide_next_speaker() [LLM-based]
  ├── panas_analyzer.py       pre/post PANAS scoring via LLM
  ├── evaluate_therapist.py   evaluate_therapeutic_alliance() → Validation/Neutrality/Guidance 0-10
  ├── evaluate_balance.py     calculate_fas(), calculate_brd(), calculate_cas()
  └── output_manager.py       save_session_json(), export_transcript_text()

batch_experiment.py           imports run_session_loop() and run_panas_analysis() from main.py
compare/evaluate_bias.py      compute_spdi(), compute_pcr() — standalone, reads saved JSON transcripts
```

### Data Flow

1. `load_all_assets()` reads `discussions/Final_therapy_discussion.json` (therapy plans), `prompts/trigger-personas.json` (persona traits), `prompts/trigger-personas_PANAS_2.json` (baseline PANAS scores), and all `.txt` prompt files from `prompts/`.
2. `setup_session_parameters()` resolves selected personas and topic into `participants` and `discussion_notes` dicts.
3. `run_session_loop()` drives the conversation: Therapist always goes first, then an LLM speaker-selector (`decide_next_speaker`) or sequential rotation picks the next patient. A hard same-speaker repeat guard enforces turn alternation.
4. After the loop, PANAS post-scores are computed via `panas_analyzer.py`, therapeutic alliance via `evaluate_therapist.py`, and balance metrics (FAS/BRD/CAS) via `evaluate_balance.py`.
5. Results are saved to `transcripts/therapy_transcript_<N>.json` (auto-incremented) and a readable `.txt` copy.

### Key Configuration (`config.py`)

| Constant | Default | Purpose |
|---|---|---|
| `CONVERSATION_MODEL` | `gpt-4o-mini` | Dialogue generation |
| `PANAS_MODEL` / `SCORING_MODEL` | `gpt-4o` | PANAS scoring & FAS/BRD/CAS |
| `SESSION_MIN_TURNS` / `SESSION_MAX_TURNS` | 25–35 | Turn range |
| `INTERVENTION_THRESHOLD` | 65 | Score threshold to fire facilitation (unused in current LLM-only mode) |
| `MAX_TOKENS_PER_TURN` | 120 | Enforces concise agent responses |

### Conversation Structures

- **Sequential**: fixed `Therapist → Patient A/B → Therapist` rotation
- **LLM Only**: `decide_next_speaker()` picks the next patient using GPT; silence (`*(silence)*`) is allowed but guarded against consecutive same-patient silence

### Prompt Injection

`conversation_engine.py` injects persona fields into prompt templates at runtime. Patient prompts contain bracketed placeholders like `[name]`, `[traits]`, `[bid_style]`, `[hidden_tension_leakage]` that get filled from the selected persona's JSON fields. The therapist prompt uses `[insert persona seeds]`.

### Evaluation Metrics (Research-Critical)

- **FAS** `(N_A − N_B) / N_T` — framing adoption score; evaluated per-therapist-turn via LLM
- **BRD** `mean_depth_B − mean_depth_A` — depth of therapist response per patient (0-5 scale)
- **CAS** `C_A − C_B` — integer count of challenge acts directed at each patient
- **SPDI** `Δ_first(e) − Δ_second(e)` — PANAS delta shift due to speaker-order position
- **PCR** `(N_consistent / N_total) × 100%` — proportion of emotions with `|SPDI| ≤ threshold`

`compare/evaluate_bias.py` is standalone: it reads two saved transcript JSONs (a swapped pair) and outputs SPDI/PCR without re-running sessions.

### Transcripts Directory

Transcripts are auto-numbered starting from the highest existing index. Each JSON contains full `session_transcript`, `participant_details`, `Patient_A/B_PANAS_DELTA`, `therapist_alliance`, and `therapeutic_balance` (FAS/BRD/CAS) fields.

## Lessons Learned

Before writing narrative claims about data (scripts, paper sections, slide notes), **always check `memory/lessons.md`** for past mistakes. Key rules:
- Cross-check every number against its source chart/table before attributing it to a category
- Alpha = A speaks first, Beta = B speaks first. Patient roles (A/B) stay fixed across conditions
- Chart annotations are usually within-session gaps, not cross-condition deltas
