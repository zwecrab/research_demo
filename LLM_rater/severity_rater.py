"""
LLM Rater — Problem Severity scoring for FSA Characterisation Study.

Reads each persona from prompts/personas_v2.json (and optionally
personas_v2_additions.json), calls three contemporary frontier raters via
OpenRouter (Claude 3 Opus, Gemini 2.5 Pro, GPT-4o), and writes per-couple
severity vectors plus inter-rater kappa to LLM_rater/ratings/.

Usage:
    python LLM_rater/severity_rater.py                      # rate all couples
    python LLM_rater/severity_rater.py --couple C1          # rate one couple
    python LLM_rater/severity_rater.py --smoke              # smoke test on C1 only

Reference: LLM_rater/severity_rubric.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = os.getenv("OPENROUTER_GPT_KEY") or os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_KEY:
    sys.exit("ERROR: set OPENROUTER_GPT_KEY (or OPENROUTER_API_KEY) in .env")

PERSONAS_FILE = PROJECT_ROOT / "prompts" / "personas_v2.json"
PERSONAS_ADDITIONS_FILE = PROJECT_ROOT / "prompts" / "personas_v2_additions.json"
PROMPT_FILE = Path(__file__).parent / "severity_rater_prompt.txt"
RATINGS_DIR = Path(__file__).parent / "ratings"
RATINGS_DIR.mkdir(exist_ok=True)

RATER_MODELS = [
    "anthropic/claude-opus-4",
    "google/gemini-2.5-pro",
    "openai/gpt-4o",
]

DIMENSIONS = [
    "anxiety",
    "depression",
    "trauma",
    "attachment_disorganisation",
    "escalation_tendency",
]


def load_personas() -> list[dict]:
    """Return combined list of personas from v2 + v2_additions."""
    with open(PERSONAS_FILE, encoding="utf-8") as f:
        personas = json.load(f)
    if PERSONAS_ADDITIONS_FILE.exists():
        with open(PERSONAS_ADDITIONS_FILE, encoding="utf-8") as f:
            personas.extend(json.load(f))
    return personas


def group_by_couple(personas: list[dict]) -> dict[str, list[dict]]:
    """Group personas into couples by couple_id."""
    couples: dict[str, list[dict]] = {}
    for p in personas:
        couples.setdefault(p["couple_id"], []).append(p)
    return couples


def load_prompt_template() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json_lenient(raw: str) -> dict:
    """Parse JSON from a model response, tolerating markdown fences.

    Some models (notably Gemini) ignore response_format and return
    ```json ... ``` fenced output. Strip fences, then fall back to
    extracting the outermost {...} block if direct parsing fails.
    """
    text = _FENCE_RE.sub("", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _OBJECT_RE.search(text)
        if not match:
            raise
        return json.loads(match.group(0))


def call_rater(client: OpenAI, model: str, prompt: str) -> dict:
    """Single rater call. Returns parsed JSON dict on success."""
    # Some models (Gemini via OpenRouter) reject response_format. Try with it
    # first; on a 4xx, retry without and use lenient parsing.
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
    except Exception:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4000,
        )
    raw = resp.choices[0].message.content.strip()
    return _parse_json_lenient(raw)


def rate_persona(persona: dict, prompt_template: str) -> dict:
    """Run all raters on one persona. Return raw rater responses."""
    persona_json = json.dumps(persona, indent=2, ensure_ascii=False)
    prompt = prompt_template.replace("{persona_json}", persona_json)

    client = OpenAI(api_key=OPENROUTER_KEY, base_url=OPENROUTER_BASE_URL)
    rater_results = []

    for model in RATER_MODELS:
        try:
            result = call_rater(client, model, prompt)
            rater_results.append({"model": model, "scores": result, "error": None})
            print(f"    [OK] {model}")
        except Exception as e:
            rater_results.append({"model": model, "scores": None, "error": str(e)})
            print(f"    [FAIL] {model}: {e}")

    return rater_results


def compute_consensus(rater_results: list[dict]) -> dict:
    """Per-dimension mean across raters (errors excluded). Float output."""
    consensus = {}
    for dim in DIMENSIONS:
        scores = [float(r["scores"][dim]) for r in rater_results
                  if r["scores"] and dim in r["scores"]]
        consensus[dim] = round(statistics.mean(scores), 2) if scores else None
    return consensus


def compute_overall(rater_results: list[dict]) -> float | None:
    """Mean of rater-reported overall_score values."""
    scores = [float(r["scores"]["overall_score"]) for r in rater_results
              if r["scores"] and "overall_score" in r["scores"]]
    return round(statistics.mean(scores), 2) if scores else None


def compute_kappa(rater_results: list[dict]) -> dict:
    """
    Inter-rater agreement per dimension on the 0-10 float scale.

    Returns:
      - within_one_rate: proportion of rater pairs whose scores fall within 1.0
      - mean_abs_diff: average |score_i - score_j| across rater pairs
    """
    valid = [r for r in rater_results if r["scores"]]
    if len(valid) < 2:
        return {dim: None for dim in DIMENSIONS}

    kappa = {}
    for dim in DIMENSIONS:
        scores = [float(r["scores"][dim]) for r in valid]
        n = len(scores)
        pairs = [(scores[i], scores[j]) for i in range(n) for j in range(i+1, n)]
        if not pairs:
            kappa[dim] = None
            continue
        within_one = sum(1 for a, b in pairs if abs(a - b) <= 1.0) / len(pairs)
        mean_diff = sum(abs(a - b) for a, b in pairs) / len(pairs)
        kappa[dim] = {
            "within_one_rate": round(within_one, 3),
            "mean_abs_diff": round(mean_diff, 3),
        }
    return kappa


def vector_diff(a: dict, b: dict) -> dict:
    """A − B per dimension."""
    return {dim: round((a.get(dim) or 0) - (b.get(dim) or 0), 2) for dim in DIMENSIONS}


def rate_couple(couple_id: str, members: list[dict], prompt_template: str) -> dict:
    """Rate both patients of a couple, compute consensus and severity_diff."""
    if len(members) != 2:
        raise ValueError(f"Couple {couple_id} has {len(members)} members; expected 2")

    print(f"\n=== Rating couple {couple_id} ===")
    out = {
        "couple_id": couple_id,
        "rated_at": datetime.now(timezone.utc).isoformat(),
        "rater_models": RATER_MODELS,
    }

    for slot, member in zip(("patient_A", "patient_B"), members):
        print(f"  {slot}: {member['name']}")
        rater_results = rate_persona(member, prompt_template)
        consensus = compute_consensus(rater_results)
        overall = compute_overall(rater_results)
        kappa = compute_kappa(rater_results)
        out[slot] = {
            "name": member["name"],
            "persona_id": member["persona_id"],
            "consensus_vector": consensus,
            "overall_score": overall,
            "rater_responses": rater_results,
            "inter_rater_agreement": kappa,
        }

    out["severity_diff_vector"] = vector_diff(
        out["patient_A"]["consensus_vector"],
        out["patient_B"]["consensus_vector"],
    )
    a_overall = out["patient_A"]["overall_score"]
    b_overall = out["patient_B"]["overall_score"]
    out["overall_score_diff"] = (
        round(a_overall - b_overall, 2)
        if a_overall is not None and b_overall is not None else None
    )
    return out


def save_rating(rating: dict) -> Path:
    out_path = RATINGS_DIR / f"{rating['couple_id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rating, f, indent=2, ensure_ascii=False)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--couple", help="Couple ID to rate (default: all)")
    ap.add_argument("--smoke", action="store_true",
                    help="Smoke test: rate C1 only and print result")
    args = ap.parse_args()

    prompt_template = load_prompt_template()
    personas = load_personas()
    couples = group_by_couple(personas)

    if args.smoke:
        target_ids = ["C1"]
    elif args.couple:
        target_ids = [args.couple]
    else:
        target_ids = sorted(couples.keys())

    for cid in target_ids:
        if cid not in couples:
            print(f"WARN: couple {cid} not found in personas")
            continue
        rating = rate_couple(cid, couples[cid], prompt_template)
        out_path = save_rating(rating)
        print(f"  -> wrote {out_path}")
        print(f"  -> overall A: {rating['patient_A']['overall_score']:.2f}  "
              f"overall B: {rating['patient_B']['overall_score']:.2f}  "
              f"diff: {rating['overall_score_diff']:+.2f}")
        print(f"  -> severity_diff_vector: {rating['severity_diff_vector']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
