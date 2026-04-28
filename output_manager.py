# output_manager.py
# File saving, summary statistics display, JSON export

import json
import os
from datetime import datetime
from pathlib import Path
import re
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

def _panas_net_by_affect(delta_list):
    """Sum PANAS deltas split by positive/negative affect.

    Returns:
        dict with positive_change, negative_change, net_change (pos - neg),
        num_improved_positive, num_improved_negative.
    """
    pos_set = {e.title() for e in PANAS_POSITIVE}
    neg_set = {e.title() for e in PANAS_NEGATIVE}
    pos_change = sum(d.get("difference", 0) for d in delta_list if d.get("feeling", "").title() in pos_set)
    neg_change = sum(d.get("difference", 0) for d in delta_list if d.get("feeling", "").title() in neg_set)
    num_improved_pos = sum(1 for d in delta_list if d.get("feeling", "").title() in pos_set and d.get("difference", 0) > 0)
    num_improved_neg = sum(1 for d in delta_list if d.get("feeling", "").title() in neg_set and d.get("difference", 0) < 0)
    return {
        "positive_change": int(pos_change),
        "negative_change": int(neg_change),
        "net_change": int(pos_change - neg_change),  # pos up + neg down = larger positive net
        "num_improved_positive": num_improved_pos,
        "num_improved_negative": num_improved_neg,
    }


def build_metrics_summary(output_json):
    """Assemble a top-of-file metrics block from all scored fields.

    Pulls FAS/BRD/CAS, therapeutic alliance, and PANAS deltas for both patients,
    plus a couple-level net PANAS (sum of both partners' net changes). Returns
    an ordered dict suitable to prepend to the saved transcript.
    """
    participants = output_json.get("participant_details", {})
    pa = participants.get("patient_A", {})
    pb = participants.get("patient_B", {})

    balance = output_json.get("therapeutic_balance", {}) or {}
    fas = balance.get("fas", {}) or {}
    brd = balance.get("brd", {}) or {}
    cas = balance.get("cas", {}) or {}

    alliance = output_json.get("therapist_alliance", {}) or {}

    pa_delta = output_json.get("Patient_A_PANAS_DELTA", [])
    pb_delta = output_json.get("Patient_B_PANAS_DELTA", [])
    pa_panas = _panas_net_by_affect(pa_delta)
    pb_panas = _panas_net_by_affect(pb_delta)

    transcript = output_json.get("session_transcript", [])
    meta = output_json.get("experiment_metadata", {}) or {}

    return {
        "fas": {
            "score": fas.get("fas_score"),
            "count_a": fas.get("count_a", 0),
            "count_b": fas.get("count_b", 0),
            "count_neutral": fas.get("count_neutral", 0),
        },
        "brd": {
            "score": brd.get("brd_score"),
            "mean_depth_a": brd.get("mean_depth_a"),
            "mean_depth_b": brd.get("mean_depth_b"),
        },
        "cas": {
            "score": cas.get("cas_score"),
            "challenges_to_a": cas.get("challenges_to_a", 0),
            "challenges_to_b": cas.get("challenges_to_b", 0),
        },
        "therapeutic_alliance": {
            "overall": alliance.get("overall"),
            "validation": alliance.get("validation"),
            "neutrality": alliance.get("neutrality"),
            "guidance": alliance.get("guidance"),
        },
        "panas_patient_a": {"name": pa.get("name"), **pa_panas},
        "panas_patient_b": {"name": pb.get("name"), **pb_panas},
        "panas_couple_net": pa_panas["net_change"] + pb_panas["net_change"],
        "session": {
            "turns": len(transcript),
            "structure": output_json.get("conversation_structure"),
            "first_speaker": output_json.get("first_speaker_selection"),
            "therapist_mode": meta.get("therapist_mode"),
            "therapist_model": meta.get("therapist_model"),
            "temperature": meta.get("temperature"),
            "couple_id": meta.get("couple_id"),
            "bid_style_a": meta.get("bid_style_a") or (pa.get("bid_style") if pa else None),
            "bid_style_b": meta.get("bid_style_b") or (pb.get("bid_style") if pb else None),
            "position": meta.get("position"),
        },
    }


