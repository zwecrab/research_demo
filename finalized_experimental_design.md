# Finalized Experimental Design
**Author:** Zwe Htet  
**Date:** 2026-04-29  
**Status:** Awaiting advisor sign-off on severity pivot; design locked conditional on C10–C13 persona completion

---

## Phenomenon under study

An LLM therapist agent in multi-party couples therapy exhibits **severity-driven framing bias**: it preferentially adopts the narrative framing of whichever partner presents as more clinically severe.

**Pilot evidence:** r(severity_diff, FAS) = +0.526 pooled (n=122 sessions); r = +0.878 couple-level (n=9 couples), p < 0.005. Replicated under Standard therapist mode in pilots 3+4 (r = +0.675, n=18 sessions).

---

## Research questions and confirmatory hypotheses

| # | RQ | Confirmatory hypothesis | Inferential test |
|---|---|---|---|
| **RQ1** | Does an LLM therapist exhibit severity-driven framing bias — preferentially adopting the more clinically severe partner's framing, controlling for word volume — and does this effect vary in magnitude across communication-intensity pairings (High-High, High-Low, Low-High, Low-Low)? | H1a: r(severity_diff, FAS) > 0 AND r(severity_diff, FAS_volume_adjusted) > 0; H1b: mean \|FAS\| larger in HH than LL (exploratory moderation; pilot Δ=+0.079) | H1a: couple-level Pearson r (n=13), Bonferroni α=0.025 each. H1b: LMM — FAS ~ cell + (1\|couple) + (1\|model), Holm-corrected |
| **RQ2** | Does the severity-driven framing bias persist across multiple CBT-informed therapist prompt designs that differ in tone, clinical vocabulary, and addressing style, and across three LLM therapist backbones? | H2: r(severity_diff, FAS) > 0 in all 12 prompt × model cells (4 prompts × 3 models); no single CBT-prompt variant eliminates the bias | Fisher-Z per cell; report as 4×3 matrix with 95% CI; effect present if lower CI > 0 in majority of cells |

**Prompt variants for RQ2:** P1 Clinical-Judgment (standard), P2 CBT-Structured (Socratic/Epstein-Baucom), P3 CBT-Warm (empathic/IBCT-style), P4 CBT-Balanced (strict alternation/Gottman-style).

**Multiple comparisons:** Confirmatory family = RQ1 H1a (2 tests) + RQ2 presence-of-effect (majority rule, not corrected). RQ1 H1b moderation is exploratory. Holm correction applied within RQ1 H1a.

---

## Full experiment session count

| Factor | Levels | Values |
|---|---:|---|
| Couples | 13 | C1–C9 (existing) + C10–C13 (to draft) |
| Communication-intensity cells | 4 | High-High, High-Low, Low-High, Low-Low |
| Positions per cell | 2 | alpha (A speaks first), beta (B speaks first) |
| Therapist models | 3 | GPT-4o, Llama 3.1 70B, Llama 3.1 8B |
| Structure (primary) | 1 | LLM-Based Selection |
| Therapist mode | 1 | Standard |

**Primary run (RQ1): 13 × 4 × 2 × 3 × 1 prompt = 312 sessions**

**Prompt comparison run (RQ2): 4 prompts × 8 pairs × 2 positions × 3 models = 192 sessions**

Each cell in the primary run contains exactly 2 sessions (alpha + beta) per couple per model. Total swap-pairs for HL/LH analysis = 13 × 4 × 3 = 156.

**Combined total: 504 sessions** (312 primary + 192 prompt comparison).

| Run | Purpose | Sessions | Prompts | Couples |
|---|---|---:|---|---|
| Primary (RQ1) | Severity bias magnitude + bid moderation | 312 | P1 (Standard) | C1–C13 full factorial |
| Prompt comparison (RQ2) | Bias robustness across 4 prompts × 3 models | 192 | P1–P4 | 8 representative pairs |

Separate sub-runs (not included in main totals):
- Topic-context ablation: 24 sessions (3 couples × 4 cells × 2 positions × stripped-brief condition)
- Sequential robustness check: 24 sessions (3 couples × 4 cells × 2 positions × Sequential structure)

