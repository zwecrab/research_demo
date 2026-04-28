# Persona Design Explanation for Full Experiment

**Prepared for**: Dr. Chaklam Silpasuwanchai (Advisor)
**Date**: 2026-04-17 (revised)
**Context**: 540-session experiment to characterize First Speaker Advantage (FSA) in LLM-simulated couples therapy. Primary outcome metrics: FAS, BRD, CAS, TA, PANAS Delta. SPDI and PCR were removed from the design per advisor guidance (2026-03-05).
**Implementation status**: V2 pipeline complete. Personas, bid-style overlays, PANAS baselines, unified symmetric patient prompt, and matrix runner (bid-style x position) are all live. C2 (Kovacs-Singh) matrix complete in both Individual Focus and Standard therapist modes (36 sessions total); remaining four couples pending.

---

## 1. Why Bid-Style Is Decoupled from Persona

In our experimental design, bid-style (passive, assertive, aggressive) is injected as a separate prompt overlay at runtime, not embedded in the persona definition. All 10 personas carry `"bid_style": "neutral"` as a placeholder; the actual bid-style is applied via principle-adherence prompting during session generation.

**Rationale and paper support:**

- **Roleplay-doh (EMNLP 2024)** demonstrated that domain experts can control LLM patient behavior through "principles" (natural language rules) injected as prompt overlays, improving response quality by 30%. We adopt this architecture: persona traits define *who* the person is, while bid-style principles define *how* they communicate in a given session. This separation means the same persona can appear under passive, assertive, or aggressive bid-style conditions without structural modification.

- **From Personas to Talks (EMNLP 2025)** provided evidence that subtle persona trait shifts (emotionality, extraversion) measurably alter the distribution of emotional support strategies in LLM-synthesized dialogue. This confirms that personas and communication styles are separable variables: traits modify dialogue dynamics independently of behavioral overlays.

- **Experimental necessity**: Decoupling makes bid-style a within-subjects variable with 5 replications per cell (one per couple). If bid-style were baked into the persona, it would be confounded with the persona's other traits (cognitive model, attachment style, OCEAN profile), making it impossible to isolate the effect of communication intensity on FSA.

**Full factorial**: 5 couples x 9 bid-style combinations (3x3: passive/assertive/aggressive for each partner) x 2 speaking positions x 3 therapist models x 2 conversation structures = **540 sessions**.

---

## 2. How the 10 Personas Were Designed

Each persona was constructed with three interlocking psychological layers, grounded in the following literature:

### 2.1 Cognitive Model (PATIENT-Psi; Cactus)

Following PATIENT-Psi (EMNLP 2024), each persona includes a structured cognitive model with three components:

| Component | Description | Example (P07, Sofia Reyes) |
|-----------|-------------|----------------------------|
| **Core belief** | CBT-format "If X then Y" belief | "If I let my guard down, the people I love will be hurt because I failed to protect them." |
| **Intermediate belief** | Belief about self or others that mediates behavior | "I must stay vigilant and involved, because nobody else will advocate as strongly for my children." |
| **Coping strategy** | Observable behavioral pattern | Oscillates between hypervigilant involvement and sudden withdrawal |

Cactus (Findings of EMNLP 2024) informed the CBT case formulation structure: each persona's cognitive model connects logically to their therapy topics, hidden tensions, and observable speaking patterns. This ensures that the LLM generates contextually coherent dialogue rooted in psychological mechanisms, not arbitrary trait lists.

### 2.2 OCEAN Profile (PersonaLLM; Behavioral Alignment)

Each persona carries a Five-Factor personality profile using qualitative labels (low, moderate, high) rather than numeric scores. This decision follows PersonaLLM (Findings of NAACL 2024), which demonstrated that Big Five prompting with qualitative descriptors produces distinguishable LLM behavior with large effect sizes across all five dimensions and up to 80% human perception accuracy.

