import json
import os
import re
from typing import List, Dict, Any

from openai import OpenAI
from secret_key import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


# =====================================================
# JSON UTILITIES
# =====================================================

def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =====================================================
# JSON EXTRACTION — ROBUST
# =====================================================

def extract_json(text: str):
    """
    Extrage primul bloc JSON valid dintr-un text.
    Funcționează chiar dacă modelul dă text nestructurat.
    """

    # caut cel mai mare bloc JSON
    matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)

    for m in matches:
        try:
            return json.loads(m)
        except:
            continue

    print("❌ Nu am putut extrage niciun JSON din răspuns!")
    print("Răspuns primit:", text)
    return None


# =====================================================
# FETCH FINAL OFFICIAL RESULTS
# =====================================================

def fetch_final_election_results() -> Dict[str, float]:
    prompt = """
    Caută pe web rezultatele oficiale ale alegerilor pentru Primăria Generală București 2024.

    Returnează STRICT un JSON valid:

    {
      "Nicușor Dan": NUMAR,
      "Gabriela Firea": NUMAR,
      "Cristian Popescu Piedone": NUMAR
    }

    Valorile pot fi voturi SAU procente.
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search"}],
        input=[{"role": "user", "content": prompt}],
        max_output_tokens=1500
    )

    raw = response.output_text
    data = extract_json(raw)

    if not data:
        return {}

    # 🔥  Detectăm dacă sunt voturi brute și le convertim în procente
    values = list(data.values())

    if any(v > 100 for v in values):
        total = sum(values)
        data = {k: round(v / total * 100, 2) for k, v in data.items()}
        print("📌 Rezultatele au fost convertite automat în procente.")

    save_json("data/results_buc.json", data)
    print("✔ Rezultatele PMB salvate în data/results_buc.json")

    return data

# =====================================================
# FETCH LATEST POLLS
# =====================================================

def fetch_latest_polls_bucuresti(max_polls: int = 10) -> List[Dict[str, Any]]:
    prompt = """
    Caută pe web cele mai recente sondaje pentru Primăria Municipiului București.

    Returnează STRICT o LISTĂ JSON de obiecte:
    [
      {
        "institut": "...",
        "data": "YYYY-MM-DD",
        "esantion": NUMAR,
        "metoda": "...",
        "procentaje": {
          "Nicușor Dan": NUMAR,
          "Gabriela Firea": NUMAR,
          "Cristian Popescu Piedone": NUMAR
        },
        "marja_eroare": NUMAR
      }
    ]
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search"}],
        input=[{"role": "user", "content": prompt}],
        max_output_tokens=3000
    )

    raw = response.output_text

    data = extract_json(raw)
    if not data:
        return []

    if isinstance(data, dict):
        data = [data]

    print(f"✔ Am găsit {len(data)} sondaje noi")
    return data[:max_polls]


# =====================================================
# MERGE POLLS
# =====================================================

def merge_polls(existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {(p["institut"], p["data"]) for p in existing}
    out = list(existing)

    for p in new:
        key = (p["institut"], p["data"])
        if key not in seen:
            out.append(p)
            seen.add(key)

    return out


def update_polls_json():
    path = "data/polls_buc.json"
    existing = load_json(path, [])
    new_polls = fetch_latest_polls_bucuresti()

    merged = merge_polls(existing, new_polls)
    save_json(path, merged)

    print(f"✔ Sondajele actualizate (total {len(merged)})")


# =====================================================
# RECALCULATE BONUS
# =====================================================

def recalc_accuracy_bonuses():
    polls = load_json("data/polls_buc.json", [])
    results = load_json("data/results_buc.json", {})

    if not polls or not results:
        print("❌ Lipsesc sondaje sau rezultate pentru recalcularea bonusurilor")
        return

    errors: Dict[str, List[float]] = {}

    for p in polls:
        inst = p["institut"]
        if inst not in errors:
            errors[inst] = []
        for cand, real in results.items():
            if cand in p["procentaje"]:
                errors[inst].append(abs(p["procentaje"][cand] - real))

    bonuses = {}
    max_err = max(sum(v)/len(v) for v in errors.values())

    for inst, vals in errors.items():
        mean_err = sum(vals)/len(vals)
        bonus = 1.2 - 0.3 * (mean_err / max_err)
        bonuses[inst] = {"bonus_greutate": round(bonus, 3)}

    save_json("data/accuracy_institutes.json", bonuses)
    print("✔ Bonusurile recalibrate.")


# =====================================================
# MAIN
# =====================================================

def main():
    print("\n==============================")
    print("      AGENT — FULL AUTO 🤖")
    print("==============================")

    print("\n1️⃣  Fetch rezultate PMB...")
    fetch_final_election_results()

    print("\n2️⃣  Fetch sondaje...")
    update_polls_json()

    print("\n3️⃣  Recalculare bonusuri...")
    recalc_accuracy_bonuses()

    print("\n==============================")
    print("       ✔ AGENT FINALIZAT")
    print("==============================\n")


if __name__ == "__main__":
    main()
