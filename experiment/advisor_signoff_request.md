# Consolidated Sign-Off Request: Full-Experiment Design Revisions

**To:** [Advisor]
**From:** Zwe Htet
**Date:** 2026-04-21
**Subject:** Four design revisions requiring approval before the full FSA experiment runs

## Overview

Four revisions have emerged from recent design work that depart from the committee-presented 540-session plan. They are statistically motivated, methodologically defensible, and largely drawn from your own guidance on the Problem Severity analysis. I am requesting one consolidated sign-off rather than four separate approvals so the changes can be implemented as a coherent package.

Each item is presented with the change, the justification, the cost, and the specific decision I need from you.

---

## Item 1: Sample-size design replaces replication with power analysis

**Change.** The pre-existing 540-session plan was built on five replicates per cell (5 couples × 9 bid combos × 2 positions × 3 models × 2 structures). The revised plan derives the couple count from a-priori power analysis using the empirical effect size from the 36-session pilot (mean DELTA_FAS = -0.183, SD = 0.368, d_z = 0.50 across 18 paired sessions).

Under hierarchical gatekeeping (RQ1 primary at α = 0.05, RQ2-4 secondary with Holm correction at α = 0.0167), N = 36 couples gives 0.80 power for all four research questions.

**Justification.** Five-couples-per-cell is not a sample size calculation. At d_z = 0.50, the per-cell paired-t power is approximately 0.30, leaving the primary FSA test under-powered by a factor of three. Power-derived sampling makes the eventual finding defensible to ACL or EMNLP reviewers who will check the calculation.

**Cost.** N = 36 couples is approximately three times the current persona pool (11 couples in `personas_v2.json` plus `personas_v2_additions.json`). Roughly 14 new couples (28 personas) need to be authored before the full run.

**Decision required.** Approve replacing replication with power-derived N = 36 couples?

Reference document: `experiment/sample_size_calculation.md`.

---

## Item 2: Drop Llama-8B and Therapist-Mode Structure from the primary factorial

**Change.** The recommended design uses 2 positions × 3 bid pairings × 2 models (GPT-4o + Llama-70B) = 12 cells per couple, totalling 432 sessions. Therapist Mode (Standard versus Individual Focus) becomes a 136-session follow-up (2 structure × 2 position × 34 couples) using the same couple pool.

Llama-8B and Individual Focus remain fully supported in the codebase. They are excluded from the primary characterisation budget only, not from the toolchain. Either can be reactivated at any time for sensitivity analyses or follow-up studies.

**Justification.**

- **Llama-8B:** the pilot showed |FAS| = 0.61 on 8B versus 0.24 on 70B. The 8B numbers are dominated by stochastic noise rather than systematic position bias. Including 8B in the primary design adds variance without adding a defensible model contrast. The publishable model comparison is RLHF GPT-4o versus non-RLHF Llama-70B.
- **Therapist Mode (Structure):** per CLAUDE.md (2026-04-17), Individual Focus is a variance-compression control rather than a primary characterisation factor. Treating it as a follow-up keeps the primary design clean and isolates the FSA characterisation claim from the IndFocus retraction.

**Cost.** Total characterisation budget becomes 432 + 136 = 568 sessions, five per cent above the old 540 plan. Power-justified rather than replication-assumed.

**Decision required.** Approve the scope change (Llama-8B and Structure excluded from the primary factorial; both retained in code; Structure addressed via a 136-session follow-up)?

---

## Item 3: Problem Severity analysis with minimal-intake therapist as design-of-record

**Change.** Per your instruction, every couple is rated ex-ante on a five-dimension severity vector (anxiety, depression, trauma, attachment disorganisation, escalation tendency) by a multi-LLM rater consensus before the conversation session begins. The therapist then runs the session with minimal intake: only patient names and a one-sentence intake note ("married couple, here for communication concerns, no prior sessions"). Patients retain their full persona injection. The severity vector enters the analysis as a covariate:

