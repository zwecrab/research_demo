import json

# List topics
plans = json.load(open('../discussions/Final_therapy_discussion.json','r',encoding='utf-8'))
if isinstance(plans, list):
    topics = list({item['header']:1 for item in plans}.keys())
else:
    topics = list(plans.keys())
print("=== TOPICS ===")
for i, t in enumerate(topics, 1):
    print(f"  {i}: {t}")

# List personas (sorted, which is what the UI does)
personas = json.load(open('../prompts/trigger-personas.json','r',encoding='utf-8'))
if isinstance(personas, list):
    names = sorted([p.get('name','?') for p in personas])
else:
    names = sorted(personas.keys())
print("\n=== PERSONAS (sorted) ===")
for i, name in enumerate(names, 1):
    print(f"  {i}: {name}")
