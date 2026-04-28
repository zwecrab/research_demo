# TA Evaluator Audit

**Date**: 2026-04-17
**Scope**: Therapeutic Alliance (TA) scorer at `evaluate_therapist.py:evaluate_therapeutic_alliance`.
**Data**: 44 matrix-run sessions from the latest C2 batches (Individual Focus and Standard modes, GPT-4o therapist, Sequential structure). Scorer model is `SCORING_MODEL` = `openai/gpt-4o` at temperature 0.3.

## Distribution of scores

| Sub-score | Mean | SD | Range | Unique values | Modal value (share) |
|---|---|---|---|---|---|
| validation | 8.33 | 0.37 | 7.5-8.5 | 3 | 8.5 (36/44 = 82%) |
| neutrality | 7.90 | 0.42 | 7.0-9.0 | 4 | 8.0 (35/44 = 80%) |
| guidance | 6.76 | 0.39 | 6.0-7.0 | 3 | 7.0 (31/44 = 70%) |
| overall | 7.65 | 0.28 | 7.2-8.2 | 5 | 7.8 (28/44 = 64%) |

Missed opportunities: `count == 3` in 44/44 sessions. The rubric says "list 2-3"; the scorer always picks 3.

## Verification: `overall` is the mean of the three sub-scores

Checked five recent sessions: `overall` matches `(V + N + G) / 3` to within 0.01 every time. The scorer is not producing an independent holistic judgement; it is averaging its own three sub-scores. This means any collapse in sub-scores automatically collapses `overall`.

## Interpretation

This is classic LLM-as-judge saturation. The scorer has collapsed onto a narrow per-pillar template:

- Validation is almost always 8.5. The rubric tells the model what NOT to do ("I hear you", "I understand") but gives no positive anchor for scores at 9 or 10.
- Neutrality is almost always 8.0. The model picks the mid-to-high default for a visibly balanced transcript and does not differentiate subtle tilts.
- Guidance is almost always 7.0. The model reads "varied techniques", fails to observe variety in a supportive session, and settles on a below-average default.

The scorer is effectively returning a session-independent prior. Between-condition variance on TA is uninformative at this rubric and this sample size.

## Recommended fixes (ranked by expected impact)

1. **Add explicit anchor language to each pillar (strongest effect).** Replace the current abstract descriptions with a 5-level anchor, for example for Validation:
   - 10: Names the specific emotional texture with precision, including somatic cues, at every moment of vulnerability.
   - 8: Validates most vulnerable moments; occasionally labels surface emotion rather than depth.
   - 6: Names emotions but stays generic ("sounds hard"); does not linger.
   - 4: Pivots past vulnerability to task work repeatedly.
   - 2: Ignores or contradicts vulnerable disclosures.
   This forces the scorer to map the session to a concrete behavior per anchor, not a fuzzy default.

2. **Force turn-quote citations per sub-score.** Require the scorer to attach one quoted turn that exemplifies each score. Current output lets the scorer give a number without evidence, which is precisely the regime where LLM priors dominate. Adding evidence-grounding tends to pull scores apart.

3. **Remove the "list 2-3" quantifier on missed opportunities.** Replace with "list every instance where the therapist could have done better, or write an empty list if none." The current phrasing forces the model to pad to 3.

4. **Drop the mean computation; let the scorer produce an independent `overall`.** Current `overall` is mechanically a mean of three saturated sub-scores. Asking the scorer for an independent holistic rating with its own anchor would add one degree of variance.

5. **Increase temperature, or use 3-sample mean, when TA is the target.** Temperature 0.3 is too low for a discrimination task the model already defaults on. At 0.7 with three samples averaged, noise goes up but so does the signal if the scorer is near a decision boundary. Caveat: this increases cost.

6. **Consider an adversarial variant as a robustness check.** Run the scorer a second time with the patient labels swapped (A/B renamed). If the same session gets a different score when only the labels change, TA is tracking something other than therapist behavior.

## Action items for the paper

- Report TA with the caveat that the rubric saturates at this dynamic range, or drop TA from the primary metric tier and keep it as a secondary descriptive statistic.
- If fix 1 and fix 2 are implemented, re-score the 72 existing matrix sessions (C2 IndFocus, C2 Standard, and any later couples) against the revised rubric. This is cheaper than re-running the sessions and preserves experimental validity of the transcripts.
- The fix should be validated on a small pilot (six sessions: one per Individual Focus bid-combo row of C2) before full re-scoring to confirm spread actually increases.

## Proposed rubric revision (for review)

A proposed draft of the revised rubric is NOT yet written; fixing the prompt is a separate authoring task. The recommendation here is to review this audit, decide whether TA stays as a primary metric, and if yes, draft the anchor-based rubric as a standalone task.
