# Project Reference Log

**Purpose:** persistent record of all papers cited during research-design discussions. Locked references must not be silently changed when writing the report.

**Status legend:** [LOCKED] = verified and used; [VERIFY] = academic-researcher flagged, must be confirmed before paper submission; [HISTORICAL] = referenced for context but not used in the cited section.

---

## Sample Size and Power Analysis (`experiment/sample_size_calculation.md`)

- [LOCKED] Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum. — Power formulas for paired t and RM-ANOVA.
- [LOCKED] Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G*Power 3. *Behavior Research Methods*, 39(2), 175-191. — Implementation reference for analytical power.
- [LOCKED] Green, P., & MacLeod, C. J. (2016). SIMR: an R package for power analysis of generalised linear mixed models by simulation. *Methods in Ecology and Evolution*, 7(4), 493-498. — Recommended confirmatory simulation.
- [LOCKED] Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70. — Multiple-comparison control.
- [LOCKED] Westfall, J., Kenny, D. A., & Judd, C. M. (2014). Statistical power and optimal design in experiments in which samples of participants respond to samples of stimuli. *JEP: General*, 143(5), 2020-2045. — Crossed within-subjects design power.
- [LOCKED] Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. *J. Royal Statistical Society B*, 57(1), 289-300. — FDR alternative to Bonferroni.

## FSA Signal Suppression and Primary Solutions (`experiment/fsa_signal_suppression_diagnosis.md`)

### Scorer redesign (S1)
- [LOCKED] Zheng et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS. — Pairwise preference and position-swap de-biasing (Section 4.2). Strongest cite for S1.
- [LOCKED] Wang et al. (2024). *Large Language Models are not Fair Evaluators*. ACL. DOI: 10.18653/v1/2024.acl-long.511. — Judge abstention under thin context.
- [LOCKED] Shi et al. (2024). *Judging the Judges*. — Small-quality-gap regime; tie-inflation.
- [LOCKED] Koo et al. (2023). CoBBLEr. — Strict rubric amplifies abstention.
- [LOCKED] Chen et al. (2024). *Humans or LLMs as the Judge?* — Judge-target mismatch as signal-loss source.

### Airtime channel reopen (S2)
- [LOCKED] Liu et al. (2023). *Lost in the Middle*. TACL. — Position effects under equalised exposure. Strongest cite for S2.
- [LOCKED] Sacks, H., Schegloff, E. A., & Jefferson, G. (1974). A simplest systematics for the organization of turn-taking for conversation. *Language*, 50(4), 696-735. — Conversation analysis grounding.

### Naming Asymmetry Score (S3)
- [LOCKED] Sharma et al. (2020). *A Computational Approach to Understanding Empathy in Text-Based Mental Health Support*. EMNLP. — Addressing-behaviour-as-descriptor precedent. Strongest cite for S3.
- [LOCKED] Gottman & Levenson (1992). RCISS multi-dimensional behavioural coding.
- [LOCKED] Wampold (2015). Therapeutic alliance multi-channel measurement.

### Secondary Solutions (S4-S8)
- [LOCKED] Shao et al. (2023). *Character-LLM*. — Persona drift without rule-level anchoring.
- [LOCKED] Wang et al. (2024). *InCharacter*. EMNLP. — Persona-controllability under shared constraints. Strongest cite for S4.
- [LOCKED] Min et al. (2023). Length-constrained generation compresses stylistic variance. — Used for S5.
- [LOCKED] Gottman, J. (1999). *The Marriage Clinic*. Norton. — Stonewalling and repair attempts. Used for S6.
- [LOCKED] Heyman, R. E. (2001). Observational coding of demand-withdraw. — Used for S6.
- [LOCKED] Xiao et al. (2023). Attention sinks. — Cited for S8 recency probe; academic flagged misapplication risk.

## Therapeutic Balance Metrics (`evaluate_balance.py` docstring, pre-existing)

- [LOCKED] Doyle, G. & Frank, M. (2016). Linguistic framing. ACL.
- [LOCKED] Kiesling, S. F. et al. (2018). Style and stance. *Computational Linguistics*.
- [LOCKED] Durandard et al. (2025). SIGDIAL.
- [LOCKED] Perez-Rosas, V. et al. (2017). Counselor reflections. ACL.
- [LOCKED] Cao, J. et al. (2019). Empathy in dialogue. ACL.
- [LOCKED] Welivita, A. et al. (2023). SIGDIAL.
- [LOCKED] Misiek, T. et al. (2020). CMCL.
- [LOCKED] Kang et al. (2024). *Can LLMs be Good Emotional Supporter?* ACL. DOI: 10.18653/v1/2024.acl-long.813. [Outstanding Paper]
- [LOCKED] Nguyen et al. (2025). CounselingBench / Core Counseling Attributes (CCA). Findings of NAACL 2025, pp. 7503-7526. DOI: 10.18653/v1/2025.findings-naacl.418
- [LOCKED] Sun et al. (2024). MI Skill Codes in Psychotherapy with LLMs. LREC-COLING. DOI: 10.18653/v1/2024.lrec-main.498

## Problem Severity Analysis (`LLM_rater/`)

### Severity rubric (5-dim vector)
- [LOCKED] Kotov, R. et al. (2017). The Hierarchical Taxonomy of Psychopathology (HiTOP). *Journal of Abnormal Psychology*. — Multi-dimensional symptom domains rejection of single composite.
- [LOCKED] Bagby, R. M. et al. (2004). Critique of composite scoring for heterogeneous symptom domains.

### Severity as covariate in dyadic conflict
- [LOCKED] Heyman, R. E. & Slep, A. M. S. (2004). Observational coding of marital conflict severity as moderator. *Journal of Family Psychology*. — Closest precedent for ex-ante severity covariate.
- [LOCKED] Kenny, D. A., Kashy, D. A., & Cook, W. L. (2006). *Dyadic Data Analysis*, ch. 7. Guilford. — Severity covariate in dyadic regression.

### Minimal-intake therapist (ecological validity)
- [VERIFY] Tryon, G. S. & Winograd, G. (2011). Goal consensus and collaboration. *Psychotherapy*, 48(1). — First-session therapist behaviour shaped by presenting complaint, not preloaded trait data. Academic-researcher flagged for verification before paper citation.
- [VERIFY] Hilsenroth, M. J. & Cromer, T. D. (2007). Intake-to-alliance pathways. — Same flag.
- [HISTORICAL] Persons, J. B. (2008). *The Case Formulation Approach to Cognitive-Behavior Therapy*. — Mid-treatment CBT formulation; NOT applicable to first session (academic retracted as wrong reference for our minimal-intake design).
- [HISTORICAL] Kuyken, W. et al. (2009). *Collaborative Case Conceptualization*. — Same retraction.

### Position-bias-after-content-control
- [LOCKED] Wang et al. (2023). *Large Language Models are not Fair Evaluators*. arXiv:2305.17926. — Position bias persists after swapping content quality. Strongest cite for the Position × severity_diff interaction defence.

## Pre-existing Project References (memory-tracked)

- See `experiment/persona_design_references.md` for the 9 ACL/EMNLP papers grounding bid-style-neutral persona design (separate file, not duplicated here).

---

## Maintenance rule

Any reference added to a paper draft, methods section, or experiment doc must first appear in this file with the [LOCKED] tag. [VERIFY]-tagged references must be confirmed (correct year, journal, page numbers) before the [LOCKED] tag is granted. [HISTORICAL] references should not appear in the final paper.
