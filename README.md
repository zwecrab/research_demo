# README: MODULAR AI COUPLES THERAPY SIMULATION

## 🎯 PROJECT SUMMARY

Status: ✅ **ALL FILES CREATED & READY TO USE**

---

## 📦 FILES CREATED (10 Modules + 2 Guides)

### Core Modules
1. ✅ **config.py** - Configuration & constants
2. ✅ **data_loader.py** - Asset loading (JSON, prompts)
3. ✅ **user_interface.py** - CLI menu system
4. ✅ **session_setup.py** - Session initialization
5. ✅ **conversation_engine.py** - Dialogue generation & speaker selection
6. ✅ **trigger_system.py** - Trigger detection (4 modalities)
7. ✅ **intervention_system.py** - LLM scoring & intervention generation
8. ✅ **panas_analyzer.py** - Emotional assessment (pre/post)
9. ✅ **output_manager.py** - File I/O & summaries
10. ✅ **main.py** - Orchestrator (ties everything together)

### Documentation
11. ✅ **REFACTORING_GUIDE.md** - Detailed module explanations
12. ✅ **QUICK_START.md** - Installation & getting started

---

## 🚀 QUICK START

### Step 1: Copy Files to Project Directory
```
your_project/
├── config.py
├── data_loader.py
├── user_interface.py
├── session_setup.py
├── conversation_engine.py
├── trigger_system.py
├── intervention_system.py
├── panas_analyzer.py
├── output_manager.py
├── main.py
└── .env (create this)
```

### Step 2: Install Dependencies
```bash
pip install openai python-dotenv
```

### Step 3: Create .env File
```
OPENAI_API_KEY=sk-your-key-here
```

### Step 4: Run
```bash
python main.py
```

---

## 📊 MODULE DEPENDENCY DIAGRAM

```
main.py (Orchestrator)
    ↓
    ├─→ data_loader.py (Load assets)
    ├─→ user_interface.py (User input)
    ├─→ session_setup.py (Initialize session)
    ├─→ conversation_engine.py (Generate dialogue)
    │   └─→ config.py (Models, temperature)
    ├─→ trigger_system.py (Detect triggers)
    ├─→ intervention_system.py (Score & generate)
    ├─→ panas_analyzer.py (Emotional analysis)
    └─→ output_manager.py (Save results)
```

---

## 🎛️ USER FLOW

```
START
  ↓
1. Select Session Topic
  ├─ ALCOHOL ABUSE
  ├─ ANXIETY
  ├─ CONFLICT
  └─ (etc.)
  ↓
2. Select Temperature (0.0-1.0)
  ├─ 0.0 = Deterministic
  ├─ 0.5 = Balanced
  └─ 1.0 = Creative
  ↓
3. Select Conversation Structure
  ├─ Sequential (fixed rotation)
  ├─ LLM Only (intelligent selection, no triggers)
  └─ LLM with Triggers (full system) ← NEW
  ↓
4. (If LLM+Triggers) Select Trigger Type
  ├─ Direct Intervention Request
  ├─ Time-based Analysis
  ├─ Semantic Analysis
  ├─ Quantitative Analysis
  └─ All Triggers
  ↓
5. (NEW!) Select First Speaker
  ├─ Patient A (affected party)
  ├─ Patient B (supporting partner)
  ├─ Random
  ↓
6. (NEW!) Persona Selection
  ├─ Random (default)
  ├─ Manual Selection (browse & choose specific personas)
  ↓
[SIMULATION RUNS: 25-35 turns]
  ↓
[POST-SESSION PANAS ANALYSIS]
  ↓
[OUTPUT: JSON transcript, summary, report]
  ↓
END
```

---

## 📋 FEATURE BREAKDOWN

### Trigger Detection (4 Modalities)

| Trigger | Detection | Example |
|---------|-----------|---------|
| **Direct Request** | Keywords | "Can you help us?" |
| **Time-based** | Silence >30s | Speaker hasn't spoken 3+ turns |
| **Semantic** | Escalation + self-harm | "I HATE this!!! I want to die" |
| **Quantitative** | Dominance + word count | 6+ consecutive messages or 100+ words |

### Intervention Scoring (4 Dimensions)