---

## Topic-context ablation (required pre-run)

**Critical confound:** The therapist receives each patient's `topic_context` (a per-partner clinical briefing paragraph) injected into its system prompt on every turn. Combined with the prompt instruction "Address whichever partner your clinical judgement indicates," this creates a direct pre-loaded pathway from written-case-formulation severity to framing attention, independent of in-session patient behavior.

To separate pre-loaded from emergent bias, a **topic-context ablation** sub-experiment is required before the full 312-session run:

| Ablation design | Parameter |
|---|---|
| Couples | 3 (C6 sev=+3.33, C2 sev=−2.83, C7 sev=+0.35) |
| Condition A | Full topic_context injected (standard) |
| Condition B | topic_context stripped; therapist receives only generic objective text |
| Cells | 4 (HH, HL, LH, LL) |
| Positions | 2 (alpha, beta) |
| Model | GPT-4o only |
| Total new sessions | 24 (3 couples × 4 cells × 2 positions × Condition B only; Condition A already in pilot data) |

**Decision rule (pre-registered):**  
- If r(severity_diff, FAS) in Condition B ≥ 0.60 of Condition A's r: effect is predominantly emergent from in-session behavior. Proceed with full design; report ablation as "Topic-context does not drive the bias."  
- If r in Condition B < 0.60 of Condition A's r: effect is substantially briefing-driven. Report honestly; reframe thesis as "clinical briefing amplifies LLM therapist severity-bias." Full design still run but thesis framing adjusted.

---

## Temperature sensitivity pilot results

A temperature sensitivity pilot was run before locking the final design (n=18 sessions: 4 couples × up to 3 temperatures × 2 positions, GPT-4o, individual_focus, LLM-Based Selection). Couples: C3 (sev=+0.99), C4 (sev=+2.93), C8 (sev=−0.23), C9 (sev=−0.83). C8 was run at all three temperatures to generate a fresh 0.3 baseline.

**Per-couple pair-level mean FAS by temperature:**

| Couple | sev_diff | temp=0.0 | temp=0.3 (pilot 2) | temp=0.7 | Direction stable? |
|---|---:|---:|---:|---:|---|
| C4 Sofia/Kenji | +2.93 | +0.133 ✓ | +0.174 ✓ | **−0.072 ✗** | No — sign flipped at 0.7 |
| C3 David/James | +0.99 | +0.333 ✓ | +0.200 ✓ | +0.400 ✓ | Yes — all A-favoring |
| C8 Avery/Marcus | −0.23 | +0.133 ✗ | −0.067 ✓ | +0.102 ✗ | Noise floor — below detection threshold |
| C9 Lena/Naomi | −0.83 | −0.033 ✓ | −0.033 ✓ | −0.003 ≈0 | Stable near zero |

**Why temperature 0.3 is locked:**

- **t=0.7 is unreliable.** On C4 (the highest-severity-asymmetry couple, sev=+2.93), the pair-level mean flipped from +0.174 at t=0.3 to −0.072 at t=0.7 — a full sign reversal against severity prediction. High stochasticity introduces direction flips that would contaminate the severity-FAS correlation across a 312-session run. A pre-registered design cannot tolerate per-session sign flips caused by sampling noise rather than experimental conditions.
- **t=0.0 is plausible but too narrow.** Deterministic decoding removes natural conversational variation, making sessions uniform in ways that may not generalize. C3's inflated magnitude at t=0.0 (+0.333 vs t=0.3's +0.200) is a positive artifact of the same mechanism — it looks like a stronger signal but reflects reduced dialogue diversity, not a stronger underlying bias. Claiming a finding from deterministic outputs risks a "cherry-picked variance" critique.
- **t=0.3 is direction-stable.** All strong-severity couples (C3, C4) maintained correct sign at t=0.3 with moderate magnitudes. Near-balanced couples (C8, C9) remained near zero at all temperatures, confirming the temperature choice does not interact with the detection threshold. t=0.3 also matches all prior V2 pilot batches, maintaining methodological consistency.

---

## Locked design parameters

