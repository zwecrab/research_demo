# Replication Guide

This document describes how to reproduce the experimental results in this repository.

> Repository state at replication snapshot: `main` HEAD as of the date this file was last edited. Run `git log -1 --format=%h` to confirm.

---

## 1. Environment

- **Python**: 3.12.2 (tested)
- **OS**: Windows 11 (primary), expected to work on macOS/Linux unmodified
- **Shell**: PowerShell or bash; UTF-8 encoding required for Unicode emoji output

### Required environment variables (`.env` at repo root)

```env
OPENAI_API_KEY=sk-...           # legacy/optional fallback
OPENROUTER_GPT_KEY=sk-or-...    # primary key for GPT-4o, scoring, PANAS
OPENROUTER_L8B_KEY=sk-or-...    # for Llama 3.1 8B therapist runs
OPENROUTER_L70B_KEY=sk-or-...   # for Llama 3.1 70B therapist runs
```

All three OpenRouter keys must be present even if you only use one therapist
model — `data_loader.load_all_assets()` does not fail on a missing key, but the
matching model calls will. The severity rater uses `OPENROUTER_GPT_KEY` to call
all three of its raters.

### Required data file (not tracked in git)

```
discussions/Final_therapy_discussion.json
```

This holds per-topic therapy plans (goals, objectives, discussion notes). It
must exist before any session can be generated. Distribution is out of scope
for this repository — request from the author.

### Pinned dependency versions (key packages)

| Package | Version |
|---|---|
| openai | 1.12.0 |
| python-dotenv | 1.0.1 |
| streamlit | 1.54.0 |
| numpy | 2.3.5 |
| pandas | 2.3.3 |
| matplotlib | 3.9.2 |
| seaborn | 0.13.2 |
| nltk | 3.9.1 |
| scikit-learn | 1.6.1 |
| pydantic | 2.6.0 |
| httpx | 0.27.0 |
| tenacity | 8.2.3 |

Capture the full list with `pip freeze > requirements-frozen.txt` from a clean
venv before running experiments.

---

## 2. Pinned model identifiers

All model calls route through OpenRouter. Identifiers are pointers to the
provider's "latest" snapshot at request time, not immutable versions.

| Role | OpenRouter identifier | Used by |
|---|---|---|
| Conversation (Therapist + Patients) | `openai/gpt-4o` | `config.CONVERSATION_MODEL`, `DEFAULT_THERAPIST_MODEL` |
| Therapist alt (Llama 8B) | `meta-llama/llama-3.1-8b-instruct` | switchable per session |
| Therapist alt (Llama 70B) | `meta-llama/llama-3.1-70b-instruct` | switchable per session |
| PANAS scoring | `openai/gpt-4o` | `config.PANAS_MODEL` |
| FAS / BRD / CAS scoring | `openai/gpt-4o` | `config.SCORING_MODEL` |
| Intervention generation (unused in current runs) | `openai/gpt-4o-mini` | `config.INTERVENTION_MODEL` |
| Severity rater (consensus) | `anthropic/claude-opus-4`, `google/gemini-2.5-pro`, `openai/gpt-4o` | `LLM_rater/severity_rater.py` |

**Replicability caveat**: OpenRouter's `openai/gpt-4o` resolves to whichever
GPT-4o snapshot is current. Anthropic/Google identifiers behave similarly.
Re-runs at a different date may yield different outputs even with identical
prompts and temperature, because the upstream model may have changed.

To pin tightly, change the identifiers to dated snapshots when OpenRouter
exposes them (e.g. `openai/gpt-4o-2024-08-06`). At the time of writing,
some snapshots are exposed and others are not.

### Sampling parameters

| Parameter | Value | Set in |
|---|---|---|
| temperature (conversation) | 0.3 | per-session config |
| temperature (PANAS scoring) | 0.1 | `panas_analyzer.py` |
| temperature (severity rater) | 0.2 | `LLM_rater/severity_rater.py` |
| max_tokens per turn | 120 | `config.MAX_TOKENS_PER_TURN` |
| max_tokens (PANAS) | 1500 | `config.PANAS_MAX_TOKENS` |
| seed | not set | non-deterministic across runs |

---

## 3. Required data files