| Dimension | Scale | Meaning |
|-----------|-------|---------|
| Flow Disruption | 0-100 | How jarring would interruption be? |
| Therapeutic Need | 0-100 | Is there genuine distress? |
| Timing | 0-100 | Is it a natural pause point? |
| Impact | 0-100 | Will it help (USR framework)? |
| **Average** | **0-100** | **Trigger threshold: ≥70** |
 
### Intervention Transparency
- **Reasoning**: The system now provides an explicit explanation for *why* an intervention was triggered, referencing the specific scoring dimension and observed behavior.

### PANAS Emotional Assessment

**20 Emotions measured:**
- **10 Positive**: Interested, Excited, Strong, Enthusiastic, Proud, Alert, Inspired, Determined, Attentive, Active
- **10 Negative**: Distressed, Upset, Guilty, Scared, Hostile, Irritable, Ashamed, Nervous, Jittery, Afraid

**Outcome Metrics:**
- Pre-session baseline (from persona)
- Post-session scoring (LLM evaluated)
- Delta calculation (improvement measure)

---

## 💡 KEY INNOVATIONS

### 1. Four-Dimensional Intervention Scoring
→ Not just *when* to intervene (triggers), but *whether* intervening will help (clinical reasoning)

### 2. NEW: First Speaker & Persona Selection
→ Research design feature: control exactly *who* speaks first and *which* specific persona characteristics are active.

### 3. Modular Architecture
→ Test components independently (Sequential vs LLM Only vs LLM+Triggers)

### 4. PANAS Pre/Post Assessment
→ Empirical outcome measurement (emotional state improvement)

---

## 🧪 EXPERIMENT EXAMPLES

### Experiment 1: Baseline (Sequential)
```
Structure: Sequential (Therapist → Patient A → Patient B cycle)
Triggers: Disabled
First Speaker: (N/A)
→ Output: Pure dialogue without AI interference
```

### Experiment 2: Speaker Selection
```
Structure: LLM Only
Triggers: Disabled
First Speaker: Patient A
→ Output: Intelligent speaker balancing
```

### Experiment 3: Full System
```
Structure: LLM with Triggers
Trigger Type: Semantic Analysis
First Speaker: Patient B
→ Output: Full adaptive facilitation with emotional crisis detection
```

### Experiment 4: First Speaker Ablation
```
Run 3 sessions, vary first speaker:
- Patient A first
- Patient B first
- Random

→ Compare PANAS deltas across sessions
```

---

## 📊 OUTPUT FILES

### Generated Files
```
transcripts/
├── therapy_transcript_1.json          # Full session data
├── therapy_transcript_2.json          # Next session
├── transcript_readable_*.txt          # Human-readable format
└── (auto-incremented numbering)
```

### JSON Structure
```json
{
  "session_topic_header": "ALCOHOL ABUSE",
  "conversation_structure": "LLM with Triggers",
  "first_speaker_selection": "Patient A",  ← NEW
  "session_transcript": [
    {
      "turn": 1,
      "speaker": "Therapist",
      "dialogue": "..."
    },
    ...
  ],
  "intervention_count": 3,
  "Patient_A_PANAS_DELTA": [
    {"feeling": "Interested", "before_score": 3, "after_score": 4, "difference": 1}
  ]
}
```

---

## 🔧 CUSTOMIZATION

### Change Intervention Threshold
**File**: `config.py`
```python
INTERVENTION_THRESHOLD = 70  # Change to 50, 60, 80, etc.
```

### Add New Trigger Type
**File**: `trigger_system.py`
```python
def detect_my_trigger(message):
    return "pattern" in message.lower()

# In detect_triggers():
if selected_trigger == "My Trigger":
    if detect_my_trigger(current_message):
        triggers_detected.append({...})
```

### Change Model
**File**: `config.py`
```python
CONVERSATION_MODEL = "gpt-4-turbo"  # Or any OpenAI model
```

---

## 📈 RESEARCH WORKFLOW

### Phase 1: Validation
- [ ] Run 3 Sequential sessions
- [ ] Verify dialogue quality
- [ ] Confirm PANAS parsing works

### Phase 2: Ablation
- [ ] 10 sessions × 3 structures = 30 sessions
- [ ] Compare PANAS outcomes
- [ ] Measure intervention effectiveness