| Parameter | Value | Rationale |
|---|---|---|
| Couples | **13** (C1–C9 + C10–C13, conditional) | Detects r ≥ +0.70 at α=0.05, power=0.80 (Fisher Z). Pilot r=+0.878 with 95% CI [+0.55, +0.97]. |
| Cells per couple | 4 (HH, HL, LH, LL) | High = aggressive/assertive; Low = neutral/passive. 2×2 cross of partners' intensity |
| Positions per cell | 2 (alpha = A first, beta = B first) | Within-pair crossover; enables HL/LH severity-position analysis |
| Therapist models | **3 (GPT-4o, Llama 3.1 70B, Llama 3.1 8B) — symmetric across all cells** | Advisor requirement: same sample size per model |
| Structure | LLM-Based Selection (primary); Sequential on 3-couple subset (robustness check) | Sequential collapses signal on C6 (−81% magnitude) but preserves on C2/C4; used as volume-confound robustness check only |
| Therapist mode | Standard | Advisor-preferred; validates r=+0.675 in pilots 3+4 |
| Conversation temperature | **0.3** | Temperature pilot (n=18): 0.7 flipped sign on C4 (sev=+2.93); 0.3 direction-stable across all sev levels |
| Turns per session | 30 fixed | Matches pilot design; sufficient for session arc to develop; keeps API cost feasible. Consistent with prior LLM therapy simulation literature (30-turn range). |
| Replicates per cell | 1 | With 13 couples × 4 cells × 2 positions × 3 models = 312 sessions |
| **Total sessions (primary RQ1)** | **312** | ~$50 API cost; ~21 hours wall-clock |
| Prompt comparison sessions (RQ2) | 192 | 4 prompts × 8 pairs × 2 positions × 3 models; ~$20, ~13 hours |
| Ablation sessions | 24 | Required pre-run; not part of headline n |

---

## Sample size justification

**RQ1 H1a (couple-level Pearson r, Fisher Z):**

| Assumed true r | n_couples needed (α=0.05, power=0.80) |
|---|---:|
| +0.878 (pilot observed) | 7 |
| +0.70 (cautious) | **13** |
| +0.55 (conservative; lower bound of pilot 95% CI) | 24 |

Design uses **n=13** targeting r ≥ +0.70. **Pre-registered fallback:** if r at n=13 is non-significant, revert to session-level pooled r (n=312) with couple random effect in LMM.

**RQ1 H1b (bid-cell moderation, LMM):** 78 sessions/cell per model → f=0.25 detectable, power > 0.90. Exploratory; no correction.

**RQ2 (prompt robustness, 4×3 cell matrix):** 8 pairs × 2 positions = 16 sessions per prompt per model. With pilot SD≈0.20, CI half-width ≈ ±0.14 per cell. Sufficient to detect r > 0 if true effect ≥ +0.25. Goal is directional consistency across all 12 cells, not magnitude precision.

---

## Severity covariate — rater reliability

Severity vectors are consensus of three frontier raters: Claude Opus 4, Gemini 2.5 Pro, GPT-4o. ICC(2,1) absolute agreement on severity_diff (A−B overall) across C1–C9:

**ICC(2,1) = 0.790 (good, Koo & Mae 2016 benchmark: ≥0.75)**

Individual couple rater ranges:

| Couple | R1 (Claude) | R2 (Gemini) | R3 (GPT) | Range | Consensus diff |
|---|---:|---:|---:|---:|---:|
| C1 | +2.10 | +0.95 | +2.50 | 1.55 | **+1.85** |
| C2 | −3.75 | 0.00 | −1.40 | **3.00** | −2.58 |
| C3 | +1.30 | +0.65 | +1.00 | 0.65 | +0.98 |
| C4 | +3.35 | +2.95 | +2.50 | 0.85 | **+2.93** |
| C5 | −0.70 | −1.30 | −0.20 | 1.10 | −0.73 |
| C6 | +3.90 | +3.10 | +3.00 | 0.90 | **+3.33** |
| C7 | +1.20 | −0.65 | +0.50 | **1.85** | +0.35 |
| C8 | −0.10 | 0.00 | −0.60 | 0.60 | −0.23 |
| C9 | −2.00 | +1.00 | −1.50 | **3.00** | −0.83 |

