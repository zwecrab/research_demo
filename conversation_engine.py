# conversation_engine.py
# Dialogue generation, speaker selection logic, OpenAI API calls

from openai import OpenAI
import re
import random
from config import (
    CONVERSATION_MODEL, MAX_TOKENS_PER_TURN,
    OPENROUTER_BASE_URL, OPENROUTER_GPT_KEY, OPENROUTER_L8B_KEY, OPENROUTER_L70B_KEY,
)

# All calls route through OpenRouter
client = OpenAI(api_key=OPENROUTER_GPT_KEY, base_url=OPENROUTER_BASE_URL)

# Patient client (same as client; kept as separate alias for clarity)
patient_client = client

# Model-to-key mapping for therapist routing
_THERAPIST_KEY_MAP = {
    "openai/gpt-4o":                     OPENROUTER_GPT_KEY,
    "meta-llama/llama-3.1-8b-instruct":  OPENROUTER_L8B_KEY,
    "meta-llama/llama-3.1-70b-instruct": OPENROUTER_L70B_KEY,
}

# Cache OpenRouter clients to avoid recreating per turn
_client_cache = {}

def _get_openrouter_client(api_key):
    """Return a cached OpenAI client for the given OpenRouter API key."""
    if api_key not in _client_cache:
        _client_cache[api_key] = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
    return _client_cache[api_key]

def generate_agent_turn(blueprint_prompt, persona, session_topic, discussion_notes,
                       conversation_history, last_responses, temperature, turn_number=1,
                       therapist_question=None, therapist_model=None):
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
        therapist_question: If set, the therapist directly addressed this patient —
                            their utterance is prepended as a priority directive.

    Returns:
        str: Generated dialogue turn
    """
    # Prepare the injected system prompt
    import json
    injected_prompt = blueprint_prompt
    
    # Inject persona seeds if present (for Therapist)
    if "persona_seeds" in persona:
        seeds_str = json.dumps(persona["persona_seeds"], indent=2)
        injected_prompt = injected_prompt.replace("[insert persona seeds]", seeds_str)
    else:
        # Format generic fields for Patients
        for field in ["name", "age", "gender", "traits", "speaking_style",
                      "hidden_intention", "hidden_tension", "bid_style",
                      "attachment_style"]:
            value = persona.get(field, "Not specified")
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            injected_prompt = injected_prompt.replace(f"[{field}]", str(value))

        # Slot label: "Partner A" / "Partner B" (symmetric framing across prompts)
        slot_label = persona.get("role", "").replace("Patient", "Partner")
        injected_prompt = injected_prompt.replace("[slot_label]", slot_label)

        # Cognitive model (v2 personas)
        cognitive_model = persona.get("cognitive_model", {})
        if cognitive_model:
            cm_text = (f"Your core belief: {cognitive_model.get('core_belief', '')}\n"
                       f"Your coping strategy: {cognitive_model.get('coping_strategy', '')}")
        else:
            cm_text = ""
        injected_prompt = injected_prompt.replace("[cognitive_model]", cm_text)

        # OCEAN profile (v2 personas)
        ocean = persona.get("ocean_profile", {})
        if ocean:
            ocean_text = "Your personality (OCEAN): " + ", ".join(
                f"{k}: {v}" for k, v in ocean.items())
        else:
            ocean_text = ""
        injected_prompt = injected_prompt.replace("[ocean_profile]", ocean_text)

        # Attachment style context (v2 personas)
        attachment = persona.get("attachment_style", "")
        if attachment:
            attach_text = f"Your attachment style: {attachment}"
        else:
            attach_text = ""
        injected_prompt = injected_prompt.replace("[attachment_info]", attach_text)

        # Relationship history (v2 personas)
        rel_history = persona.get("relationship_history", "")
        injected_prompt = injected_prompt.replace("[relationship_context]",
            f"Relationship background: {rel_history}" if rel_history else "")

        # Bid-style behavioral principles (v2, injected from overlay)
        bid_principles = persona.get("bid_style_principles", [])
        if bid_principles:
            principles_text = "BID-STYLE BEHAVIORAL RULES (follow these strictly):\n"
            for p in bid_principles:
                principles_text += f"- {p}\n"
            bid_modifiers = persona.get("bid_style_speaking_modifiers", [])
            if bid_modifiers:
                principles_text += "\nSPEAKING PATTERN MODIFIERS:\n"
                for m in bid_modifiers:
                    principles_text += f"- {m}\n"
        else:
            principles_text = ""
        injected_prompt = injected_prompt.replace("[bid_style_principles]", principles_text)

        # Interruption frequency (from persona or bid-style overlay)
        interruption_freq = persona.get("interruption_frequency", "")
        interruption_rules = ""
        if interruption_freq and interruption_freq != "none":
            interruption_rules += f"- INTERRUPTION FREQUENCY: {interruption_freq}.\n"

        # Hidden tension leakage
        tension_examples = persona.get("hidden_tension_examples", [])
        tension_leakage = "LEAK YOUR HIDDEN TENSION DURING THE SESSION:\n"
        for example in tension_examples:
            tension_leakage += f"- {example}\n"

        injected_prompt = injected_prompt.replace("[trigger_specific_rules]", interruption_rules)
        injected_prompt = injected_prompt.replace("[hidden_tension_leakage]", tension_leakage)
        
    # Inject topic
    injected_prompt = injected_prompt.replace("[insert topic]", session_topic)
    
    # Inject objectives/notes (mainly for therapist)
    # Include goals (which contain patient names) so the therapist knows
    # who the patients are from Turn 1 — prevents name hallucination.
    if isinstance(discussion_notes, dict):
        goals = discussion_notes.get('goals', [])
        objectives = discussion_notes.get('objectives', [])
        notes_parts = []
        if goals:
            notes_parts.append(', '.join(goals))
        if objectives:
            notes_parts.append(', '.join(objectives))
        notes_str = '. '.join(notes_parts) if notes_parts else ''
    else:
        notes_str = str(discussion_notes)
    injected_prompt = injected_prompt.replace("[insert specific notes]", notes_str)

    # Build context message
    context = f"""
