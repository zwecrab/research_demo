# trigger_system.py
# All trigger detection functions (4 modalities)

import random
from config import (
    DIRECT_INTERVENTION_KEYWORDS, SEMANTIC_ESCALATION_KEYWORDS,
    SEMANTIC_SELF_HARM_KEYWORDS, QUANTITATIVE_CONSECUTIVE_THRESHOLD,
    QUANTITATIVE_WORD_THRESHOLD, TIME_SILENCE_THRESHOLD
)

def detect_help_request(message):
    """Detect direct intervention request keywords."""
    for keyword in DIRECT_INTERVENTION_KEYWORDS:
        if keyword.lower() in message.lower():
            return True
    return False

def detect_emotional_escalation(message):
    """
    Detect emotional escalation via:
    - Keywords + caps (>30%) + multiple exclamation marks (≥2)
    """
    escalation_indicators = 0
    message_lower = message.lower()
    
    # Keyword check
    for keyword in SEMANTIC_ESCALATION_KEYWORDS:
        if keyword in message_lower:
            escalation_indicators += 1
    
    # Caps ratio check
    if message:
        caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
        if caps_ratio > 0.3:
            escalation_indicators += 1
    
    # Exclamation mark check
    if message.count('!') >= 2:
        escalation_indicators += 1
    
    return escalation_indicators >= 2

def detect_self_harm_language(message):
    """Detect self-harm or crisis language."""
    for keyword in SEMANTIC_SELF_HARM_KEYWORDS:
        if keyword.lower() in message.lower():
            return True
    return False

def count_consecutive_messages(conversation_history, speaker):
    """Count consecutive messages from same speaker."""
    count = 0
    for entry in reversed(conversation_history):
        if speaker in entry:
            count += 1
        else:
            break
    return count

def count_words(message):
    """Count words in message."""
    return len(message.split())

def simulate_silence_duration(conversation_history, current_speaker):
    """
    Simulate silence duration for time-based analysis.
    
    If speaker hasn't spoken recently (not in last 3 turns),
    simulate longer silence (15-45 sec). Otherwise, normal (1-10 sec).
    """
    recent_messages = (
        conversation_history[-3:] if len(conversation_history) >= 3
        else conversation_history
    )
    
    speaker_messages = [msg for msg in recent_messages if current_speaker in msg]
    
    if not speaker_messages:  # Speaker hasn't spoken recently
        return random.randint(15, 45)
    return random.randint(1, 10)

def detect_triggers(conversation_history, current_speaker, current_message, selected_trigger):
    """
    Detect triggers based on selected trigger type.
    
    Args:
        conversation_history: List of dialogue entries
        current_speaker: Who just spoke
        current_message: What they said
        selected_trigger: Which trigger type to detect
    
    Returns:
        list: Detected triggers with type/subtype/description
    """
    triggers_detected = []
    
    # ==================================================================
    # TRIGGER TYPE 1: DIRECT INTERVENTION REQUEST
    # ==================================================================
    if selected_trigger in ["Direct Intervention Request", "All Triggers"]:
        if detect_help_request(current_message):
            triggers_detected.append({
                "type": "Direct Intervention Request",
                "subtype": "Help Request",
                "value": 1,
                "description": f"{current_speaker} directly requested intervention"
            })
    
    # ==================================================================
    # TRIGGER TYPE 2: TIME-BASED ANALYSIS
    # ==================================================================
    if selected_trigger in ["Time-based Analysis", "All Triggers"]:
        silence_duration = simulate_silence_duration(conversation_history, current_speaker)
        if silence_duration > TIME_SILENCE_THRESHOLD:
            triggers_detected.append({
                "type": "Time-based Analysis",
                "subtype": "Extended Silence",
                "value": silence_duration,
                "description": f"Simulated {silence_duration}s silence from {current_speaker}"
            })
    
    # ==================================================================
    # TRIGGER TYPE 3: SEMANTIC ANALYSIS
    # ==================================================================
    if selected_trigger in ["Semantic Analysis", "All Triggers"]:
        if detect_self_harm_language(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Self-Harm Language",
                "value": 1,
                "description": "Crisis indicator detected",
                "severity": "CRITICAL"
            })
        elif detect_emotional_escalation(current_message):
            triggers_detected.append({
                "type": "Semantic Analysis",
                "subtype": "Emotional Escalation",
                "value": 1,
                "description": "High emotional intensity detected (keywords + caps + punctuation)"
            })
    
    # ==================================================================
    # TRIGGER TYPE 4: QUANTITATIVE ANALYSIS
    # ==================================================================
    if selected_trigger in ["Quantitative Analysis", "All Triggers"]:
        consecutive = count_consecutive_messages(conversation_history, current_speaker)
        if consecutive >= QUANTITATIVE_CONSECUTIVE_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis",
                "subtype": "Message Dominance",
                "value": consecutive,
                "description": f"{current_speaker} sent {consecutive} consecutive messages"
            })
        
        word_count = count_words(current_message)
        if word_count > QUANTITATIVE_WORD_THRESHOLD:
            triggers_detected.append({
                "type": "Quantitative Analysis",
                "subtype": "Information Overload",
                "value": word_count,
                "description": f"Message exceeds {QUANTITATIVE_WORD_THRESHOLD} words ({word_count} total)"
            })
    
    return triggers_detected
