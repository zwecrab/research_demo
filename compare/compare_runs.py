import json

# Analyze PANAS from the two new experiment transcripts
files = {
    'T21 (A first)': '../transcripts/therapy_transcript_21.json',
    'T22 (B first)': '../transcripts/therapy_transcript_22.json',
}

# Load persona baseline for comparison
personas = json.load(open('../prompts/trigger-personas_PANAS_2.json', encoding='utf-8'))
persona_baselines = {}
for p in personas:
    name = p['persona']['name']
    persona_baselines[name] = {e['feeling']: e['score'] for e in p['panas_emotions']}

neg = ['Distressed','Upset','Guilty','Scared','Hostile','Irritable','Ashamed','Nervous','Jittery','Afraid']
pos = ['Interested','Excited','Strong','Enthusiastic','Proud','Alert','Inspired','Determined','Attentive','Active']

print("=" * 90)
print("COMPARISON: T21 (Patient A first) vs T22 (Patient B first)")
print("=" * 90)

for label, filepath in files.items():
    data = json.load(open(filepath, encoding='utf-8'))
    
    first_speaker = data.get('first_speaker_selection', '?')
    pa = data.get('participant_details', {}).get('patient_A', {}).get('name', '?')
    pb = data.get('participant_details', {}).get('patient_B', {}).get('name', '?')
    
    a_delta = data.get('Patient_A_PANAS_DELTA', [])
    b_delta = data.get('Patient_B_PANAS_DELTA', [])
    
    print(f"\n{'─' * 90}")
    print(f"  {label} | {pa}(A) / {pb}(B) | First Speaker: {first_speaker}")
    print(f"{'─' * 90}")
    
    # Patient A
    if a_delta:
        a_before_neg = {x['feeling']: x['before_score'] for x in a_delta if x['feeling'] in neg}
        a_after_neg = {x['feeling']: x['after_score'] for x in a_delta if x['feeling'] in neg}
        a_before_pos = {x['feeling']: x['before_score'] for x in a_delta if x['feeling'] in pos}
        a_after_pos = {x['feeling']: x['after_score'] for x in a_delta if x['feeling'] in pos}
        
        # Check vs baseline
        baseline_a = persona_baselines.get(pa, {})
        mismatches_a = []
        for e in neg + pos:
            bval = a_before_neg.get(e) or a_before_pos.get(e)
            pval = baseline_a.get(e)
            if bval is not None and pval is not None and bval != pval:
                mismatches_a.append(f"{e}: transcript={bval} persona={pval}")
        
        neg_change = sum((a_after_neg.get(e,0) - a_before_neg.get(e,0)) for e in neg if e in a_before_neg)
        pos_change = sum((a_after_pos.get(e,0) - a_before_pos.get(e,0)) for e in pos if e in a_before_pos)
        
        print(f"  Patient A ({pa}):")
        print(f"    Positive change: {'+' if pos_change >= 0 else ''}{pos_change}")
        print(f"    Negative change: {'+' if neg_change >= 0 else ''}{neg_change}")
        if mismatches_a:
            print(f"    ⚠️  Before-score MISMATCHES vs persona: {len(mismatches_a)}")
            for m in mismatches_a:
                print(f"       {m}")
        else:
            print(f"    ✅ Before-scores MATCH persona baseline")
    
    # Patient B
    if b_delta:
        b_before_neg = {x['feeling']: x['before_score'] for x in b_delta if x['feeling'] in neg}
        b_after_neg = {x['feeling']: x['after_score'] for x in b_delta if x['feeling'] in neg}
        b_before_pos = {x['feeling']: x['before_score'] for x in b_delta if x['feeling'] in pos}
        b_after_pos = {x['feeling']: x['after_score'] for x in b_delta if x['feeling'] in pos}
        
        baseline_b = persona_baselines.get(pb, {})
        mismatches_b = []
        for e in neg + pos:
            bval = b_before_neg.get(e) or b_before_pos.get(e)
            pval = baseline_b.get(e)
            if bval is not None and pval is not None and bval != pval:
                mismatches_b.append(f"{e}: transcript={bval} persona={pval}")
        
        neg_change = sum((b_after_neg.get(e,0) - b_before_neg.get(e,0)) for e in neg if e in b_before_neg)
        pos_change = sum((b_after_pos.get(e,0) - b_before_pos.get(e,0)) for e in pos if e in b_before_pos)
        
        print(f"  Patient B ({pb}):")
        print(f"    Positive change: {'+' if pos_change >= 0 else ''}{pos_change}")
        print(f"    Negative change: {'+' if neg_change >= 0 else ''}{neg_change}")
        if mismatches_b:
            print(f"    ⚠️  Before-score MISMATCHES vs persona: {len(mismatches_b)}")
            for m in mismatches_b:
                print(f"       {m}")
        else:
            print(f"    ✅ Before-scores MATCH persona baseline")

# Now compare specific emotions side by side
print(f"\n{'=' * 90}")
print("DETAILED BEFORE-SCORE COMPARISON (Negative Affect)")
print(f"{'=' * 90}")
print(f"  {'Emotion':<15} {'Nathan baseline':>16} {'T21 A-before':>13} {'T22 A-before':>13} {'Victoria baseline':>18} {'T21 B-before':>13} {'T22 B-before':>13}")
print(f"  {'-'*15} {'-'*16} {'-'*13} {'-'*13} {'-'*18} {'-'*13} {'-'*13}")

t21 = json.load(open('../transcripts/therapy_transcript_21.json', encoding='utf-8'))
t22 = json.load(open('../transcripts/therapy_transcript_22.json', encoding='utf-8'))

t21_a_delta = {x['feeling']: x for x in t21.get('Patient_A_PANAS_DELTA', [])}
t21_b_delta = {x['feeling']: x for x in t21.get('Patient_B_PANAS_DELTA', [])}
t22_a_delta = {x['feeling']: x for x in t22.get('Patient_A_PANAS_DELTA', [])}
t22_b_delta = {x['feeling']: x for x in t22.get('Patient_B_PANAS_DELTA', [])}

nathan_base = persona_baselines.get('Nathan Pierce', {})
victoria_base = persona_baselines.get('Victoria Hayes', {})

for e in neg:
    nb = nathan_base.get(e, '?')
    t21a = t21_a_delta.get(e, {}).get('before_score', '?')
    t22a = t22_a_delta.get(e, {}).get('before_score', '?')
    vb = victoria_base.get(e, '?')
    t21b = t21_b_delta.get(e, {}).get('before_score', '?')
    t22b = t22_b_delta.get(e, {}).get('before_score', '?')
    
    a_match = '✅' if nb == t21a == t22a else '❌'
    b_match = '✅' if vb == t21b == t22b else '❌'
    
    print(f"  {e:<15} {str(nb):>16} {str(t21a):>13} {str(t22a):>13} {str(vb):>18} {str(t21b):>13} {str(t22b):>13}  {a_match} {b_match}")

# Also check if Nathan and Victoria even EXIST in persona_baselines
print(f"\n{'=' * 90}")
print("PERSONA FILE CHECK")
print(f"{'=' * 90}")
if 'Nathan Pierce' in persona_baselines:
    print(f"  Nathan Pierce: FOUND in persona file")
    print(f"    Neg: { {e: nathan_base.get(e) for e in neg} }")
else:
    print(f"  Nathan Pierce: NOT FOUND in persona file")

if 'Victoria Hayes' in persona_baselines:
    print(f"  Victoria Hayes: FOUND in persona file")
    print(f"    Neg: { {e: victoria_base.get(e) for e in neg} }")
else:
    print(f"  Victoria Hayes: NOT FOUND in persona file")
