import json

# Load trigger types from config
TRIGGER_TYPES = [
    "Direct Intervention Request",
    "Emotional Escalation",
    "Crisis Language",
    "Conversational Imbalance",
    "All Triggers"
]
print("=== TRIGGER TYPE OPTIONS ===")
for i, t in enumerate(TRIGGER_TYPES, 1):
    print(f"  {i}: {t}")

# Load personas and check their trigger_type fields
personas = json.load(open('../prompts/trigger-personas.json','r',encoding='utf-8'))
if isinstance(personas, list):
    persona_dict = {p['name']: p for p in personas}
else:
    persona_dict = personas

# Show each persona's trigger_type
print("\n=== PERSONA TRIGGER TYPES ===")
for name in sorted(persona_dict.keys()):
    tt = persona_dict[name].get('trigger_type', '?')
    print(f"  {name}: {tt}")

# Show SEMANTIC ANALYSIS filtered list (sorted)
print("\n=== SEMANTIC ANALYSIS PERSONAS (sorted) ===")
semantic = {k: v for k, v in persona_dict.items() if v.get('trigger_type') == 'Semantic Analysis'}
for i, name in enumerate(sorted(semantic.keys()), 1):
    print(f"  {i}: {name}")

# Also show "All Triggers" = all personas sorted
print("\n=== ALL TRIGGERS PERSONAS (sorted) ===")
for i, name in enumerate(sorted(persona_dict.keys()), 1):
    print(f"  {i}: {name}")
