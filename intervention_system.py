# intervention_system.py
# LLM-based intervention scoring, generation, and decision logic

from openai import OpenAI
import json
import os
from config import (
    SCORING_MODEL, INTERVENTION_MODEL, INTERVENTION_THRESHOLD,
    INTERVENTION_SCORING_MAX_TOKENS, INTERVENTION_GENERATION_MAX_TOKENS,
    OPENROUTER_GPT_KEY, OPENROUTER_BASE_URL, PROMPTS_DIR
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



def calculate_intervention_score(context_window, current_speaker, current_message, participants):
    """
    Calculate intervention need score across 4 clinical dimensions.
    
    Dimensions:
    1. Flow Disruption (0-100): How jarring would intervention be?
    2. Therapeutic Need (0-100): Is there genuine distress/breakdown?
    3. Timing Appropriateness (0-100): Is this a natural pause point?
    4. Impact Potential (0-100): Will intervention help (USR framework)?
    
    Args:
        context_window: Recent conversation history
        current_speaker: Who just spoke
        current_message: What they said
        participants: Session participant data
    
    Returns:
        dict: Scoring details with average and recommendation
    """
    
    # Load prompt dynamically to support live-reloading
    SCORING_PROMPT_TEMPLATE = load_prompt("intervention_scoring_prompt.txt")
    
    # Format the scoring prompt from template
    context_text = context_window[-2000:] if context_window else "Session start"
    scoring_prompt = SCORING_PROMPT_TEMPLATE.format(
        context_window=context_text,
        current_speaker=current_speaker,
        current_message=current_message,
        intervention_threshold=INTERVENTION_THRESHOLD
    )
    
    try:
        response = client.chat.completions.create(
            model=SCORING_MODEL,
            messages=[{"role": "user", "content": scoring_prompt}],
            temperature=0.4,  # Consistent scoring
            max_tokens=INTERVENTION_SCORING_MAX_TOKENS
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Try direct JSON parsing first
            score_dict = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: extract JSON from text
            import re
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                score_dict = json.loads(json_match.group())
            else:
                # Return default if parsing fails
                return {
                    "flow_disruption": 50,
                    "therapeutic_need": 50,
                    "timing": 50,
                    "impact": 50,
                    "average": 50,
                    "recommendation": "CONTINUE",
                    "reasoning": "Unable to parse scoring response"
                }
        
        return score_dict
    
    except Exception as e:
        print(f"❌ Error calculating intervention score: {e}")
        return {
            "flow_disruption": 50,
            "therapeutic_need": 50,
            "timing": 50,
            "impact": 50,
            "average": 50,
            "recommendation": "CONTINUE",
            "reasoning": f"Error: {str(e)}"
        }

def should_intervene(intervention_score):
    """
    Check if score meets intervention threshold.
    
    Args:
        intervention_score: Score dict from calculate_intervention_score
    
    Returns:
        bool: True if average >= INTERVENTION_THRESHOLD
    """
    average = intervention_score.get('average', 0)
    return average >= INTERVENTION_THRESHOLD

def generate_intervention(triggers_detected, context_window, participants, intervention_score, current_speaker):
    """
    Generate AI facilitation response based on trigger type.
    
    Args:
        triggers_detected: List of detected triggers
        context_window: Conversation history
        participants: Session data
        intervention_score: Scoring details
    
    Returns:
        str: AI facilitator response
    """
    if not triggers_detected:
        return None
    
    primary_trigger = triggers_detected[0]
    trigger_type = primary_trigger.get("type", "Unknown")
    trigger_subtype = primary_trigger.get("subtype", "Unknown")
    
    # Build trigger-specific template
    if trigger_type == "Direct Intervention Request":
        template = """Acknowledge their request for help. Provide structured guidance. 
Facilitate dialogue between partners. Validate their vulnerability in asking for help."""
    
    elif trigger_type == "Emotional Escalation":
        template = """De-escalate emotional intensity. Validate emotions. 
Slow down the pace. Help them regain perspective without dismissing feelings."""
    
    elif trigger_type == "Extended Silence":
        template = """Gently check in with the silent party. Offer space or invite them to share.
Make sure they feel safe and heard. Don't force, but create safety for expression."""
    
    elif trigger_type == "Message Dominance":
        template = """Acknowledge the speaking partner's passion. Invite the other partner to respond.
Create balanced dialogue opportunity. Ensure both voices matter equally."""
    
    elif trigger_type == "Information Overload":
        template = """Help simplify the complex message. Break it into digestible pieces.
Invite the other partner to respond to key points one at a time."""
    
    else:
        template = """Provide appropriate therapeutic guidance based on the situation."""
    
    # Extract participant names (use first names for natural dialogue)
    patient_a_full = participants.get('patient_A', {}).get('name', 'Patient A')
    patient_b_full = participants.get('patient_B', {}).get('name', 'Patient B')
    patient_a_name = patient_a_full.split()[0] if patient_a_full else 'Patient A'
    patient_b_name = patient_b_full.split()[0] if patient_b_full else 'Patient B'
    
    # Determine target based on current_speaker
    speaker_key = 'patient_A' if current_speaker == 'Patient A' else 'patient_B'
    target_full = participants.get(speaker_key, {}).get('name', current_speaker)
    target_first_name = target_full.split()[0] if target_full else current_speaker
    
    # Load prompt dynamically to support live-reloading
    GENERATION_PROMPT_TEMPLATE = load_prompt("intervention_generation_prompt.txt")
    
    # Generate intervention using template
    context_text = context_window[-2000:] if context_window else "Session start"
    intervention_prompt = GENERATION_PROMPT_TEMPLATE.format(
        context_window=context_text,
        trigger_subtype=trigger_subtype,
        template=template,
        patient_a_name=patient_a_name,
        patient_b_name=patient_b_name,
        target_first_name=target_first_name
    )
    
    try:
        response = client.chat.completions.create(
            model=INTERVENTION_MODEL,
            messages=[{"role": "user", "content": intervention_prompt}],
            temperature=0.7,
            max_tokens=INTERVENTION_GENERATION_MAX_TOKENS
        )
        
        intervention = response.choices[0].message.content.strip()
        # Safety net: strip em-dashes from output (banned formatting)
        intervention = intervention.replace('\u2014', ',').replace('\u2013', ',')
        return intervention
    
    except Exception as e:
        print(f"❌ Error generating intervention: {e}")
        return None
