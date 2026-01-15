# user_interface.py
# All menu functions and user input handling

from config import CONVERSATION_STRUCTURES, TRIGGER_TYPES, FIRST_SPEAKER_OPTIONS, CONSOLE_WIDTH, DIVIDER

def select_session_topic(therapy_plans):
    """Let user select therapy session topic."""
    print("\n" + DIVIDER)
    print("SELECT SESSION TOPIC")
    print(DIVIDER)
    
    topic_options = list(therapy_plans.keys())
    for i, topic in enumerate(topic_options, 1):
        print(f" {i}: {topic}")
    
    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(topic_options):
                selected_topic = topic_options[choice - 1]
                return therapy_plans[selected_topic]
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")

def select_temperature():
    """Let user select model temperature (0.0-1.0)."""
    print("\n" + DIVIDER)
    print("SELECT TEMPERATURE")
    print(DIVIDER)
    print("Temperature controls response randomness:")
    print(" 0.0  = Deterministic (same response every time)")
    print(" 0.5  = Balanced")
    print(" 1.0  = Maximum creativity (very varied)")
    
    while True:
        try:
            temp = float(input("\nEnter temperature (0.0-1.0): "))
            if 0.0 <= temp <= 1.0:
                return temp
        except ValueError:
            pass
        print("❌ Invalid input. Enter a number between 0.0 and 1.0")

def select_conversation_structure():
    """Let user select conversation structuring approach."""
    print("\n" + DIVIDER)
    print("SELECT CONVERSATION STRUCTURE")
    print(DIVIDER)
    
    structures_desc = {
        "Sequential": "Fixed order: Therapist → Patient A → Patient B (cycle)",
        "LLM Only": "AI chooses speaker for balance (no intervention triggers)",
        "LLM with Triggers": "AI chooses speaker + detects triggers + intervenes"
    }
    
    for i, structure in enumerate(CONVERSATION_STRUCTURES, 1):
        print(f" {i}: {structure}")
        print(f"    → {structures_desc[structure]}")
    
    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(CONVERSATION_STRUCTURES):
                return CONVERSATION_STRUCTURES[choice - 1]
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")

def select_trigger_type():
    """Let user select trigger type (only if LLM with Triggers)."""
    print("\n" + DIVIDER)
    print("SELECT TRIGGER TYPE")
    print(DIVIDER)
    
    trigger_desc = {
        "Direct Intervention Request": "Patient directly asks for help (keywords)",
        "Time-based Analysis": "Simulated silence > 30 seconds",
        "Semantic Analysis": "Emotional escalation or self-harm indicators",
        "Quantitative Analysis": "Message dominance or extreme length",
        "All Triggers": "Test all trigger types together"
    }
    
    for i, ttype in enumerate(TRIGGER_TYPES, 1):
        print(f" {i}: {ttype}")
        print(f"    → {trigger_desc[ttype]}")
    
    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(TRIGGER_TYPES):
                return TRIGGER_TYPES[choice - 1]
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")

def select_first_speaker():
    """
    NEW FEATURE: Let user select who speaks first after therapist.
    
    Returns:
        str: "Patient A", "Patient B", or "Random"
    """
    print("\n" + DIVIDER)
    print("SELECT FIRST SPEAKER")
    print(DIVIDER)
    print("After therapist introduction, who should speak first?")
    
    speaker_desc = {
        "Patient A": "More affected by the issue (primary voice)",
        "Patient B": "Supporting partner (validation)",
        "Random": "Randomly selected (no control)"
    }
    
    for i, speaker in enumerate(FIRST_SPEAKER_OPTIONS, 1):
        print(f" {i}: {speaker}")
        print(f"    → {speaker_desc[speaker]}")
    
    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(FIRST_SPEAKER_OPTIONS):
                return FIRST_SPEAKER_OPTIONS[choice - 1]
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")

def display_session_configuration(config):
    """Display session configuration summary."""
    print("\n" + DIVIDER)
    print("SESSION CONFIGURATION SUMMARY")
    print(DIVIDER)
    
    for key, value in config.items():
        print(f"{key.replace('_', ' ').title():.<30} {value}")
    
    print(DIVIDER + "\n")
