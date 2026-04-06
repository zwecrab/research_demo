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

# OpenRouter (for alternative therapist models — Llama, Gemma, etc.)
OPENROUTER_API_KEY  = os.getenv("OEPNROUTER_API_KEY")   # note: typo in .env key name
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection
CONVERSATION_MODEL = "gpt-4o"      # Patient dialogue generation (always OpenAI)
PANAS_MODEL = "gpt-4o"             # Emotional assessment
INTERVENTION_MODEL = "gpt-4o-mini" # Facilitation responses
SCORING_MODEL = "gpt-4o"           # FAS/BRD/CAS scoring

# Therapist model options (default = GPT-4o via OpenAI)
# Free OpenRouter models are placeholders for Llama 3.1 8B / 70B (paid) during testing
THERAPIST_MODEL_OPTIONS = {
    "GPT-4o (OpenAI)":              "gpt-4o",
    "Llama 3.3 70B — free test":    "meta-llama/llama-3.3-70b-instruct:free",
    "Gemma 3 27B — free test":      "google/gemma-3-27b-it:free",
}
DEFAULT_THERAPIST_MODEL = "gpt-4o"

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
THERAPIST_INDIVIDUAL_FOCUS_PROMPT_FILE = PROMPTS_DIR / "therapist_option2_prompt.txt"
PATIENT_A_PROMPT_FILE = PROMPTS_DIR / "patient_A_prompt.txt"
PATIENT_B_PROMPT_FILE = PROMPTS_DIR / "patient_B_prompt.txt"
THERAPIST_INTERVENTION_PROMPT_FILE = PROMPTS_DIR / "therapist_intervention_decision.txt"

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

INTERVENTION_THRESHOLD = 65  # 0-100 average score needed to intervene (raised from 40 to reduce over-intervention)
INTERVENTION_COOLDOWN_TURNS = 3  # Minimum patient turns between facilitator interventions

# ============================================================================
# CONVERSATION STRUCTURES
# ============================================================================

CONVERSATION_STRUCTURES = [
    "Sequential",
    "LLM-Based Selection",
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
MAX_TOKENS_PER_TURN = 120  # Enforce concise 2-4 sentence responses (~30-60 words)
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
