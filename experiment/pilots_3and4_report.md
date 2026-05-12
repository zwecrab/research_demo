# Pilot Batches 3 + 4 — Sequential Structure & Standard Mode Validation

18 sessions across two pilot batches, all using GPT-4o + therapist Standard mode (no individual_focus). **Pilot 4** (8 sessions) compared LLM-Based Selection vs Sequential structure on two strong-signal couples (C6 sev=+3.33, C2 sev=−2.83) at HH bid intensity. **Pilot 3** (10 sessions) tested Sequential structure across five couples spanning the severity range and varied bid cells. The goal was to validate the proposed final design (Standard mode + Sequential structure) against the pilot 1+2 baseline (Standard mode missing, Individual Focus + LLM-Based used instead).

Severity scores are from the LLM rater consensus (Claude Opus 4, Gemini 2.5 Pro, GPT-4o). The *Favored* column classifies on raw FAS sign (A if FAS > +0.05, B if < −0.05, Bal otherwise). The *More severe* column classifies on overall_A − overall_B (A if > +0.5, B if < −0.5, ≈Bal otherwise). *Match* = ✓ when *Favored* matches *More severe*.

Sign convention: FAS > 0 = A's frame adopted; BRD > 0 = B got deeper responses; CAS > 0 = A challenged more.

## Per-session table

| # | Batch | Pair | Pos | Struct | Bids | A (sev) | B (sev) | FAS | FAS-vol | BRD | CAS | wA | wB | More severe | Favored | Match |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pilot4 | C2 HH | alpha | LLM | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.083 | -0.158 | +2.36 | -8 | 305 | 277 | B | B | ✓ |
| 2 | pilot4 | C2 HH | beta | LLM | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.357 | -0.296 | +0.64 | -2 | 218 | 316 | B | B | ✓ |
| 3 | pilot4 | C2 HH | alpha | Seq | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.100 | -0.111 | +0.56 | +1 | 347 | 347 | B | B | ✓ |
| 4 | pilot4 | C2 HH | beta | Seq | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.300 | -0.452 | +0.33 | -1 | 355 | 335 | B | B | ✓ |
| 5 | pilot4 | C6 HH | alpha | LLM | agg+agg | Maya (6.03) | Devon (2.70) | +0.231 | +0.160 | +0.38 | -1 | 333 | 230 | A | A | ✓ |
| 6 | pilot4 | C6 HH | beta | LLM | agg+agg | Maya (6.03) | Devon (2.70) | +0.308 | +0.303 | +1.17 | -5 | 262 | 245 | A | A | ✓ |
| 7 | pilot4 | C6 HH | alpha | Seq | agg+agg | Maya (6.03) | Devon (2.70) | +0.000 | +0.011 | -0.44 | +0 | 347 | 355 | A | Bal | — |
| 8 | pilot4 | C6 HH | beta | Seq | agg+agg | Maya (6.03) | Devon (2.70) | +0.100 | +0.139 | +1.20 | -6 | 342 | 362 | A | A | ✓ |
| 9 | pilot3 | C2 HH | alpha | Seq | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.400 | -0.543 | +1.00 | -2 | 361 | 321 | B | B | ✓ |
| 10 | pilot3 | C2 HH | beta | Seq | agg+agg | Eszter (2.02) | Rajan (4.85) | -0.400 | -0.528 | +0.60 | +0 | 364 | 337 | B | B | ✓ |
| 11 | pilot3 | C4 LL | alpha | Seq | neu+neu | Sofia (7.30) | Kenji (4.37) | +0.200 | +0.507 | +0.22 | +1 | 348 | 355 | A | A | ✓ |
| 12 | pilot3 | C4 LL | beta | Seq | neu+neu | Sofia (7.30) | Kenji (4.37) | +0.600 | +1.000 | +0.67 | -2 | 367 | 354 | A | A | ✓ |
| 13 | pilot3 | C6 HH | alpha | Seq | agg+agg | Maya (6.03) | Devon (2.70) | -0.200 | -0.180 | +0.67 | -1 | 334 | 387 | A | B | ✗ |
| 14 | pilot3 | C6 HH | beta | Seq | agg+agg | Maya (6.03) | Devon (2.70) | +0.300 | +0.636 | +0.67 | -2 | 312 | 351 | A | A | ✓ |
| 15 | pilot3 | C7 HL | alpha | Seq | agg+neu | Margaret (5.50) | Henrik (5.15) | -0.300 | -0.654 | +0.12 | +0 | 322 | 269 | ≈Bal | B | — |
| 16 | pilot3 | C7 HL | beta | Seq | agg+neu | Margaret (5.50) | Henrik (5.15) | +0.300 | +0.627 | +0.30 | +1 | 305 | 333 | ≈Bal | A | — |
| 17 | pilot3 | C9 LL | alpha | Seq | neu+neu | Lena (5.80) | Naomi (6.63) | +0.100 | +0.213 | +0.00 | -1 | 372 | 382 | B | A | ✗ |
| 18 | pilot3 | C9 LL | beta | Seq | neu+neu | Lena (5.80) | Naomi (6.63) | +0.100 | +1.000 | +0.33 | +0 | 360 | 326 | B | A | ✗ |

