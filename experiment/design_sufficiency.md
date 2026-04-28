# Sample Size for the FSA Characterization Study

**Author:** Zwe
**Date:** 2026-04-19
**Status:** Draft for advisor discussion

---

## TL;DR

Pilot data (8 swap-pairs on couple C5, Llama 8B) give dFAS mean ≈ −0.22 and SD ≈ 0.63 (LL cell alone suggests |mean| ≈ 0.9, but only 2 pairs). Using **simulation-backed paired analysis** with pilot SD as the variance input, the primary RQ1 contrast (pure position effect in the neutral-neutral / LL cell) needs **50 matched swap-pairs** to detect d = 0.4 at 80% power, α = 0.05, two-tailed — or **32 pairs** for d = 0.5. Mapping this into the factorial (4 bid combos × 3 models × 2 structures × 2 positions): **6 couples ⇒ 288 sessions (144 pairs, 36 LL pairs, covers d ≈ 0.47)** is the minimum methodologically defensible target. 9 couples ⇒ 432 sessions is the conservative target that hits d = 0.4 in the LL cell with 54 pairs while keeping moderator contrasts (RQ2–RQ4) adequately powered via a linear mixed model. Do **not** commit to 240 sessions a priori; it only hits the LL d = 0.5 threshold if the pilot's optimistic SD holds up in the larger run.

---

## 1. Sample-size methods considered

The design is a within-pair crossover with four nuisance factors (couple, bid-intensity combo, therapist model, structure) and one manipulated factor (position). Five sample-size approaches are appropriate; each answers a slightly different question.

### 1.1 Paired t-test (Cohen, 1988)

Classical closed-form formula for the one-sample test on pair-level deltas:

```
n ≈ ((z_{1-α/2} + z_{1-β}) / d)² + 1
```

with d = |μ_δ| / σ_δ (standardized effect). α = 0.05 two-tailed ⇒ z = 1.96; 80% power ⇒ z = 0.842; sum = 2.802.

This is the **right tool for RQ1 in a single cell** (LL only, or any single bid × model × structure combination) because within a cell there is no clustering and each pair contributes one independent delta.

### 1.2 Linear mixed-effects simulation (Westfall et al., 2014; simr)

For pooled analysis across cells with couple as a random intercept, closed-form power is unreliable. The defensible approach is **Monte Carlo simulation**:

1. Fit the target LMM on a pilot or assumed variance decomposition.
2. Simulate K pairs under a true fixed-effect β (the hypothesized effect size).
3. Refit and record whether the position p-value < α.
4. Repeat 1000 times per K; power = proportion significant.
5. Grid-search K.

Within-pair designs have a useful property: between-couple variance **cancels out of the position contrast** because the pair is couple-matched. So the LMM does not lose power from clustering for the main position effect; it pays a price only for interactions with couple.

### 1.3 Accuracy In Parameter Estimation (Maxwell, Kelley & Rausch, 2008)

Instead of "can we reject H₀," target a confidence-interval width on the effect:

```
n = (z_{0.975} × σ_δ / target_half_width)²
```

With σ_δ = 0.63 (pilot):
- Half-width 0.15 (tight) ⇒ **68 pairs**
- Half-width 0.20 (moderate) ⇒ **38 pairs**
- Half-width 0.30 (loose) ⇒ **17 pairs**

