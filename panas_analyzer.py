# panas_analyzer.py (FIXED - Score Calculation)
# PANAS scoring, parsing, delta calculation, outcome measurement

from openai import OpenAI
import re
import os
from config import (
    PANAS_MODEL, PANAS_MAX_TOKENS, OPENROUTER_GPT_KEY, OPENROUTER_BASE_URL,
    PANAS_POSITIVE, PANAS_NEGATIVE, PROMPTS_DIR
)

client = OpenAI(api_key=OPENROUTER_GPT_KEY, base_url=OPENROUTER_BASE_URL)

# ============================================================================
# PROMPT LOADING
# ============================================================================

def load_prompt(filename):
    """Load prompt from external file in prompts directory."""
    prompt_path = os.path.join(PROMPTS_DIR, filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

# Load PANAS scoring prompt
PANAS_PROMPT_TEMPLATE = load_prompt("panas_scoring_prompt.txt")

def get_after_panas_scores(persona, transcript_text):
    """
    Generate post-session PANAS scores using LLM.
    
    Args:
        persona: Persona dictionary
        transcript_text: Patient's dialogue from session
    
    Returns:
        str: LLM response with 20 PANAS emotions
    """
    
    persona_name = persona.get("name", "Patient")
    persona_desc = persona.get("description", "")
    # v2 personas lack a "description" field; construct one from available fields
    if not persona_desc:
        parts = []
        if persona.get("traits"):
            traits = persona["traits"]
            if isinstance(traits, list):
                traits = ", ".join(traits)
            parts.append(f"Traits: {traits}")
        if persona.get("speaking_style"):
            parts.append(f"Style: {persona['speaking_style']}")
        if persona.get("attachment_style"):
            parts.append(f"Attachment: {persona['attachment_style']}")
        if persona.get("hidden_tension"):
            parts.append(f"Inner conflict: {persona['hidden_tension']}")
        persona_desc = ". ".join(parts)
    
    # Format the PANAS prompt from template
    transcript_truncated = transcript_text[-2000:] if len(transcript_text) > 2000 else transcript_text
    panas_prompt = PANAS_PROMPT_TEMPLATE.format(
        persona_name=persona_name,
        persona_desc=persona_desc,
        transcript_text=transcript_truncated
    )
    
    try:
        response = client.chat.completions.create(
            model=PANAS_MODEL,
            messages=[{"role": "user", "content": panas_prompt}],
            temperature=0.1,
            max_tokens=PANAS_MAX_TOKENS
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"❌ Error getting PANAS scores: {e}")
        return ""

def normalize_emotion_name(name):
    """Normalize emotion name for matching - IMPROVED VERSION."""
    if not name:
        return ""
    
    # Strip whitespace and convert to lowercase
    cleaned = name.strip().lower()
    
    # Remove common prefixes/suffixes
    cleaned = re.sub(r'^[\*\-\d\.\s#]+', '', cleaned)  # Remove prefixes
    cleaned = re.sub(r'[\*\s]+$', '', cleaned)          # Remove trailing spaces
    cleaned = re.sub(r':', '', cleaned)                 # Remove colons
    
    # Direct mapping to exact PANAS emotions
    emotion_map = {
        'interested': 'interested',
        'excited': 'excited',
        'strong': 'strong',
        'enthusiastic': 'enthusiastic',
        'proud': 'proud',
        'alert': 'alert',
        'inspired': 'inspired',
        'determined': 'determined',
        'attentive': 'attentive',
        'active': 'active',
        'distressed': 'distressed',
        'upset': 'upset',
        'guilty': 'guilty',
        'scared': 'scared',
        'hostile': 'hostile',
        'irritable': 'irritable',
        'ashamed': 'ashamed',
        'nervous': 'nervous',
        'jittery': 'jittery',
        'afraid': 'afraid'
    }
    
    # Direct lookup
    if cleaned in emotion_map:
        return cleaned
    
    # Fuzzy matching - check if emotion appears in string
    for key in emotion_map.keys():
        if key in cleaned:
            return key
    
    return cleaned

def parse_panas_output(panas_text):
    """
    Parse PANAS LLM output into structured format.
    Robust handling of various formats.
    
    Args:
        panas_text: Raw LLM output
    
    Returns:
        list: Parsed emotions with scores
    """
    emotions = []
    processed_emotions = set()
    
    # All valid PANAS emotion names
    valid_emotions = set([e.lower() for e in PANAS_POSITIVE + PANAS_NEGATIVE])
    
    for line in panas_text.strip().split('\n'):
        line = line.strip()
        
        # Skip empty or non-data lines
        if not line or len(line) < 5:
            continue
        if any(skip in line.lower() for skip in ['here', 'the person', 'based on', 'note:', 'example', 'provide']):
            continue
        
        # Parse: emotion, explanation, score
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
            
            if len(parts) >= 2:
                emotion_raw = parts[0]
                explanation = parts[1] if len(parts) > 1 else ""
                score_str = parts[2] if len(parts) > 2 else parts[-1]
                
                # Normalize emotion name
                emotion_normalized = normalize_emotion_name(emotion_raw)
                
                # Check if it's a valid PANAS emotion
                if emotion_normalized not in valid_emotions or emotion_normalized in processed_emotions:
                    continue
                
                # Extract score (1-5)
                try:
                    # Try to find digits in score_str
                    score_matches = [int(s) for s in score_str.split() if s.isdigit() and 1 <= int(s) <= 5]
                    score = score_matches[0] if score_matches else 3
                except:
                    score = 3
                
                # Add to results
                emotions.append({
                    "feeling": emotion_normalized.title(),  # Capitalize first letter
                    "explanation": explanation.strip(),
                    "score": score
                })
                processed_emotions.add(emotion_normalized)
    
    return emotions

def compute_panas_delta(before_emotions, after_emotions, persona_name):
    """
    Compute difference between pre and post PANAS scores.
    FIXED VERSION with better matching logic.
    
    Args:
        before_emotions: List of before emotions with scores
        after_emotions: List of after emotions with scores  
        persona_name: Name for logging
    
    Returns:
        list: Delta scores with differences
    """
    delta = []
    
    print(f"\n🔍 Computing PANAS delta for {persona_name}")
    print(f"   Before count: {len(before_emotions)}")
    print(f"   After count: {len(after_emotions)}")
    
    if not before_emotions or not after_emotions:
        print(f"   ⚠️  Missing data: before={len(before_emotions)}, after={len(after_emotions)}")
        return delta
    
    # Create normalized lookup for after emotions
    after_dict = {}
    for emotion in after_emotions:
        normalized = normalize_emotion_name(emotion.get("feeling", ""))
        after_dict[normalized] = emotion
    
    print(f"   After emotions index: {list(after_dict.keys())[:5]}...")  # Show first 5
    
    # Match baseline with after
    matched_count = 0
    for before_emotion in before_emotions:
        before_normalized = normalize_emotion_name(before_emotion.get("feeling", ""))
        
        # Lookup in after dict
        if before_normalized in after_dict:
            after_emotion = after_dict[before_normalized]
            
            try:
                before_score = int(before_emotion.get("score", 3))
                after_score = int(after_emotion.get("score", 3))
                difference = after_score - before_score
                
                delta.append({
                    "feeling": before_emotion.get("feeling", before_normalized.title()),
                    "before_score": before_score,
                    "after_score": after_score,
                    "difference": difference
                })
                matched_count += 1
                
                if difference != 0:  # Only log non-zero changes
                    print(f"   ✓ {before_normalized}: {before_score} → {after_score} (Δ{difference:+d})")
            
            except (ValueError, TypeError) as e:
                print(f"   ✗ Score error for {before_normalized}: {e}")
        else:
            print(f"   ✗ No match for {before_normalized}")
    
    print(f"   ✓ Matched {matched_count}/{len(before_emotions)} emotions")
    return delta

def summarize_panas_changes(panas_delta, patient_label, positive_emotions_lower, negative_emotions_lower):
    """
    Summarize overall PANAS changes (positive affect, negative affect).
    
    Args:
        panas_delta: Delta scores
        patient_label: Patient identifier
        positive_emotions_lower: List of positive emotion names (lowercase)
        negative_emotions_lower: List of negative emotion names (lowercase)
    
    Returns:
        dict: Summary statistics
    """
    
    positive_changes = [d for d in panas_delta if d["feeling"].lower() in positive_emotions_lower]
    negative_changes = [d for d in panas_delta if d["feeling"].lower() in negative_emotions_lower]
    
    pos_total = sum([d["difference"] for d in positive_changes if isinstance(d["difference"], int)])
    neg_total = sum([d["difference"] for d in negative_changes if isinstance(d["difference"], int)])
    
    num_improved_positive = len([d for d in positive_changes if d["difference"] > 0])
    num_improved_negative = len([d for d in negative_changes if d["difference"] < 0])
    
    return {
        "patient": patient_label,
        "positive_emotion_change": pos_total,
        "negative_emotion_change": neg_total,
        "num_improved_positive": num_improved_positive,
        "num_improved_negative": num_improved_negative,
        "net_change": pos_total + neg_total
    }
