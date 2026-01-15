import os
import json
import random
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "Missing OPENAI_API_KEY in environment variables."

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Model Configuration ---
CONVERSATION_MODEL = "gpt-4o"  # For dialogue generation
PANAS_MODEL = "gpt-4"         # For PANAS scoring
INTERVENTION_MODEL = "gpt-4o" # For AI interventions

# --- File paths ---
TOPIC_FILE = "discussions/Final_therapy_discussion.json"
PERSONA_FILE = "prompts/trigger-personas.json"
THERAPIST_PROMPT_FILE = "prompts/therapist_prompt.txt"
PATIENT_A_PROMPT_FILE = "prompts/patient_A_prompt.txt"
PATIENT_B_PROMPT_FILE = "prompts/patient_B_prompt.txt"
BASELINE_PANAS_FILE = "prompts/trigger-personas_PANAS_2.json"

# --- Intervention Scoring Configuration ---
INTERVENTION_THRESHOLD = 70  # Only intervene if average score >= 70
SCORING_MODEL = "gpt-4"      # For intervention scoring

# --- Trigger Detection Configuration ---
QUANTITATIVE_CONSECUTIVE_THRESHOLD = 6
QUANTITATIVE_WORD_THRESHOLD = 100
TIME_SILENCE_THRESHOLD = 30  # seconds (simulated)
SEMANTIC_ESCALATION_KEYWORDS = ["always", "never", "hate", "sick of", "can't stand", "ridiculous", "pathetic", "stupid"]
SEMANTIC_SELF_HARM_KEYWORDS = ["hurt myself", "better off without me", "want to disappear", "end it all", "kill myself"]
DIRECT_INTERVENTION_KEYWORDS = ["help us", "need guidance", "step in", "what should we do", "can you help"]

# PANAS emotions for reference
PANAS_POSITIVE = ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"]
PANAS_NEGATIVE = ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"]
ALL_PANAS_EMOTIONS = PANAS_POSITIVE + PANAS_NEGATIVE