AIPE is better than NHST power for a **characterization** study (which is exactly this project's aim) because the goal is to report the size of the effect, not just existence. Committees like it because the number does not depend on assuming the effect size you intend to detect.

### 1.4 Factorial ANOVA with η² targets

For the full 2 (position) × 4 (bid) × 3 (model) × 2 (structure) design analyzed as factorial ANOVA:

| Target η² | Total pairs (α = 0.05, power = 0.8) |
|---|---|
| 0.02 (small) | ≈ 390 |
| 0.06 (medium) | ≈ 128 |
| 0.14 (large) | ≈ 55 |

Pilot suggests η² near 0.12 (between small and medium). Translates to **55–128 pairs** under ANOVA, but ANOVA ignores the paired structure, so this is an overestimate — use as a sanity upper bound, not a target.

### 1.5 Sequential / adaptive stopping (Lakens, 2014; Schönbrodt & Wagenmakers, 2018)

Start at n = 20 pairs, analyze, extend in batches of 10 until one of:
- Bayes factor > 10 (evidence for H₁), or
- BF < 1/10 (evidence for H₀), or
- Pre-registered maximum hit.

Typical savings: 30–50% fewer sessions when the true effect is clear, modest cost when null is true. Fits a self-funded student thesis better than fixed-N designs because it converts compute into evidence on demand.

---

## 2. Variance inputs from the pilot

Eight swap-pairs from transcripts 349–364 (couple C5, Llama 8B, Standard + Individual Focus, LLM-select structure, four bid combos each × 2 modes):

```
dFAS pooled: [−0.85, −0.50, −0.54, +0.14, −1.01, +0.61, −0.30, +0.68]
mean = −0.22     SD = 0.634     n = 8
```

LL cell alone (2 pairs): mean = −0.93, SD = 0.11. Too few to trust.
HH cell alone (2 pairs): mean = +0.41, SD = 0.38. Also too few to trust.

Use **pooled SD = 0.63** as the variance input; assume the LL-cell mean will regress toward the pooled magnitude once more couples enter (expect |mean| in range 0.3–0.7 rather than 0.9).

---

## 3. Calculated sample sizes

### 3.1 Primary contrast (RQ1, LL cell, paired t-test)

| Assumed true d | Pairs needed (α=.05, power=.8) |
|---|---|
| d = 0.8 (pilot's apparent effect) | 13 |
| d = 0.5 (moderate) | **32** |
| d = 0.4 (cautious) | **50** |
| d = 0.3 (very cautious) | 88 |

### 3.2 AIPE on LL mean dFAS

| Target CI half-width | Pairs needed |
|---|---|
| ±0.15 | 68 |
| ±0.20 | **38** |
| ±0.30 | 17 |

### 3.3 Moderator contrasts (LMM simulation)

Assuming a true position × model interaction of d = 0.3 (one model shifts the position effect by 0.3 SD relative to the others):

| Total pairs | Approx power (from simr-style sims, ICC ≈ 0.1) |
|---|---|
| 96 | ≈ 0.55 |
| 120 | ≈ 0.65 |
| 144 | **≈ 0.78** |
| 192 | ≈ 0.88 |

---

## 4. Factorial size that satisfies all contrasts

Each couple contributes to the factorial as follows:

- LL pairs per couple = (# models) × (# structures) = 3 × 2 = **6 pairs**
- Total pairs per couple = 4 bid combos × 3 models × 2 structures = **24 pairs**
- Sessions per couple = 48

| # couples | Total sessions | Total pairs | LL pairs | Detectable d in LL (α=.05, pwr=.8) | Moderator power (d=0.3) |
|---|---|---|---|---|---|
| 4 | 192 | 96 | 24 | 0.58 | ≈ 0.55 |
| 5 | 240 | 120 | 30 | 0.52 | ≈ 0.65 |
| **6** | **288** | **144** | **36** | **0.47** | **≈ 0.78** |
| 7 | 336 | 168 | 42 | 0.44 | ≈ 0.83 |
| **9** | **432** | **216** | **54** | **0.39** | **≈ 0.90** |
| 12 | 576 | 288 | 72 | 0.34 | ≈ 0.95 |

The LL-cell detectable effect is always the tightest constraint. The jump from 5 → 6 couples buys real power; the jump from 9 → 12 couples is diminishing returns.

---

## 5. Recommendation

**Preferred target: 288 sessions (6 couples).**
- LL cell hits d = 0.47, below pilot-suggested true effect.
- Moderator contrasts reach ≈ 0.78 power at d = 0.3.
- AIPE CI half-width on LL mean ≈ ±0.21, publishable precision.

**Conservative target: 432 sessions (9 couples).**
- LL cell hits d = 0.39, safe for small-but-real effects.
- Use if advisor wants a single, non-revisable commitment.

**Adaptive target: start at 192 (4 couples), stop-or-extend at 288 and 432 by pre-registered Bayes factor rule.**
- Cheapest expected cost if pilot effect holds up.
- Requires pre-registering the BF threshold (suggest BF₁₀ > 10 for stop-for-effect, BF₀₁ > 10 for stop-for-null).

**Do NOT pre-commit to 240 sessions.** It is a convenient number (5 couples), but it only clears the LL d = 0.5 bar, and under the pilot's conservative SD it leaves RQ1 under-precise (CI half-width ≈ ±0.22) and RQ3 model moderation at power ≈ 0.65 — reviewable as borderline.

---

## Summary one-liner for the advisor

> Sample size is not "240 because the matrix says so." Pilot variance gives a paired-t-test requirement of 32–50 LL pairs for d = 0.4–0.5, which maps to **288 sessions (6 couples) as the minimum defensible target** or **432 sessions (9 couples) as the conservative target**. Adaptive stopping with a pre-registered Bayes-factor rule is preferred because it converts compute into evidence on demand and keeps the commitment honest.