CONVERSATION CONTEXT (Turn {turn_number}):
{conversation_history if conversation_history else "Session just started."}

LAST RESPONSES:
{', '.join([f'{k}: {v[:50]}...' for k, v in last_responses.items()]) if last_responses else "None yet"}
"""
    
    # Build user message (keep conversation context here)
    user_message = f"""
{context}

Session Topic: {session_topic}
Objectives: {notes_str}

Generate a natural, concise response (1-3 sentences, up to 40 words) specifically from the perspective of {persona['name']} ({persona['role']}).
Be authentic to their character. Build on what's been said. Keep it short and punchy, real people don't give speeches in therapy.
Do NOT repeat any point, metaphor, or phrase you have already used in the conversation. Each turn must advance the topic.

CRITICAL INSTRUCTION: DO NOT prefix your response with your name or role (e.g. no "{persona['name']}:" or "{persona['role']}:"). Output ONLY the spoken dialogue.
"""

    # If the therapist directly addressed this patient, prepend a priority directive
    if therapist_question and persona.get('role') != 'Therapist':
        user_message = (
            f"IMPORTANT — THE THERAPIST JUST ADDRESSED YOU DIRECTLY:\n"
            f"\"{therapist_question}\"\n"
            f"Acknowledge or respond to the therapist before anything else.\n\n"
        ) + user_message

    def calculate_jaccard_similarity(str1, str2):
        # Remove parenthetical actions before comparison
        s1 = re.sub(r'\*.*?\*', '', str1).lower().split()
        s2 = re.sub(r'\*.*?\*', '', str2).lower().split()
        set1, set2 = set(s1), set(s2)
        if not set1 or not set2:
            return 0.0
        return len(set1.intersection(set2)) / len(set1.union(set2))

    # Route: patients use patient_client (OpenRouter GPT-4o),
    # therapist uses model-specific OpenRouter key
    is_therapist = persona.get('role') == 'Therapist'
    speaker_prefix = "Dr. Anya Forger:" if is_therapist else f"{persona['name']}:"
    recent_own_turns = [t.replace(speaker_prefix, "").strip() for t in conversation_history[-10:] if t.startswith(speaker_prefix)]

    if is_therapist and therapist_model:
        _model = therapist_model
        _key = _THERAPIST_KEY_MAP.get(therapist_model, OPENROUTER_GPT_KEY)
        _client = _get_openrouter_client(_key)
    elif is_therapist:
        _client = patient_client  # default therapist = same GPT-4o
        _model  = CONVERSATION_MODEL
    else:
        _client = patient_client
        _model  = CONVERSATION_MODEL

    max_retries = 1
    for attempt in range(max_retries + 1):
        try:
            response = _client.chat.completions.create(
                model=_model,
                messages=[
                    {"role": "system", "content": injected_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=MAX_TOKENS_PER_TURN
            )
            
            dialogue = response.choices[0].message.content.strip()
            # Safety net: strip em-dashes from output (banned formatting)
            dialogue = dialogue.replace('\u2014', ',').replace('\u2013', ',')
            # Strip leading interrupt marker (–That's not what I meant → That's not what I meant)
            if dialogue.startswith('-'):
                dialogue = dialogue.lstrip('-').lstrip()

            
            if is_therapist:
                # Therapist repetition check — lower threshold (0.45) because
                # therapeutic interventions must vary their framing each turn.
                if recent_own_turns:
                    similarity_scores = [calculate_jaccard_similarity(dialogue, prev) for prev in recent_own_turns[-2:]]
                    if any(score > 0.45 for score in similarity_scores):
                        print(f"⚠️ Therapist intervention too repetitive. Retrying... ({attempt+1}/{max_retries})")
                        user_message += (
                            "\n\nCRITICAL WARNING: Your previous intervention was too similar to what you said earlier. "
                            "You MUST use a completely different therapeutic technique this turn — "
                            "switch to a NEW lens: somatic, pattern-naming, direct instruction, reframe, "
                            "emotion excavation, behavioral challenge, or relational mirroring. "
                            "Do NOT ask the same style of question again."
                        )
                        continue
            else:
                # Patient sentence limit check (split by . ! ?) ignoring parentheticals
                text_only = re.sub(r'\*.*?\*', '', dialogue).strip()
                # Clean out ellipses so they don't cause overcounting
                text_cleaned = re.sub(r'\.{2,}', '.', text_only)
                sentences = [s for s in re.split(r'[.!?]+(?=\s|$)', text_cleaned) if s.strip()]
                
                if len(sentences) > 4:
                    print(f"⚠️ Sentences > 4 ({len(sentences)}). Retrying... ({attempt+1}/{max_retries})")
                    user_message += "\n\nCRITICAL WARNING: Your previous output was too long. You MUST respond in EXACTLY 2-4 sentences. Do NOT give long speeches."
                    continue
                
                # Patient repetition check — threshold 0.6
                if recent_own_turns:
                    similarity_scores = [calculate_jaccard_similarity(dialogue, prev) for prev in recent_own_turns[-2:]]
                    if any(score > 0.6 for score in similarity_scores):
                        print(f"⚠️ High repetition detected. Retrying... ({attempt+1}/{max_retries})")
                        user_message += "\n\nCRITICAL WARNING: Your previous output was too repetitive of your past thoughts. Advance the conversation or express fresh raw frustration without using the exact same phrasing."
                        continue

            return dialogue
        
        except Exception as e:
            print(f"❌ Error generating dialogue: {e}")
            if attempt == max_retries:
                return f"[Unable to generate response: {e}]"
    
    # If we exhausted retries and still failed checks, just return the last generated dialogue
    return dialogue

def decide_therapist_intervention(conversation_history, decision_prompt, temperature=0.0):
    """
    Asks the Therapist LLM if it should intervene based on the recent conversation history.
    
    Args:
        conversation_history: List of formatted dialogue strings
        decision_prompt: The system instruction for the binary YES/NO decision
        temperature: Low temperature for deterministic output
        
    Returns:
        bool: True if the therapist decides to intervene, False otherwise.
    """
    # Only need recent context, e.g., last 4-6 turns to make a decision
    recent_history = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
    history_text = "\n".join(recent_history)
    
    messages = [
        {"role": "system", "content": decision_prompt},
        {"role": "user", "content": f"Recent Conversation History:\n{history_text}\n\nShould you intervene? (Output only YES or NO)"}
    ]
    
    try:
        response = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=10
        )
        
        reply = response.choices[0].message.content.strip().upper()
        # Clean up any trailing punctuation the model might add
        reply = reply.replace(".", "").replace("!", "")
        
        should_intervene = (reply == "YES")
        if should_intervene:
            print(f"🔔 Therapist decided to intervene.")
        else:
            print(f"🔇 Therapist observing (Decision: NO).")
            
        return should_intervene
        
    except Exception as e:
        print(f"❌ Error deciding intervention: {e}")
        return False

def _speaker_in(history_entry: str, speaker: str) -> bool:
    """Return True if the formatted history line was spoken by `speaker`.

    History entries look like "Therapist: ...", "Patient A: ...", etc.
    Matches the substring conventions used elsewhere in this file.
    """
    if speaker == "Therapist":
        return "Therapist:" in history_entry or "Dr." in history_entry[:20]
    return speaker in history_entry


def sequential_speaker_selection(turn_number, first_speaker="Patient A"):
    """
    Sequential speaker selection: Therapist → first_speaker → second_speaker cycle.
    The cycle order adjusts based on who is selected to speak first.
    
    Args:
        turn_number: Current turn number (1-indexed)
        first_speaker: Who speaks first after therapist ("Patient A" or "Patient B")
    
    Returns:
        str: Next speaker ("Therapist", "Patient A", or "Patient B")
    """
    if first_speaker == "Patient B" or first_speaker == "Patient B First":
        speakers = ["Therapist", "Patient B", "Patient A"]
    else:
        speakers = ["Therapist", "Patient A", "Patient B"]
        
    return speakers[(turn_number - 1) % 3]

def intelligent_speaker_selection(conversation_history, current_speaker, intervention_occurred=False, patients_only=False):
    """
    Intelligent speaker selection based on therapeutic balance.

    S2 (2026-04-21): hard "never same speaker twice in a row" rule replaced
    by a soft guard that blocks ONLY 3+ consecutive same-speaker turns. Two
    consecutive turns by the same speaker are now legal so first-speaker
    airtime dominance can manifest as an FSA channel.

    Args:
        conversation_history: List of dialogue entries
        current_speaker: Who just spoke
        intervention_occurred: Whether AI just intervened
        patients_only: If True, exclude Therapist from candidates (used in trigger mode)

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

    # S2 soft guard: block current_speaker only if they spoke the last TWO
    # turns (i.e., another consecutive turn would make it three in a row).
    last_two = conversation_history[-2:] if len(conversation_history) >= 2 else []
    spoke_last_two = (
        len(last_two) == 2
        and all(_speaker_in(entry, current_speaker) for entry in last_two)
    )

    if patients_only:
        candidates = ["Patient A", "Patient B"]
    else:
        candidates = ["Therapist", "Patient A", "Patient B"]

    if spoke_last_two:
        possible_speakers = [s for s in candidates if s != current_speaker]
    else:
        possible_speakers = candidates[:]
    
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