# --- Helper Functions ---

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def select_session_topic(therapy_plans):
    """Displays a menu for the user to select the therapy session topic."""
    print("\nPlease select a therapy session topic:")
    headers = [plan['header'] for plan in therapy_plans]
    for i, header in enumerate(headers):
        print(f"  {i + 1}: {header}")

    while True:
        try:
            choice = int(input(f"Enter your choice (1-{len(headers)}): "))
            if 1 <= choice <= len(headers):
                return therapy_plans[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def select_temperature():
    """Prompts the user to select a temperature for the AI model's responses."""
    print("\nPlease select the AI model's temperature (creativity level):")
    print("  - A low value (e.g., 0.2) makes the output more predictable and focused.")
    print("  - A high value (e.g., 0.9) makes the output more creative and random.")
    
    min_temp = 0.0
    max_temp = 1.0

    while True:
        try:
            temp_choice = float(input(f"Enter a temperature value between {min_temp} and {max_temp}: "))
            if min_temp <= temp_choice <= max_temp:
                return temp_choice
            else:
                print(f"Invalid choice. Please enter a number between {min_temp} and {max_temp}.")
        except ValueError:
            print("Invalid input. Please enter a valid number (e.g., 0.7).")

def select_conversation_structure():
    """Prompts user to select conversation structuring method."""
    print("\nPlease select conversation structuring method:")
    print("  1: Sequential (Fixed order: Therapist → Patient A → Patient B → repeat)")
    print("  2: LLM Only (AI decides speaker order, no trigger detection)")  
    print("  3: LLM with Triggers (AI decides + trigger-based interventions)")
    
    while True:
        try:
            choice = int(input("Enter your choice (1-3): "))
            if 1 <= choice <= 3:
                structure_types = [
                    "Sequential",
                    "LLM Only", 
                    "LLM with Triggers"
                ]
                return structure_types[choice - 1]
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def select_trigger_type():
    """Prompts user to select trigger type for persona filtering (reduced from 6 to 5 options)."""
    print("\nPlease select the trigger type to test:")
    print("  1: Direct Intervention Request")
    print("  2: Time-based Analysis") 
    print("  3: Semantic Analysis")
    print("  4: Quantitative Analysis")
    print("  5: All Triggers (detect all types)")
    
    while True:
        try:
            choice = int(input("Enter your choice (1-5): "))
            if 1 <= choice <= 5:
                trigger_types = [
                    "Direct Intervention Request",
                    "Time-based Analysis", 
                    "Semantic Analysis",
                    "Quantitative Analysis",
                    "All Triggers"
                ]
                return trigger_types[choice - 1]
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def filter_personas_by_trigger(personas, selected_trigger):
    """Filters personas based on selected trigger type."""
    if selected_trigger in ["No Trigger", "All Triggers"]:
        return personas
    
    filtered = [p for p in personas if p.get("trigger_type") == selected_trigger]
    print(f"\nFound {len(filtered)} personas matching '{selected_trigger}' trigger type")
    return filtered

def setup_session_parameters(session_topic_data, personas, selected_trigger, conversation_structure):
    """Randomly selects participant personas and formats the session details."""
    session_topic_header = session_topic_data['header']
    long_term_goals = session_topic_data['long_term_goals']
    
    num_objectives = random.randint(3, 5)
    selected_objectives = random.sample(session_topic_data['sessions'], num_objectives)
    
    session_details = {
        "long_term_goals": long_term_goals,
        "short_term_objectives": [obj['short_term_objective'] for obj in selected_objectives]
    }
    
    discussion_notes = "\n".join(
        [f"- Objective: {obj['short_term_objective']}\n  Discussion Points: {' '.join(obj['discussion'])}" for obj in selected_objectives]
    )

    # Persona selection based on conversation structure
    if conversation_structure in ["Sequential", "LLM Only"]:
        available_personas = personas  # Use all personas
        print(f"\nUsing all personas for '{conversation_structure}' mode")
    else:
        # LLM with Triggers mode - filter by trigger type
        available_personas = filter_personas_by_trigger(personas, selected_trigger)
    
    if len(available_personas) < 2:
        print(f"Error: Not enough personas available for trigger type '{selected_trigger}'")
        exit()
    
    patient_a_persona, patient_b_persona = random.sample(available_personas, 2)
    
    therapist_persona = {
        "name": "Dr. Anya Sharma",
        "persona_seeds": {
            "age": 45,
            "traits": ["empathetic", "resilient", "reflective"],
            "sample_utterances": ["I understand how that feels...", "Let's explore that further..."],
        }
    }

    participant_details = {
        "therapist": therapist_persona,
        "patient_A": patient_a_persona,
        "patient_B": patient_b_persona,
        "selected_trigger_type": selected_trigger,
        "conversation_structure": conversation_structure
    }
    
    return session_topic_header, session_details, participant_details, discussion_notes

def sequential_speaker_selection(current_turn_number):
    """Sequential speaker selection: Therapist → Patient A → Patient B → repeat"""
    speaker_order = ["Therapist", "Patient A", "Patient B"]
    return speaker_order[(current_turn_number - 1) % 3]

# --- LLM-Based Intervention Scoring System ---

def calculate_intervention_score(conversation_context, current_speaker, current_message, participants):
    """
    Calculate intervention necessity score using LLM-based evaluation
    Based on ACL research: FED, USR, and therapeutic dialogue assessment
    """
    
    # Get recent conversation context (last 500 characters for efficiency)
    context_window = conversation_context[-500:] if len(conversation_context) > 500 else conversation_context
    
    scoring_prompt = f"""
You are an expert in therapeutic dialogue analysis, trained on research from ACL conferences including FED (Fine-grained Evaluation of Dialogue) and USR frameworks.

Evaluate whether an AI intervention is needed in this couples therapy conversation.

CONVERSATION CONTEXT:
{context_window}

CURRENT SPEAKER: {current_speaker}
CURRENT MESSAGE: "{current_message}"

PARTICIPANTS:
- Patient A: {participants['patient_A']['name']} 
- Patient B: {participants['patient_B']['name']}
- Therapist: {participants['therapist']['name']}

Rate each dimension (0-100 scale):

1. FLOW_DISRUPTION (0=intervention flows naturally, 100=would be jarring):
   - How disruptive would an AI intervention be to the natural conversation flow?
   - Consider: Is this a natural therapeutic pause or mid-conversation?

2. THERAPEUTIC_NEED (0=no help needed, 100=urgent intervention required):
   - Are participants showing genuine distress, communication breakdown, or being stuck?
   - Consider: Emotional escalation, circular arguments, withdrawal, crisis indicators

3. TIMING_APPROPRIATENESS (0=terrible timing, 100=perfect moment):
   - Is this an optimal moment for external facilitation?
   - Consider: Natural pause points, completion of thoughts, readiness for guidance

4. IMPACT_POTENTIAL (0=won't help, 100=will significantly improve situation):
   - How likely is an AI intervention to actually improve the therapeutic outcome?
   - Consider: Participant receptiveness, nature of the issue, intervention effectiveness

Return ONLY a JSON object with no additional text:
{{"flow_disruption": X, "therapeutic_need": Y, "timing": Z, "impact": W, "average": (X+Y+Z+W)/4, "recommendation": "INTERVENE" or "CONTINUE", "reasoning": "brief 1-sentence explanation"}}

CRITICAL: Only recommend "INTERVENE" if average >= 70. Most healthy therapeutic conversations should score below 70.
"""

    try:
        response = client.chat.completions.create(
            model=SCORING_MODEL,
            messages=[{"role": "user", "content": scoring_prompt}],
            temperature=0.3,  # Low temperature for consistent scoring
            max_tokens=300
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            score_data = json.loads(json_match.group())
            return score_data
        else:
            print("Warning: Could not parse intervention score JSON")
            return {"average": 50, "recommendation": "CONTINUE", "reasoning": "Scoring parse error"}
            
    except Exception as e:
        print(f"Intervention scoring failed: {e}")
        return {"average": 50, "recommendation": "CONTINUE", "reasoning": "Scoring system error"}

# --- Trigger Detection Functions ---

def count_consecutive_messages(conversation_history, speaker):
    """Count consecutive messages from the same speaker at the end of conversation"""
    if not conversation_history:
        return 0
    
    count = 0
    for entry in reversed(conversation_history):
        if speaker in entry:
            count += 1
        else:
            break
    return count

def count_words(message):
    """Count words in a message"""
    return len(message.split())

def detect_emotional_escalation(message):
    """Detect emotional escalation through keywords and patterns"""
    message_lower = message.lower()
    escalation_indicators = 0
    
    # Check for escalation keywords
    for keyword in SEMANTIC_ESCALATION_KEYWORDS:
        if keyword in message_lower:
            escalation_indicators += 1
    
    # Check for caps (shouting)
    caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
    if caps_ratio > 0.3:  # More than 30% caps
        escalation_indicators += 1
    
    # Check for exclamation marks
    if message.count('!') >= 2:
        escalation_indicators += 1
    
    return escalation_indicators >= 2

def detect_self_harm_language(message):
    """Detect concerning self-harm language"""
    message_lower = message.lower()
    for keyword in SEMANTIC_SELF_HARM_KEYWORDS:
        if keyword in message_lower:
            return True
    return False

def detect_help_request(message):
    """Detect direct intervention requests"""
    message_lower = message.lower()
    for keyword in DIRECT_INTERVENTION_KEYWORDS:
        if keyword in message_lower:
            return True
    return False

def simulate_silence_duration(conversation_history, current_speaker):
    """Simulate silence duration based on conversation patterns"""
    if not conversation_history:
        return 0
    
    # Look for patterns indicating silence (simple simulation)
    recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
    speaker_messages = [msg for msg in recent_messages if current_speaker in msg]
    
    # If speaker hasn't spoken in recent turns, simulate longer silence
    if not speaker_messages:
        return random.randint(15, 45)  # 15-45 second simulated silence
    
    return random.randint(1, 10)  # Normal response time

def detect_triggers(conversation_history, current_speaker, current_message, selected_trigger):
    """Main trigger detection function - only detects selected trigger type"""
    triggers_detected = []
    
    # If "No Trigger" selected, don't detect any triggers
    if selected_trigger == "No Trigger":
        return triggers_detected
    
    # If specific trigger type selected, only detect that type
    if selected_trigger == "Direct Intervention Request":
        if detect_help_request(current_message):
            triggers_detected.append({
                "type": "Direct Intervention Request",
                "subtype": "Help Request",
                "value": 1,
                "description": f"{current_speaker} directly requested intervention"
            })
    
    elif selected_trigger == "Time-based Analysis":
        silence_duration = simulate_silence_duration(conversation_history, current_speaker)
        if silence_duration > TIME_SILENCE_THRESHOLD:
            triggers_detected.append({
                "type": "Time-based Analysis",
                "subtype": "Extended Silence",
                "value": silence_duration,
                "description": f"{current_speaker} was silent for {silence_duration} seconds"
            })
    
    elif selected_trigger == "Semantic Analysis":
        if detect_emotional_escalation(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Emotional Escalation",
                "value": 1,
                "description": f"{current_speaker} shows signs of emotional escalation"
            })
        
        if detect_self_harm_language(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Self-harm Language",
                "value": 1,
                "description": f"{current_speaker} used concerning self-harm language"
            })
    
    elif selected_trigger == "Quantitative Analysis":
        consecutive_count = count_consecutive_messages(conversation_history, current_speaker)
        if consecutive_count >= QUANTITATIVE_CONSECUTIVE_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis", 
                "subtype": "Consecutive Messages",
                "value": consecutive_count,
                "description": f"{current_speaker} sent {consecutive_count} consecutive messages"
            })
        
        word_count = count_words(current_message)
        if word_count > QUANTITATIVE_WORD_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis",
                "subtype": "Long Message", 
                "value": word_count,
                "description": f"{current_speaker} sent a {word_count}-word message"
            })
    
    elif selected_trigger == "All Triggers":
        # Detect all trigger types when "All Triggers" is selected
        # Quantitative Analysis Triggers
        consecutive_count = count_consecutive_messages(conversation_history, current_speaker)
        if consecutive_count >= QUANTITATIVE_CONSECUTIVE_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis", 
                "subtype": "Consecutive Messages",
                "value": consecutive_count,
                "description": f"{current_speaker} sent {consecutive_count} consecutive messages"
            })
        
        word_count = count_words(current_message)
        if word_count > QUANTITATIVE_WORD_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis",
                "subtype": "Long Message", 
                "value": word_count,
                "description": f"{current_speaker} sent a {word_count}-word message"
            })
        
        # Time-based Analysis Triggers
        silence_duration = simulate_silence_duration(conversation_history, current_speaker)
        if silence_duration > TIME_SILENCE_THRESHOLD:
            triggers_detected.append({
                "type": "Time-based Analysis",
                "subtype": "Extended Silence",
                "value": silence_duration,
                "description": f"{current_speaker} was silent for {silence_duration} seconds"
            })
        
        # Semantic Analysis Triggers
        if detect_emotional_escalation(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Emotional Escalation",
                "value": 1,
                "description": f"{current_speaker} shows signs of emotional escalation"
            })
        
        if detect_self_harm_language(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Self-harm Language",
                "value": 1,
                "description": f"{current_speaker} used concerning self-harm language"
            })
        
        # Direct Intervention Request Triggers
        if detect_help_request(current_message):
            triggers_detected.append({
                "type": "Direct Intervention Request",
                "subtype": "Help Request",
                "value": 1,
                "description": f"{current_speaker} directly requested intervention"
            })
    
    return triggers_detected

