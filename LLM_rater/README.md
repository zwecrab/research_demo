# LLM Rater (Problem Severity Analysis)

**Purpose:** ex-ante mental-health severity rating of each patient persona, using a multi-LLM rater consensus, to enter as a covariate in the FSA regression model.

**Status:** scaffolded (2026-04-21). Implementation pending advisor sign-off on the full Problem Severity design.

## Why this folder exists separately from `experiment/`

The rater pipeline is a measurement instrument applied to personas. It runs once per couple and produces a severity vector that the experiment pipeline consumes. Keeping it isolated from `experiment/` prevents the rater from being mistaken for a session-generation component and prevents its model dependencies (Claude, Gemini, GPT-4o via OpenRouter) from leaking into the conversation pipeline.

## Planned Contents

| File | Status | Purpose |
|---|---|---|
| `severity_rubric.md` | pending | 5-dimensional severity rubric: anxiety, depression, trauma, attachment disorganisation, escalation tendency. Anchor descriptions per dimension (passive / moderate / severe markers). |
| `severity_rater_prompt.txt` | pending | Template prompt sent to each rater LLM. Contains rubric, persona content, and JSON output schema. |
| `severity_rater.py` | pending | Python script. Reads `prompts/personas_v2.json` + `personas_v2_additions.json`, calls three rater LLMs through OpenRouter, computes inter-LLM kappa, writes per-couple severity vectors to `ratings/`. |
| `ratings/` | pending | Per-couple severity rating JSONs. Schema: `{couple_id, severity_A: {anxiety, depression, trauma, attachment, escalation}, severity_B: {...}, inter_rater_kappa, raters: [...]}`. |

## Models (all via OpenRouter)

Per project convention (CLAUDE.md): all API calls route through OpenRouter. Rater models are deliberately drawn from a different family than the conversation therapist to avoid circularity.

| Rater slot | Planned model | OpenRouter ID (to be confirmed) |
|---|---|---|
| Rater 1 | Claude 3 Opus | `anthropic/claude-3-opus` |
| Rater 2 | Gemini 2.5 Pro | `google/gemini-2.5-pro` |
| Rater 3 | GPT-4o | `openai/gpt-4o` |

**Generation cohort rationale:** all three raters were Anthropic / Google / OpenAI flagship models from the same general timeframe (early 2024 to early 2025), so capability is broadly comparable. Using same-generation contemporaries prevents one rater from systematically dominating the consensus due to a generational gap.

If the conversation therapist model is GPT-4o, the GPT rater is excluded from the consensus to preserve model-family independence; only the two non-GPT raters contribute to severity_diff for that condition.

## Output Schema (per couple)

```json
{
  "couple_id": "C1_Okafor",
  "rated_at": "2026-04-21T14:00:00Z",
  "patient_A": {
    "name": "Adaeze Okafor",
    "severity_vector": {
      "anxiety": 0.0,
      "depression": 0.0,
      "trauma": 0.0,
      "attachment_disorganisation": 0.0,
      "escalation_tendency": 0.0
    },
    "raters": [
      {"model": "anthropic/claude-opus-4-7", "scores": {...}},
      {"model": "google/gemini-2.5-pro", "scores": {...}},
      {"model": "openai/gpt-4o", "scores": {...}}
    ]
  },
  "patient_B": { ... },
  "severity_diff_vector": {
    "anxiety": 0.0,
    "depression": 0.0,
    "trauma": 0.0,
    "attachment_disorganisation": 0.0,
    "escalation_tendency": 0.0
  },
  "inter_rater_kappa": {
    "anxiety": 0.0,
    "depression": 0.0,
    "trauma": 0.0,
    "attachment_disorganisation": 0.0,
    "escalation_tendency": 0.0,
    "overall": 0.0
  }
}
```

## Pipeline Position

```
prompts/personas_v2.json
       │
       ▼
LLM_rater/severity_rater.py        (one-time per couple)
       │
       ▼
LLM_rater/ratings/<couple_id>.json
       │
       ▼
batch_experiment.py                (reads severity_diff_vector at session-init)
       │
       ▼
transcripts/<session>.json         (severity_diff_vector copied into session metadata)
       │
       ▼
analysis: FAS ~ Position + intake_richness + severity_diff_vector + ... + (1 | Couple)
```

## Pending Advisor Sign-Off

Before any of the planned files are drafted:
1. Advisor confirms the 5-dimension rubric covers the right symptom domains for couples-therapy context.
2. Advisor confirms the multi-LLM rater (no human anchoring) is acceptable.
3. Advisor confirms the dual-condition intake design (minimal-intake as design-of-record + full-injection as oracle control).

References for the rubric design and methodology are tracked in `REFERENCES.md` under "Problem Severity Analysis (`LLM_rater/`)".
