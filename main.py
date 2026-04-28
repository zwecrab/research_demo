import os
import random
import time
from datetime import datetime

from config import SESSION_MIN_TURNS, SESSION_MAX_TURNS
from data_loader import load_all_assets
from user_interface import (
    select_session_topic, select_temperature, select_conversation_structure,
    select_first_speaker, display_session_configuration,
    select_persona_version, select_couple, select_bid_style_pair,
    select_v2_topic
)
from data_loader import apply_bid_style_overlay
from session_setup import (
    setup_session_parameters, setup_v2_session,
    initialize_session_state, log_session_start
)
from conversation_engine import (
    generate_agent_turn, sequential_speaker_selection,
    decide_next_speaker, extract_therapist_addressee, _speaker_in
)
from emotion_tracker import EmotionTracker
from panas_analyzer import (
    get_after_panas_scores, parse_panas_output, compute_panas_delta,
    summarize_panas_changes
)
from output_manager import (
    build_patient_transcript, save_session_json, display_session_summary,
    display_session_details, export_transcript_text, generate_experiment_report
)

def run_session_loop(output_json, participants, discussion_notes, conversation_structure,
                    first_speaker, session_temperature, prompts, baseline_panas, max_turns_override=None,
                    turn_callback=None, enable_progress=False, therapist_mode='standard',
                    therapist_model=None):
    conversation_history = []

    if max_turns_override:
        max_turns = int(max_turns_override)
    else:
        max_turns = random.randint(SESSION_MIN_TURNS, SESSION_MAX_TURNS)

    arc_template = None
    if enable_progress:
        arc_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts", "session_arc_prompt.txt")
        try:
            with open(arc_file, 'r', encoding='utf-8') as f:
                arc_template = f.read()
            print("📈 Session progress arc: ENABLED")
        except FileNotFoundError:
            print(f"⚠️  session_arc_prompt.txt not found — progress arc disabled.")

    current_turn_number = 1
    current_speaker = "Therapist"
    emotion_tracker = EmotionTracker()

    therapist_last_addressed = None
    therapist_last_dialogue = None
    current_is_silent = False
    last_silent_speaker = None

    if first_speaker == "Patient B First":
        resolved_first_speaker = "Patient B"
    elif first_speaker == "Patient A First":
        resolved_first_speaker = "Patient A"
    else:
        resolved_first_speaker = first_speaker if first_speaker in ["Patient A", "Patient B"] else "Patient A"
    
    session_topic_header = output_json["session_topic_header"]
    
    print(f"\n🎬 Starting simulation: {session_topic_header}")
    print(f"   Structure: {conversation_structure}")
    print(f"   Temperature: {session_temperature}")
    print(f"   Max Turns: {max_turns}")
    print(f"   First Speaker (after Therapist): {first_speaker}\n")
    while current_turn_number <= max_turns:
        # Consecutive silence guard: same patient cannot be silent twice in a row
        if current_is_silent and current_speaker == last_silent_speaker:
            print(f"⏭️  {current_speaker} already silent last turn — skipping, re-selecting.")
            if conversation_structure.strip().lower() != "sequential":
                next_speaker, is_silent = decide_next_speaker(
                    conversation_history,
                    participants['patient_A']['name'],
                    participants['patient_B']['name']
                )
                # Prevent infinite loop if LLM insists on same silent patient
                if is_silent and next_speaker == last_silent_speaker:
                    is_silent = False
                current_speaker = next_speaker
                current_is_silent = is_silent
            else:
                current_speaker = sequential_speaker_selection(
                    current_turn_number, first_speaker=resolved_first_speaker
                )
                current_is_silent = False
            continue

        print(f"\n--- Turn {current_turn_number} of {max_turns} ---")
        
        full_history_str = "\n".join(conversation_history)
        last_responses = {}
        for entry in reversed(conversation_history):
            if "Therapist:" in entry and 'therapist' not in last_responses:
                last_responses['therapist'] = entry.split(":", 1)[1].strip()
            if "Patient A" in entry and 'patient_a' not in last_responses:
                last_responses['patient_a'] = entry.split(":", 1)[1].strip()
            if "Patient B" in entry and 'patient_b' not in last_responses:
                last_responses['patient_b'] = entry.split(":", 1)[1].strip()
        
        dialogue = ""
        speaker_name_for_history = ""
        
        if current_speaker == "Therapist":
            print("🤔 Therapist is thinking...")
            therapist_prompt = prompts['therapist_individual_focus'] if therapist_mode == 'individual_focus' else prompts['therapist']
            dialogue = generate_agent_turn(
                therapist_prompt,
                participants['therapist'],
                session_topic_header,
                discussion_notes,
                full_history_str,
                last_responses,
                session_temperature,
                turn_number=current_turn_number,
                therapist_model=therapist_model
            )
            speaker_name_for_history = "Therapist"
            therapist_last_addressed = extract_therapist_addressee(
                dialogue,
                participants['patient_A']['name'],
                participants['patient_B']['name']
            )
            therapist_last_dialogue = dialogue

        elif current_speaker == "Patient A":
            if current_is_silent:
                dialogue = "*(silence)*"
                print(f"🤫 Patient A ({participants['patient_A']['name']}) stays silent.")
            else:
                print(f"🤔 Patient A ({participants['patient_A']['name']}) is thinking...")
                patient_a_prompt = prompts['patient']
                if arc_template:
                    progress_pct = round((current_turn_number / max_turns) * 100)
                    patient_a_prompt = patient_a_prompt + "\n\n" + arc_template.replace("[PROGRESS_PCT]", str(progress_pct))
                therapist_q = therapist_last_dialogue if therapist_last_addressed == "Patient A" else None
                dialogue = generate_agent_turn(
                    patient_a_prompt,
                    participants['patient_A'],
                    session_topic_header,
                    discussion_notes,
                    full_history_str,
                    last_responses,
                    session_temperature,
                    turn_number=current_turn_number,
                    therapist_question=therapist_q
                )
            speaker_name_for_history = f"Patient A ({participants['patient_A']['name']})"
            therapist_last_addressed = None
            therapist_last_dialogue = None

        elif current_speaker == "Patient B":
            if current_is_silent:
                dialogue = "*(silence)*"
                print(f"🤫 Patient B ({participants['patient_B']['name']}) stays silent.")
            else:
                print(f"🤔 Patient B ({participants['patient_B']['name']}) is thinking...")
                patient_b_prompt = prompts['patient']
                if arc_template:
                    progress_pct = round((current_turn_number / max_turns) * 100)
                    patient_b_prompt = patient_b_prompt + "\n\n" + arc_template.replace("[PROGRESS_PCT]", str(progress_pct))
                therapist_q = therapist_last_dialogue if therapist_last_addressed == "Patient B" else None
                dialogue = generate_agent_turn(
                    patient_b_prompt,
                    participants['patient_B'],
                    session_topic_header,
                    discussion_notes,
                    full_history_str,
                    last_responses,
                    session_temperature,
                    turn_number=current_turn_number,
                    therapist_question=therapist_q
                )
            speaker_name_for_history = f"Patient B ({participants['patient_B']['name']})"
            therapist_last_addressed = None
            therapist_last_dialogue = None
        
        last_silent_speaker = current_speaker if dialogue == "*(silence)*" else None

        emotion_label = None
        trajectory = None
        output_json["session_transcript"].append({
            "turn": current_turn_number,
            "speaker": current_speaker,
            "dialogue": dialogue
        })
        
        full_log_entry = f"{speaker_name_for_history}: {dialogue}"
        conversation_history.append(full_log_entry)
        full_history_str = "\n".join(conversation_history)
        
        print(f"{speaker_name_for_history}: {dialogue[:80]}..." if len(dialogue) > 80 else f"{speaker_name_for_history}: {dialogue}")

        intervention_occurred = False
        next_speaker_override = None

        if turn_callback:
            turn_callback(speaker_name_for_history, dialogue,
                          emotion_label=emotion_label, trajectory=trajectory)
        
        # First speaker override (turn 1 → turn 2)
        if current_turn_number == 1 and first_speaker != "Random":
            if first_speaker == "Patient A First":
                next_speaker_override = "Patient A"
            elif first_speaker == "Patient B First":
                next_speaker_override = "Patient B"
            else:
                next_speaker_override = first_speaker
            print(f"🎯 First speaker override: {next_speaker_override}")
        else:
            next_speaker_override = None

        if next_speaker_override:
            next_speaker = next_speaker_override
            current_is_silent = False
        elif conversation_structure.strip().lower() == "sequential":
            next_speaker = sequential_speaker_selection(current_turn_number + 1, first_speaker=resolved_first_speaker)
            current_is_silent = False
        else:
            next_speaker, is_silent = decide_next_speaker(
                conversation_history,
                participants['patient_A']['name'],
                participants['patient_B']['name'],
                therapist_addressed=therapist_last_addressed
            )
            # S2 (2026-04-21): outer guard now only blocks 3+ consecutive
            # turns by the same speaker. Two consecutive turns are legal so
            # first-speaker airtime dominance can manifest as an FSA channel.
            if not is_silent:
                last_two = conversation_history[-2:]
                spoke_last_two = (
                    len(last_two) == 2
                    and all(_speaker_in(e, current_speaker) for e in last_two)
                )
                if spoke_last_two and next_speaker == current_speaker:
                    candidates = [s for s in ["Therapist", "Patient A", "Patient B"]
                                  if s != current_speaker]
                    next_speaker = candidates[0]
                    print(f"⚠️  3+ consecutive same-speaker blocked — forced to {next_speaker}")
            current_is_silent = is_silent
        
        current_speaker = next_speaker
        current_turn_number += 1
        time.sleep(0.5)

    print(f"\n✅ Simulation complete: {current_turn_number - 1} turns")
    
    return output_json, conversation_history

