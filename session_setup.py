# session_setup.py
# Session initialization, persona selection, trigger filtering

import random
from config import PANAS_POSITIVE, PANAS_NEGATIVE


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
        "models_used": {
            "conversation": "gpt-4o",
            "panas": "gpt-4",
            "intervention": "gpt-4o",
            "scoring": "gpt-4"
        }
    }
    
    return output_json

def log_session_start(header, conversation_structure, first_speaker):
    """Log session startup information."""
    print(f"\n🎬 Starting Session")
    print(f"   Topic: {header}")
    print(f"   Structure: {conversation_structure}")
    print(f"   First Speaker (after Therapist): {first_speaker}")
