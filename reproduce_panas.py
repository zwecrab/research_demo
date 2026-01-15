
import json
from panas_analyzer import compute_panas_delta
from data_loader import load_baseline_panas

def reproduce():
    # Load baseline
    print("Loading baseline...")
    baseline_data = load_baseline_panas()
    patient_name = "Gregory Adams"
    baseline = baseline_data.get(patient_name, [])
    
    print(f"Baseline for {patient_name}: {len(baseline)} items")
    
    # Load session data
    print("Loading transcript data...")
    with open("transcripts/therapy_transcript_3.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    after_panas = data.get("Patient_B_AFTER_PANAS", [])
    print(f"After PANAS for {patient_name}: {len(after_panas)} items")
    
    # Run computation
    print("\n--- RUNNING COMPUTE_PANAS_DELTA ---")
    delta = compute_panas_delta(baseline, after_panas, patient_name)
    print("--- COMPUTATION COMPLETE ---")
    
    print(f"\nDelta items: {len(delta)}")

if __name__ == "__main__":
    reproduce()
