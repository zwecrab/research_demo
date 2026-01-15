# intervention_system.py
# LLM-based intervention scoring, generation, and decision logic

from openai import OpenAI
import json
from config import (
    SCORING_MODEL, INTERVENTION_MODEL, INTERVENTION_THRESHOLD,
    INTERVENTION_SCORING_MAX_TOKENS, INTERVENTION_GENERATION_MAX_TOKENS, OPENAI_API_KEY
)

client = OpenAI(api_key=OPENAI_API_KEY)

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
    
    scoring_prompt = f"""You are an expert in therapeutic dialogue analysis, trained on ACL research 
including FED (Fine-grained Evaluation of Dialogue) and USR (User Satisfaction) frameworks.

Evaluate whether an AI facilitation intervention is needed in this couples therapy conversation.

CONVERSATION CONTEXT (last 1000 chars):
{context_window[-1000:] if context_window else "Session start"}

CURRENT SPEAKER: {current_speaker}
CURRENT MESSAGE: "{current_message}"

Rate each dimension (0-100 scale):
1. FLOW_DISRUPTION: How jarring/natural would intervention feel? (0=natural, 100=very interrupting)
2. THERAPEUTIC_NEED: Is there genuine distress/communication breakdown? (0=no need, 100=critical)
3. TIMING_APPROPRIATENESS: Is this a natural pause point for facilitation? (0=bad timing, 100=perfect)
4. IMPACT_POTENTIAL: Will intervention likely improve outcome? (0=won't help, 100=transformative)

Return ONLY valid JSON (no markdown, no extra text):
{{
    "flow_disruption": X,
    "therapeutic_need": Y,
    "timing": Z,
    "impact": W,
    "average": (X+Y+Z+W)/4,
    "recommendation": "INTERVENE" or "CONTINUE",
    "reasoning": "brief 1-sentence explanation"
}}

CRITICAL: Only recommend "INTERVENE" if average >= 70.
Most healthy therapeutic conversations score below 70."""
    
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

def generate_intervention(triggers_detected, context_window, participants, intervention_score):
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
    
    # Generate intervention
    intervention_prompt = f"""You are Dr. Anya Sharma, an experienced couples therapist.

RECENT CONVERSATION:
{context_window[-500:] if context_window else "Session start"}

SITUATION: {trigger_subtype}
GUIDANCE TEMPLATE: {template}

Generate a brief, natural AI facilitator intervention (2-3 sentences max).
Be warm, professional, and focus on moving the dialogue forward.
Speak directly to the couple - acknowledge what you're noticing and offer a gentle redirect or validation."""
    
    try:
        response = client.chat.completions.create(
            model=INTERVENTION_MODEL,
            messages=[{"role": "user", "content": intervention_prompt}],
            temperature=0.7,
            max_tokens=INTERVENTION_GENERATION_MAX_TOKENS
        )
        
        intervention = response.choices[0].message.content.strip()
        return intervention
    
    except Exception as e:
        print(f"❌ Error generating intervention: {e}")
        return None
