
import json
import sys
from output_manager import display_session_summary

def verify():
    with open("verify_output.txt", "w", encoding="utf-8") as out:
        sys.stdout = out
        
        print("Loading transcript data...")
        with open("transcripts/therapy_transcript_3.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        participants = data.get("participant_details", {})
        name_a = participants.get("patient_A", {}).get("name")
        name_b = participants.get("patient_B", {}).get("name")
        
        summaries = [
            {
                "patient": name_a,
                "positive_emotion_change": 1, 
                "negative_emotion_change": 1,
                "num_improved_positive": 2,
                "num_improved_negative": 3
            },
            {
                "patient": name_b,
                "positive_emotion_change": 2,
                "negative_emotion_change": 2,
                "num_improved_positive": 4,
                "num_improved_negative": 5
            }
        ]
        
        print("\n--- TEST DISPLAY SUMMARY ---")
        display_session_summary(data, summaries)
        print("--- END TEST ---")

if __name__ == "__main__":
    verify()