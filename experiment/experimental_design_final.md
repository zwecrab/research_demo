# Experimental Design — Final (Locked 2026-04-29)

**Author:** Zwe (with advisor sign-off pending)
**Status:** locked pending advisor approval of severity pivot

## Phenomenon under study

Bias in an LLM therapist agent during multi-party couples therapy. The therapist preferentially adopts the framing of whichever partner presents as more clinically severe (severity-driven framing bias). Position bias (FSA) is investigated as a residual effect.

## Research questions and hypotheses

| # | RQ | Paired hypothesis |
|---|---|---|
| RQ1 | Does an LLM therapist exhibit severity-driven framing bias — adopting the more clinically severe partner's framing, controlling for word volume — and does this vary across communication-intensity pairings (HH/HL/LH/LL)? | H1a: r(severity_diff, FAS) > 0 AND r(severity_diff, FAS_volume_adjusted) > 0. H1b (exploratory): \|FAS\| largest in HH, smallest in LL |
| RQ2 | Does the severity-driven framing bias persist across four CBT-informed therapist prompt variants (Clinical-Judgment, CBT-Structured, CBT-Warm, CBT-Balanced) and across three LLM models? | r(severity_diff, FAS) > 0 in all 12 prompt × model cells; no single variant eliminates the bias |
| RQ3 | (Subsumed by RQ2) | Model comparison embedded in the 4×3 prompt × model matrix |

Communication intensity: High = aggressive or assertive bid; Low = neutral or passive bid.
Prompt variants: P1 Clinical-Judgment (standard), P2 CBT-Structured (Socratic, balanced), P3 CBT-Warm (empathic, plain language), P4 CBT-Balanced (strict alternation).

## Locked design parameters

| Parameter | Value |
|---|---|
| Couples | **13** (C1–C9 existing + C10–C13 to draft) |
| Cells per couple | 4 (HH, HL, LH, LL) |
| Positions per cell | 2 (alpha = A first, beta = B first) |
| Therapist models | 3 (GPT-4o, Llama 3.1 70B, Llama 3.1 8B) — **symmetric across all cells** |
| Structure | LLM-Based Selection (Sequential as robustness check on subset) |
| Therapist mode | Standard |
| Replicates per cell | 1 |
| Conversation temperature | 0.3 (sensitivity tested at 0.0 and 0.7 in pre-final pilot; see §Temperature pilot below) |
| Turns per session | 30 fixed |
| **Total sessions (primary RQ1)** | **312** |
| **Total sessions (prompt comparison RQ2)** | **192** (4 prompts × 8 pairs × 2 pos × 3 models) |

## Sample size justification

**RQ1 (couple-level Pearson r):** with 13 couples, detect r ≥ +0.70 at α=0.05, power=0.80 (Fisher Z; n=13 minimum). Pilot observed r=+0.878.

**RQ1 H1b — bid moderation (4-cell LMM):** 78 sessions/cell per model → f=0.25 detectable, power > 0.90. Exploratory.

**RQ2 — prompt robustness (4×3 matrix):** 8 pairs × 2 positions = 16 sessions per prompt-model cell. CI ±0.14; sufficient to confirm directional consistency.

## Metrics

| Metric | Role | Source |
|---|---|---|
| FAS (raw, signed) | Primary DV | `evaluate_balance.calculate_fas` |
| FAS volume-adjusted | Primary DV (RQ1 robustness) | `evaluate_balance.calculate_fas` (post 2026-04-29) |
| BRD | Secondary | `evaluate_balance.calculate_brd` |
| CAS | Secondary | `evaluate_balance.calculate_cas` |
| Severity diff (overall_A − overall_B) | Primary covariate | `LLM_rater/ratings/C*.json` (consensus of 3 frontier raters) |
| TA (Validation/Neutrality/Guidance) | Robustness (not headline) | `evaluate_therapist.evaluate_therapeutic_alliance` (per-turn timeline disabled) |
| PANAS Delta | Optional (drop unless patient-outcome claim is desired) | `panas_analyzer` |
| NAS, TSI | Supplementary descriptors only | `evaluate_balance.calculate_nas`, `calculate_tsi` |

## Temperature pilot (pre-final)

Advisor requirement: validate temperature sensitivity before locking. Pilot 2's 5 pairs were at temperature 0.3. Run 4 of those pairs at temperature 0.0 and 0.7, then compare with the existing 0.3 data.

- 4 pairs × 2 new temperatures × 2 positions = 16 new sessions
- Compare against existing pilot 2 (10 sessions at 0.3)
- Total comparison set: 26 sessions across 3 temperature levels
- Output: temperature × FAS magnitude/variance table; decide if 0.3 is the right primary temperature

## Cost and time estimate

312 sessions × ~$0.16 (mixed GPT-4o + Llama OpenRouter pricing) ≈ **~$50**.
Wall-clock at ~4 min/session: **~21 hours** (run in batches with overnight gaps).

## Pre-run checklist

1. Draft personas C10–C13 (4 couples, balanced under no-victim principle)
2. Run severity rater on C10–C13
3. Generate PANAS baselines for C10–C13 personas
4. Run temperature pilot (16 sessions); confirm 0.3 is appropriate
5. Pre-register primary contrasts (RQ1 H1a, RQ2 directional consistency) before final run
6. Execute 312-session run in 4-6 sub-batches

## Out of scope (deferred to future work)

- Sequential structure as full factor (collapsed signal on C6 in pilot 4)
- Individual Focus mode comparison (variance-compression control, used in pilots 1-2 only)
- 2-structure × 2-mode factorial (would inflate to 1248 sessions)
- C5 label-swap test for B-label-preference confound (mentioned as limitation in writeup)