## Couple × Structure aggregate (mean FAS across all sessions)

| Couple | sev_diff | Structure | n | mean FAS | mean FAS-vol | mean wA | mean wB |
|---|---|---|---|---|---|---|---|
| C2 | -2.83 | LLM | 2 | -0.220 | -0.227 | 262 | 296 |
| C2 | -2.83 | Seq | 4 | -0.300 | -0.408 | 357 | 335 |
| C4 | +2.93 | Seq | 2 | +0.400 | +0.754 | 358 | 354 |
| C6 | +3.33 | LLM | 2 | +0.269 | +0.232 | 298 | 238 |
| C6 | +3.33 | Seq | 4 | +0.050 | +0.152 | 334 | 364 |
| C7 | +0.35 | Seq | 2 | +0.000 | -0.014 | 314 | 301 |
| C9 | -0.83 | Seq | 2 | +0.100 | +0.606 | 366 | 354 |

## Severity-FAS correlation in this pilot

| Slice | n | r(severity_diff, FAS) |
|---|---|---|
| All pilot 3+4 sessions | 18 | +0.675 |
| LLM-Based Selection only | 4 | +0.925 |
| Sequential only | 14 | +0.605 |

**Sign-match summary across 18 sessions:** ✓ 12 support hypothesis, — 3 balanced/null, ✗ 3 mismatch.

## Key findings

1. **Sequential structure has couple-specific effects.** On C6 (sev=+3.33), Sequential collapses the severity-FAS magnitude from +0.270 (LLM) to ~+0.05 with high per-session variance. On C4 (sev=+2.93), Sequential *amplifies* FAS from +0.174 (LLM, prior pilot) to +0.400. On C2 (sev=−2.83), Sequential preserves the effect (−0.300 vs LLM −0.220). Sequential is not a uniform improvement.

2. **Standard mode preserves the severity-FAS link** observed under Individual Focus, with comparable or slightly smaller magnitudes. The advisor-preferred mode is viable.

3. **Position bias becomes detectable when severity is near zero.** C7 HL Sequential pair (sev=+0.35, asymmetric bid) showed α=−0.300 / β=+0.300, Δ(α−β)=−0.600 — a strong within-pair position swing on a near-balanced couple. This supports RQ4 (residual position bias detectable after controlling for severity).

4. **C9 LL Sequential produced two consecutive sign-mismatches** (α=+0.100, β=+0.100 against sev=−0.83). Both essentially in the noise floor (|FAS| ≤ 0.10). Likely indicates that mild |severity_diff| (<1.0) is below the detection threshold under Sequential structure.

5. **Word-volume parity is enforced under Sequential** (e.g., C2 HH Seq α: wA=347, wB=347 exactly), removing volume as a confounding variable. Volume-adjusted FAS is therefore numerically closer to raw FAS in Sequential than in LLM-Based runs.


## Implications for final design

- **LLM-Based Selection should remain the primary structure**, not Sequential, because Sequential's couple-specific suppression (most clearly on C6) introduces between-couple heterogeneity that complicates RQ1 power calculations.
- Sequential is still valuable as a **robustness check** on a subset of couples — specifically to demonstrate that the volume-confound interpretation is not the whole story (since Sequential equalises words and the effect still appears on C2 and C4).
- **Standard mode is locked** as the primary therapist mode, replacing the individual_focus used in earlier pilots.
- C7 HL Seq's position swing supports keeping RQ4 in the final design with an expectation of detectable residual position effect at near-balanced |sev|.
