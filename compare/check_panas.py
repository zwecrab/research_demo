"""Quick script to check PANAS before-score hallucination across all transcripts."""
import json, os

transcripts_dir = '../transcripts'
persona_file = '../prompts/trigger-personas_PANAS_2.json'

# Load initial PANAS from persona file
personas = json.load(open(persona_file, encoding='utf-8'))
print("=" * 80)
print("INITIAL PANAS FROM PERSONA FILE (Negative Affect only)")
print("=" * 80)
neg_feelings = ['Distressed','Upset','Guilty','Scared','Hostile','Irritable','Ashamed','Nervous','Jittery','Afraid']
for i, p in enumerate(personas[:6]):
    name = p['persona']['name']
    scores = {x['feeling']: x['score'] for x in p['panas_emotions'] if x['feeling'] in neg_feelings}
    print(f"  Persona {i}: {name}")
    print(f"    {scores}")

print()
print("=" * 80)
print("PANAS DELTA BEFORE-SCORES FROM EACH TRANSCRIPT")
print("=" * 80)

files = sorted(
    [f for f in os.listdir(transcripts_dir) if f.startswith('therapy_transcript_') and f.endswith('.json')],
    key=lambda x: int(x.split('_')[2].split('.')[0])
)

for f in files:
    path = os.path.join(transcripts_dir, f)
    try:
        data = json.load(open(path, encoding='utf-8'))
    except:
        print(f"\n  {f}: FAILED TO PARSE")
        continue
    
    num = f.split('_')[2].split('.')[0]
    
    # Get participant names
    pd_section = data.get('participant_details', {})
    pa_name = pd_section.get('patient_A', {}).get('name', '?')
    pb_name = pd_section.get('patient_B', {}).get('name', '?')
    first_speaker = data.get('first_speaker_selection', '?')
    
    a_delta = data.get('Patient_A_PANAS_DELTA', [])
    b_delta = data.get('Patient_B_PANAS_DELTA', [])
    
    if not a_delta and not b_delta:
        print(f"\n  T{num}: NO PANAS_DELTA sections found")
        continue
    
    print(f"\n  T{num}: {pa_name} (A) / {pb_name} (B)  |  First Speaker: {first_speaker}")
    
    if a_delta:
        a_neg_before = {x['feeling']: x['before_score'] for x in a_delta if x['feeling'] in neg_feelings}
        a_neg_after = {x['feeling']: x['after_score'] for x in a_delta if x['feeling'] in neg_feelings}
        print(f"    Patient A BEFORE (neg): {a_neg_before}")
        print(f"    Patient A AFTER  (neg): {a_neg_after}")
    else:
        print(f"    Patient A: NO DELTA")
    
    if b_delta:
        b_neg_before = {x['feeling']: x['before_score'] for x in b_delta if x['feeling'] in neg_feelings}
        b_neg_after = {x['feeling']: x['after_score'] for x in b_delta if x['feeling'] in neg_feelings}
        print(f"    Patient B BEFORE (neg): {b_neg_before}")
        print(f"    Patient B AFTER  (neg): {b_neg_after}")
    else:
        print(f"    Patient B: NO DELTA")

print()
print("=" * 80)
print("DONE")
