# session_setup.py
# Session initialization, persona selection, trigger filtering

import random
from config import (
    PANAS_POSITIVE, PANAS_NEGATIVE, DEFAULT_V2_THERAPY_TOPIC,
    CONVERSATION_MODEL, PANAS_MODEL, SCORING_MODEL, INTERVENTION_MODEL,
    DEFAULT_THERAPIST_MODEL,
)


def _current_models_used():
    """Snapshot of which OpenRouter-routed model fills each pipeline role."""
    return {
        "conversation": CONVERSATION_MODEL,
        "therapist_default": DEFAULT_THERAPIST_MODEL,
        "panas": PANAS_MODEL,
        "scoring": SCORING_MODEL,
        "intervention": INTERVENTION_MODEL,
    }


def setup_session_parameters(topic_data, all_personas, conversation_structure,
                             patient_a_name=None, patient_b_name=None):
    """
    Setup session: select participants, objectives, etc.
    
    Args:
        topic_data: Selected therapy domain data
        all_personas: All available personas
        conversation_structure: Conversation structure type
        patient_a_name: Specific name for Patient A (optional)
        patient_b_name: Specific name for Patient B (optional)
    
    Returns:
        tuple: (header, details, participants_dict, discussion_notes)
    """
    # Extract topic data
    header = topic_data.get("header", "Unknown Topic")
    details = {
        "long_term_goals": topic_data.get("long_term_goals", []),
        "short_term_objectives": [s.get("short_term_objective") for s in topic_data.get("sessions", []) if s.get("short_term_objective")]
    }
    
    available_personas = all_personas
    
    # Select therapist (always Dr. Anya Forger)
    therapist = {
        "name": "Dr. Anya Forger",
        "role": "Therapist",
        "persona_seeds": {
            "professional_style": "Empathetic, structured",
            "approach": "CBT-informed with attachment focus"
        }
    }
    
    # Select two patients from filtered personas
    if len(available_personas) < 2 and not (patient_a_name and patient_b_name):
        raise ValueError(f"Not enough personas ({len(available_personas)}) for trigger type '{selected_trigger}'")
    
    # Validation / Selection
    if patient_a_name:
        if patient_a_name not in all_personas:
             raise ValueError(f"Patient A '{patient_a_name}' not found in personas.")
        # If specifically requested, use them even if filtered out
    else:
        patient_a_name = random.choice(list(available_personas.keys()))
        
    if patient_b_name:
        if patient_b_name not in all_personas:
             raise ValueError(f"Patient B '{patient_b_name}' not found in personas.")
    else:
        # Pick random distinct from A from AVAILABLE list
        remaining = [p for p in available_personas.keys() if p != patient_a_name]
        if not remaining:
             raise ValueError("Not enough distinct personas available")
        patient_b_name = random.choice(remaining)

    # Get persona details
    
    patient_a = {
        "name": patient_a_name,
        "role": "Patient A",
        **all_personas[patient_a_name]
    }
    
    patient_b = {
        "name": patient_b_name,
        "role": "Patient B",
        **all_personas[patient_b_name]
    }
    
    participants = {
        "therapist": therapist,
        "patient_A": patient_a,
        "patient_B": patient_b,
        "conversation_structure": conversation_structure
    }
    
    # Discussion notes from topic
    discussion_notes = {
        "topic": header,
        "goals": details["long_term_goals"],
        "objectives": details["short_term_objectives"]
    }
    
    print(f"\n✅ Session Setup Complete")
    print(f"  Therapist: {therapist['name']}")
    print(f"  Patient A: {patient_a['name']}")
    print(f"  Patient B: {patient_b['name']}")
    print(f"  Topic: {header}")
    
    return header, details, participants, discussion_notes

def initialize_session_state(header, details, participants, discussion_notes, 
                           conversation_structure, first_speaker):
    """
    Initialize the output JSON structure.
    
    Args:
        header: Topic header
        details: Topic details (goals, objectives)
        participants: Participant info dict
        discussion_notes: Session notes
        conversation_structure: Structure type
        first_speaker: Who speaks first (NEW)
    
    Returns:
        dict: Empty but structured output JSON
    """
    output_json = {
        "session_topic_header": header,
        "session_details": details,
        "participant_details": participants,
        "conversation_structure": conversation_structure,
        "first_speaker_selection": first_speaker,  # NEW FIELD
        "session_transcript": [],
        "trigger_log": [],
        "intervention_scores": [],
        "intervention_count": 0,
        "scored_interventions_rejected": 0,
        "models_used": _current_models_used(),
    }
    
    return output_json

def setup_v2_session(persona_a, persona_b, conversation_structure,
                     topic_override=None):
    """Setup session using v2 personas with standardized therapy topic.

    Uses DEFAULT_V2_THERAPY_TOPIC for experiment standardization. Each persona's
    topic_context field provides couple-specific context that feeds into session
    goals, while the header stays consistent across all couples.

    Args:
        persona_a: v2 persona dict for Patient A (already has bid-style applied)
        persona_b: v2 persona dict for Patient B (already has bid-style applied)
        conversation_structure: Conversation structure type
        topic_override: Optional topic string to replace the default

    Returns:
        tuple: (header, details, participants, discussion_notes)
    """
    header = topic_override if topic_override else DEFAULT_V2_THERAPY_TOPIC

    # Build goals from couple-specific topic_context if available
    context_a = persona_a.get("topic_context", "")
    context_b = persona_b.get("topic_context", "")
    long_term_goals = [
        f"Address {header.lower()} between {persona_a['name']} and {persona_b['name']}"
    ]
    if context_a:
        long_term_goals.append(f"{persona_a['name']}: {context_a}")
    if context_b:
        long_term_goals.append(f"{persona_b['name']}: {context_b}")

    details = {
        "long_term_goals": long_term_goals,
        "short_term_objectives": [
            f"Explore each partner's perspective on their recurring conflict patterns",
            "Identify underlying emotional needs driving the conflict cycle",
            "Practice constructive communication techniques"
        ]
    }

    therapist = {
        "name": "Dr. Anya Forger",
        "role": "Therapist",
        "persona_seeds": {
            "professional_style": "Empathetic, structured",
            "approach": "CBT-informed with attachment focus"
        }
    }

    patient_a = {"name": persona_a["name"], "role": "Patient A", **persona_a}
    patient_b = {"name": persona_b["name"], "role": "Patient B", **persona_b}

    participants = {
        "therapist": therapist,
        "patient_A": patient_a,
        "patient_B": patient_b,
        "conversation_structure": conversation_structure
    }

    discussion_notes = {
        "topic": header,
        "goals": details["long_term_goals"],
        "objectives": details["short_term_objectives"]
    }

    print(f"\n  Session Setup Complete")
    print(f"  Therapist: {therapist['name']}")
    print(f"  Patient A: {patient_a['name']} (bid: {persona_a.get('bid_style', 'neutral')})")
    print(f"  Patient B: {patient_b['name']} (bid: {persona_b.get('bid_style', 'neutral')})")
    print(f"  Topic: {header}")

    return header, details, participants, discussion_notes


def log_session_start(header, conversation_structure, first_speaker):
    """Log session startup information."""
    print(f"\n🎬 Starting Session")
    print(f"   Topic: {header}")
    print(f"   Structure: {conversation_structure}")
    print(f"   First Speaker (after Therapist): {first_speaker}")
