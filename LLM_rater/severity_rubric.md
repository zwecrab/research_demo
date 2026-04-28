# Severity Rating Rubric (5-Dimension Vector)

**Purpose:** ex-ante rating of each patient persona on five orthogonal mental-health dimensions, used as covariates in the FSA regression.

**Rated subject:** the *textual persona profile* (traits, cognitive_model, hidden_tension, attachment_style, ocean_profile, relationship_history). The rater does not infer real-world clinical illness; it judges how strongly the profile presents each dimension.

**Scale:** continuous **0.0 to 10.0** float per dimension, two decimal places. Higher = stronger presentation. Use the full range: do not collapse to round numbers if the profile sits between two anchors.

**Grounding:** HiTOP (Kotov et al., 2017) for the multi-dimensional rejection of single composites; Heyman & Slep (2004) for severity-as-covariate in dyadic conflict; Gottman (1999) Four Horsemen for the escalation dimension.

---

## Anchor Reference (applies to every dimension unless noted)

| Range | Label | Meaning |
|---|---|---|
| 0.0 - 1.0 | None | No textual evidence at all. |
| 1.5 - 3.0 | Mild | Occasional or implied presence. Not a recurring theme. |
| 3.5 - 5.0 | Moderate | Recurring theme. Cited in cognitive_model OR hidden_tension OR speaking_style. |
| 5.5 - 7.0 | Marked | Dominant in two or more persona fields. Shapes how the patient enters conflict. |
| 7.5 - 10.0 | Severe | The organising feature of the persona. Pervasive across cognitive_model, hidden_tension, relationship_history, and speaking_style. |

You are encouraged to place scores between integer points (e.g., 4.3, 6.7, 7.8) where the profile sits between two anchor regions. Do NOT default to round numbers.

---

## Dimension 1 — Anxiety

Generalised worry, hypervigilance, rumination, somatic anxiety markers in the text.

- 0.0-1.0: No worry-themed content. ocean.neuroticism low. No hypervigilance markers.
- 1.5-3.0: Occasional worry. ocean.neuroticism moderate. Some doubt without catastrophising.
- 3.5-5.0: Worry is a recurring theme. hidden_tension contains a fear-of-X frame. ocean.neuroticism high.
- 5.5-7.0: Hypervigilance evident in speaking_style. cognitive_model shows clear anxious appraisal.
- 7.5-10.0: cognitive_model.core_belief is a catastrophising premise. Constant rumination across all persona fields.

## Dimension 2 — Depression

Anhedonia, hopelessness, withdrawal, loss-of-meaning markers in the text.

- 0.0-1.0: No depressive content. Engaged with hobbies, occupation, relationship goals.
- 1.5-3.0: Occasional discouragement. Energy reduced in some contexts. No hopelessness.
- 3.5-5.0: Persistent low-mood frame. Loss of pleasure or meaning in one major life domain.
- 5.5-7.0: Withdrawal from previously valued activities. cognitive_model carries a defeated tone.
- 7.5-10.0: Pervasive hopelessness. Future framed negatively. cognitive_model.core_belief is hopelessness-themed.

## Dimension 3 — Trauma

Flashbacks, avoidance, hyperarousal, attachment trauma, unprocessed loss in the text.

- 0.0-1.0: No trauma history mentioned.
- 1.5-3.0: Past adverse event noted but not framed as ongoing burden.
- 3.5-5.0: A specific past event shapes current behaviour or coping (relationship trauma, loss, betrayal).
- 5.5-7.0: Avoidance or hyperarousal is present. Trauma references appear in two or more persona fields.
- 7.5-10.0: Trauma is the central organising feature. Unprocessed loss / betrayal / abandonment dominates cognitive_model and hidden_tension.

## Dimension 4 — Attachment Disorganisation

Conflicting attachment impulses (simultaneous approach and withdrawal), unresolved loss, fear-of-figure-as-source-of-comfort, disorganised relational strategy.

- 0.0-1.0: attachment_style = secure. Coherent relational strategy.
- 1.5-3.0: attachment_style = anxious or avoidant alone. Strategy coherent even if dysregulating.
- 3.5-5.0: Mixed anxious-avoidant features in cognitive_model or hidden_tension. Push-pull dynamics evident.
- 5.5-7.0: cognitive_model contains internally contradictory strategies. Patient seeks AND fears partner's attention.
- 7.5-10.0: attachment_style = disorganised OR fearful-avoidant. Simultaneous approach and withdrawal toward partner is the dominant relational pattern.

## Dimension 5 — Escalation Tendency

Four Horsemen markers (Gottman 1999): criticism, contempt, defensiveness, stonewalling. Conflict escalation under stress.

- 0.0-1.0: bid_style = assertive. Collaborative under conflict. No Horsemen markers.
- 1.5-3.0: bid_style = passive (stonewalling/withdrawal under stress) OR speaking_style shows occasional defensiveness, but no contempt or criticism.
- 3.5-5.0: Two Horsemen markers present (e.g., criticism + defensiveness). hidden_tension contains a "you always / you never" frame.
- 5.5-7.0: Three Horsemen markers detectable. Persona text frames partner as a problem to be managed rather than a partner.
- 7.5-10.0: bid_style = aggressive AND contempt is evident in the persona text (eye-rolling described, name-calling, dismissive framing of partner). All four Horsemen detectable.

---

## Output Format (per patient)

Each rater returns:

```json
{
  "anxiety": <float 0.0-10.0>,
  "depression": <float 0.0-10.0>,
  "trauma": <float 0.0-10.0>,
  "attachment_disorganisation": <float 0.0-10.0>,
  "escalation_tendency": <float 0.0-10.0>,
  "overall_score": <float 0.0-10.0>,
  "evidence": {
    "anxiety": "<one short quote or paraphrase>",
    "depression": "...",
    "trauma": "...",
    "attachment_disorganisation": "...",
    "escalation_tendency": "..."
  }
}
```

`overall_score` is the rater's holistic at-a-glance summary. **It is provided for display only and is NOT used in the regression analysis.** The regression operates on the 5-dimension vector to honour the HiTOP critique of single-composite scoring for heterogeneous symptom domains.

## Consensus Computation

Three raters score each patient. Per dimension:
- **Consensus score** = arithmetic mean of the three rater scores (float, kept to 2 decimals).
- **Inter-rater agreement rate** = proportion of rater pairs whose scores fall within 1.0 of each other.
- **Mean absolute pairwise difference** = average of |score_i − score_j| across rater pairs.
- **severity_diff_vector** (per couple) = patient_A.consensus_vector − patient_B.consensus_vector, rounded to 2 decimals.
- **overall_score_diff** (per couple) = patient_A.overall_score − patient_B.overall_score, for at-a-glance comparison only.

If mean absolute pairwise difference exceeds 2.0 on any dimension for any couple, that dimension is flagged for human review and excluded from the regression for that couple.

## Constraints on Rater LLMs

- Models from three different vendors (Anthropic, Google, OpenAI).
- The therapist conversation model is excluded from the rater pool to prevent circularity.
- All calls route through OpenRouter.
- Temperature = 0 for reproducibility.
- Same prompt, same persona content sent to each rater.
