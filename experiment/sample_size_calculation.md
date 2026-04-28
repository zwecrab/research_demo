# Sample Size Calculation for the FSA Characterization Study

## 1. Research Questions

- **RQ1 (primary):** Does the LLM therapist exhibit a First Speaker Advantage (FSA)? Test of position main effect on DELTA_FAS across couples.
- **RQ2:** Does FSA magnitude vary by patient bid-style pairing? Position × Bid-Style interaction.
- **RQ3:** Does FSA magnitude vary by therapist model? Position × Model interaction.
- **RQ4:** Does FSA magnitude vary by therapist mode? Position × Structure interaction.

## 2. Method Selection

Chosen method: **A-priori analytical power analysis using Cohen (1988) formulas, as implemented in G*Power 3.1 (Faul et al., 2007)**. Mixed-effects Monte-Carlo simulation via the `simr` package (Green & MacLeod, 2016) is the recommended confirmatory follow-up; analytical calculation is used here for transparency.

- Primary test (RQ1): two-tailed paired-samples t-test on DELTA_FAS.
- Secondary tests (RQ2-4): 2 × k within-subjects repeated-measures ANOVA, interaction term.
- **Multiple-comparison control:** hierarchical gatekeeping with Holm (1979) within the secondary family. RQ1 is the a-priori gatekeeper tested at α = 0.05 (uncorrected). RQ2-4 form a secondary family tested only conditional on RQ1 rejection, with α_family = 0.05 and Holm-adjusted per-test α = 0.0167 at the first rank. This dominates simple Bonferroni and avoids the common planning error of inflating N on the primary test by over-correcting.
- Target power: 1 − β = 0.80.

## 3. Pilot-Derived Effect Size (Empirical)

Computed directly from the 18 position-swap pairs in `experiment/transcripts/`:

| Subset | n pairs | mean DELTA_FAS | SD DELTA_FAS | d_z |
|---|---|---|---|---|
| Llama-70B only | 9 | −0.267 | 0.224 | 1.19 |
| Llama-8B only | 9 | −0.100 | 0.472 | 0.21 |
| **Combined (planning)** | **18** | **−0.183** | **0.368** | **0.50** |

The 70B-only d_z of 1.19 is artificially high for three reasons: (a) n = 9 gives an unstable point estimate, (b) the 36-session batch ran Individual Focus + Sequential, a condition explicitly flagged in CLAUDE.md (2026-04-17) as variance-compressing, and (c) the recommended design in Section 5 retains two models rather than one, so cross-model variance remains part of the operating regime. The **combined d_z = 0.50** is adopted as the conservative planning estimate.

## 4. Per-RQ Sample Size

Analytical paired-t formula: N = ((z_{α/2} + z_{β}) / d_z)² + 1. Under the hierarchical gatekeeping scheme:

| Test | d / f | α (two-tailed) | z_{α/2} | z_{β} | N couples |
|---|---|---|---|---|---|
| RQ1 paired-t (gatekeeper) | d_z = 0.50 | 0.05 | 1.960 | 0.842 | **32** |
| RQ2 2×3 RM-ANOVA interaction | f = 0.25 | 0.0167 (Holm rank 1) | 2.394 | 0.842 | 29 |
| RQ3 2×3 RM-ANOVA interaction | f = 0.25 | 0.0167 | 2.394 | 0.842 | 29 |
| RQ4 2×2 RM-ANOVA interaction | f = 0.25 | 0.0167 | 2.394 | 0.842 | 34 |

Governing cell: **RQ4 at N = 34 couples.** Rounding up to **N = 36 couples** for balanced counterbalancing across the three bid-pairings.

### 4.1 Sensitivity to Planning Effect Size

If the true effect size deviates from the pilot-derived d_z = 0.50, N for RQ1 (primary) scales as follows at α = 0.05 two-tailed, power = 0.80:

| Planning d_z | RQ1 N couples | Total sessions (Option C, 12 cells/couple) |
|---|---|---|
| 0.40 (conservative) | 52 | 624 |
| 0.50 (adopted) | 32 | 432 (recommended) |
| 0.60 (optimistic) | 24 | 288 |

The d_z = 0.50 adopted value sits at the mid-point of the defensible range. If a Standard-mode re-run of the 36-session pilot recovers d_z closer to 0.60, Option C shrinks toward 288 sessions. If Standard mode proves noisier than expected and d_z falls to 0.40, N rises to 52 and Option C grows to 624 sessions.

## 5. Total Sessions (No Replication)

Each couple contributes exactly one session per cell. Cells per couple depend on which factors are crossed within-subjects.

