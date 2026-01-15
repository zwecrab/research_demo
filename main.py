# main.py
# Main orchestrator - calls functions from all modules to run the simulation

import random
import time
from datetime import datetime

# Import all modules
from config import SESSION_MIN_TURNS, SESSION_MAX_TURNS
from data_loader import load_all_assets
from user_interface import (
    select_session_topic, select_temperature, select_conversation_structure,
    select_trigger_type, select_first_speaker, display_session_configuration
)
from session_setup import (
    setup_session_parameters, initialize_session_state, log_session_start
)
from conversation_engine import (
    generate_agent_turn, sequential_speaker_selection, intelligent_speaker_selection
)
from trigger_system import detect_triggers
from intervention_system import (
    calculate_intervention_score, generate_intervention, should_intervene
)
from panas_analyzer import (
    get_after_panas_scores, parse_panas_output, compute_panas_delta,
    summarize_panas_changes
)
from output_manager import (
    build_patient_transcript, save_session_json, display_session_summary,
    display_session_details, export_transcript_text, generate_experiment_report
)

def run_session_loop(output_json, participants, discussion_notes, conversation_structure,
                    first_speaker, session_temperature, prompts, baseline_panas):
    """
    Main simulation loop - runs conversation turns until completion.
    
    Args:
        output_json: Session data structure
        participants: Participant details
        discussion_notes: Session objectives
        conversation_structure: Which structure to use
        first_speaker: Who speaks first (after therapist)
        session_temperature: Model temperature
        prompts: System prompts for agents
        baseline_panas: Pre-computed baseline PANAS scores
    
    Returns:
        Updated output_json with conversation data
    """
    conversation_history = []
    max_turns = random.randint(SESSION_MIN_TURNS, SESSION_MAX_TURNS)
    current_turn_number = 1
    current_speaker = "Therapist"  # Always start with therapist
    
    session_topic_header = output_json["session_topic_header"]
    
    print(f"\n🎬 Starting simulation: {session_topic_header}")
    print(f"   Structure: {conversation_structure}")
    print(f"   Temperature: {session_temperature}")
    print(f"   Max Turns: {max_turns}")
    print(f"   First Speaker (after Therapist): {first_speaker}\n")
    
    # ========================================================================
    # MAIN SIMULATION LOOP
    # ========================================================================
    
    while current_turn_number <= max_turns:
        print(f"\n--- Turn {current_turn_number} of {max_turns} ---")
        
        full_history_str = "\n".join(conversation_history)
        
        # Build last_responses dict
        last_responses = {}
        for entry in reversed(conversation_history):
            if "Therapist:" in entry and 'therapist' not in last_responses:
                last_responses['therapist'] = entry.split(":", 1)[1].strip()
            if "Patient A" in entry and 'patient_a' not in last_responses:
                last_responses['patient_a'] = entry.split(":", 1)[1].strip()
            if "Patient B" in entry and 'patient_b' not in last_responses:
                last_responses['patient_b'] = entry.split(":", 1)[1].strip()
        
        # ====================================================================
        # STEP 1: GENERATE DIALOGUE
        # ====================================================================
        
        dialogue = ""
        speaker_name_for_history = ""
        
        if current_speaker == "Therapist":
            print("🤔 Therapist is thinking...")
            dialogue = generate_agent_turn(
                prompts['therapist'],
                participants['therapist'].get('persona_seeds', {}),
                session_topic_header,
                discussion_notes,
                full_history_str,
                last_responses,
                session_temperature
            )
            speaker_name_for_history = "Therapist"
        
        elif current_speaker == "Patient A":
            print(f"🤔 Patient A ({participants['patient_A']['name']}) is thinking...")
            dialogue = generate_agent_turn(
                prompts['patient_a'],
                participants['patient_A'],
                session_topic_header,
                discussion_notes,
                full_history_str,
                last_responses,
                session_temperature
            )
            speaker_name_for_history = f"Patient A ({participants['patient_A']['name']})"
        
        elif current_speaker == "Patient B":
            print(f"🤔 Patient B ({participants['patient_B']['name']}) is thinking...")
            dialogue = generate_agent_turn(
                prompts['patient_b'],
                participants['patient_B'],
                session_topic_header,
                discussion_notes,
                full_history_str,
                last_responses,
                session_temperature
            )
            speaker_name_for_history = f"Patient B ({participants['patient_B']['name']})"
        
        # ====================================================================
        # STEP 1.5: LOG TURN
        # ====================================================================
        
        output_json["session_transcript"].append({
            "turn": current_turn_number,
            "speaker": current_speaker,
            "dialogue": dialogue
        })
        
        full_log_entry = f"{speaker_name_for_history}: {dialogue}"
        conversation_history.append(full_log_entry)
        full_history_str = "\n".join(conversation_history)
        
        print(f"{speaker_name_for_history}: {dialogue[:80]}..." if len(dialogue) > 80 else f"{speaker_name_for_history}: {dialogue}")

        # ====================================================================
        # STEP 2: TRIGGER DETECTION (if applicable)
        # ====================================================================
        
        intervention_occurred = False
        next_speaker_override = None
        
        if conversation_structure == "LLM with Triggers" and current_speaker != "Therapist":
            triggers_detected = detect_triggers(
                conversation_history,
                current_speaker,
                dialogue,
                participants['selected_trigger_type']
            )
            
            if triggers_detected:
                print(f"🔍 Triggers detected: {[t['subtype'] for t in triggers_detected]}")
                
                # ============================================================
                # STEP 3: INTERVENTION SCORING
                # ============================================================
                
                intervention_score = calculate_intervention_score(
                    full_history_str,
                    current_speaker,
                    dialogue,
                    participants
                )
                
                output_json["intervention_scores"].append({
                    "turn": current_turn_number,
                    "triggers": triggers_detected,
                    "score": intervention_score,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"📊 Score: {intervention_score.get('average', 0):.1f}/100 - {intervention_score.get('recommendation', '?')}")
                print(f"💭 Reasoning: {intervention_score.get('reasoning', 'N/A')}")
                
                # Update history string for intervention context (re-generating in case it changed, though it shouldn't have)
                full_history_str = "\n".join(conversation_history)

                # ============================================================
                # STEP 4: CONDITIONAL INTERVENTION
                # ============================================================
                
                if should_intervene(intervention_score):
                    print("✅ INTERVENING...")
                    
                    intervention = generate_intervention(
                        triggers_detected,
                        full_history_str,
                        participants,
                        intervention_score
                    )
                    
                    if intervention:
                        # Add intervention turn to transcript
                        current_turn_number += 1
                        
                        output_json["session_transcript"].append({
                            "turn": current_turn_number,
                            "speaker": "AI_Facilitator",
                            "dialogue": intervention,
                            "intervention_for_triggers": triggers_detected,
                            "intervention_score": intervention_score,
                            "intervention_type": "llm_scored"
                        })
                        
                        facilitator_entry = f"AI Facilitator: {intervention}"
                        conversation_history.append(facilitator_entry)
                        
                        print(f"🤖 AI Facilitator: {intervention}")
                        
                        # Log the intervention
                        output_json["trigger_log"].append({
                            "turn": current_turn_number - 1, # Referencing the trigger turn
                            "triggers": triggers_detected,
                            "intervention": intervention,
                            "score": intervention_score,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        output_json["intervention_count"] += 1
                        intervention_occurred = True
                else:
                    print("❌ Score below threshold - No intervention")
                    output_json["scored_interventions_rejected"] += 1
        
        # ====================================================================
        # STEP 6: FIRST SPEAKER OVERRIDE (Turn 1 → Turn 2 transition)
        # ====================================================================
        
        if current_turn_number == 1 and first_speaker != "Random":
            next_speaker_override = first_speaker
            print(f"🎯 First speaker override: {first_speaker}")
        else:
            next_speaker_override = None
        
        # ====================================================================
        # STEP 7: SPEAKER SELECTION FOR NEXT TURN
        # ====================================================================
        
        if next_speaker_override:
            next_speaker = next_speaker_override
        elif conversation_structure == "Sequential":
            next_speaker = sequential_speaker_selection(current_turn_number + 1)
        else:  # LLM Only or LLM with Triggers
            next_speaker = intelligent_speaker_selection(
                conversation_history,
                current_speaker,
                intervention_occurred
            )
        
        current_speaker = next_speaker
        current_turn_number += 1
        
        time.sleep(0.5)  # Small delay for realistic pacing
    
    # End of simulation loop
    print(f"\n✅ Simulation complete: {current_turn_number - 1} turns")
    
    return output_json, conversation_history

def run_panas_analysis(output_json, baseline_panas, conversation_history):
    """
    Perform post-session PANAS analysis.
    
    Args:
        output_json: Session data
        baseline_panas: Pre-computed baseline PANAS
        conversation_history: Full conversation transcript
    
    Returns:
        PANAS summaries and updated output_json
    """
    print("\n" + "="*70)
    print("POST-SESSION ANALYSIS: PANAS EMOTIONAL ASSESSMENT")
    print("="*70)
    
    participants = output_json["participant_details"]
    panas_summaries = []
    
    # Analyze Patient A
    print("\n📊 Analyzing Patient A...")
    patient_a_name = participants["patient_A"]["name"]
    patient_a_transcript = build_patient_transcript(output_json["session_transcript"], "Patient A")
    
    print(f"   Getting post-session PANAS for {patient_a_name}...")
    after_panas_text = get_after_panas_scores(participants["patient_A"], patient_a_transcript)
    after_panas = parse_panas_output(after_panas_text)
    
    baseline_panas_a = baseline_panas.get(patient_a_name, [])
    panas_delta_a = compute_panas_delta(baseline_panas_a, after_panas, patient_a_name)
    
    panas_summary_a = summarize_panas_changes(
        panas_delta_a,
        patient_a_name,
        [e.lower() for e in ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"]],
        [e.lower() for e in ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"]]
    )
    
    output_json[f"Patient_A_AFTER_PANAS"] = after_panas
    output_json[f"Patient_A_PANAS_DELTA"] = panas_delta_a
    panas_summaries.append(panas_summary_a)
    
    # Analyze Patient B
    print("\n📊 Analyzing Patient B...")
    patient_b_name = participants["patient_B"]["name"]
    patient_b_transcript = build_patient_transcript(output_json["session_transcript"], "Patient B")
    
    print(f"   Getting post-session PANAS for {patient_b_name}...")
    after_panas_text = get_after_panas_scores(participants["patient_B"], patient_b_transcript)
    after_panas = parse_panas_output(after_panas_text)
    
    baseline_panas_b = baseline_panas.get(patient_b_name, [])
    panas_delta_b = compute_panas_delta(baseline_panas_b, after_panas, patient_b_name)
    
    panas_summary_b = summarize_panas_changes(
        panas_delta_b,
        patient_b_name,
        [e.lower() for e in ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"]],
        [e.lower() for e in ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"]]
    )
    
    output_json[f"Patient_B_AFTER_PANAS"] = after_panas
    output_json[f"Patient_B_PANAS_DELTA"] = panas_delta_b
    panas_summaries.append(panas_summary_b)
    
    return output_json, panas_summaries

def main():
    """Main entry point - orchestrates the complete simulation."""
    
    print("\n" + "="*70)
    print("🤖 AI COUPLES THERAPY SIMULATION WITH ADAPTIVE INTERVENTION")
    print("="*70)
    
    # ========================================================================
    # STAGE 1: LOAD ALL ASSETS
    # ========================================================================
    
    assets = load_all_assets()
    
    # ========================================================================
    # STAGE 2: USER SELECTIONS
    # ========================================================================
    
    print("\n" + "="*70)
    print("CONFIGURATION STAGE")
    print("="*70)
    
    session_topic_data = select_session_topic(assets["therapy_plans"])
    session_temperature = select_temperature()
    conversation_structure = select_conversation_structure()
    
    # Trigger type selection (only for LLM with Triggers)
    if conversation_structure == "LLM with Triggers":
        selected_trigger = select_trigger_type()
    else:
        selected_trigger = "No Trigger"
    
    # First speaker selection (NEW FEATURE)
    first_speaker = select_first_speaker()
    
    # ------------------------------------------------------------------------
    # Manual Persona Selection
    # ------------------------------------------------------------------------
    from session_setup import filter_personas_by_trigger
    from user_interface import select_specific_persona

    # Get available personas based on trigger filter
    if conversation_structure == "LLM with Triggers":
        valid_personas = filter_personas_by_trigger(assets["personas"], selected_trigger)
    else:
        valid_personas = assets["personas"]

    # Select Patient A
    selected_patient_a = select_specific_persona(valid_personas, "Patient A")
    
    # Select Patient B (exclude A)
    selected_patient_b = select_specific_persona(valid_personas, "Patient B", exclude_name=selected_patient_a)

    # Display configuration summary
    config_summary = {
        "topic": session_topic_data["header"],
        "temperature": session_temperature,
        "structure": conversation_structure,
        "trigger_type": selected_trigger,
        "first_speaker": first_speaker,
        "patient_a": selected_patient_a,
        "patient_b": selected_patient_b
    }
    display_session_configuration(config_summary)
    
    # ========================================================================
    # STAGE 3: SESSION SETUP
    # ========================================================================
    
    print("\n" + "="*70)
    print("SESSION SETUP")
    print("="*70)
    
    header, details, participants, discussion_notes = setup_session_parameters(
        session_topic_data,
        assets["personas"],
        selected_trigger,
        conversation_structure,
        patient_a_name=selected_patient_a,
        patient_b_name=selected_patient_b
    )
    
    output_json = initialize_session_state(
        header, details, participants, discussion_notes,
        conversation_structure, first_speaker
    )
    
    log_session_start(header, conversation_structure, first_speaker)
    
    # ========================================================================
    # STAGE 4: RUN SIMULATION LOOP
    # ========================================================================
    
    print("\n" + "="*70)
    print("SIMULATION STAGE")
    print("="*70)
    
    output_json, conversation_history = run_session_loop(
        output_json,
        participants,
        discussion_notes,
        conversation_structure,
        first_speaker,
        session_temperature,
        assets["prompts"],
        assets["baseline_panas"]
    )
    
    # ========================================================================
    # STAGE 5: POST-SESSION ANALYSIS (PANAS)
    # ========================================================================
    
    output_json, panas_summaries = run_panas_analysis(
        output_json,
        assets["baseline_panas"],
        conversation_history
    )
    
    # ========================================================================
    # STAGE 6: OUTPUT & SUMMARY
    # ========================================================================
    
    print("\n" + "="*70)
    print("OUTPUT & SUMMARY STAGE")
    print("="*70)
    
    # Save JSON transcript
    saved_file = save_session_json(output_json)
    
    # Display summaries
    display_session_summary(output_json, panas_summaries)
    display_session_details(output_json)
    
    # Export readable transcript
    export_transcript_text(output_json)
    
    # Generate report
    report = generate_experiment_report(output_json)
    print("\n" + report)
    
    print("\n" + "="*70)
    print("✅ SESSION COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