```
FAS ~ Position + intake_richness + severity_diff_vector + Position × severity_diff_dim + (1 | Couple)
```

The current full-injection therapist (which receives Big Five OCEAN, hidden_intention, hidden_tension, cognitive_model, and full relationship history) is demoted to an "oracle therapist" comparison condition that runs in parallel.

**Justification.**

- The current full-injection therapist is ecologically invalid. Real first-session therapists do not receive private hidden intentions or full personality profiles. They receive a presenting complaint and basic demographics. The minimal-intake design matches actual first-session conditions.
- The severity covariate disambiguates "FSA" from "therapist correctly attending to the sicker patient." If the position coefficient survives partialling out severity, the FSA claim is robust against the severity confound. If it does not survive, what we were calling FSA was actually severity-tracking. Either result is publishable.
- The five-dimension vector is preferred over a single composite score per the HiTOP framework (Kotov et al., 2017): heterogeneous symptom domains should not be summed.
- The rater consensus uses three contemporary frontier models from different vendors: Claude 3 Opus, Gemini 2.5 Pro, and GPT-4o, all routed through OpenRouter. The therapist model is excluded from the rater pool to prevent circularity. No human clinician is involved per your guidance.

**Cost.** One additional LLM call per couple (severity rating). New minimal-intake therapist prompt. New rater prompt with rubric. Two new prompt files plus a rater script under a separate `LLM_rater/` directory.

**Decision required.** Approve all of: (a) the five-dimension severity rubric, (b) the multi-LLM rater approach, (c) the minimal-intake therapist as design-of-record, (d) the full-injection therapist demoted to oracle-control comparison?

Reference documents: `LLM_rater/README.md`; rubric draft to be circulated separately for your review before the rater is run.

---

## Item 4: Bundle the three primary FSA-suppression fixes into the same pilot re-run

**Change.** Three structural issues in the current pipeline absorb FSA signal before it can register in the metrics:

- **S1 Scorer redesign:** switch the FAS scorer from three-way categorical to pairwise preference (Zheng et al., 2023, Section 4.2), remove the auto-N rule for thin context, symmetrise the vocabulary-borrow disambiguation, and require judge-side A/B presentation swap. **This affects every reported FAS number, hence the explicit sign-off ask.**
- **S2 Airtime reopen:** drop the hard "never same speaker twice in a row" rule in the speaker-selection logic, replace with a soft three-or-more-consecutive guard, and add a Turn Share Index metric.
- **S3 Naming Asymmetry Score:** add a supplementary descriptive statistic counting how often the therapist names each patient by first name, computed retroactively on existing transcripts.

These three fixes were verified by both the project-management and academic-research review tracks. They will be implemented and tested together in the pilot re-run rather than three separate sequential re-runs.

**Justification.** Bundling halves the wall-clock cost of revalidation and avoids the diagnostic ambiguity that would arise from running them in sequence (an effect appearing after S1 might or might not have appeared without S2; bundling lets the regression model attribute variance correctly).

**Cost.** Re-run of the 36-session pilot from scratch. Existing transcripts cannot be retrofitted because the minimal-intake therapist prompt is a different prompt entirely.

**Decision required.** Approve the scorer scale change (the only one with reviewer-visible consequences for previously reported FAS numbers) and the bundling strategy?

Reference document: `experiment/fsa_signal_suppression_diagnosis.md`.

---

## Summary of decisions requested

| Item | Decision |
|---|---|
| 1 | Approve power-derived N = 36 couples replacing five-replicate cells |
| 2 | Approve dropping Llama-8B and Structure from the primary factorial (retained in code) |
| 3 | Approve Problem Severity design with five-dim vector, multi-LLM rater, minimal-intake design-of-record, full-injection demoted to oracle control |
| 4 | Approve the FAS scorer redesign and the bundling of S1-S3 into the pilot re-run |

I am happy to walk through any of these in person or to provide additional documentation. Reference papers are tracked in `REFERENCES.md` at project root and will be locked in the methodology section once approved.
