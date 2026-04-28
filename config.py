import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_GPT_KEY  = os.getenv("OPENROUTER_GPT_KEY")
OPENROUTER_L8B_KEY  = os.getenv("OPENROUTER_L8B_KEY")
OPENROUTER_L70B_KEY = os.getenv("OPENROUTER_L70B_KEY")

CONVERSATION_MODEL = "openai/gpt-4o"
PANAS_MODEL = "openai/gpt-4o"
INTERVENTION_MODEL = "openai/gpt-4o-mini"
SCORING_MODEL = "openai/gpt-4o"

THERAPIST_MODEL_OPTIONS = {
    "GPT-4o":        {"model": "openai/gpt-4o",                      "key_env": "OPENROUTER_GPT_KEY"},
    "Llama 3.1 8B":  {"model": "meta-llama/llama-3.1-8b-instruct",   "key_env": "OPENROUTER_L8B_KEY"},
    "Llama 3.1 70B": {"model": "meta-llama/llama-3.1-70b-instruct",  "key_env": "OPENROUTER_L70B_KEY"},
}
DEFAULT_THERAPIST_MODEL = "openai/gpt-4o"

PROJECT_ROOT = Path(__file__).parent
CHUNKS_DIR = PROJECT_ROOT / "discussions"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"

THERAPY_PLANS_FILE = CHUNKS_DIR / "Final_therapy_discussion.json"
PERSONAS_FILE = PROMPTS_DIR / "trigger-personas.json"
PERSONAS_V2_FILE = PROMPTS_DIR / "personas_v2.json"
BID_STYLES_FILE = PROMPTS_DIR / "bid_styles.json"
PERSONAS_PANAS_FILE = PROMPTS_DIR / "trigger-personas_PANAS_2.json"
PERSONAS_V2_PANAS_FILE = PROMPTS_DIR / "personas_v2_PANAS.json"

THERAPIST_PROMPT_FILE = PROMPTS_DIR / "therapist_prompt.txt"
THERAPIST_INDIVIDUAL_FOCUS_PROMPT_FILE = PROMPTS_DIR / "therapist_option2_prompt.txt"
PATIENT_PROMPT_FILE = PROMPTS_DIR / "patient_prompt.txt"
THERAPIST_INTERVENTION_PROMPT_FILE = PROMPTS_DIR / "therapist_intervention_decision.txt"

TRANSCRIPTS_DIR.mkdir(exist_ok=True)

SESSION_MIN_TURNS = 30
SESSION_MAX_TURNS = 30

INTERVENTION_THRESHOLD = 65
INTERVENTION_COOLDOWN_TURNS = 3

CONVERSATION_STRUCTURES = [
    "Sequential",
    "LLM-Based Selection",
]

FIRST_SPEAKER_OPTIONS = [
    "Patient A",
    "Patient B",
    "Random"
]

DEFAULT_V2_THERAPY_TOPIC = "Recurring conflict patterns and unmet emotional needs"

PANAS_POSITIVE = [
    "Interested", "Excited", "Strong", "Enthusiastic", "Proud",
    "Alert", "Inspired", "Determined", "Attentive", "Active"
]

PANAS_NEGATIVE = [
    "Distressed", "Upset", "Guilty", "Scared", "Hostile",
    "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"
]

PANAS_ALL = PANAS_POSITIVE + PANAS_NEGATIVE

MAX_TOKENS_PER_TURN = 120
PANAS_MAX_TOKENS = 1500
INTERVENTION_SCORING_MAX_TOKENS = 500
INTERVENTION_GENERATION_MAX_TOKENS = 200

TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 1.0
TEMPERATURE_STEP = 0.1

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

CONSOLE_WIDTH = 70
DIVIDER = "=" * CONSOLE_WIDTH


def validate_config():
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

config_issues = validate_config()
if config_issues:
    print("⚠️  Configuration issues:")
    for issue in config_issues:
        print(f"  - {issue}")
