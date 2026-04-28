import json
from pathlib import Path
from config import (
    THERAPY_PLANS_FILE, PERSONAS_FILE, PERSONAS_V2_FILE, BID_STYLES_FILE,
    PERSONAS_PANAS_FILE, PERSONAS_V2_PANAS_FILE,
    THERAPIST_PROMPT_FILE, THERAPIST_INDIVIDUAL_FOCUS_PROMPT_FILE,
    PATIENT_PROMPT_FILE,
    THERAPIST_INTERVENTION_PROMPT_FILE
)

def load_json(filepath):
    """Load JSON file with error handling."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")

def load_txt(filepath):
    """Load text file with error handling."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")

def load_therapy_plans():
    """Load therapy domains and session plans."""
    data = load_json(THERAPY_PLANS_FILE)
    
    # Handle both dict and list formats
    if isinstance(data, list):
        # Convert list to dict using 'header' as key
        converted = {}
        for item in data:
            if isinstance(item, dict) and "header" in item:
                converted[item["header"]] = item
        return converted
    return data

def load_personas():
    """Load all personas with their properties."""
    data = load_json(PERSONAS_FILE)
    
    # Handle both dict and list formats
    if isinstance(data, list):
        # Convert list to dict using 'name' as key
        converted = {}
        for item in data:
            if isinstance(item, dict) and "name" in item:
                converted[item["name"]] = item
        return converted
    return data

def load_baseline_panas():
    """
    Load pre-computed baseline PANAS scores for each persona.
    
    Handles both dict and list formats for flexibility.
    """
    data = load_json(PERSONAS_PANAS_FILE)
    baseline = {}
    
    # Handle dict format: {persona_name: {panas_emotions: [...]}}
    if isinstance(data, dict):
        for persona_name, persona_data in data.items():
            if isinstance(persona_data, dict) and "panas_emotions" in persona_data:
                baseline[persona_name] = persona_data["panas_emotions"]
    
    # Handle list format: [{persona: {name: "..."}, panas_emotions: [...]}]
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Try to get name from nested 'persona' dict first (matches JSON structure)
                persona_data = item.get("persona", {})
                name = persona_data.get("name")
                
                # Fallback to top-level if not found (legacy support)
                if not name:
                    name = item.get("name") or item.get("persona_name")
                
                panas = item.get("panas_emotions")
                
                if name and panas:
                    baseline[name] = panas
    
    if not baseline:
        print("⚠️  Warning: No PANAS baseline data extracted. Check file format.")
    
    return baseline

def load_v2_personas():
    """Load v2 personas (bid-style-neutral, couple-based).

    Returns:
        tuple: (personas_by_name, couples)
            personas_by_name: dict keyed by persona name
            couples: dict keyed by couple_id, value is list of persona dicts
    """
    data = load_json(PERSONAS_V2_FILE)
    personas_by_name = {}
    couples = {}
    for item in data:
        name = item["name"]
        personas_by_name[name] = item
        cid = item["couple_id"]
        couples.setdefault(cid, []).append(item)
    return personas_by_name, couples


def load_bid_styles():
    """Load bid-style overlay definitions.

    Returns:
        dict keyed by bid_style_id (e.g. 'passive', 'assertive', 'aggressive')
    """
    data = load_json(BID_STYLES_FILE)
    return {bs["bid_style_id"]: bs for bs in data["bid_styles"]}


def apply_bid_style_overlay(persona, bid_style_data):
    """Apply a bid-style overlay to a persona dict (mutates in place).

    Sets bid_style, interruption_frequency, and injects behavioral principles
    and speaking modifiers into the persona for prompt injection.

    Args:
        persona: persona dict (will be modified)
        bid_style_data: one bid-style object from bid_styles.json

    Returns:
        persona (same reference, mutated)
    """
    persona["bid_style"] = bid_style_data["bid_style_id"]
    persona["interruption_frequency"] = bid_style_data["interruption_frequency"]
    persona["bid_style_principles"] = bid_style_data["behavioral_principles"]
    persona["bid_style_speaking_modifiers"] = bid_style_data["speaking_modifiers"]
    return persona


def load_prompts():
    """Load system prompts for all agents and decision points.

    Patient prompt is a single unified template; slot differentiation is
    handled at runtime via the [slot_label] placeholder ("Partner A" / "Partner B").
    """
    therapist_prompt = load_txt(THERAPIST_PROMPT_FILE)
    therapist_individual_focus_prompt = load_txt(THERAPIST_INDIVIDUAL_FOCUS_PROMPT_FILE)
    patient_prompt = load_txt(PATIENT_PROMPT_FILE)
    therapist_intervention_decision = load_txt(THERAPIST_INTERVENTION_PROMPT_FILE)

    return {
        "therapist": therapist_prompt,
        "therapist_individual_focus": therapist_individual_focus_prompt,
        "patient": patient_prompt,
        "therapist_intervention": therapist_intervention_decision
    }

def load_all_assets():
    """
    Master loader - loads all assets at once.
    Handles both dict and list formats for maximum compatibility.
    
    Returns:
        dict with keys: therapy_plans, personas, baseline_panas, prompts
    """
    print("Loading assets...")

    try:
        therapy_plans = load_therapy_plans()
        prompts = load_prompts()
        baseline_panas = load_baseline_panas()

        # Legacy v1 personas (kept for backward compatibility)
        personas = load_personas()
        print(f"  [v1] {len(personas)} legacy personas, {len(baseline_panas)} PANAS baselines")

        # V2 experiment personas and bid styles
        v2_personas = {}
        v2_couples = {}
        bid_styles = {}
        if PERSONAS_V2_FILE.exists():
            v2_personas, v2_couples = load_v2_personas()
        if BID_STYLES_FILE.exists():
            bid_styles = load_bid_styles()

        # Merge v2 PANAS baselines into main baseline dict
        v2_panas_count = 0
        if PERSONAS_V2_PANAS_FILE.exists():
            v2_panas_data = load_json(PERSONAS_V2_PANAS_FILE)
            for item in v2_panas_data:
                name = item.get("persona", {}).get("name")
                panas = item.get("panas_emotions")
                if name and panas:
                    baseline_panas[name] = panas
                    v2_panas_count += 1

        if v2_personas:
            print(f"  [v2] {len(v2_personas)} personas ({len(v2_couples)} couples), "
                  f"{len(bid_styles)} bid-styles, {v2_panas_count} PANAS baselines")
        print(f"  Prompts: 4 agent prompts loaded")

        return {
            "therapy_plans": therapy_plans,
            "personas": personas,
            "baseline_panas": baseline_panas,
            "prompts": prompts,
            "v2_personas": v2_personas,
            "v2_couples": v2_couples,
            "bid_styles": bid_styles,
        }
    
    except Exception as e:
        print(f"❌ Error loading assets: {e}")
        raise
