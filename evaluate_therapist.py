import json
from openai import OpenAI
from config import SCORING_MODEL as EVALUATION_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def evaluate_therapeutic_alliance(transcript, therapist_name="Therapist"):
    """
    Score each therapist turn on three pillars (0-10 each).
    Also evaluates missed opportunities and a per-turn alliance timeline.

    Pillars are grounded in:
      - Bordin (1979) Working Alliance (Bond + Goal + Task)
      - Kivlighan & Shaughnessy (2000) - non-linear alliance patterns
      - Norcross (2011) - Psychotherapy Relationships That Work (2nd ed.)
      
    Args:
        transcript: List of dictionary containing 'speaker' and 'dialogue'
        therapist_name: Name of the therapist speaker in the transcript
        
    Returns:
        Dictionary containing scores, feedback, timeline, and missed opportunities
    """
    print("\n" + "="*70)
    print("THERAPEUTIC ALLIANCE EVALUATION")
    print("="*70)
    print("⏳ Evaluating therapist performance (Validation, Neutrality, Guidance)...")

    # --- Format full transcript for session-level scoring ---
    formatted_transcript = ""
    for turn in transcript:
        speaker = turn.get("speaker", "Unknown")
        dialogue = turn.get("dialogue", "")
        formatted_transcript += f"{speaker}: {dialogue}\n\n"

    # --- Collect only therapist turns for per-turn timeline ---
    therapist_turns = [
        {"turn": t.get("turn"), "dialogue": t.get("dialogue")}
        for t in transcript
        if t.get("speaker") in (therapist_name, "Therapist", "Dr. Anya Forger")
    ]

    # =========================================================
    # PROMPT 1: Session-level evaluation (Validation, Neutrality, Guidance)
    # =========================================================
    session_prompt = """
You are an expert clinical psychology supervisor evaluating a couples therapist's performance in a session transcript.

Your evaluation framework is grounded in:
- Bordin (1979): Working Alliance (Bond, Goal Agreement, Task Agreement)
- Norcross (2011): Psychotherapy Relationships That Work - empirically supported relationship factors
- Kivlighan & Shaughnessy (2000): Non-linear alliance rupture-repair patterns

You must score the therapist on three pillars, from 0.0 to 10.0:
1. VALIDATION (Bond quality): Did the therapist validate feelings before pivoting?
   - Does NOT use clichés like "I hear you", "I understand", "That is valid"
   - Reflects the depth of emotion accurately
   - Creates emotional safety before task work
2. NEUTRALITY (Impartiality): Did the therapist remain unbiased?
   - Balanced attention between partners
   - Does not blame or minimize one side
   - Reframes issues as relational/shared
3. GUIDANCE (Task + Goal Alliance): Did the therapist steer toward resolution?
   - Offers concrete suggestions at appropriate moments
   - Names stuckness and explores it before problem-solving
   - Uses varied techniques across turns (avoids same question structure)
   - Sits in emotional weight when needed, does not rush to solutions

Also identify:
- STRENGTHS: list what the therapist did well
- WEAKNESSES: list what the therapist did poorly
- MISSED_OPPORTUNITIES: list 2-3 SPECIFIC MOMENTS in the transcript (e.g., "Turn 7 - when Victoria said 'I just... I'm scared', the therapist pivoted to a task instead of acknowledging the vulnerability") where an alternative response would have been more effective. Quote the patient's actual words briefly.
- COMPARISON_NOTE: A single sentence interpreting what these scores mean in context of a typical couples therapy session (e.g., "These scores suggest solid empathic validation but a tendency to rush past emotional peaks into problem-solving mode").

You MUST respond strictly in valid JSON format matching this EXACT structure:
{
  "validation": 8.0,
  "neutrality": 7.5,
  "guidance": 6.5,
  "overall": 7.3,
  "strengths": ["string"],
  "weaknesses": ["string"],
  "missed_opportunities": ["string"],
  "comparison_note": "string"
}
"""

    # =========================================================
    # PROMPT 2: Per-turn alliance timeline
    # =========================================================
    timeline_prompt = """
You are an expert clinical psychology supervisor.
For each therapist turn provided below, score it on a single 0-10 ALLIANCE scale that combines:
- Emotional attunement (did it match what the couple needed emotionally?)
- Technique variety (was this a fresh approach or a repetition?)
- Clinical appropriateness (was the timing right?)

Respond ONLY with a valid JSON array in this exact structure, one entry per therapist turn:
[
  {"turn": 1, "score": 7.5, "technique": "somatic", "note": "One sentence rationale"},
  ...
]
Classify the technique used as one of: somatic, pattern-naming, direct_instruction, reframe, emotion_excavation, behavioral_challenge, relational_mirroring, validation_only, silence, other.
"""

    session_result = {}
    timeline_result = []

    # --- Call 1: Session-level ---
    try:
        response1 = client.chat.completions.create(
            model=EVALUATION_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": session_prompt},
                {"role": "user", "content": f"Here is the full session transcript to evaluate:\n\n{formatted_transcript}"}
            ],
            temperature=0.3
        )
        session_result = json.loads(response1.choices[0].message.content.strip())
        print("✅ Session-level Therapeutic Alliance Evaluation Complete")
    except Exception as e:
        print(f"❌ Error during session-level TA evaluation: {e}")
        session_result = {
            "validation": 0.0, "neutrality": 0.0, "guidance": 0.0, "overall": 0.0,
            "strengths": ["Evaluation failed"], "weaknesses": [str(e)],
            "missed_opportunities": [], "comparison_note": "Evaluation error."
        }

    # --- Call 2: Per-turn timeline ---
    if therapist_turns:
        turns_text = "\n\n".join(
            [f"Turn {t['turn']}: {t['dialogue']}" for t in therapist_turns]
        )
        try:
            response2 = client.chat.completions.create(
                model=EVALUATION_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": timeline_prompt},
                    {"role": "user", "content": f"Therapist turns to evaluate:\n\n{turns_text}\n\nReturn a JSON object with key 'timeline' containing the array."}
                ],
                temperature=0.3
            )
            raw2 = json.loads(response2.choices[0].message.content.strip())
            # Handle both {"timeline": [...]} and direct array responses
            if isinstance(raw2, dict) and "timeline" in raw2:
                timeline_result = raw2["timeline"]
            elif isinstance(raw2, list):
                timeline_result = raw2
            print("✅ Per-Turn Alliance Timeline Complete")
        except Exception as e:
            print(f"❌ Error during per-turn timeline evaluation: {e}")
            timeline_result = []

    # Merge into unified output
    session_result["alliance_timeline"] = timeline_result
    return session_result
