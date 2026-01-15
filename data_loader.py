import json
from pathlib import Path
from config import (
    THERAPY_PLANS_FILE, PERSONAS_FILE, PERSONAS_PANAS_FILE,
    THERAPIST_PROMPT_FILE, PATIENT_A_PROMPT_FILE, PATIENT_B_PROMPT_FILE
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

def load_prompts():
    """Load system prompts for all three agents."""
    therapist_prompt = load_txt(THERAPIST_PROMPT_FILE)
    patient_a_prompt = load_txt(PATIENT_A_PROMPT_FILE)
    patient_b_prompt = load_txt(PATIENT_B_PROMPT_FILE)
    
    return {
        "therapist": therapist_prompt,
        "patient_a": patient_a_prompt,
        "patient_b": patient_b_prompt
    }

def load_all_assets():
    """
    Master loader - loads all assets at once.
    Handles both dict and list formats for maximum compatibility.
    
    Returns:
        dict with keys: therapy_plans, personas, baseline_panas, prompts
    """
    print("📦 Loading assets...")
    
    try:
        therapy_plans = load_therapy_plans()
        print(f"  ✅ Loaded {len(therapy_plans)} therapy domains")
        
        personas = load_personas()
        print(f"  ✅ Loaded {len(personas)} personas")
        
        baseline_panas = load_baseline_panas()
        print(f"  ✅ Loaded baseline PANAS for {len(baseline_panas)} personas")
        
        prompts = load_prompts()
        print(f"  ✅ Loaded 3 agent prompts (therapist, patient A, patient B)")
        
        return {
            "therapy_plans": therapy_plans,
            "personas": personas,
            "baseline_panas": baseline_panas,
            "prompts": prompts
        }
    
    except Exception as e:
        print(f"❌ Error loading assets: {e}")
        raise
