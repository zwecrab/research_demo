# FSA Signal Suppression: Structural Diagnosis

**Date:** 2026-04-21
**Author:** therapy-llm-specialist (verified by project-manager and academic-researcher)
**Scope:** Why current sessions under-produce First Speaker Advantage signal, excluding sample-size explanations.

## Context

The 36-session test batch produced mean DELTA_FAS of minus 0.18 and median absolute FAS of 0.24 on the 70B therapist. The signal is both small in magnitude and inconsistent in sign (recency-leaning rather than primacy-leaning). Six structural mechanisms in the current pipeline absorb or redirect position bias before it can register in FAS, BRD, or CAS.

## Primary Suppressors (literature-strong)

1. **Scorer neutral-defaulting.** `evaluate_balance.py` auto-classifies any therapist turn with thin bilateral context as N (lines 136 to 142), and its vocabulary-borrowing disambiguation (lines 110 to 115) pushes ambiguous turns toward N rather than A or B. Under 120-token therapist turns, most turns are ambiguous. This matches Wang et al. 2024 (ACL) and Zheng et al. 2023 on judge-abstention in small-quality-gap regimes, producing a measurement ceiling that compresses FAS toward zero.

2. **Airtime-channel removal.** `decide_next_speaker` forbids the same speaker twice in a row (line 458), and `intelligent_speaker_selection` enforces balance across patients. Canonical position bias (first speaker claims more airtime) cannot manifest. FSA must express itself only through framing and depth, a weaker channel (Liu et al. 2023, TACL).

3. **Prompt-scorer channel misalignment.** The Standard therapist prompt licenses addressing asymmetry ("do not force equal attention"), yet FAS measures content-framing adoption, not naming frequency. A therapist who names Partner A frequently while adopting Partner B's framing registers as N. This mirrors Chen et al. 2024 on judge-target mismatch as a primary source of signal loss and reproduces the 2026-04-17 IndFocus retraction pattern.

## Primary Solutions (tri-agent aligned: therapy-llm-specialist, PM, academic-researcher)

### S1 — Scorer redesign (addresses Suppressor 1)

- **Primary judge:** pairwise preference. Score each therapist turn against a swap of A/B labels in the judge prompt. Keep the label that wins. Source: Zheng et al. 2023, Section 4.2.
- **Robustness check:** 3-point categorical {A, N, B} with forced-abstention token.
- **Remove auto-N rule** at `evaluate_balance.py` lines 136-142. Score from turn 2 onward on available context.
- **Symmetrise vocabulary-borrow rule** at lines 110-115. Current wording channels B→A only; make it bidirectional.
- **Mandatory judge-side de-biasing:** randomise A/B presentation order to the judge per call. Log the seed.
- **Pilot gate:** re-run the scorer twice on the same 10 sessions. Report weighted Cohen's kappa with 95% CI. Proceed to full rescore only if kappa ≥ 0.7.
- **Advisor sign-off:** required. Scale change affects every reported FAS number.

### S2 — Airtime channel reopen (addresses Suppressor 2)

- **Drop the hard rule** "Never let the same speaker go twice in a row" in `conversation_engine.py:458` (`decide_next_speaker`) and in `intelligent_speaker_selection:374`.
- **Add a soft guard:** block only 3 or more consecutive same-speaker turns. Two in a row is now legal.
- **Add Turn Share Index (TSI):** TSI = turns_A / (turns_A + turns_B) per session. Report alongside FAS.
- **Expected effect:** first-speaker airtime dominance becomes observable. TSI > 0.5 in alpha sessions and < 0.5 in beta sessions is the predicted FSA surface. Source: Liu et al. 2023 (TACL, *Lost in the Middle*); Sacks, Schegloff & Jefferson 1974 on turn-taking.
- **Re-run scope:** affected cells only. TSI is additive and does not invalidate prior FAS/BRD/CAS numbers.

### S3 — Naming Asymmetry Score (addresses Suppressor 3)

- **Compute NAS** = count of first-name mentions of Partner A minus Partner B in therapist turns. Per session, not per turn.
- **Status:** supplementary descriptive statistic. **Not a bias metric.** Explicit viva framing: NAS quantifies the addressing channel to empirically confirm the 2026-04-17 decoupling of naming from content framing. It is reported FOR, not against, the decoupling decision.
- **Compute retroactively** on all 36 existing transcripts. Zero re-run cost.
- **Report alongside** FAS/BRD/CAS in every transcript JSON and every results table.
- **Source:** Sharma et al. 2020 (EMNLP, *A Computational Approach to Understanding Empathy*) for addressing-behaviour-as-descriptor precedent.

## Secondary Suppressors (moderate)

4. **Patient rule-floor homogenisation.** In `patient_prompt.txt`, rules 5 to 15 apply to all bid-styles; only rule 16 is aggressive-specific. Passive and assertive patients share identical behavioural floors, reducing the stimulus contrast that would pull the therapist asymmetrically.

5. **Token-budget crowding.** A 120-token, three-to-four-sentence therapist budget forces framing, depth, and challenge to compete within the same short response, shrinking per-channel amplitude.

6. **Compliance forcing.** `therapist_addressed` short-circuit (lines 446 to 448) compels the named patient to respond, removing natural silence or withdrawal asymmetry, a real clinical FSA channel (Gottman 1999; Heyman 2001).

Two adjacent concerns compound the above: bid-style is decoupled from position, so randomised pairing washes position main-effects, and the observed recency-leaning sign indicates the residual bias enters through recent-context weighting rather than primacy.

## Key Takeaway

Weak FSA signal is not a sampling artefact. It is an architectural consequence of three reinforcing design choices: scorer abstention under thin context, mechanical airtime equalisation, and mismatch between the channel the prompt licenses and the channel the metric measures. Restoring signal requires at minimum reopening the airtime channel (permit consecutive same-speaker turns), widening the therapist token budget, and either adding a naming-asymmetry metric or tightening the therapist prompt to content-framing commitments. These are three levers inside the pipeline; increasing session count will not compensate for them.