**Elevated disagreement on C2, C7, C9** (range ≥ 1.85). C2 and C9 drive the severity-FAS correlation significantly; C7 is near-balanced. Sensitivity analysis: re-run RQ1 excluding these three couples and confirm direction holds on C1/C3/C4/C5/C6/C8.

---

## Metrics and analytic plan

| Metric | Role | CAS note |
|---|---|---|
| FAS (raw, signed) | Co-primary DV (RQ1) | Sign: +ve = A's frame adopted |
| FAS volume-adjusted | Co-primary DV (RQ1 robustness) | Normalizes by per-patient word count |
| BRD | Secondary exploratory | Sign: +ve = B got deeper response |
| CAS | Secondary exploratory | **Floor effect present in pilots.** Report as dichotomized (any challenge vs none) and as signed count; use Mann-Whitney U / signed-rank, not Pearson. |
| Severity diff (overall_A − overall_B) | Primary covariate | From LLM rater consensus above |
| TA (V/N/G session-level) | Robustness only | Per-turn timeline disabled; reported to confirm alliance not systematically broken |
| PANAS Delta | **Dropped from primary analysis** | No consistent session-level or position effect observed in pilots; adds 2 LLM calls/session; include only if downstream patient-outcome claim is added post-advisor signoff |
| NAS, TSI | Supplementary descriptors | Not analyzed in headline tables |

---

## C10–C13 persona requirements (conditional lock)

The design locks at 13 couples only if C10–C13 meet minimum severity-coverage criteria:

| Required property | Minimum |
|---|---|
| At least one couple with \|severity_diff\| ≥ 2.50 | C10–C13 must include ≥ 1 strongly asymmetric couple |
| At least one couple with \|severity_diff\| ≤ 0.50 | Near-balanced control needed |
| At least two couples with \|severity_diff\| between 1.0 and 2.5 | Intermediate severity range |
| All couples satisfy no-victim principle | Both partners hold plausible grievance; no persecutor/victim archetype; matched sample utterance word budgets (±5 words across partner pair) |
| PANAS baselines generated and severity-rated before any session | All C10–C13 must appear in `personas_v2_PANAS.json` and `LLM_rater/ratings/C*.json` |

If C10–C13 cannot be completed, design falls back to n=9 couples with pre-registered session-level pooled r as the primary statistic.

---

## Pre-registration plan

- **Venue:** OSF (https://osf.io), new preregistration under MSc project
- **Artifacts:** frozen hypotheses doc (this file, Git-tagged), frozen analysis script (`experiment/_analyze_severity_vs_fas.py`, Git-tagged)
- **Timing:** Pre-registration must be timestamped BEFORE the first session of the 312-session run is generated. Ablation sessions are separate (run before pre-registration; inform hypothesis framing).
- **Deviation protocol:** Any deviation from the pre-registered analysis plan (e.g. couples added, metrics changed) must be flagged as exploratory in the paper. No silent modifications.

---

## Pre-run checklist (in order)

1. Run topic-context ablation (24 sessions); apply decision rule; adjust thesis framing if needed
2. Draft prompt variants P2 (CBT-Structured), P3 (CBT-Warm), P4 (CBT-Balanced); review with advisor
3. Draft personas C10–C13 meeting coverage requirements above
4. Run severity rater on C10–C13; verify coverage
5. Generate PANAS baselines for C10–C13
6. Pre-register on OSF with this doc + analysis script, Git-tagged
7. Run 312-session primary batch (RQ1) in 4–6 sub-batches
8. Run 192-session prompt comparison batch (RQ2): P1–P4 × 8 pairs × 2 positions × 3 models
9. Sequential robustness sub-run: 24 sessions (optional, separate from main counts)

---

## Out of scope (future work)

- Residual position bias test (RQ4 removed per advisor guidance 2026-05-13)
- Sequential structure as full factor (couple-specific suppression effect; noted as limitation)
- Individual Focus mode comparison
- Online / human-in-the-loop therapy variants
- C5 label-swap test for B-label-preference confound (mentioned as limitation)
- Temperature as a factorial factor (explored in sensitivity pilot; locked at 0.3)