### Phase 3: First Speaker Analysis
- [ ] 15 sessions varying first speaker
- [ ] Analyze PANAS deltas
- [ ] Statistical hypothesis testing

### Phase 4: Threshold Optimization
- [ ] Test INTERVENTION_THRESHOLD = 50, 60, 70, 80, 90
- [ ] Find sweet spot
- [ ] Correlate with quality

### Phase 5: Human Evaluation
- [ ] Have therapists rate interventions
- [ ] Collect feedback on appropriateness
- [ ] Iterate on prompt templates

### Phase 6: Publication
- [ ] Summarize findings
- [ ] Compare to related work
- [ ] Submit to ACL/therapy journals

---

## 🎓 ACADEMIC GROUNDING

### ACL Research Integration
- **FED Framework**: 4D intervention scoring reflects dialogue quality metrics
- **USR Framework**: Impact Potential dimension measures user satisfaction

### Therapeutic Practice
- **PANAS**: Validated 20-item emotion inventory (Watson & Clark, 1988)
- **Couples Therapy**: Multi-party dialogue with therapeutic balance

### Innovation
- Few systems combine trigger detection + LLM scoring + PANAS measurement
- Adaptive speaker selection with post-intervention control is novel

---

## 📚 DOCUMENTATION

- **QUICK_START.md** - Installation & basic usage
- **REFACTORING_GUIDE.md** - Detailed module explanations
- **config.py** - Inline documentation of all constants
- **[Each module]** - Docstrings for all functions

---

## ✅ VALIDATION CHECKLIST

- [ ] All 10 modules created
- [ ] Imports work: `python -c "from config import *"`
- [ ] Assets load: Check chunks/, prompts/ directories
- [ ] .env file created with valid API key
- [ ] First test run: `python main.py`
- [ ] Output generated: Check transcripts/
- [ ] JSON valid: `python -c "import json; json.load(open('transcripts/therapy_transcript_1.json'))"`
- [ ] PANAS data present: Check Patient_A_PANAS_DELTA in JSON
- [ ] Summary displays: Check console output

---

## 🆘 TROUBLESHOOTING

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: config` | All .py files in same directory as main.py |
| `OPENAI_API_KEY not found` | Create .env with valid key |
| `FileNotFoundError: chunks/` | Move data files to correct location |
| PANAS parsing fails | Check panas_analyzer.py error message, adjust regex |
| Intervention score always 50 | Check JSON extraction in intervention_system.py |

---

## 🚀 NEXT STEPS

1. **Copy files** to your project directory
2. **Install dependencies**: `pip install openai python-dotenv`
3. **Create .env** with your OpenAI API key
4. **Run**: `python main.py`
5. **Check output**: `ls -lh transcripts/`
6. **Analyze**: Open JSON file, review results
7. **Iterate**: Modify config.py for experiments
8. **Publish**: Share findings with research community

---

## 📞 SUPPORT

- Check docstrings in each module
- Review REFACTORING_GUIDE.md for details
- Read QUICK_START.md for setup
- Debug by adding print statements in specific modules

---

## 📝 LICENSE & ATTRIBUTION

This modular refactoring maintains all functionality of the original test5.py while providing:
- Clear separation of concerns
- Production-ready architecture
- Research-grade output
- Extensible design for future work

---

**Status**: ✅ **COMPLETE & READY TO USE**

**Created**: January 8, 2026
**Version**: 2.1 (Modular + First Speaker + Persona Selection)

**Start with**: `QUICK_START.md` → `python main.py` → Check `transcripts/`

Good luck with your research! 🎓

---

## 📚 Module Quick Reference

| Module | Purpose | Key Functions |
|--------|---------|---|
| **config.py** | Constants & settings | All configuration |
| **data_loader.py** | Load assets | `load_all_assets()` |
| **user_interface.py** | User input | `select_*` functions |
| **session_setup.py** | Initialize session | `setup_session_parameters()` |
| **conversation_engine.py** | Generate dialogue | `generate_agent_turn()` |
| **trigger_system.py** | Detect triggers | `detect_triggers()` |
| **intervention_system.py** | Score & generate interventions | `calculate_intervention_score()` |
| **panas_analyzer.py** | Emotional assessment | `compute_panas_delta()` |
| **output_manager.py** | Save & display results | `save_session_json()` |
| **main.py** | Orchestrate everything | `main()` |
