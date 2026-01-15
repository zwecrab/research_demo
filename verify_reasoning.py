from intervention_system import generate_intervention

def test_trigger_reasoning():
    # Mock data
    triggers = [{
        "type": "Time-based Analysis",
        "subtype": "Extended Silence",
        "value": 45,
        "description": "Patient A has been silent for 45 seconds"
    }]
    
    context = "Therapist: How are you?\nPatient B: I'm fine."
    participants = {"patient_A": {"name": "TestUser"}}
    score = {"average": 85, "recommendation": "INTERVENE"}
    
    print("Testing intervention generation...")
    response = generate_intervention(triggers, context, participants, score)
    
    print("\nGenerated Intervention:")
    print(response)
    
    # Verification check
    if "noticed" in response.lower() or "observed" in response.lower() or "silent" in response.lower():
        print("\n✅ Verification PASSED: Reasoning sentence detected.")
    else:
        print("\n❌ Verification FAILED: No reasoning sentence found.")

if __name__ == "__main__":
    test_trigger_reasoning()
