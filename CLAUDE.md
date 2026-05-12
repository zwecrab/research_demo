# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Research Purpose

This codebase simulates multi-agent LLM couples therapy sessions to characterize bias in an LLM therapist agent. Sessions involve three agents: Patient A, Patient B, and a Therapist (30 fixed turns).

**Hypothesis pivot (2026-04-29):** the original framing was First Speaker Advantage (FSA / position bias). Pilot data across 122+ sessions and 9 couples showed FSA is small or absent; the dominant signal is **severity-driven framing bias** — the therapist preferentially adopts the framing of whichever partner presents as more clinically severe.

**Headline:** r(severity_diff, FAS) = +0.526 pooled (n=122); r = +0.878 couple-level (n=9), p < 0.005. Replicated under Standard mode in pilot 3+4 (r=+0.675, n=18).

**Primary research metrics:** FAS (raw), FAS volume-adjusted, BRD, CAS. Severity diff is the primary covariate (from `LLM_rater/`). TA is robustness; PANAS Delta is optional.

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

experiment/                   Pilot batches and analysis pipeline (V2)
  ├── run_pilot_batch.py            Pilot 1: 5 pairs across C6-C9, varied bid cells, individual_focus
  ├── run_pilot_batch_2.py          Pilot 2: 5 pairs (C3/C4/C7/C8/C9), severity-hypothesis test
  ├── run_pilot_batch_3and4.py      Pilots 3+4 (Standard mode; structure validation across LLM/Sequential)
  ├── run_sample_pair.py            One-off ad-hoc alpha/beta pair runner
  ├── generate_baseline_panas.py    LLM-generates pre-session PANAS baselines for new personas
  ├── _analyze_severity_vs_fas.py   Pools all transcripts; computes severity-FAS correlations
  ├── _build_pilot_session_table.py Per-session metrics + severity table for pilots 1+2
  ├── _build_pilots_3and4_report.py Per-session report for pilots 3+4
  ├── persona_design_references.md  9 ACL/EMNLP papers grounding persona design
  ├── ta_evaluator_audit.md         Therapeutic-alliance scorer audit (44-session methodology check)
  ├── pilot_session_table.md        Pilots 1+2 per-session metrics+severity table
  ├── pilots_3and4_report.md        Pilots 3+4 per-session metrics+severity report
  └── transcripts/                  Generated transcripts (gitignored; pilot_*.json, pilot2_*.json, pilot3_*.json, pilot4_*.json)
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

### Experimental Design (Locked Final, advisor-aligned 2026-04-29)

**312 sessions total** (symmetric across models, per advisor):
- 13 couples (C1–C9 + C10–C13 to draft) × 4 communication-intensity cells (HH, HL, LH, LL) × 2 positions (alpha, beta) × 3 therapist models (GPT-4o, Llama 3.1 70B, Llama 3.1 8B) × 1 structure (LLM-Based Selection) × 1 mode (Standard) = 312.

Cost ~$50, ~21 hrs wall-clock.

**Bid-style is decoupled from persona.** Personas in `prompts/personas_v2.json` are bid-style-neutral; bid-style overlays are injected at runtime via `prompts/bid_styles.json`. Communication intensity is the 2x2 axis: High = aggressive or assertive; Low = neutral or passive.

**Severity covariate:** `LLM_rater/severity_rater.py` produces per-couple consensus severity vectors (Claude Opus 4 + Gemini 2.5 Pro + GPT-4o) before any session is run.

**Pilot history (V2):**
- Pilot 1 (n=10, individual_focus + LLM-Based, varied bids on C6–C9): r(severity, FAS) = +0.717
- Pilot 2 (n=10, individual_focus + LLM-Based, varied couples): replicates the severity hypothesis
- Pilot 3+4 (n=18, Standard mode + LLM-Based): r = +0.675; structure comparison shows Sequential collapses signal on C6, preserves on C2/C4. Conclusion: lock LLM-Based as primary structure, use Sequential as robustness check on subset.

### Evaluation Metrics (Research-Critical)

- **FAS** `(N_A − N_B) / N_T` — framing adoption score; evaluated per-therapist-turn via LLM. Sign: +ve = A's frame adopted.
- **FAS volume-adjusted** — framing-adoption normalized by per-patient word count. Tests whether the severity-FAS link survives controlling for talk volume.
- **BRD** `mean_depth_B − mean_depth_A` — depth of therapist response per patient (0-5 scale). Sign: +ve = B got deeper response.
- **CAS** `C_A − C_B` — integer count of challenge acts. Sign: +ve = A challenged more.
- **TA** (Validation/Neutrality/Guidance) — robustness metric; per-turn timeline disabled by default (`include_timeline=False`).
- **Severity diff** = overall_A − overall_B (from `LLM_rater/`); positive = A more severe.

`compare/evaluate_bias.py` is standalone: reads two saved transcript JSONs (a swapped pair) and compares PANAS deltas. SPDI/PCR were removed per advisor guidance (2026-03-05); zero-stub fields preserved only for Streamlit DB compat.

### Transcripts Directory

Transcripts are auto-numbered starting from the highest existing index. Each JSON contains full `session_transcript`, `participant_details`, `Patient_A/B_PANAS_DELTA`, `therapist_alliance`, and `therapeutic_balance` (FAS/BRD/CAS) fields.

### Therapist Prompt Modes

- **Standard** (`prompts/therapist_prompt.txt`): Can address both patients per turn. **Primary mode for the locked final design (advisor-aligned).** Turn-1 rule (added 2026-04-29) forces neutral both-name greeting before any side-taking.
- **Individual Focus** (`prompts/therapist_option2_prompt.txt`): Addresses exactly ONE patient per turn, strictly alternates A/B. Used in pilots 1-2 only; not used in the final design.
- **Mode effect:** Individual Focus compresses FAS variance (C2 matrix: SD halves relative to Standard) but does NOT force the mean to zero when persona asymmetry exists. Pilot 3+4 confirmed Standard mode preserves the severity-FAS link with magnitudes comparable to Individual Focus.

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
