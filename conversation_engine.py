# conversation_engine.py
# Dialogue generation, speaker selection logic, OpenAI API calls

from openai import OpenAI
import random
from config import (
    CONVERSATION_MODEL, MAX_TOKENS_PER_TURN, OPENAI_API_KEY
)

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_agent_turn(blueprint_prompt, persona, session_topic, discussion_notes,
                       conversation_history, last_responses, temperature):
    """
    Generate dialogue for an agent using OpenAI API.
    
    Args:
        blueprint_prompt: System prompt for agent
        persona: Persona data (name, traits, etc.)
        session_topic: Topic header
        discussion_notes: Session objectives
        conversation_history: Full dialogue history as string
        last_responses: Dict of recent responses from other agents
        temperature: Model temperature (0.0-1.0)
    
    Returns:
        str: Generated dialogue turn (~150 words)
    """
    # Build context message
    context = f"""
CONVERSATION CONTEXT:
{conversation_history[-2000:] if conversation_history else "Session just started."}

LAST RESPONSES:
{', '.join([f'{k}: {v[:50]}...' for k, v in last_responses.items()]) if last_responses else "None yet"}
"""
    
    # Build user message
    user_message = f"""
{context}

Session Topic: {session_topic}
Objectives: {', '.join(discussion_notes.get('objectives', [])) if isinstance(discussion_notes, dict) else str(discussion_notes)}

Generate a natural, concise response (about 100-150 words) from this person's perspective.
Be authentic to their character. Build on what's been said. Keep it conversational.
"""
    
    try:
        response = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=[
                {"role": "system", "content": blueprint_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS_PER_TURN
        )
        
        dialogue = response.choices[0].message.content.strip()
        return dialogue
    
    except Exception as e:
        print(f"❌ Error generating dialogue: {e}")
        return f"[Unable to generate response: {e}]"

def sequential_speaker_selection(turn_number):
    """
    Sequential speaker selection: Therapist → Patient A → Patient B cycle.
    
    Args:
        turn_number: Current turn number (1-indexed)
    
    Returns:
        str: Next speaker ("Therapist", "Patient A", or "Patient B")
    """
    speakers = ["Therapist", "Patient A", "Patient B"]
    return speakers[(turn_number - 1) % 3]

def intelligent_speaker_selection(conversation_history, current_speaker, intervention_occurred=False):
    """
    Intelligent speaker selection based on therapeutic balance.
    
    Logic:
    - After AI intervention, prefer patients (balance therapy)
    - Never select same speaker twice
    - Track recent participation (last 6 turns)
    - Ensure therapist isn't overused
    - Balance between Patient A and Patient B
    
    Args:
        conversation_history: List of dialogue entries
        current_speaker: Who just spoke
        intervention_occurred: Whether AI just intervened
    
    Returns:
        str: Next speaker to maximize therapeutic balance
    """
    # Count recent participation (last 6 turns)
    speaker_counts = {"Therapist": 0, "Patient A": 0, "Patient B": 0, "AI_Facilitator": 0}
    recent_history = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
    
    for entry in recent_history:
        if "Therapist:" in entry:
            speaker_counts["Therapist"] += 1
        elif "Patient A" in entry:
            speaker_counts["Patient A"] += 1
        elif "Patient B" in entry:
            speaker_counts["Patient B"] += 1
        elif "AI_Facilitator:" in entry:
            speaker_counts["AI_Facilitator"] += 1
    
    # Possible next speakers (never same speaker twice)
    possible_speakers = [s for s in ["Therapist", "Patient A", "Patient B"] if s != current_speaker]
    
    # If AI just intervened, strongly prefer patients
    if intervention_occurred:
        patients = [s for s in possible_speakers if "Patient" in s]
        if patients:
            # Choose least-spoken patient
            if speaker_counts["Patient A"] <= speaker_counts["Patient B"]:
                return "Patient A"
            else:
                return "Patient B"
    
    # Normal selection logic
    # If therapist underutilized (< 2 turns in recent history), bring them in
    if speaker_counts["Therapist"] < 2 and len(recent_history) > 4:
        if "Therapist" in possible_speakers:
            return "Therapist"
    
    # Balance patients
    patient_options = [s for s in possible_speakers if "Patient" in s]
    if patient_options:
        if speaker_counts["Patient A"] <= speaker_counts["Patient B"]:
            return "Patient A" if "Patient A" in patient_options else "Patient B"
        else:
            return "Patient B" if "Patient B" in patient_options else "Patient A"
    
    # Fallback
    return random.choice(possible_speakers)