We use qualitative labels rather than numeric scores for two reasons: (1) numeric scores imply false precision for LLM persona prompting, and (2) the Evaluating Behavioral Alignment paper (EMNLP 2025) showed that Five-Factor profiles in conflict dialogue operate on broad behavioral ranges rather than precise numeric intervals.

All OCEAN profiles are bid-style-neutral: no persona is defined as aggressive, passive, submissive, or confrontational at the trait level. Traits describe stable personality characteristics (e.g., "introspective," "driven," "values reciprocity") rather than communication behaviors.

### 2.3 Attachment Style (Bowlby/Gottman)

Each persona has one of four attachment styles (secure, anxious, avoidant, disorganized) assigned based on clinical compatibility with their cognitive model and couple archetype. Attachment style influences the hidden tension, hidden intention, and coping strategy fields, ensuring internal consistency.

---

## 3. Attachment Pairings and Clinical Rationale

| Couple | Archetype | Partner A | Partner B | Pairing | Clinical Rationale |
|--------|-----------|-----------|-----------|---------|-------------------|
| C1 (Okafor) | Early 30s, new parents | Anxious | Avoidant | Anxious + Avoidant | The classic pursue-withdraw dynamic. Adaeze seeks reassurance; Chidi retreats under pressure. This is the most commonly studied insecure pairing in couples therapy literature and produces reliable interactional patterns (Gottman's "demand-withdraw" cycle). |
| C2 (Kovacs-Singh) | Late 20s, intercultural | Secure + Anxious | Secure + Anxious | Secure + Anxious | A partially secure dyad. Eszter's security provides a stabilizing anchor, while Rajan's anxious attachment introduces tension around voicing needs. This pairing tests whether a secure partner moderates FSA effects compared to fully insecure dyads. |
| C3 (Thompson) | Mid 40s, empty-nest | Anxious + Anxious | Anxious + Anxious | Anxious + Anxious | Both partners share anxious attachment but express it differently (David through fear of change, James through restlessness about stagnation). This same-style pairing creates a "co-escalation" dynamic where both seek reassurance but neither can provide it sustainably. |
| C4 (Reyes-Nakamura) | Early 30s, blended family | Disorganized | Avoidant | Disorganized + Avoidant | Sofia's disorganized attachment (oscillating between hypervigilance and withdrawal, rooted in a custody trauma) paired with Kenji's avoidant style creates unpredictable interactional patterns. This is the most clinically complex pairing and tests FSA under conditions of high behavioral variability. |
| C5 (Al-Rashid) | Late 30s, career imbalance | Secure | Avoidant | Secure + Avoidant | Nadia's secure attachment provides clarity and directness; Farah's avoidant pattern manifests as accumulated silent resentment. This pairing tests whether a secure partner's communication style resists or amplifies position-dependent therapist bias. |

The five pairings cover four of the most clinically relevant attachment combinations, with deliberate inclusion of both symmetrical (C3: anxious + anxious) and asymmetrical (C1, C4) pairings to capture different interactional dynamics.

---

## 4. Therapy Topics

Each couple is assigned 2 therapy topics that are:
- Clinically compatible with their archetype and attachment pairing
- Rich enough to sustain 30-turn sessions across multiple bid-style conditions
- Distinct from other couples' topics to avoid content confounding

| Couple | Topic 1 | Topic 2 | Selection Rationale |
|--------|---------|---------|---------------------|
| C1 (Okafor) | Division of labor after becoming new parents | Emotional disconnection during high-stress career periods | Classic new-parent stressors that activate the anxious-avoidant dynamic. Chidi's residency hours provide an ecologically valid career pressure context. |
| C2 (Kovacs-Singh) | Relocation decisions and competing family obligations | Navigating cultural differences in conflict resolution styles | Directly addresses the intercultural relocation archetype. Cultural differences in conflict expression (Hungarian directness vs. Indian-American harmony prioritization) provide natural variation. |
| C3 (Thompson) | Identity and purpose after children leave home | Renegotiating the relationship when long-established roles shift | Empty-nest topics that activate both partners' anxious attachment in complementary ways (David fears loss, James fears stagnation). |
| C4 (Reyes-Nakamura) | Co-parenting boundaries in a blended family | Balancing protectiveness with shared parental authority | Blended-family topics that directly engage Sofia's disorganized attachment (custody trauma) and Kenji's avoidant coping (deferring to avoid conflict). |
| C5 (Al-Rashid) | Career imbalance and domestic equity | Maintaining connection when professional demands dominate | Career-imbalance topics that test whether Nadia's secure directness and Farah's avoidant accumulation pattern interact differently with position bias. |

---

## 5. Agreeableness Variance for Sycophancy Confound Control

A critical design consideration comes from Dr. Chaklam's ACL 2026 paper, "Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models." That paper demonstrated a strong correlation (r = 0.87 across 9 of 13 models, including Llama 3.1 8B) between persona agreeableness and sycophancy, as measured by the Trait-Truthfulness Gap (TTG) metric. High-agreeableness personas produce more agreeable, less truthful outputs, which could confound FSA metrics if all personas shared similar agreeableness levels.

**Design response**: We deliberately varied agreeableness across the 10 personas to ensure that sycophancy-driven behavioral differences do not systematically bias our results in one direction.

- **High agreeableness** (4 personas): P01 Adaeze Okafor, P03 Eszter Kovacs, P08 Kenji Nakamura, P10 Farah Al-Rashid
- **Low agreeableness** (3 personas): P02 Chidi Okafor, P06 James Thompson, P07 Sofia Reyes
- **Moderate agreeableness** (3 personas): P04 Rajan Singh, P05 David Thompson, P09 Nadia Al-Rashid

This distribution ensures:
1. **Within-couple variance**: No couple has two high-agreeableness or two low-agreeableness partners (verified in the OCEAN distribution table below). This prevents sycophancy from loading uniformly onto one position in a swapped pair.
2. **Cross-couple balance**: High and low agreeableness personas are distributed across all five couples, so sycophancy effects can be observed and controlled for in analysis.
3. **Interaction with bid-style**: Since bid-style is injected at runtime, the same high-agreeableness persona will appear under aggressive bid-style conditions. This allows us to test whether persona-level sycophancy interacts with externally imposed communication intensity, a direct extension of Dr. Chaklam's TTG findings.

---

## 6. Full Experimental Design

| Factor | Levels | Count |
|--------|--------|-------|
| Couple (persona pair) | C1, C2, C3, C4, C5 | 5 |
| Bid-style combination (Patient A x Patient B) | passive-passive, passive-assertive, passive-aggressive, assertive-passive, assertive-assertive, assertive-aggressive, aggressive-passive, aggressive-assertive, aggressive-aggressive | 9 |
| Speaking position | Alpha (A first), Beta (B first) | 2 |
| Therapist model | GPT-4o, Llama 3.1 8B, Llama 3.1 70B | 3 |
| Conversation structure | Sequential, LLM-Based Selection | 2 |
| **Total sessions** | 5 x 9 x 2 x 3 x 2 | **540** |

Each of the 540 sessions uses a fixed 30-turn protocol. Persona roles (Patient A, Patient B) remain fixed within a couple; only speaking order and bid-style vary. This ensures that any observed FAS, BRD, or CAS differences between positions are attributable to position and model effects, not persona identity confounding.

---

## 7. Field-by-Field Justification

| JSON Field | Purpose | Paper Reference |
|------------|---------|----------------|
| `persona_id`, `couple_id` | Unique identifiers for data management | (experimental design) |
| `name`, `gender`, `age` | Demographic grounding; gender and age affect LLM persona adherence | Can LLM Agents Maintain Persona (EMNLP 2025) |
| `role_in_couple`, `partner_name` | Relational context for prompt injection | (experimental design) |
| `occupation` | Provides cognitive and behavioral anchoring | PATIENT-Psi (EMNLP 2024); Cactus (Findings of EMNLP 2024) |
| `hobbies` | Adds behavioral specificity and conversational material | Crafting Customisable Characters (Findings of EMNLP 2025) |
| `traits` | Bid-style-neutral personality descriptors | PersonaLLM (Findings of NAACL 2024); Behavioral Alignment (EMNLP 2025) |
| `speaking_style` | Communication pattern description, neutral intensity | From Personas to Talks (EMNLP 2025) |
| `cognitive_model` | CBT-structured beliefs and coping strategies | PATIENT-Psi (EMNLP 2024); Cactus (Findings of EMNLP 2024) |
| `ocean_profile` | Five-Factor personality (qualitative labels) | PersonaLLM (Findings of NAACL 2024); Too Nice to Tell the Truth (ACL 2026) |
| `attachment_style` | Bowlby/Gottman attachment classification | (clinical psychology literature) |
| `relationship_history` | Narrative context for session coherence | Crafting Customisable Characters (Findings of EMNLP 2025) |
| `therapy_topics` | Session content scope (2 per couple) | (experimental design) |
| `hidden_intention` | Latent therapeutic goal, not stated explicitly | PATIENT-Psi (EMNLP 2024) |
| `hidden_tension` | Unspoken relational conflict driving behavior | PATIENT-Psi (EMNLP 2024); Cactus (Findings of EMNLP 2024) |
| `hidden_tension_examples` | Behavioral leakage instances for prompt grounding | Roleplay-doh (EMNLP 2024) |
| `bid_style` | Placeholder ("neutral"); actual value injected at runtime | Roleplay-doh (EMNLP 2024); Too Nice to Tell the Truth (ACL 2026) |
| `sample_utterances` | Neutral-intensity speech examples for LLM calibration | From Personas to Talks (EMNLP 2025); Two Tales of Persona (Findings of EMNLP 2024) |

---

## 8. OCEAN Distribution Table

The table below shows the full OCEAN profile distribution across all 10 personas, confirming that each dimension has at least 2 high and 2 low values, and that no couple shares identical profiles.

| ID | Name | Couple | O | C | E | A | N |
|----|------|--------|---|---|---|---|---|
| P01 | Adaeze Okafor | C1 | **H** | M | M | **H** | **H** |
| P02 | Chidi Okafor | C1 | M | **H** | **L** | **L** | **L** |
| P03 | Eszter Kovacs | C2 | **H** | M | **H** | **H** | **L** |
| P04 | Rajan Singh | C2 | **L** | **H** | M | M | **H** |
| P05 | David Thompson | C3 | M | **L** | **L** | M | **H** |
| P06 | James Thompson | C3 | **L** | M | **H** | **L** | M |
| P07 | Sofia Reyes | C4 | **H** | **L** | M | **L** | **H** |
| P08 | Kenji Nakamura | C4 | M | **H** | **L** | **H** | **L** |
| P09 | Nadia Al-Rashid | C5 | M | M | **H** | M | **L** |
| P10 | Farah Al-Rashid | C5 | **L** | **L** | M | **H** | M |

### Constraint Verification

| Dimension | High (>=2?) | Low (>=2?) | Verified |
|-----------|-------------|------------|----------|
| Openness | P01, P03, P07 (3) | P04, P06, P10 (3) | Yes |
| Conscientiousness | P02, P04, P08 (3) | P05, P07, P10 (3) | Yes |
| Extraversion | P03, P06, P09 (3) | P02, P05, P08 (3) | Yes |
| Agreeableness | P01, P03, P08, P10 (4) | P02, P06, P07 (3) | Yes |
| Neuroticism | P01, P04, P05, P07 (4) | P02, P03, P08, P09 (4) | Yes |

### Within-Couple Profile Uniqueness

| Couple | Partner A OCEAN | Partner B OCEAN | Identical? |
|--------|----------------|-----------------|------------|
| C1 | H-M-M-H-H | M-H-L-L-L | No |
| C2 | H-M-H-H-L | L-H-M-M-H | No |
| C3 | M-L-L-M-H | L-M-H-L-M | No |
| C4 | H-L-M-L-H | M-H-L-H-L | No |
| C5 | M-M-H-M-L | L-L-M-H-M | No |

### Same-Sex Couples

- **C3 (Thompson)**: David (male, 46) and James (male, 47), married 12 years. Clinical rationale: empty-nest transition in a long-term male same-sex couple surfaces identity renegotiation dynamics that are well-documented in LGBTQ+ couples therapy literature but underrepresented in LLM simulation research.
- **C5 (Al-Rashid)**: Nadia (female, 37) and Farah (female, 36), married 5 years. Clinical rationale: career imbalance and domestic equity in a female same-sex couple avoids heteronormative assumptions about gendered division of labor, forcing the model to engage with the presenting issue on its own terms rather than defaulting to gendered scripts.

---

## 9. Bid-Style Overlay Design (Principle-Adherence Prompting)

### 9.1 What Is Principle-Adherence Prompting?

Roleplay-doh (EMNLP 2024) introduced a prompting architecture in which domain experts define behavioral "principles" (natural language rules) that are injected into an LLM's system or user prompt at runtime. These principles constrain the LLM's behavior within the roleplay without modifying the underlying persona definition. Roleplay-doh demonstrated a 30% improvement in simulated patient response quality when principles were used compared to persona-only prompting. We adopt this architecture to implement bid-style as a separable experimental variable.

In our design, persona traits define *who* the character is (personality, attachment style, cognitive model, life history). Bid-style principles define *how* that character communicates in a given session. The overlay is a JSON object containing 5 to 7 behavioral rules, speaking pattern modifiers, and sample utterance transformations. At runtime, the experiment runner loads the appropriate bid-style overlay and injects its principles into the prompt template alongside the persona fields.

### 9.2 The Three Bid-Style Levels

Each bid-style is defined as a coherent behavioral profile with consistent internal logic:

| Dimension | Passive | Assertive | Aggressive |
|-----------|---------|-----------|------------|
| Communication intensity | Low | Moderate | High |
| Interruption frequency | None | Medium (to clarify or redirect) | High (to correct, contradict, or dominate) |
| Emotional expression | Suppressed, understated, deflected | Regulated, named directly, proportionate | Intense, externalized, blaming |
| Conflict behavior | Yields quickly, changes subject | Engages constructively, proposes compromises | Escalates, refuses to yield, personalizes |
| Turn length | Short (1 to 3 sentences) | Balanced (3 to 5 sentences) | Long (4 to 7 sentences) |
| Core speech pattern | Hedging, trailing off, minimizing | "I feel... when... because..." framework | "You always/never," absolute statements |

**Passive** models a withdrawn, conflict-avoidant communication style. The persona defers to the partner and therapist, minimizes their own needs, and uses hedging language extensively. This style is relevant to FSA research because a passive first speaker may fail to establish framing dominance despite positional advantage.

**Assertive** models regulated, boundaried communication. The persona expresses needs clearly, acknowledges the partner's perspective, and seeks resolution without escalation. This is the communication style most commonly modeled in couples therapy literature and serves as the behavioral midpoint.

**Aggressive** models a dominant, escalatory communication style. The persona uses blame language, dismisses the partner's feelings, and intensifies when challenged. This style tests whether conversational dominance through communication intensity overrides or amplifies position-dependent therapist bias.

### 9.3 How the Overlay Interacts with Persona Traits

The bid-style overlay operates on a different behavioral layer than persona traits. Persona traits (OCEAN profile, attachment style, cognitive model) define stable psychological characteristics. Bid-style principles define session-level communication behavior. This separation is analogous to the distinction between personality (trait) and state (situational behavior) in personality psychology.

Critical interaction cases:

- **High agreeableness + aggressive overlay**: The persona's underlying agreeableness is overridden by the aggressive bid-style principles. Per Dr. Chaklam's findings (Too Nice to Tell the Truth, ACL 2026), high-agreeableness personas produce more sycophantic outputs. The aggressive overlay must be strong enough to counteract this tendency, which is why the aggressive behavioral principles use imperative language ("Dominate the conversational space," "Dismiss or minimize your partner's feelings") rather than suggestive framing.

- **Low agreeableness + passive overlay**: The persona's natural directness is constrained by the passive principles. The overlay instructs the LLM to defer, hedge, and minimize, which may produce tension with the persona's low-agreeableness baseline. This tension is a feature, not a bug: it tests whether externally imposed communication constraints can override persona-level behavioral tendencies, which is precisely the separability question motivating the decoupled design.

- **Avoidant attachment + aggressive overlay**: Avoidant personas naturally withdraw from emotional engagement. The aggressive overlay forces high-intensity engagement, creating a persona that attacks but does not connect emotionally. This combination produces a distinctive behavioral signature that differs from an anxious persona under the same aggressive overlay (which would produce intensity driven by need for closeness rather than by hostility).

### 9.4 Why Interruption Frequency Belongs to Bid-Style, Not Persona

Interruption frequency is a *communication behavior*, not a *personality trait*. The same person can interrupt frequently in one context (e.g., a heated argument) and not at all in another (e.g., a calm discussion). In our experimental design:

- Persona traits are fixed across all conditions for a given character. If interruption were a persona-level trait, it could not vary with bid-style, eliminating an important behavioral dimension from the experimental manipulation.
- Interruption directly affects turn-taking dynamics, which are central to FSA. A high-interruption first speaker may amplify position advantage by dominating conversational space. A zero-interruption first speaker may lose positional advantage despite going first. These are testable hypotheses that require interruption to vary with bid-style.
- The `decide_next_speaker()` function in `conversation_engine.py` uses LLM-based speaker selection. Interruption frequency in the bid-style overlay influences how aggressively the persona bids for the floor, which in turn affects the speaker-selector's decisions. This creates a measurable pathway from bid-style to turn distribution to FSA metrics.

### 9.5 Runtime Combination: Persona + Bid-Style

The matrix runner (invoked from `app/app.py` Bid-Style Matrix tab, or the 540-session batch equivalent) combines persona and bid-style at runtime through the following process:

1. **Load persona**: `data_loader.load_v2_personas()` reads `prompts/personas_v2.json`. The persona's `bid_style` field is `"neutral"` (placeholder).
2. **Load bid-style overlay**: `data_loader.load_bid_styles()` reads `prompts/bid_styles.json` and returns a dict keyed by `bid_style_id`.
3. **Apply overlay**: `data_loader.apply_bid_style_overlay(persona, bid_style_data)` mutates the persona in place, setting four fields: `bid_style` (ID), `interruption_frequency`, `bid_style_principles` (behavioral rules array), `bid_style_speaking_modifiers` (speaking pattern array).
4. **Inject into prompt**: `conversation_engine.generate_agent_turn()` fills the unified `prompts/patient_prompt.txt` template. Persona fields (`[name]`, `[traits]`, `[hidden_tension_leakage]`, `[bid_style]`, etc.) are replaced with the overlaid persona values. The slot label (`[slot_label]`) resolves to "Partner A" or "Partner B" based on the persona's role, keeping prompt framing symmetric across positions.
5. **Generate session**: The filled prompt is used for every turn by that patient. The bid-style remains fixed for the full 30-turn session. Both patients use the same template file with different slot-label and persona fills, eliminating the prompt asymmetry that was present in the v1 pipeline (separate `patient_A_prompt.txt` / `patient_B_prompt.txt` with systematically different framing language).

This process ensures that the persona's psychological identity remains intact while the communication behavior is systematically varied across experimental conditions, and that any measured position bias cannot be attributed to prompt-level asymmetries between slots.

**Prompt asymmetry fix (2026-04):** In the v1 pipeline the Patient A prompt described the partner as "most directly affected" by the concern while the Patient B prompt framed them as "equally invested." Patient A's rule 4a hardcoded "withdrawal" as the hidden-tension leakage example; Patient B's rule 4a described the behavior generically. Patient B's rule 13 contained a hardcoded persona name ("Victoria") that leaked across all sessions. Patient A contained a PROACTIVE CONTEMPT rule (16) that Patient B lacked. These systematic differences created a prompt-level confound: any observed position bias could be attributed partly to the prompts rather than to position. The v2 unified template removes every such asymmetry. Both slots now read the same file with the same rules; only `[slot_label]`, persona fields, and bid-style overlay differ.

### 9.6 Session Output Structure

Each session writes a JSON transcript to `transcripts/therapy_transcript_<N>.json` plus a readable `.txt` copy. The JSON now leads with a `metrics_summary` block containing all primary outcomes in one place:

```
metrics_summary
  fas (score, direction, reasoning)
  brd (score, mean_depth_A, mean_depth_B)
  cas (score, C_A, C_B)
  therapeutic_alliance (overall, validation, neutrality, guidance)
  panas_patient_a (positive_change, negative_change, net_change)
  panas_patient_b (positive_change, negative_change, net_change)
  panas_couple_net (sum of both partners' net_change)
  session_metadata (turns, structure, first_speaker, therapist_mode,
                    therapist_model, temperature, couple_id,
                    bid_style_a, bid_style_b, position)
```

This block is followed by the transcript, participant details, PANAS before/after arrays, and the full therapist-alliance and therapeutic-balance evaluator outputs. The legacy v1 fields (`trigger_log`, `intervention_scores`, `intervention_count`, `scored_interventions_rejected`) are dropped on save because the trigger-based intervention pathway is inactive in the v2 matrix design.

---

## 10. Empirical Context (as of 2026-04-17)

Two batches have been run against the v2 pipeline. Findings are reported to calibrate expectations for the remaining 504 sessions of the full design.

### 10.1 Test experiment (36 sessions, pre-matrix)

Ran on the 9 cross-couple bid-style cells x 2 therapist models (Llama 3.1 8B, 70B) x 2 positions (alpha, beta) under Individual Focus + Sequential. Findings:

- **Recency advantage, not primacy.** Mean DELTA_FAS (beta - alpha) = -0.18 across all pairs; only 22% of pairs produced positive delta. Individual Focus pushes the signal toward second-speaker advantage because the therapist's last-addressed framing dominates the FAS scorer's perception.
- **Model noise scales with size inversely.** Llama 8B: mean |FAS| 0.61, |BRD| 3.31, |CAS| 5.0. Llama 70B: |FAS| 0.24, |BRD| 0.68, |CAS| 2.4. The 8B model is unusable as a stable therapist for bias measurement at this session length.
- **70B shows complete B-skew under Individual Focus.** 0 of 9 pairs produced positive DELTA_FAS. This is consistent with the recency interpretation, not a 70B-specific artifact.

### 10.2 C2 matrix (36 sessions, Sequential, GPT-4o)

Ran the full 3x3 bid-style matrix x 2 positions = 18 sessions under Individual Focus, then repeated under Standard. Both batches on couple C2 (Eszter Kovacs x Rajan Singh). Summary:

| Metric | Individual Focus (n=18) | Standard (n=18) | Observation |
|---|---|---|---|
| FAS mean (SD) | -0.18 (0.17) | -0.34 (0.34) | Mean shifts slightly more B-favoring; **SD doubles** |
| FAS range | [-0.5, +0.1] | [-0.8, +0.5] | Standard expands both tails |
| BRD mean (SD) | +0.31 (0.28) | +0.56 (0.61) | **SD doubles**; Standard can hit BRD = +2.0 |
| CAS mean (SD) | -0.78 (1.55) | -0.33 (1.56) | Essentially unchanged (CAS counts content type, not addressing pattern) |
| TA mean | 7.73 | 7.58 | Flat in both modes; 14/18 cells at 7.2-8.2 |
| Eszter PANAS net | -10.4 (3.56) | -9.94 (5.16) | Persona floor persists in both modes |
| Rajan PANAS net | +2.89 (4.11) | +3.22 (4.39) | Persona ceiling persists in both modes |

**Interpretation:**

- The claim in earlier documentation that Individual Focus "destroys the FAS signal" is partially wrong. Individual Focus *compresses FAS variance* (halves the SD) but does not zero the mean when persona asymmetry exists; the FAS scorer judges content framing adoption, not naming frequency.
- Standard mode recovers FAS spread (the expected effect) and recovers BRD spread (new finding), but does not flip the sign. Both modes remain B-favoring because the underlying content skew is driven by Eszter's floor-prone persona, not by the therapist's addressing rule.
- TA is saturating at the evaluator's upper band across both modes. This is a measurement ceiling, not a true alliance plateau. TA should not be used as a primary discriminator between experimental cells in its current form.
- CAS is orthogonal to therapist mode in this couple because the therapist's challenge behavior is rare overall (mean |CAS| around 1.2 to 1.3 in both batches).

### 10.3 Implications for the full 540-session design

1. **Run all five couples.** C2 alone cannot separate persona-floor effects from position or mode effects. C1 (classic anxious-avoidant), C3 (symmetric anxious), C4 (disorganized-avoidant), and C5 (secure-avoidant) each load the design differently; only the across-couple contrast can decouple persona from position.
2. **Standard is the preferred primary condition for FAS characterization.** Individual Focus is still useful as a control because it compresses variance; contrast with Standard gives a handle on how much of the observed FAS is driven by addressing count versus content adoption.
3. **Report SD and max-|metric| alongside means.** The C2 matrix would look null if only means were reported. Mode-induced spread is the actual signal.
4. **Audit or revise the TA evaluator.** Ceiling saturation across 36 sessions indicates the rubric is not extracting session-level variation. Options: tighten the rubric, switch the TA scoring model, or drop TA from the primary-metric tier.

---

## References

1. Wang, R., et al. (2024). PATIENT-Psi: Using Large Language Models to Simulate Patients for Training Mental Health Professionals. *EMNLP 2024 Main*. https://aclanthology.org/2024.emnlp-main.711/
2. Kim, S., et al. (2024). Cactus: Towards Psychological Counseling Conversations using Cognitive Behavioral Theory. *Findings of EMNLP 2024*. https://aclanthology.org/2024.findings-emnlp.832/
3. Choi, S., et al. (2024). Roleplay-doh: Enabling Domain-Experts to Create LLM-simulated Patients via Eliciting and Adhering to Principles. *EMNLP 2024 Main*. https://aclanthology.org/2024.emnlp-main.591/
4. Zhang, Y., et al. (2025). From Personas to Talks: Revisiting the Impact of Personas on LLM-Synthesized Emotional Support Conversations. *EMNLP 2025 Main*. https://aclanthology.org/2025.emnlp-main.277/
5. Lee, J., et al. (2025). Can LLM Agents Maintain a Persona in Discourse? *EMNLP 2025 Main*. https://aclanthology.org/2025.emnlp-main.1487/
6. Park, H., et al. (2025). Evaluating Behavioral Alignment in Conflict Dialogue: A Multi-Dimensional Comparison of LLM Agents and Humans. *EMNLP 2025 Main*. https://aclanthology.org/2025.emnlp-main.828/
7. Jiang, H., et al. (2024). PersonaLLM: Investigating the Ability of Large Language Models to Express Personality Traits. *Findings of NAACL 2024*. https://aclanthology.org/2024.findings-naacl.229/
8. Tseng, Y.-C., et al. (2024). Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization. *Findings of EMNLP 2024*. https://aclanthology.org/2024.findings-emnlp.969/
9. Liu, W., et al. (2025). Crafting Customisable Characters with LLMs: A Persona-Driven Role-Playing Agent Framework. *Findings of EMNLP 2025*. https://aclanthology.org/2025.findings-emnlp.1100/
10. Shah, A., Silpasuwanchai, C., et al. (2026). Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models. *ACL 2026 Main*. https://arxiv.org/abs/2604.10733
