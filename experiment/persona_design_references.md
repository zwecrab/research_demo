# Persona Design Reference Papers

Last updated: 2026-04-14

Papers used to ground the design of 10 bid-style-neutral personas (5 couples) for the full 540-session experiment.

---

## Tier 1: Directly Applicable (Therapy/Counseling + Persona Design)

### 1. PATIENT-Psi (EMNLP 2024)
- **Title**: PATIENT-Psi: Using Large Language Models to Simulate Patients for Training Mental Health Professionals
- **Venue**: EMNLP 2024 Main
- **URL**: https://aclanthology.org/2024.emnlp-main.711/
- **GitHub**: https://github.com/ruiyiw/patient-psi
- **Use for**: Primary reference for persona structure. Builds simulated therapy patients using a cognitive model (core beliefs, intermediate beliefs, coping strategies) integrated with GPT-4. Patients can take on different conversational styles. Validated with 13 trainees + 20 experts.

### 2. Cactus (Findings of EMNLP 2024)
- **Title**: Cactus: Towards Psychological Counseling Conversations using Cognitive Behavioral Theory
- **Venue**: Findings of EMNLP 2024
- **URL**: https://aclanthology.org/2024.findings-emnlp.832/
- **GitHub**: https://github.com/coding-groot/cactus
- **Use for**: CBT-specific persona design. Designs clients with varied personas and has counselors apply CBT techniques. Grounded in CBT case formulation. Use for structuring the relationship between persona traits and therapeutic context.

### 3. Roleplay-doh (EMNLP 2024)
- **Title**: Roleplay-doh: Enabling Domain-Experts to Create LLM-simulated Patients via Eliciting and Adhering to Principles
- **Venue**: EMNLP 2024 Main
- **URL**: https://aclanthology.org/2024.emnlp-main.591/
- **Website**: https://roleplay-doh.github.io/
- **Use for**: Prompt engineering architecture for bid-style injection. Expert counselors create AI patients via "principles" (natural language rules). Principle-adherence prompting improved response quality by 30%. From Stanford SALT Lab.

### 4. From Personas to Talks (EMNLP 2025)
- **Title**: From Personas to Talks: Revisiting the Impact of Personas on LLM-Synthesized Emotional Support Conversations
- **Venue**: EMNLP 2025 Main
- **URL**: https://aclanthology.org/2025.emnlp-main.277/
- **Use for**: Evidence that persona traits modify LLM dialogue dynamics in measurable ways. Subtle shifts in emotionality and extraversion change the distribution of emotional support strategies. Validates decoupling bid-style from persona.

---

## Tier 2: Persona Maintenance and Evaluation (Methodology Support)

### 5. Can LLM Agents Maintain a Persona in Discourse? (EMNLP 2025)
- **Title**: Can LLM Agents Maintain a Persona in Discourse?
- **Venue**: EMNLP 2025 Main
- **URL**: https://aclanthology.org/2025.emnlp-main.1487/
- **Use for**: Justifying pilot test and model comparison. Tests OCEAN-based persona maintenance; finds consistency varies by model. Supports why 8B vs 70B comparison matters for persona fidelity.

### 6. Evaluating Behavioral Alignment in Conflict Dialogue (EMNLP 2025)
- **Title**: Evaluating Behavioral Alignment in Conflict Dialogue: A Multi-Dimensional Comparison of LLM Agents and Humans
- **Venue**: EMNLP 2025 Main
- **URL**: https://aclanthology.org/2025.emnlp-main.828/
- **Use for**: Evaluation methodology and Five-Factor personality in conflict. Simulates multi-turn conflict dialogues with Five-Factor profiles. Evaluates linguistic style, emotional expression (anger dynamics), and strategic behavior.

### 7. PersonaLLM (NAACL 2024)
- **Title**: PersonaLLM: Investigating the Ability of Large Language Models to Express Personality Traits
- **Venue**: Findings of NAACL 2024
- **URL**: https://aclanthology.org/2024.findings-naacl.229/
- **Use for**: Evidence that Big Five prompting produces distinguishable behavior. LLM personas' BFI scores are consistent with assigned traits; large effect sizes across five traits; humans perceive traits with up to 80% accuracy.

---

## Tier 3: Surveys and Frameworks

### 8. Two Tales of Persona in LLMs (Findings of EMNLP 2024)
- **Title**: Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization
- **Venue**: Findings of EMNLP 2024
- **URL**: https://aclanthology.org/2024.findings-emnlp.969/
- **Use for**: Related work section. Comprehensive survey covering role-playing vs personalization paradigms.

### 9. Crafting Customisable Characters (Findings of EMNLP 2025)
- **Title**: Crafting Customisable Characters with LLMs: A Persona-Driven Role-Playing Agent Framework
- **Venue**: Findings of EMNLP 2025
- **URL**: https://aclanthology.org/2025.findings-emnlp.1100/
- **Use for**: Self-questioning chains for persona consistency maintenance.

### 10. Too Nice to Tell the Truth (ACL 2026 Main)
- **Title**: Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models
- **Venue**: ACL 2026 Main
- **URL**: https://arxiv.org/abs/2604.10733
- **GitHub**: https://github.com/aryashah2k/Quantifying-Agreeableness-Driven-Sycophancy-in-Role-Playing-Language-Models
- **HuggingFace**: https://huggingface.co/datasets/aryashah00/Persona-Induced-Sycophancy
- **Use for**: Critical reference for agreeableness variance in persona design. 275 personas scored on NEO-IPIP agreeableness subscales (Trust, Altruism, Cooperation, Sympathy; 40 items, 1-5 Likert, normalized 0-1). Found r=0.87 correlation between persona agreeableness and sycophancy in 9/13 models (including Llama 3.1 8B). Introduced Trait-Truthfulness Gap (TTG) metric. Co-authored by Dr. Chaklam Silpasuwanchai (committee member).

---

## Design Approach (derived from papers above)

Each of the 10 personas should include:
1. **Cognitive model** (PATIENT-Psi): core beliefs, intermediate beliefs, coping strategies
2. **OCEAN profile** (PersonaLLM, Behavioral Alignment): Five-Factor personality dimensions using qualitative labels (low/moderate/high), bid-style-neutral
3. **Attachment style** (Bowlby/Gottman): secure, anxious, avoidant, or disorganized
4. **Bid-style as separate runtime injection** (Roleplay-doh): principle-adherence prompting pattern
5. **Agreeableness variance** (Too Nice to Tell the Truth): deliberate variation across personas to control for sycophancy confound
