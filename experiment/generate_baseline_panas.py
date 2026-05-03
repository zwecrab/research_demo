"""
Generate baseline (pre-session) PANAS scores for new personas (C6-C9, P11-P18).

Produces entries in the same shape as existing personas_v2_PANAS.json:
  {"persona": {name, gender, age, traits, attachment_style, neuroticism},
   "panas_emotions": [{feeling, explanation, score}, ...20 items]}

Calls PANAS_MODEL via OpenRouter to write a one-line per-emotion explanation
grounded in each persona's traits, OCEAN, attachment, and hidden tension.

Run:
  python experiment/generate_baseline_panas.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import (
    PANAS_MODEL, PANAS_MAX_TOKENS, PANAS_ALL,
    OPENROUTER_GPT_KEY, OPENROUTER_BASE_URL,
)

PERSONAS_FILE = "prompts/personas_v2.json"
PANAS_FILE = "prompts/personas_v2_PANAS.json"
NEW_IDS = {f"P{n:02d}" for n in range(11, 19)}

client = OpenAI(api_key=OPENROUTER_GPT_KEY, base_url=OPENROUTER_BASE_URL)


def build_persona_profile(p):
    ocean = p.get("ocean_profile", {})
    cm = p.get("cognitive_model", {})
    traits = ", ".join(p.get("traits", [])) if isinstance(p.get("traits"), list) else p.get("traits", "")
    return (
        f"Name: {p['name']} ({p.get('age')}, {p.get('gender')}, {p.get('role_in_couple','partner')})\n"
        f"Occupation: {p.get('occupation','')}\n"
        f"Traits: {traits}\n"
        f"Speaking style: {p.get('speaking_style','')}\n"
        f"OCEAN: O={ocean.get('openness')}, C={ocean.get('conscientiousness')}, "
        f"E={ocean.get('extraversion')}, A={ocean.get('agreeableness')}, N={ocean.get('neuroticism')}\n"
        f"Attachment: {p.get('attachment_style','')}\n"
        f"Core belief: {cm.get('core_belief','')}\n"
        f"Coping strategy: {cm.get('coping_strategy','')}\n"
        f"Therapy topic: {'; '.join(p.get('therapy_topics',[]))}\n"
        f"Topic context: {p.get('topic_context','')}\n"
        f"Hidden tension: {p.get('hidden_tension','')}\n"
        f"Hidden intention: {p.get('hidden_intention','')}\n"
    )


def baseline_prompt(persona_profile):
    emotions_list = "\n".join(f"- {e}" for e in PANAS_ALL)
    return f"""You are a clinical psychologist administering the PANAS (Positive and Negative Affect Schedule) to a patient who is about to enter a couples therapy session. You are rating their emotional state RIGHT BEFORE they walk into the therapy room, based on their persona profile.

PATIENT PROFILE:
{persona_profile}

SCORING ANCHORS (1-5 Likert):
  5 = Extremely strong, dominant baseline state
  4 = Quite a bit, frequently present
  3 = Moderately present
  2 = A little, mild background presence
  1 = Not at all

INSTRUCTIONS:
- Score each of the 20 PANAS emotions based on what this person likely feels as they sit in the waiting room.
- Ground each score in their traits, OCEAN profile, attachment style, hidden tension, and topic context.
- High neuroticism + anxious attachment → elevated negative affect (Distressed, Nervous, Afraid).
- Low neuroticism + secure attachment → moderate baseline negative affect.
- Determination/Attentive should reflect their motivation to be in therapy.
- Pre-session means anticipatory: NOT post-conflict, NOT crying yet.

OUTPUT FORMAT (exactly 20 lines, one per emotion, in this order):
{emotions_list}

For each emotion, output a single line:
EMOTION: <score 1-5> | <one-sentence explanation grounded in profile>

Do not include preamble or summary. Just the 20 lines."""


def parse_response(text, persona_name):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^[\*\-\d\.\s]*([A-Za-z]+)\s*[:\-]\s*(\d)\s*[\|\-]\s*(.+)$", line)
        if not m:
            continue
        feeling = m.group(1).strip().capitalize()
        score = int(m.group(2))
        explanation = m.group(3).strip()
        if feeling in PANAS_ALL and 1 <= score <= 5:
            out.append({"feeling": feeling, "explanation": explanation, "score": score})

    found = {x["feeling"] for x in out}
    missing = [e for e in PANAS_ALL if e not in found]
    if missing:
        print(f"  ! {persona_name}: missing {missing}")
        return None
    out.sort(key=lambda x: PANAS_ALL.index(x["feeling"]))
    return out


def generate_for_persona(p):
    profile = build_persona_profile(p)
    prompt = baseline_prompt(profile)
    resp = client.chat.completions.create(
        model=PANAS_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=PANAS_MAX_TOKENS,
    )
    text = resp.choices[0].message.content
    parsed = parse_response(text, p["name"])
    if parsed is None:
        print(f"  ! retrying {p['name']} once...")
        resp = client.chat.completions.create(
            model=PANAS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=PANAS_MAX_TOKENS,
        )
        parsed = parse_response(resp.choices[0].message.content, p["name"])
    return parsed


def main():
    personas = json.load(open(PERSONAS_FILE, encoding="utf-8"))
    panas = json.load(open(PANAS_FILE, encoding="utf-8"))

    existing_names = set()
    for entry in panas:
        n = (entry.get("persona") or {}).get("name") or entry.get("name")
        if n:
            existing_names.add(n)

    new_personas = [p for p in personas if p["persona_id"] in NEW_IDS]
    to_generate = [p for p in new_personas if p["name"] not in existing_names]
    print(f"Generating PANAS for {len(to_generate)} personas: {[p['persona_id'] for p in to_generate]}")

    added = 0
    for p in to_generate:
        print(f"- {p['persona_id']} {p['name']}...")
        try:
            emotions = generate_for_persona(p)
            if not emotions:
                print(f"  ! skipped (parse fail)")
                continue
            entry = {
                "persona": {
                    "name": p["name"],
                    "gender": p["gender"].capitalize(),
                    "age": p["age"],
                    "traits": ", ".join(p["traits"]) if isinstance(p["traits"], list) else p["traits"],
                    "attachment_style": p.get("attachment_style", ""),
                    "neuroticism": p.get("ocean_profile", {}).get("neuroticism", ""),
                },
                "panas_emotions": emotions,
            }
            panas.append(entry)
            added += 1
            pos = sum(e["score"] for e in emotions if e["feeling"] in PANAS_ALL[:10])
            neg = sum(e["score"] for e in emotions if e["feeling"] in PANAS_ALL[10:])
            print(f"  + PA={pos} NA={neg}")
        except Exception as e:
            print(f"  ! error: {e}")

    if added:
        json.dump(panas, open(PANAS_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"\nWrote {added} entries to {PANAS_FILE} (total {len(panas)})")
    else:
        print("\nNothing added.")


if __name__ == "__main__":
    main()