| Design option | Factors crossed | Cells / couple | Total sessions (N = 36) |
|---|---|---|---|
| A. Full factorial | 2 pos × 3 bid × 3 model × 2 struct | 36 | 1296 |
| B. Drop Structure (per 2026-04-17 variance-control rationale) | 2 × 3 × 3 | 18 | 648 |
| C. Drop Structure + Llama-8B (pilot flagged 8B as noise-dominated) | 2 × 3 × 2 | 12 | **432** |
| D. Minimal | 2 × 2 × 2 | 8 | 288 |

**Recommendation: Option C (432 sessions, 36 couples).** Keeps the 3-level bid factor required for the Gottman-grounded passive/assertive/aggressive contrast, retains two contrasting models (GPT-4o RLHF vs Llama-70B) and defers RQ4 to a targeted follow-up (2 structure × 2 position × 34 couples = 136 sessions, reusing the same couple pool).

**Scope-change flag (requires advisor sign-off):** Option C removes Llama-8B and Structure from the primary factorial. Both were in the committee-presented 540-session design. This revision is a scope change, not an administrative tweak. Advisor approval is required before implementation.

**Code retention note:** Llama-8B and Individual Focus structure remain fully supported in the codebase (`config.py`, therapist routing in `conversation_engine.py`, `prompts/therapist_option2_prompt.txt`) and can be reused at any time for sensitivity analyses, supplementary tables, or follow-up studies. The exclusion is from the primary characterisation budget only, not from the toolchain.

## 6. Carryover and Random-Effects Justification

LLM-actor sessions have no episodic memory across API calls; each session is a fresh context window. Behavioural carryover in the human-experiment sense (learning, fatigue, demand characteristics) is not applicable. Two residual concerns:

1. **Couple-specific FAS floors** (some persona pairs are intrinsically easier to read as biased). Handled by treating Couple as a random intercept in the mixed-effects model `FAS ~ Position × Bid × Model + (1 | Couple)`.
2. **Judge-model drift across cells** (scoring calls aggregated over time). Handled by running all scoring in a single batch with a frozen judge model ID and recording `experiment_metadata.judge_version` per session.

Counterbalancing of cell order within couples is not required for identifiability under (1); it is recommended for cosmetic balance and is trivially cheap (randomise presentation order of cells per couple and log the seed).

## 7. Comparison to the Pre-Existing 540-Session Plan

The 540-session plan derives from 5 couples × 9 bid × 2 position × 3 model × 2 structure. At 5 couples per cell, within-cell paired-t power for d_z = 0.50, α = 0.05 is approximately 0.30 — under-powered for the primary FSA test by roughly a factor of three.

Option C (432 sessions, 36 couples) is 20 per cent below the old budget and correctly powered for all tests under hierarchical gatekeeping. RQ4 follow-up adds 136 sessions, bringing the total characterisation budget to **568 sessions**: 5 per cent above the old 540 plan, but fully power-justified rather than replication-assumed.

## 8. Assumptions and Limitations

- Planning d_z = 0.50 is the pilot combined-model estimate; the 70B-only d_z of 1.19 is treated as an upper bound rather than a planning value because n = 9 is small and the pilot used a variance-compressing mode.
- Analytical formulas assume normal DELTA_FAS distribution and sphericity for RM-ANOVA. A `simr` confirmatory simulation using the actual `FAS ~ Position × Bid × Model + (1 | Couple)` structure is recommended before final commitment to N = 36.
- Hierarchical gatekeeping depends on a statistically significant RQ1 outcome to license RQ2-4 inference. A non-significant RQ1 reduces the family to descriptive moderator analyses.
- 36 couples requires at least a 22-persona pool (11 couples exist in v2 + v2_additions). An additional **~14 couples (~28 personas)** must be authored before the full experiment runs.

## 9. Key Takeaway

Under hierarchical gatekeeping with pilot-derived d_z = 0.50 (empirical SD = 0.368 from 18 swap pairs) and α = 0.05 on the primary RQ, power = 0.80 is achieved at **N = 36 couples**. The defensible session budget is **Option C = 432 sessions** for RQ1-3, with RQ4 as a 136-session follow-up (total 568). The pre-existing 540-session plan is under-powered by a factor of ~3 on the primary test because 5-couples-per-cell is not a substitute for a sample-size calculation. Option C requires advisor sign-off to drop Llama-8B and Structure from the primary factorial, and persona-pool expansion by ~14 couples before the full experiment can begin.

## References

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum.
- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G*Power 3. *Behavior Research Methods*, 39(2), 175-191.
- Green, P., & MacLeod, C. J. (2016). SIMR: an R package for power analysis of generalised linear mixed models by simulation. *Methods in Ecology and Evolution*, 7(4), 493-498.
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
- Westfall, J., Kenny, D. A., & Judd, C. M. (2014). Statistical power and optimal design in experiments in which samples of participants respond to samples of stimuli. *Journal of Experimental Psychology: General*, 143(5), 2020-2045.
