# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Research Purpose

This codebase simulates multi-agent LLM couples therapy sessions to **characterize** (not mitigate) First Speaker Advantage / position bias. Sessions involve three OpenAI agents: Patient A, Patient B, and a Therapist. The primary research metrics are FAS, BRD, CAS (therapist bias), TA (therapeutic alliance), and PANAS Delta (patient outcome).

## Setup

```bash
pip install openai python-dotenv
```

Create a `.env` file with:
```
OPENAI_API_KEY=sk-your-key-here
OPENROUTER_GPT_KEY=sk-or-...
OPENROUTER_L8B_KEY=sk-or-...
OPENROUTER_L70B_KEY=sk-or-...
```

All API calls (conversation generation, scoring, evaluation) route through OpenRouter.

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
python compare/evaluate_bias.py --t1 T1.json --t2 T2.json
```

## Architecture

```
main.py (orchestrator)
  ├── data_loader.py          load_all_assets() → personas, prompts, therapy plans, baseline PANAS
  ├── user_interface.py       CLI menus for topic / temperature / structure / first speaker / persona
  ├── session_setup.py        setup_session_parameters(), initialize_session_state()
  ├── conversation_engine.py  generate_agent_turn() [OpenRouter API], decide_next_speaker() [LLM-based]
  ├── panas_analyzer.py       pre/post PANAS scoring via LLM
  ├── evaluate_therapist.py   evaluate_therapeutic_alliance() → Validation/Neutrality/Guidance 0-10
  ├── evaluate_balance.py     calculate_fas(), calculate_brd(), calculate_cas()
  └── output_manager.py       save_session_json(), export_transcript_text()

batch_experiment.py           imports run_session_loop() and run_panas_analysis() from main.py
compare/evaluate_bias.py      generate_evaluation_report() — standalone, reads saved JSON transcripts (SPDI/PCR removed)

experiment/                   Test experiment (36 sessions, Individual Focus + Sequential)
  ├── run_test_experiment.py  Batch runner for 9 cells x 2 models x 2 positions; resume-capable
  ├── analyze_test_results.py Position effect, bid-style pairing, and model comparison analysis
  ├── generate_charts.py      3 chart types: position effect, bid-style, model comparison (200dpi PNG)
  ├── persona_design_references.md  9 ACL/EMNLP papers grounding persona design
  └── transcripts/            36 test session JSONs (test_cell01-09_llama8b/70b_alpha/beta.json)
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
| `CONVERSATION_MODEL` | `openai/gpt-4o` | Dialogue generation (OpenRouter) |
| `PANAS_MODEL` / `SCORING_MODEL` | `openai/gpt-4o` | PANAS scoring & FAS/BRD/CAS (OpenRouter) |
| `INTERVENTION_MODEL` | `openai/gpt-4o-mini` | Facilitation responses (unused in current mode) |
| `DEFAULT_THERAPIST_MODEL` | `openai/gpt-4o` | Therapist; switchable to Llama 8B/70B via OpenRouter |
| `SESSION_MIN_TURNS` / `SESSION_MAX_TURNS` | 30/30 | Fixed at 30 turns for experiment standardization |
| `INTERVENTION_THRESHOLD` | 65 | Score threshold to fire facilitation (unused in current LLM-only mode) |
| `MAX_TOKENS_PER_TURN` | 120 | Enforces concise agent responses |

### Conversation Structures

- **Sequential**: fixed `Therapist → Patient A/B → Therapist` rotation
- **LLM Only**: `decide_next_speaker()` picks the next patient using GPT; silence (`*(silence)*`) is allowed but guarded against consecutive same-patient silence

### Prompt Injection

`conversation_engine.py` injects persona fields into prompt templates at runtime. Patient prompts contain bracketed placeholders like `[name]`, `[traits]`, `[bid_style]`, `[hidden_tension_leakage]` that get filled from the selected persona's JSON fields. The therapist prompt uses `[insert persona seeds]`.

### Experimental Design (Full Experiment)

540 sessions total: 5 couples (10 personas) x 9 bid-style combos x 2 positions x 3 models x 2 structures.

