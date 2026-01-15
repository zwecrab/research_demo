# output_manager.py
# File saving, summary statistics display, JSON export

import json
import os
from datetime import datetime
from pathlib import Path
from config import TRANSCRIPTS_DIR, PANAS_POSITIVE, PANAS_NEGATIVE

def build_patient_transcript(transcript, patient_label):
    """Build transcript summary for a specific patient."""
    lines = []
    for turn in transcript:
        if turn.get("speaker") == patient_label:
            lines.append(turn.get("dialogue", ""))
    return "\n".join(lines)

def random_filename(base="therapy_transcript"):
    """Generate a unique filename for output."""
    base_filename = f"{base}_"
    max_num = 0
    
    for f in os.listdir(TRANSCRIPTS_DIR):
        if f.startswith(base_filename) and f.endswith(".json"):
            try:
                num = int(f[len(base_filename):-5])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    return TRANSCRIPTS_DIR / f"{base_filename}{max_num + 1}.json"

def save_session_json(output_json, include_panas=False):
    """
    Save session data to JSON file.
    
    Args:
        output_json: Complete session data dictionary
        include_panas: If True, also includes PANAS analysis
    
    Returns:
        Path to saved file
    """
    filename = random_filename()
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Session saved to: {filename}")
        return filename
    
    except Exception as e:
        print(f"❌ Error saving session: {e}")
        return None

def display_session_summary(output_json, panas_summaries=None):
    """Display comprehensive session summary to console."""
    print("\n" + "="*70)
    print("SESSION SUMMARY")
    print("="*70)
    
    # Basic session info
    print(f"Topic:                      {output_json.get('session_topic_header', 'N/A')}")
    print(f"Conversation Structure:     {output_json.get('conversation_structure', 'N/A')}")
    print(f"First Speaker Selection:    {output_json.get('first_speaker_selection', 'N/A')}")
    
    # Participants
    participants = output_json.get('participant_details', {})
    print(f"\nParticipants:")
    print(f"  Therapist:  {participants.get('therapist', {}).get('name', 'N/A')}")
    print(f"  Patient A:  {participants.get('patient_A', {}).get('name', 'N/A')}")
    print(f"  Patient B:  {participants.get('patient_B', {}).get('name', 'N/A')}")
    
    # Transcript stats
    transcript = output_json.get('session_transcript', [])
    print(f"\nTranscript Statistics:")
    print(f"  Total Turns:                {len(transcript)}")
    print(f"  Therapist Turns:            {len([t for t in transcript if 'Therapist' in t.get('speaker', '')])}")
    print(f"  Patient A Turns:            {len([t for t in transcript if 'Patient A' in t.get('speaker', '')])}")
    print(f"  Patient B Turns:            {len([t for t in transcript if 'Patient B' in t.get('speaker', '')])}")
    print(f"  AI Facilitator Turns:       {len([t for t in transcript if 'AI Facilitator' in t.get('speaker', '')])}")
    
    # Intervention stats
    print(f"\nIntervention Statistics:")
    print(f"  Interventions Generated:    {output_json.get('intervention_count', 0)}")
    print(f"  Interventions Rejected:     {output_json.get('scored_interventions_rejected', 0)}")
    
    # Trigger log
    trigger_log = output_json.get('trigger_log', [])
    trigger_types = {}
    for log_entry in trigger_log:
        for trigger in log_entry.get('triggers', []):
            ttype = trigger.get('type', 'Unknown')
            trigger_types[ttype] = trigger_types.get(ttype, 0) + 1
    
    if trigger_types:
        print(f"\nTrigger Breakdown:")
        for ttype, count in trigger_types.items():
            print(f"  {ttype}:         {count}")
    
    # PANAS summary
    if panas_summaries:
        print(f"\nPANAS Emotional State Changes:")
        for summary in panas_summaries:
            patient = summary.get('patient', 'Unknown')
            pos_change = summary.get('positive_emotion_change', 0)
            neg_change = summary.get('negative_emotion_change', 0)
            
            print(f"\n  {patient}:")
            print(f"    Positive Affect Change:     {pos_change:+d}")
            print(f"    Negative Affect Change:     {neg_change:+d}")
            print(f"    Overall Change:             {pos_change + neg_change:+d}")
            print(f"    Improved Positive Emotions: {summary.get('num_improved_positive', 0)}")
            print(f"    Improved Negative Emotions: {summary.get('num_improved_negative', 0)}")
            
            # Print significant changes from output_json
            patient_key = "Patient_A" if patient == participants.get('patient_A', {}).get('name') else "Patient_B"
            delta_key = f"{patient_key}_PANAS_DELTA"
            deltas = output_json.get(delta_key, [])
            
            significant_changes = [d for d in deltas if d.get('difference', 0) != 0]
            if significant_changes:
                print("\n    Significant Changes:")
                for change in significant_changes:
                    feeling = change.get('feeling', 'Unknown')
                    before = change.get('before_score', '?')
                    after = change.get('after_score', '?')
                    diff = change.get('difference', 0)
                    print(f"      • {feeling}: {before} -> {after} ({diff:+d})")
    
    print("="*70 + "\n")