| File | Purpose |
|---|---|
| `discussions/Final_therapy_discussion.json` | therapy topic plans (NOT tracked) |
| `prompts/personas_v2.json` | 18 v2 personas, 9 couples C1–C9 |
| `prompts/personas_v2_PANAS.json` | pre-session baseline PANAS for all 18 personas |
| `prompts/bid_styles.json` | bid-style overlays (neutral, passive, assertive, aggressive) |
| `prompts/patient_prompt.txt` | unified patient prompt template |
| `prompts/therapist_prompt.txt` | Standard therapist prompt |
| `prompts/therapist_option2_prompt.txt` | Individual Focus therapist prompt |
| `prompts/panas_scoring_prompt.txt` | post-session PANAS scoring prompt |
| `prompts/trigger-personas.json` | legacy v1 personas (compat with older runners) |
| `prompts/trigger-personas_PANAS_2.json` | v1 PANAS baselines |
| `LLM_rater/ratings/C1.json` … `C9.json` | severity ratings per couple |

If the v2 persona file changes, severity ratings must be regenerated:

```bash
python LLM_rater/severity_rater.py --couple C<id>
```

---

## 4. Reproduction sequence

### 4.1 Generate severity ratings (one-time per persona set)

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python LLM_rater/severity_rater.py
```

Output: `LLM_rater/ratings/C*.json` for all couples in `personas_v2.json`.

### 4.2 Generate PANAS baselines (one-time per persona set)

PANAS for new personas:

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/generate_baseline_panas.py
```

Output: appended entries in `prompts/personas_v2_PANAS.json`.

### 4.3 Run pilot batch 1 (FSA hypothesis test, varied bid cells)

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_batch.py
```

Output: 10 sessions in `transcripts/pilot_<couple>_<bids>_<cell>_<position>.json`.

### 4.4 Run pilot batch 2 (severity hypothesis test)

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/run_pilot_batch_2.py
```

Output: 10 sessions in `transcripts/pilot2_<couple>_<bids>_<cell>_<position>.json`.

### 4.5 Run severity-vs-FAS analysis

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/_analyze_severity_vs_fas.py
```

Reads all pilot, sample, and matrix-run transcripts. Computes per-pilot,
pooled, couple-level, and per-dimension correlations.

### 4.6 Generate per-session metrics table

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/_build_pilot_session_table.py
```

Output: `experiment/pilot_session_table.md`.

### 4.7 (Optional) Single ad-hoc pair

```bash
SAMPLE_COUPLE=C7 SAMPLE_BID_A=neutral SAMPLE_BID_B=neutral \
  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 \
  python experiment/run_sample_pair.py
```

---

## 5. Run-time and cost expectations

Per session (30 turns, GPT-4o, individual_focus, LLM-Based Selection structure):

- Wall-clock: 3–5 minutes
- API calls: ~30 dialogue turns × 1 + speaker selector × ~30 + post-session
  scoring (FAS × ~15, BRD × ~15, CAS × ~15, NAS, TSI, PANAS × 2, TA × 1) ≈
  90–110 calls/session
- Token cost (GPT-4o, OpenRouter pricing as of 2026-04): ~$0.15–0.30 per session

A 10-session pilot batch: ~30–50 minutes wall-clock, ~$2–3 in API cost.

A full hypothetical 432-session design: ~30 hours wall-clock, ~$80–130 in API.

---

## 6. Known non-determinism

- OpenRouter does not currently expose a stable `seed` parameter for GPT-4o.
  Re-running an identical session yields slightly different transcripts.
- Severity ratings vary across runs because the rater uses temperature 0.2
  and prompts non-trivial reasoning. The consensus aggregate is stable across
  runs to ±0.3 on the overall score.
- FAS classifier runs once per therapist turn; integer counts can land on the
  same total even with different turn-by-turn classifications (verified
  against `pilot_C6_aggressive+neutral_HL_alpha.json` and
  `..._HL_beta.json`, which both produced FAS = +0.267 with different
  per-turn classification sequences).

---

## 7. Verifying a clean replication

After running the pilot batches, verify the headline statistic:

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python experiment/_analyze_severity_vs_fas.py | grep "couple-level"
```

Expected (within ±0.05 due to model drift):

```
r(severity_diff, mean_FAS) = +0.878
```

If the value drops below +0.7 or rises above +0.95, investigate model
identifier drift first, persona file integrity second.

---

## 8. Glossary of metric sign conventions

- **FAS** ∈ [−1, +1]: positive = therapist adopts Patient A's frame.
- **FAS volume-adjusted** ∈ [−1, +1]: same direction, normalized by per-patient word count.
- **BRD**: positive = Patient B got deeper response (higher mean depth).
- **CAS**: positive = Patient A challenged more.
- **NAS** (supplementary): positive = Patient A named more often.
- **severity_diff** = overall_A − overall_B: positive = A more severe.
- **dFAS** (alpha − beta): positive = FSA-direction; negative = SSA-direction.

The volume-adjusted FAS column will be missing for transcripts generated
before commit `0d30a5a` (added 2026-04-29) because the field did not exist
in those runs.