**Bid-style is decoupled from persona.** Personas are bid-style-neutral (no aggression/passivity baked in). Bid-style (passive, assertive, aggressive) is injected at runtime as a separate prompt overlay, making it a within-subjects variable with 5 replications per cell. Persona file: `prompts/personas_v2.json` (pending).

**Three therapist models:** GPT-4o, Llama 3.1 8B, Llama 3.1 70B (all via OpenRouter).

**Test experiment findings (36 sessions, Individual Focus + Sequential):**
- Individual Focus produces consistent second-speaker (recency) advantage, not first-speaker (primacy) advantage. Mean DELTA_FAS = -0.18, only 22% of pairs show positive delta.
- Llama 8B is significantly noisier than 70B: |FAS| 0.61 vs 0.24, |BRD| 3.31 vs 0.68, |CAS| 5.0 vs 2.4.
- 70B shows 100% B-favoring DELTA_FAS (0/9 pairs positive).

### Evaluation Metrics (Research-Critical)

- **FAS** `(N_A − N_B) / N_T` — framing adoption score; evaluated per-therapist-turn via LLM
- **BRD** `mean_depth_B − mean_depth_A` — depth of therapist response per patient (0-5 scale)
- **CAS** `C_A − C_B` — integer count of challenge acts directed at each patient
`compare/evaluate_bias.py` is standalone: it reads two saved transcript JSONs (a swapped pair) and compares PANAS deltas without re-running sessions. SPDI/PCR were removed per advisor guidance (2026-03-05).

### Transcripts Directory

Transcripts are auto-numbered starting from the highest existing index. Each JSON contains full `session_transcript`, `participant_details`, `Patient_A/B_PANAS_DELTA`, `therapist_alliance`, and `therapeutic_balance` (FAS/BRD/CAS) fields.

### Therapist Prompt Modes

- **Standard** (`prompts/therapist_prompt.txt`): Can address both patients per turn, produce FAS = N (neutral). Default for primary FSA characterization.
- **Individual Focus** (`prompts/therapist_option2_prompt.txt`): Addresses exactly ONE patient per turn, strictly alternates A/B.
- **Mode effect (revised 2026-04-17):** Individual Focus *compresses* FAS and BRD variance (C2 matrix: SD halves relative to Standard) but does **not** force the mean to zero when persona asymmetry exists. The FAS scorer judges content framing adoption, not naming frequency, so a floor-prone persona still biases the therapist's content regardless of addressing rule. Use Standard as the primary characterization condition; Individual Focus is a variance-compression control, not a signal-destroyer. (Earlier guidance said IndFocus "forces FAS ≈ 0 by design" — this was observed in the 36-session test batch and did not generalize to C2.)

### CAS = 0 Is Legitimate

CAS counts cognitive challenges, assumption probes, and confrontations. Open-ended invitations ("What did you hear in Monica's words?", "Can you two explore...") are explicitly excluded. A supportive, validating session will produce CAS = 0. This is real data, not a bug.

## Prompt Quality — Challenge Protocol

Before executing any user request, assess whether it is going in the right direction. If the request contains a questionable assumption, a likely-wrong approach, or a direction that conflicts with prior findings, **challenge it explicitly** before proceeding.

Rules:
- Reference similar past tasks or data when relevant (e.g. "T192 had the same issue — aggressive B overrode position sign")
- Offer 2-4 concrete options with tradeoffs, not just "do you want to proceed?"
- If the user's framing contradicts established research findings (metrics, session patterns), flag the contradiction with evidence
- Do not just comply and note the problem afterwards — catch it before execution
- Keep the challenge brief (3-6 lines) and direct; no softening language
- Still challenge even if the user seems confident — they may be working under pressure or misremembering

This applies to: session generation choices, figure design, paper claim wording, code changes, and analysis interpretation.

## Lessons Learned

Before writing narrative claims about data (scripts, paper sections, slide notes), **always check `memory/lessons.md`** for past mistakes. Key rules:
- Cross-check every number against its source chart/table before attributing it to a category
- Alpha = A speaks first, Beta = B speaks first. Patient roles (A/B) stay fixed across conditions
- Chart annotations are usually within-session gaps, not cross-condition deltas