def generate_intervention(triggers, conversation_context, participants, intervention_score):
    """Generate AI facilitation intervention based on detected triggers and scoring"""
    
    if not triggers:
        return None
    
    primary_trigger = triggers[0]  # Focus on first detected trigger
    trigger_type = primary_trigger["type"]
    trigger_subtype = primary_trigger["subtype"]
    
    intervention_prompts = {
        "Quantitative Analysis": {
            "Consecutive Messages": f"""
As an AI therapy facilitator, you've detected conversation imbalance with consecutive messages. 
Generate a brief, gentle intervention to encourage balanced participation.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with a gentle, professional intervention that:
1. Acknowledges the speaker's input
2. Invites the quieter participant to share
3. Maintains therapeutic neutrality

Keep response under 40 words.
""",
            "Long Message": f"""
As an AI therapy facilitator, you've detected an overly long message that might overwhelm the conversation.
Generate a brief intervention to help break down the content.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with a brief intervention that:
1. Acknowledges the detailed sharing
2. Helps focus on key points
3. Invites response from partner

Keep response under 40 words.
"""
        },
        
        "Time-based Analysis": {
            "Extended Silence": f"""
As an AI therapy facilitator, you've detected extended silence from a participant.
Generate a gentle check-in intervention.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with a supportive intervention that:
1. Gently checks in with the silent participant
2. Provides emotional safety
3. Invites participation without pressure

Keep response under 40 words.
"""
        },
        
        "Semantic Analysis": {
            "Emotional Escalation": f"""
As an AI therapy facilitator, you've detected emotional escalation in the conversation.
Generate a de-escalating intervention.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with a calming intervention that:
1. Acknowledges the emotions
2. Gently de-escalates tension
3. Redirects to constructive dialogue

Keep response under 40 words.
""",
            "Self-harm Language": f"""
As an AI therapy facilitator, you've detected concerning language that suggests self-harm.
Generate an immediate supportive intervention.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with an urgent but supportive intervention that:
1. Addresses the concern directly
2. Provides emotional support
3. Suggests professional resources if needed

Keep response under 50 words.
"""
        },
        
        "Direct Intervention Request": {
            "Help Request": f"""
As an AI therapy facilitator, a participant has directly requested your help.
Generate a helpful facilitation response.

Context: {conversation_context[-300:]}
Trigger: {primary_trigger['description']}
Intervention Score: {intervention_score.get('average', 0)}/100

Respond as the AI Facilitator with a helpful intervention that:
1. Acknowledges the request
2. Provides guidance or structure
3. Facilitates continued dialogue

Keep response under 40 words.
"""
        }
    }
    
    prompt = intervention_prompts.get(trigger_type, {}).get(trigger_subtype, 
        f"Generate a brief therapeutic intervention for: {primary_trigger['description']}")
    
    try:
        response = client.chat.completions.create(
            model=INTERVENTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for consistent interventions
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Intervention generation failed: {e}")
        return f"I notice there might be an imbalance in our conversation. Let's make sure everyone has a chance to share."

# --- Conversation Functions ---

def build_patient_transcript(transcript, patient_label):
    """Build transcript summary for a specific patient"""
    lines = []
    for turn in transcript:
        if turn["speaker"] == patient_label:
            lines.append(turn["dialogue"])
    return "\n".join(lines)

def load_baseline_panas():
    """Load baseline PANAS scores from precomputed file"""
    with open(BASELINE_PANAS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for d in data:
        name = d["persona"]["name"]
        out[name] = d["panas_emotions"]
        print(f"DEBUG: Loaded baseline PANAS for '{name}' with {len(d['panas_emotions'])} emotions")
    return out

def normalize_emotion_name(emotion_name):
    """Normalize emotion name for better matching"""
    if not emotion_name:
        return ""
    
    # Remove everything after colon, dash, or "Score"
    cleaned = re.split(r'[:\-]|Score', str(emotion_name))[0]
    
    # Remove common prefixes and formatting
    cleaned = re.sub(r'^[*\-\d\.\s#]+', '', cleaned)
    cleaned = re.sub(r'\*+', '', cleaned)
    cleaned = cleaned.strip().lower()
    
    # Extract the actual PANAS emotion from contaminated text
    for panas_emotion in ALL_PANAS_EMOTIONS:
        if panas_emotion.lower() in cleaned:
            return panas_emotion.lower()
    
    # Direct mapping for common variations
    emotion_mappings = {
        'interested': 'interested',
        'excitement': 'excited',
        'strong': 'strong', 
        'enthusiasm': 'enthusiastic',
        'enthusiastic': 'enthusiastic',
        'proud': 'proud',
        'alert': 'alert',
        'inspired': 'inspired',
        'determined': 'determined',
        'attentive': 'attentive',
        'active': 'active',
        'distressed': 'distressed',
        'upset': 'upset',
        'guilty': 'guilty',
        'scared': 'scared',
        'hostile': 'hostile',
        'irritable': 'irritable',
        'ashamed': 'ashamed',
        'nervous': 'nervous',
        'jittery': 'jittery',
        'afraid': 'afraid'
    }
    
    return emotion_mappings.get(cleaned, cleaned)

def parse_panas_output(text):
    """Parse PANAS scoring output with improved parsing and cleaning"""
    emotions = []
    processed_emotions = set()  # Track processed emotions to avoid duplicates
    
    print(f"DEBUG: Parsing PANAS output with {len(text.strip().splitlines())} lines")
    
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.lower().startswith(('here', 'the person', 'based on', 'note:', 'explanation:', 'overall')):
            continue
            
        # Handle comma-separated format: emotion, explanation, score
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                feeling_raw = parts[0].strip()
                explanation = parts[1].strip()
                score_str = parts[2].strip()
                
                # Clean emotion name aggressively
                feeling_clean = normalize_emotion_name(feeling_raw)
                
                # Find exact PANAS emotion match
                matched_emotion = None
                for panas_emotion in ALL_PANAS_EMOTIONS:
                    if panas_emotion.lower() == feeling_clean:
                        matched_emotion = panas_emotion
                        break
                
                if matched_emotion and matched_emotion not in processed_emotions:
                    # Clean explanation (remove "Score:" and extra text)
                    explanation = explanation.replace("Score:", "").strip()
                    explanation = explanation.strip('*').strip()
                    
                    # Extract score
                    try:
                        score_match = [int(s) for s in score_str.split() if s.isdigit() and 1 <= int(s) <= 5]
                        score = score_match[0] if score_match else 3
                    except:
                        score = 3
                    
                    emotions.append({
                        "feeling": matched_emotion,  # Use clean PANAS emotion name
                        "explanation": explanation,
                        "score": score
                    })
                    processed_emotions.add(matched_emotion)
                    print(f"DEBUG: Parsed emotion {len(emotions)}: {matched_emotion} = {score}")
    
    print(f"DEBUG: Successfully parsed {len(emotions)} emotions")
    return emotions

def compute_panas_delta(before, after, persona_name):
    """Compute difference between before and after PANAS scores with robust matching"""
    delta = []
    
    print(f"DEBUG: Computing PANAS delta for {persona_name}")
    print(f"DEBUG: Before emotions count: {len(before)}")
    print(f"DEBUG: After emotions count: {len(after)}")
    
    if not before:
        print("DEBUG: No baseline emotions found")
        return delta
    
    if not after:
        print("DEBUG: No after emotions found")  
        return delta
    
    # Create normalized mapping from after emotions
    after_dict = {}
    for emotion in after:
        normalized_name = normalize_emotion_name(emotion["feeling"])
        after_dict[normalized_name] = emotion
        print(f"DEBUG: After emotion mapped: '{normalized_name}' = {emotion['score']}")
    
    # Match baseline emotions with after emotions
    matched_count = 0
    for before_emotion in before:
        before_name_normalized = normalize_emotion_name(before_emotion["feeling"])
        
        # Try to find matching after emotion
        after_match = after_dict.get(before_name_normalized)
        
        if after_match:
            try:
                before_score = int(before_emotion["score"])
                after_score = int(after_match["score"]) 
                difference = after_score - before_score
                
                delta.append({
                    "feeling": before_emotion["feeling"],  # Keep original case from baseline
                    "before_score": before_score,
                    "after_score": after_score,
                    "difference": difference
                })
                
                matched_count += 1
                print(f"DEBUG: Matched '{before_name_normalized}': {before_score} -> {after_score} (Δ{difference:+d})")
                
            except (ValueError, KeyError) as e:
                print(f"DEBUG: Score conversion error for {before_name_normalized}: {e}")
        else:
            print(f"DEBUG: No after-match found for baseline emotion: '{before_name_normalized}'")
    
    print(f"DEBUG: Successfully matched {matched_count}/{len(before)} emotions")
    return delta

def generate_agent_turn(blueprint, persona, session_topic, discussion_notes, history_str, last_responses, temperature):
    """Constructs the prompt and calls the OpenAI API for a single agent turn."""
    
    prompt = blueprint.replace("[insert persona seeds]", json.dumps(persona, indent=2))
    prompt = prompt.replace("[insert topic]", session_topic)
    prompt = prompt.replace("[insert previous turns]", history_str)
    prompt = prompt.replace("[insert specific notes]", discussion_notes)
    
    # Add instruction for concise responses
    prompt += "\n\nIMPORTANT: Keep your response concise and focused, preferably under 100 words unless deep emotional expression is absolutely necessary."
    
    prompt = prompt.replace("[insert if applicable]", "Not applicable for this turn.")
    if 'therapist' in last_responses:
        prompt = prompt.replace("Therapist's last response: [insert if applicable]", f"Therapist's last response: {last_responses['therapist']}")
    if 'patient_a' in last_responses:
        prompt = prompt.replace("Partner A's last response: [insert if applicable]", f"Partner A's last response: {last_responses['patient_a']}")
    if 'patient_b' in last_responses:
        prompt = prompt.replace("Partner B's last response: [insert if applicable]", f"Partner B's last response: {last_responses['patient_b']}")

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=CONVERSATION_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=150  # Reduced from 300 to 150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API call failed on attempt {attempt + 1}: {e}")
            time.sleep(5)
    
    return "I'm sorry, there seems to be a technical issue. Let's take a brief pause."

def intelligent_speaker_selection(conversation_history, current_speaker, intervention_occurred=False):
    """
    Enhanced speaker selection considering conversation balance and therapeutic flow
    Used for LLM Only and LLM with Triggers modes
    """
    
    if not conversation_history:
        return random.choice(["Patient A", "Patient B"])
    
    # Count recent participation (last 6 turns)
    recent_history = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
    speaker_counts = {"Therapist": 0, "Patient A": 0, "Patient B": 0, "AI_Facilitator": 0}
    
    for entry in recent_history:
        speaker = entry.split(":")[0]
        if "Therapist" in speaker:
            speaker_counts["Therapist"] += 1
        elif "Patient A" in speaker:
            speaker_counts["Patient A"] += 1
        elif "Patient B" in speaker:
            speaker_counts["Patient B"] += 1
        elif "AI Facilitator" in speaker:
            speaker_counts["AI_Facilitator"] += 1
    
    # Determine last speaker
    last_speaker_full = conversation_history[-1].split(":")[0]
    last_speaker_role = "Therapist"
    if "Patient A" in last_speaker_full:
        last_speaker_role = "Patient A"
    elif "Patient B" in last_speaker_full:
        last_speaker_role = "Patient B"
    elif "AI Facilitator" in last_speaker_full:
        last_speaker_role = "AI_Facilitator"
    
    # Special handling after AI intervention
    if last_speaker_role == "AI_Facilitator":
        # After AI intervention, prefer patients (never therapist immediately after)
        patient_counts = [speaker_counts["Patient A"], speaker_counts["Patient B"]]
        if patient_counts[0] <= patient_counts[1]:
            return "Patient A"  # Patient A has spoken less or equal
        else:
            return "Patient B"  # Patient B has spoken less
    
    # Normal speaker selection logic
    possible_speakers = ["Therapist", "Patient A", "Patient B"]
    if last_speaker_role in possible_speakers:
        possible_speakers.remove(last_speaker_role)
    
    # Therapeutic balance: Prefer therapist if they've been quiet, otherwise balance patients
    if speaker_counts["Therapist"] < 2 and len(recent_history) > 4:  # Therapist underutilized
        if "Therapist" in possible_speakers:
            return "Therapist"
    
    # Balance between patients
    remaining_patients = [s for s in possible_speakers if "Patient" in s]
    if remaining_patients:
        # Choose patient who has spoken less recently
        if len(remaining_patients) == 2:  # Both patients available
            if speaker_counts["Patient A"] <= speaker_counts["Patient B"]:
                return "Patient A"
            else:
                return "Patient B"
        else:
            return remaining_patients[0]
    
    # Fallback
    return random.choice(possible_speakers)

def get_after_panas_scores(persona_json, transcript_text):
    """Generate post-therapy PANAS scores using OpenAI GPT-4 with improved prompt"""
    
    # Create improved PANAS prompt
    prompt = f"""
You are a clinical psychologist evaluating a patient's emotional state after completing a therapy session.

Rate this person's emotional state on each of the 20 PANAS emotions using the scale 1-5:
1 = Very slightly or not at all
2 = A little  
3 = Moderately
4 = Quite a bit
5 = Extremely

POSITIVE EMOTIONS: {', '.join(PANAS_POSITIVE)}
NEGATIVE EMOTIONS: {', '.join(PANAS_NEGATIVE)}

Person's profile: {json.dumps(persona_json, ensure_ascii=False)}

Their dialogue during the session: {transcript_text[-1000:]}  # Last 1000 chars

For each emotion, provide your assessment in this EXACT format:
emotion_name, brief_clinical_explanation, score_number

Example:
Interested, Shows genuine curiosity about therapeutic solutions discussed, 4
Distressed, Exhibits moderate anxiety about relationship issues, 3

Provide ratings for ALL 20 emotions listed above. Be realistic - use the full 1-5 scale based on the person's responses and progress in therapy.
"""
    
    try:
        response = client.chat.completions.create(
            model=PANAS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,  # Slightly higher for more varied scoring
            max_tokens=1500  # Increased for all 20 emotions
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"PANAS scoring failed: {e}")
        return ""

def random_filename(base="therapy_transcript"):
    """Generate a unique filename for output"""
    output_dir = "transcripts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    base_filename = f"{base}_"
    max_num = 0
    for f in os.listdir(output_dir):
        if f.startswith(base_filename) and f.endswith(".json"):
            try:
                num = int(f[len(base_filename):-5])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    return os.path.join(output_dir, f"{base_filename}{max_num + 1}.json")

# --- Main Program ---

def main():
    """Main function to run the therapy session simulation with enhanced conversation structuring."""
    print("--- AI Couples Therapy Simulation with Enhanced Conversation Structuring ---")
    print(f"🤖 Using {CONVERSATION_MODEL} for conversations, {PANAS_MODEL} for PANAS scoring")

    # 1. Load all assets
    print("Loading assets...")
    therapy_plans = load_json(TOPIC_FILE)
    personas = load_json(PERSONA_FILE)
    therapist_bp = load_txt(THERAPIST_PROMPT_FILE)
    patient_a_bp = load_txt(PATIENT_A_PROMPT_FILE)
    patient_b_bp = load_txt(PATIENT_B_PROMPT_FILE)
    baseline_panas = load_baseline_panas()
    
    # 2. Enhanced user selections
    session_topic_data = select_session_topic(therapy_plans)
    session_temperature = select_temperature()
    conversation_structure = select_conversation_structure()  # NEW
    
    # Only show trigger selection if "LLM with Triggers" is selected
    if conversation_structure == "LLM with Triggers":
        selected_trigger = select_trigger_type()
    else:
        selected_trigger = "No Trigger"  # Default for Sequential and LLM Only

    # 3. Set up session parameters
    print("Setting up session parameters...")
    header, details, participants, notes = setup_session_parameters(session_topic_data, personas, selected_trigger, conversation_structure)
    
    # 4. Initialize simulation state
    output_json = {
        "session_topic_header": header,
        "session_details": details,
        "participant_details": participants,
        "conversation_structure": conversation_structure,  # NEW
        "session_transcript": [],
        "trigger_log": [],
        "intervention_scores": [],
        "intervention_count": 0,
        "scored_interventions_rejected": 0,
        "models_used": {
            "conversation": CONVERSATION_MODEL,
            "panas": PANAS_MODEL,
            "intervention": INTERVENTION_MODEL,
            "scoring": SCORING_MODEL
        }
    }
    
    conversation_history = []
    max_turns = random.randint(25, 35)  
    current_turn_number = 1
    current_speaker = "Therapist"  # Always start with therapist

    print(f"\nSimulating a session on '{header}' with temperature={session_temperature}...")
    print(f"Conversation structure: {conversation_structure}")
    if conversation_structure == "LLM with Triggers":
        print(f"Testing trigger type: {selected_trigger}")
        print("🤖 LLM-based intervention scoring is active...")
    print()

    # 5. Run the enhanced simulation loop
    while current_turn_number <= max_turns:
        print(f"\n--- Turn {current_turn_number} ---")
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
            print("Therapist is thinking...")
            dialogue = generate_agent_turn(therapist_bp, participants['therapist']['persona_seeds'], header, notes, full_history_str, last_responses, session_temperature)
            speaker_name_for_history = "Therapist"
            
        elif current_speaker == "Patient A":
            print(f"Patient A ({participants['patient_A']['name']}) is thinking...")
            dialogue = generate_agent_turn(patient_a_bp, participants['patient_A'], header, notes, full_history_str, last_responses, session_temperature)
            speaker_name_for_history = f"Patient A ({participants['patient_A']['name']})"

        elif current_speaker == "Patient B":
            print(f"Patient B ({participants['patient_B']['name']}) is thinking...")
            dialogue = generate_agent_turn(patient_b_bp, participants['patient_B'], header, notes, full_history_str, last_responses, session_temperature)
            speaker_name_for_history = f"Patient B ({participants['patient_B']['name']})"

        # INTERVENTION SYSTEM - Only active for "LLM with Triggers" mode
        intervention_occurred = False
        
        if conversation_structure == "LLM with Triggers" and current_speaker != "Therapist":
            # Step 1: Detect triggers using existing system
            triggers_detected = detect_triggers(conversation_history, current_speaker, dialogue, selected_trigger)
            
            if triggers_detected:
                print(f"🔍 Triggers detected: {[t['subtype'] for t in triggers_detected]}")
                
                # Step 2: Calculate intervention score using LLM
                intervention_score = calculate_intervention_score(full_history_str, current_speaker, dialogue, participants)
                
                # Log the scoring attempt
                output_json["intervention_scores"].append({
                    "turn": current_turn_number,
                    "triggers": triggers_detected,
                    "score": intervention_score,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"📊 Intervention score: {intervention_score.get('average', 0):.1f}/100 - {intervention_score.get('recommendation', 'UNKNOWN')}")
                print(f"💭 Reasoning: {intervention_score.get('reasoning', 'No reasoning provided')}")
                
                # Step 3: Only intervene if score meets threshold
                if intervention_score.get('average', 0) >= INTERVENTION_THRESHOLD:
                    print("✅ Score above threshold - Generating intervention...")
                    
                    intervention = generate_intervention(triggers_detected, full_history_str, participants, intervention_score)
                    
                    if intervention:
                        current_turn_number += 1
                        
                        # Log intervention turn
                        output_json["session_transcript"].append({
                            "turn": current_turn_number,
                            "speaker": "AI_Facilitator",
                            "dialogue": intervention,
                            "intervention_for_triggers": triggers_detected,
                            "intervention_score": intervention_score,
                            "intervention_type": "llm_scored"
                        })
                        
                        # Add to conversation history
                        facilitator_entry = f"AI Facilitator: {intervention}"
                        conversation_history.append(facilitator_entry)
                        print(f"🤖 AI Facilitator: {intervention}")
                        
                        # Log trigger and intervention
                        output_json["trigger_log"].append({
                            "turn": current_turn_number - 1,
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
        
        # Log the regular turn
        output_json["session_transcript"].append({
            "turn": current_turn_number, 
            "speaker": current_speaker, 
            "dialogue": dialogue,
            "triggers_detected": triggers_detected if 'triggers_detected' in locals() else None
        })
        
        full_log_entry = f"{speaker_name_for_history}: {dialogue}"
        conversation_history.append(full_log_entry)
        print(full_log_entry)
        
        # SPEAKER SELECTION - Based on conversation structure
        if conversation_structure == "Sequential":
            next_speaker = sequential_speaker_selection(current_turn_number + 1)
        elif conversation_structure == "LLM Only":
            next_speaker = intelligent_speaker_selection(conversation_history, current_speaker, intervention_occurred)
        elif conversation_structure == "LLM with Triggers":
            next_speaker = intelligent_speaker_selection(conversation_history, current_speaker, intervention_occurred)
        
        current_speaker = next_speaker
        current_turn_number += 1
        
        # Add small delay to simulate conversation flow
        time.sleep(0.5)
    
    # 6. Generate post-session PANAS scores
    print("\nGenerating post-session PANAS scores...")
    
    for label, patient_key in [("Patient A", "patient_A"), ("Patient B", "patient_B")]:
        persona = participants[patient_key]
        transcript_text = build_patient_transcript(output_json["session_transcript"], label)
        
        print(f"DEBUG: Generating PANAS for {label} ({persona['name']})")
        after_panas_raw = get_after_panas_scores(persona, transcript_text)
        after_panas = parse_panas_output(after_panas_raw)

        # Get baseline with better debugging
        persona_name = persona["name"]
        before_panas = baseline_panas.get(persona_name, [])
        
        print(f"DEBUG: Found baseline for '{persona_name}': {len(before_panas)} emotions")
        if not before_panas:
            print(f"DEBUG: Available baseline personas: {list(baseline_panas.keys())}")
        
        delta_scores = compute_panas_delta(before_panas, after_panas, persona_name)
        output_json[f"{label}_AFTER_PANAS"] = after_panas
        output_json[f"{label}_PANAS_DELTA"] = delta_scores

    # 7. Save files
    conversation_filename = random_filename()
    panas_filename = conversation_filename.replace(".json", "_PANAS.json")

    # Save conversation transcript
    with open(conversation_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "session_topic_header": output_json["session_topic_header"],
            "session_details": output_json["session_details"],
            "participant_details": output_json["participant_details"],
            "conversation_structure": output_json["conversation_structure"],
            "session_transcript": output_json["session_transcript"]
        }, f, indent=2, ensure_ascii=False)
    
    # Save complete data with PANAS and intervention analysis
    with open(panas_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
        
    print(f"\n--- Simulation Complete ---")
    print(f"Conversation transcript saved to: {conversation_filename}")
    print(f"Complete data with PANAS & intervention scores saved to: {panas_filename}")
    
    # Display summary statistics
    print(f"\n--- Session Summary ---")
    print(f"Conversation structure: {conversation_structure}")
    print(f"Total turns: {current_turn_number - 1}")
    
    if conversation_structure == "LLM with Triggers":
        print(f"AI interventions: {output_json['intervention_count']}")
        print(f"Interventions scored but rejected: {output_json['scored_interventions_rejected']}")
        print(f"Total intervention attempts: {len(output_json['intervention_scores'])}")
        
        if output_json["intervention_scores"]:
            avg_score = sum(s["score"].get("average", 0) for s in output_json["intervention_scores"]) / len(output_json["intervention_scores"])
            print(f"Average intervention score: {avg_score:.1f}/100")
        
        if output_json["trigger_log"]:
            trigger_types = {}
            for log_entry in output_json["trigger_log"]:
                for trigger in log_entry["triggers"]:
                    trigger_key = f"{trigger['type']} - {trigger['subtype']}"
                    trigger_types[trigger_key] = trigger_types.get(trigger_key, 0) + 1
            
            print("\nTrigger breakdown:")
            for trigger_type, count in trigger_types.items():
                print(f"  {trigger_type}: {count}")
    
    # Display PANAS summary
    print(f"\n--- PANAS Summary ---")
    for label in ["Patient A", "Patient B"]:
        if f"{label}_PANAS_DELTA" in output_json:
            delta = output_json[f"{label}_PANAS_DELTA"]
            if delta:  # Only if we have delta data
                pos_changes = [d for d in delta if d["feeling"].lower() in [p.lower() for p in PANAS_POSITIVE]]
                neg_changes = [d for d in delta if d["feeling"].lower() in [n.lower() for n in PANAS_NEGATIVE]]
                
                pos_total = sum([d["difference"] for d in pos_changes if isinstance(d["difference"], int)])
                neg_total = sum([d["difference"] for d in neg_changes if isinstance(d["difference"], int)])
                
                print(f"{label} ({participants[f'patient_{label.split()[1]}']['name']}):")
                print(f"  Positive Affect Change: {pos_total:+d}")
                print(f"  Negative Affect Change: {neg_total:+d}")
                print(f"  Emotions matched: {len(delta)}/20")
            else:
                print(f"{label}: PANAS delta calculation failed")

if __name__ == "__main__":
    main()