def display_session_details(output_json):
    """Display detailed session configuration."""
    print("\n" + "="*70)
    print("DETAILED SESSION CONFIGURATION")
    print("="*70)
    
    # Topic and objectives
    details = output_json.get('session_details', {})
    print("\nLong-term Goals:")
    for goal in details.get('long_term_goals', []):
        print(f"  • {goal}")
    
    print("\nShort-term Objectives:")
    for obj in details.get('short_term_objectives', []):
        print(f"  • {obj}")
    
    # Models used
    models = output_json.get('models_used', {})
    print("\nModels Used:")
    print(f"  Conversation:  {models.get('conversation', 'N/A')}")
    print(f"  PANAS Scoring: {models.get('panas', 'N/A')}")
    print(f"  Intervention:  {models.get('intervention', 'N/A')}")
    print(f"  Scoring:       {models.get('scoring', 'N/A')}")
    
    print("="*70 + "\n")

def export_transcript_text(output_json, filename=None):
    """
    Export conversation transcript as readable text file.
    
    Args:
        output_json: Session data
        filename: Optional custom filename
    
    Returns:
        Path to exported file
    """
    if filename is None:
        filename = TRANSCRIPTS_DIR / f"transcript_readable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"SESSION: {output_json.get('session_topic_header', 'N/A')}\n")
            f.write(f"Structure: {output_json.get('conversation_structure', 'N/A')}\n")
            f.write("="*70 + "\n\n")
            
            for turn in output_json.get('session_transcript', []):
                speaker = turn.get('speaker', 'Unknown')
                dialogue = turn.get('dialogue', '')
                f.write(f"{speaker}:\n{dialogue}\n\n")
        
        print(f"✅ Transcript exported to: {filename}")
        return filename
    
    except Exception as e:
        print(f"❌ Error exporting transcript: {e}")
        return None

def generate_experiment_report(output_json, panas_data=None):
    """
    Generate comprehensive experiment report suitable for thesis documentation.
    
    Args:
        output_json: Session data
        panas_data: Pre/post PANAS data
    
    Returns:
        Report text
    """
    report = []
    report.append("# THERAPY SESSION EXPERIMENT REPORT")
    report.append(f"\nGenerated: {datetime.now().isoformat()}")
    report.append("\n## SESSION CONFIGURATION")
    report.append(f"- Topic: {output_json.get('session_topic_header', 'N/A')}")
    report.append(f"- Structure: {output_json.get('conversation_structure', 'N/A')}")
    report.append(f"- First Speaker: {output_json.get('first_speaker_selection', 'N/A')}")
    
    participants = output_json.get('participant_details', {})
    report.append("\n## PARTICIPANTS")
    report.append(f"- Therapist: {participants.get('therapist', {}).get('name', 'N/A')}")
    report.append(f"- Patient A: {participants.get('patient_A', {}).get('name', 'N/A')}")
    report.append(f"- Patient B: {participants.get('patient_B', {}).get('name', 'N/A')}")
    
    report.append(f"\n## TRANSCRIPT STATISTICS")
    transcript = output_json.get('session_transcript', [])
    report.append(f"- Total Turns: {len(transcript)}")
    report.append(f"- AI Facilitator Interventions: {output_json.get('intervention_count', 0)}")
    from config import INTERVENTION_THRESHOLD
    report.append(f"- Rejected Interventions (score < {INTERVENTION_THRESHOLD}): {output_json.get('scored_interventions_rejected', 0)}")
    
    report.append("\n## MODELS")
    models = output_json.get('models_used', {})
    for component, model in models.items():
        report.append(f"- {component}: {model}")
    
    return "\n".join(report)
