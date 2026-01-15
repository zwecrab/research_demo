# session_setup.py
# Session initialization, persona selection, trigger filtering

import random
from config import PANAS_POSITIVE, PANAS_NEGATIVE

def filter_personas_by_trigger(personas, selected_trigger):
    """
    Filter personas by their assigned trigger type.
    
    Args:
        personas: dict of all personas
        selected_trigger: selected trigger type or "All Triggers"
    
    Returns:
        dict of filtered personas
    """
    if selected_trigger == "All Triggers":
        return personas
    
    filtered = {}
    for name, persona in personas.items():
        if persona.get("trigger_type") == selected_trigger:
            filtered[name] = persona
    
    return filtered

def setup_session_parameters(topic_data, all_personas, selected_trigger, conversation_structure):
    """
    Setup session: select participants, objectives, etc.
    
    Args:
        topic_data: Selected therapy domain data
        all_personas: All available personas
        selected_trigger: Selected trigger type
        conversation_structure: Conversation structure type
    
    Returns:
        tuple: (header, details, participants_dict, discussion_notes)
    """
    # Extract topic data
    header = topic_data.get("header", "Unknown Topic")
    details = {
        "long_term_goals": topic_data.get("long_term_goals", []),
        "short_term_objectives": topic_data.get("short_term_objectives", [])
    }
    
    # Filter personas by trigger (if LLM+Triggers)
    if conversation_structure == "LLM with Triggers":
        available_personas = filter_personas_by_trigger(all_personas, selected_trigger)
    else:
        available_personas = all_personas
    
    # Select therapist (always Dr. Anya Sharma)
    therapist = {
        "name": "Dr. Anya Sharma",
        "role": "Therapist",
        "persona_seeds": {
            "professional_style": "Empathetic, structured",
            "approach": "CBT-informed with attachment focus"
        }
    }
    
    # Select two random patients from filtered personas
    if len(available_personas) < 2:
        raise ValueError(f"Not enough personas ({len(available_personas)}) for trigger type '{selected_trigger}'")
    
    patient_names = random.sample(list(available_personas.keys()), 2)
    patient_a_name = patient_names[0]
    patient_b_name = patient_names[1]
    
    patient_a = {
        "name": patient_a_name,
        "role": "Patient A",
        **available_personas[patient_a_name]
    }
    
    patient_b = {
        "name": patient_b_name,
        "role": "Patient B",
        **available_personas[patient_b_name]
    }
    
    participants = {
        "therapist": therapist,
        "patient_A": patient_a,
        "patient_B": patient_b,
        "selected_trigger_type": selected_trigger,
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