# V1 fields that are no longer populated by the current pipeline; dropped on save.
_LEGACY_V1_FIELDS = (
    "trigger_log",
    "intervention_scores",
    "intervention_count",
    "scored_interventions_rejected",
)


def save_session_json(output_json, include_panas=False):
    """
    Save session data to JSON file.

    Reorders the output so the metrics_summary block sits at the top of the
    file, followed by configuration, transcript, and raw scoring detail.
    Drops unused v1 legacy fields.

    Args:
        output_json: Complete session data dictionary
        include_panas: Retained for backward compatibility (unused).

    Returns:
        Path to saved file
    """
    filename = random_filename()

    try:
        metrics_summary = build_metrics_summary(output_json)

        # Build ordered output: summary first, then config, then transcript, then raw scoring
        ordered_keys = [
            "metrics_summary",
            "session_topic_header",
            "session_details",
            "participant_details",
            "conversation_structure",
            "first_speaker_selection",
            "experiment_metadata",
            "models_used",
            "session_transcript",
            "therapist_alliance",
            "therapeutic_balance",
            "Patient_A_AFTER_PANAS",
            "Patient_A_PANAS_DELTA",
            "Patient_B_AFTER_PANAS",
            "Patient_B_PANAS_DELTA",
        ]

        json_to_save = {"metrics_summary": metrics_summary}
        for key in ordered_keys[1:]:
            if key in output_json and key not in _LEGACY_V1_FIELDS:
                json_to_save[key] = output_json[key]
        # Append any remaining keys we didn't explicitly order, skipping legacy fields
        for key, value in output_json.items():
            if key not in json_to_save and key not in _LEGACY_V1_FIELDS:
                json_to_save[key] = value

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_to_save, f, indent=2, ensure_ascii=False)
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
            
    # Therapist Alliance Evaluation
    alliance = output_json.get('therapist_alliance')
    if alliance:
        print("\nTherapeutic Alliance Evaluation:")
        print(f"  Overall Score: {alliance.get('overall', 0)}/10")
        print(f"  Validation:    {alliance.get('validation', 0)}")
        print(f"  Neutrality:    {alliance.get('neutrality', 0)}")
        print(f"  Guidance:      {alliance.get('guidance', 0)}")
        
        strengths = alliance.get('strengths', [])
        if strengths:
            print(f"  Strengths:")
            for s in strengths:
                print(f"    • {s}")
                
        weaknesses = alliance.get('weaknesses', [])
        if weaknesses:
            print(f"  Weaknesses:")
            for w in weaknesses:
                print(f"    • {w}")
    
    # Therapeutic Balance (FAS/BRD/CAS)
    balance = output_json.get('therapeutic_balance', {})
    if balance:
        print("\nTherapeutic Balance (Position Bias Metrics):")
        fas = balance.get('fas', {})
        if fas:
            print(f"  FAS (Framing Adoption):  {fas.get('fas_score', 'N/A'):+.3f}"
                  f"  (A:{fas.get('count_a', 0)}, B:{fas.get('count_b', 0)}, N:{fas.get('count_neutral', 0)})")
        brd = balance.get('brd', {})
        if brd:
            print(f"  BRD (Bid Responsiveness): {brd.get('brd_score', 'N/A'):+.3f}"
                  f"  (depth A:{brd.get('mean_depth_a', 0):.2f}, B:{brd.get('mean_depth_b', 0):.2f})")
        cas = balance.get('cas', {})
        if cas:
            print(f"  CAS (Challenge Asymmetry): {cas.get('cas_score', 'N/A'):+d}"
                  f"  (A:{cas.get('challenges_to_a', 0)}, B:{cas.get('challenges_to_b', 0)})")

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