def extract_therapist_addressee(dialogue, patient_a_name, patient_b_name):
    """
    Detect if the therapist opened by directly addressing one patient by first name.

    Args:
        dialogue: Therapist's generated utterance
        patient_a_name: Full name of Patient A
        patient_b_name: Full name of Patient B

    Returns:
        "Patient A", "Patient B", or None
    """
    snippet = dialogue[:80]
    a_first = patient_a_name.split()[0]
    b_first = patient_b_name.split()[0]
    if re.match(rf'^{re.escape(a_first)}[\s,.]', snippet, re.IGNORECASE):
        return "Patient A"
    if re.match(rf'^{re.escape(b_first)}[\s,.]', snippet, re.IGNORECASE):
        return "Patient B"
    return None


def decide_next_speaker(conversation_history, patient_a_name, patient_b_name,
                        therapist_addressed=None):
    """
    LLM-based speaker selection for natural therapy turn-taking.

    If the therapist just addressed a specific patient directly, that patient
    is returned immediately (short-circuit, no API call).
    Otherwise a gpt-4o-mini call decides, allowing silence for passive patients.

    Args:
        conversation_history: List of formatted dialogue strings
        patient_a_name: Full name of Patient A
        patient_b_name: Full name of Patient B
        therapist_addressed: "Patient A", "Patient B", or None

    Returns:
        tuple[str, bool]: (next_speaker, is_silent)
            next_speaker — "Therapist", "Patient A", or "Patient B"
            is_silent    — True if the patient chose not to speak this turn
    """
    # Short-circuit: therapist directly addressed someone
    if therapist_addressed in ("Patient A", "Patient B"):
        return therapist_addressed, False

    recent = "\n".join(conversation_history[-6:]) if conversation_history else "Session just started."
    prompt = (
        "You are managing turn order in a couples therapy session.\n"
        f"Patient A: {patient_a_name}  |  Patient B: {patient_b_name}\n\n"
        "Recent turns:\n"
        f"{recent}\n\n"
        "Who should speak next? Rules:\n"
        "- If Therapist has not spoken in the last 3 turns, strongly prefer Therapist.\n"
        "- A speaker may take two consecutive turns when their content warrants it; "
        "do NOT force alternation just to be balanced. Three or more consecutive "
        "turns by the same speaker is not allowed.\n"
        "- A withdrawn or passive patient may elect silence this turn.\n\n"
        "Reply with EXACTLY ONE of these options (no other text):\n"
        "Therapist | Patient A | Patient B | Patient A Silent | Patient B Silent"
    )
    try:
        resp = client.chat.completions.create(
            model=CONVERSATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8,
            temperature=0.0
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠️  Speaker decision error: {e} — defaulting to Patient A")
        raw = "Patient A"

    if "Patient A Silent" in raw:
        return "Patient A", True
    if "Patient B Silent" in raw:
        return "Patient B", True
    if "Patient A" in raw:
        return "Patient A", False
    if "Patient B" in raw:
        return "Patient B", False
    if "Therapist" in raw:
        return "Therapist", False
    return "Patient A", False
