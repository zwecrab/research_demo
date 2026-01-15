# config.py
# Central configuration - constants, thresholds, file paths, model names

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ============================================================================
# API & MODEL CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Selection
CONVERSATION_MODEL = "gpt-4o"      # Main dialogue generation (faster, cheaper)
PANAS_MODEL = "gpt-4"              # Emotional assessment (more analytical)
INTERVENTION_MODEL = "gpt-4o"      # Facilitation responses (balance speed/quality)
SCORING_MODEL = "gpt-4"            # Intervention necessity scoring

# ============================================================================
# FILE PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
CHUNKS_DIR = PROJECT_ROOT / "discussions"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"

# Data files
THERAPY_PLANS_FILE = CHUNKS_DIR / "Final_therapy_discussion.json"
PERSONAS_FILE = PROMPTS_DIR / "trigger-personas.json"
PERSONAS_PANAS_FILE = PROMPTS_DIR / "trigger-personas_PANAS_2.json"

# Prompt files
THERAPIST_PROMPT_FILE = PROMPTS_DIR / "therapist_prompt.txt"
PATIENT_A_PROMPT_FILE = PROMPTS_DIR / "patient_A_prompt.txt"
PATIENT_B_PROMPT_FILE = PROMPTS_DIR / "patient_B_prompt.txt"

# Create transcripts directory if it doesn't exist
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# SESSION CONTROL
# ============================================================================

SESSION_MIN_TURNS = 25
SESSION_MAX_TURNS = 35

# ============================================================================
# INTERVENTION THRESHOLDS & SCORING
# ============================================================================

INTERVENTION_THRESHOLD = 70  # 0-100 average score needed to intervene

# Trigger Type Keywords
DIRECT_INTERVENTION_KEYWORDS = [
    "help us", "need guidance", "step in", "what should we do", 
    "can you help", "need your help", "help please", "intervene",
    "guide us"
]

SEMANTIC_ESCALATION_KEYWORDS = [
    "always", "never", "hate", "sick of", "can't stand",
    "ridiculous", "pathetic", "stupid", "awful", "terrible",
    "disgusted", "frustrated", "angry", "furious"
]

SEMANTIC_SELF_HARM_KEYWORDS = [
    "hurt myself", "better off without me", "want to disappear",
    "end it all", "kill myself", "suicide", "suicidal", "self-harm",
    "cut myself"
]

# Quantitative Analysis Thresholds
QUANTITATIVE_CONSECUTIVE_THRESHOLD = 6    # Messages before trigger
QUANTITATIVE_WORD_THRESHOLD = 100         # Words per message

# Time-based Analysis
TIME_SILENCE_THRESHOLD = 30  # Seconds (simulated)

# ============================================================================
# CONVERSATION STRUCTURES
# ============================================================================

CONVERSATION_STRUCTURES = [
    "Sequential",
    "LLM Only",
    "LLM with Triggers"
]

TRIGGER_TYPES = [
    "Direct Intervention Request",
    "Time-based Analysis",
    "Semantic Analysis",
    "Quantitative Analysis",
    "All Triggers"
]

FIRST_SPEAKER_OPTIONS = [
    "Patient A",
    "Patient B",
    "Random"
]

# ============================================================================
# PANAS EMOTION LISTS (Positive & Negative Affect Schedule)
# ============================================================================

PANAS_POSITIVE = [
    "Interested", "Excited", "Strong", "Enthusiastic", "Proud",
    "Alert", "Inspired", "Determined", "Attentive", "Active"
]

PANAS_NEGATIVE = [
    "Distressed", "Upset", "Guilty", "Scared", "Hostile",
    "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"
]

PANAS_ALL = PANAS_POSITIVE + PANAS_NEGATIVE

# ============================================================================
# API REQUEST CONFIGURATION
# ============================================================================

MAX_TOKENS_PER_TURN = 150  # Force concise responses
PANAS_MAX_TOKENS = 1500
INTERVENTION_SCORING_MAX_TOKENS = 500
INTERVENTION_GENERATION_MAX_TOKENS = 200

# Temperature ranges for user selection
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 1.0
TEMPERATURE_STEP = 0.1

# ============================================================================
# OUTPUT & LOGGING
# ============================================================================

# Emoji indicators for console output
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_THINKING = "🤔"
EMOJI_SEARCH = "🔍"
EMOJI_SCORE = "📊"
EMOJI_REASONING = "💭"
EMOJI_INTERVENTION = "🤖"
EMOJI_START = "🎬"
EMOJI_END = "✅"
EMOJI_CONFIG = "⚙️"

# Console formatting
CONSOLE_WIDTH = 70
DIVIDER = "=" * CONSOLE_WIDTH

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate that all required configuration is present."""
    issues = []
    
    if not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY not set in .env file")
    
    if not THERAPY_PLANS_FILE.exists():
        issues.append(f"Therapy plans file not found: {THERAPY_PLANS_FILE}")
    
    if not PERSONAS_FILE.exists():
        issues.append(f"Personas file not found: {PERSONAS_FILE}")
    
    if not THERAPIST_PROMPT_FILE.exists():
        issues.append(f"Therapist prompt file not found: {THERAPIST_PROMPT_FILE}")
    
    return issues

# Run validation on import
config_issues = validate_config()
if config_issues:
    print("⚠️  Configuration issues:")
    for issue in config_issues:
        print(f"  - {issue}")