def run_panas_analysis(output_json, baseline_panas, conversation_history):
    print("\n" + "="*70)
    print("POST-SESSION ANALYSIS: PANAS EMOTIONAL ASSESSMENT")
    print("="*70)
    
    participants = output_json["participant_details"]
    panas_summaries = []

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
    print("\n" + "="*70)
    print("🤖 AI COUPLES THERAPY SIMULATION WITH ADAPTIVE INTERVENTION")
    print("="*70)

    assets = load_all_assets()

    print("\n" + "="*70)
    print("CONFIGURATION STAGE")
    print("="*70)

    persona_version = select_persona_version()

    session_temperature = select_temperature()
    conversation_structure = select_conversation_structure()
    first_speaker = select_first_speaker()

    arc_choice = input("\nEnable session progress arc? (y/n, default n): ").strip().lower()
    enable_progress = arc_choice == "y"

    print("\nTherapist mode:")
    print("  1 = Standard (addresses both partners per turn)")
    print("  2 = Individual Focus (addresses one partner per turn)")
    mode_choice = input("Select (default 1): ").strip()
    therapist_mode = 'individual_focus' if mode_choice == '2' else 'standard'

    print("\n" + "="*70)
    print("SESSION SETUP")
    print("="*70)

    if persona_version == "v2":
        import copy
        couple_id, raw_persona_a, raw_persona_b = select_couple(assets["v2_couples"])
        bid_a_id, bid_b_id = select_bid_style_pair(assets["bid_styles"])
        topic_override = select_v2_topic()

        # Deep-copy so overlays don't mutate the originals
        persona_a = copy.deepcopy(raw_persona_a)
        persona_b = copy.deepcopy(raw_persona_b)
        apply_bid_style_overlay(persona_a, assets["bid_styles"][bid_a_id])
        apply_bid_style_overlay(persona_b, assets["bid_styles"][bid_b_id])
        header, details, participants, discussion_notes = setup_v2_session(
            persona_a, persona_b, conversation_structure,
            topic_override=topic_override
        )

        config_summary = {
            "couple": couple_id,
            "topic": header,
            "temperature": session_temperature,
            "structure": conversation_structure,
            "first_speaker": first_speaker,
            "patient_a": f"{persona_a['name']} ({bid_a_id})",
            "patient_b": f"{persona_b['name']} ({bid_b_id})",
        }
    else:
        session_topic_data = select_session_topic(assets["therapy_plans"])
        from user_interface import select_specific_persona
        valid_personas = assets["personas"]
        selected_patient_a = select_specific_persona(valid_personas, "Patient A")
        selected_patient_b = select_specific_persona(valid_personas, "Patient B",
                                                     exclude_name=selected_patient_a)

        header, details, participants, discussion_notes = setup_session_parameters(
            session_topic_data, assets["personas"], conversation_structure,
            patient_a_name=selected_patient_a, patient_b_name=selected_patient_b
        )

        config_summary = {
            "topic": header,
            "temperature": session_temperature,
            "structure": conversation_structure,
            "first_speaker": first_speaker,
            "patient_a": selected_patient_a,
            "patient_b": selected_patient_b,
        }

    display_session_configuration(config_summary)

    output_json = initialize_session_state(
        header, details, participants, discussion_notes,
        conversation_structure, first_speaker
    )
    
    log_session_start(header, conversation_structure, first_speaker)

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
        assets["baseline_panas"],
        enable_progress=enable_progress,
        therapist_mode=therapist_mode
    )

    output_json, panas_summaries = run_panas_analysis(
        output_json,
        assets["baseline_panas"],
        conversation_history
    )

    from evaluate_therapist import evaluate_therapeutic_alliance
    alliance_scores = evaluate_therapeutic_alliance(output_json.get('session_transcript', []))
    output_json['therapist_alliance'] = alliance_scores

    from evaluate_balance import (
        calculate_fas, calculate_brd, calculate_cas,
        calculate_nas, calculate_tsi,
    )
    transcript = output_json.get('session_transcript', [])
    pa_name = participants['patient_A']['name']
    pb_name = participants['patient_B']['name']
    balance = {}
    try:
        balance["fas"] = calculate_fas(transcript, pa_name, pb_name)
    except Exception as e:
        print(f"FAS scoring failed: {e}")
    try:
        balance["brd"] = calculate_brd(transcript, pa_name, pb_name)
    except Exception as e:
        print(f"BRD scoring failed: {e}")
    try:
        balance["cas"] = calculate_cas(transcript, pa_name, pb_name)
    except Exception as e:
        print(f"CAS scoring failed: {e}")
    try:
        balance["nas"] = calculate_nas(transcript, pa_name, pb_name)
    except Exception as e:
        print(f"NAS scoring failed: {e}")
    try:
        balance["tsi"] = calculate_tsi(transcript, pa_name, pb_name)
    except Exception as e:
        print(f"TSI scoring failed: {e}")
    output_json['therapeutic_balance'] = balance

    print("\n" + "="*70)
    print("OUTPUT & SUMMARY STAGE")
    print("="*70)

    saved_file = save_session_json(output_json)
    display_session_summary(output_json, panas_summaries)
    display_session_details(output_json)
    export_transcript_text(output_json)
    report = generate_experiment_report(output_json)
    print("\n" + report)
    
    print("\n" + "="*70)
    print("✅ SESSION COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
