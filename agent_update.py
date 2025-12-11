import json
import os
import re
from datetime import date
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

    matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)

    for m in matches:
        try:
            return json.loads(m)
        except Exception:
            continue

    print("❌ Nu am putut extrage niciun JSON din răspuns!")
    print("Răspuns primit:", text)
    return None


# =====================================================
# FETCH FINAL OFFICIAL RESULTS
# =====================================================

def fetch_final_election_results() -> Dict[str, float]:
    path = "data/results_buc.json"

    # 1️⃣ Dacă există fișierul, îl folosim direct
    if os.path.exists(path):
        print("✔ Rezultatele finale există deja. Nu refacem fetch-ul.")
        return load_json(path, {})

    # 2️⃣ Altfel îl căutăm pe web
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
        print("❌ Nu s-au găsit rezultate. Revin la fișier dacă există.")
        return load_json(path, {})

    values = list(data.values())

    # Dacă sunt voturi brute → transformăm în procente
    if any(v > 100 for v in values):
        total = sum(values)
        data = {k: round(v / total * 100, 2) for k, v in data.items()}
        print("📌 Rezultatele au fost convertite automat în procente.")

    save_json(path, data)
    print("✔ Rezultatele PMB au fost salvate în data/results_buc.json")

    return data


# =====================================================
# FETCH LATEST POLLS
# =====================================================

def fetch_latest_polls_bucuresti(max_polls: int = 10) -> List[Dict[str, Any]]:
    prompt = """
    Caută pe web cele mai recente sondaje pentru Primăria Municipiului București 2024 (alegerile din iunie 2024).

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

    if isinstance(data, dict):  # dacă întoarce un singur sondaj
        data = [data]

    target_candidates = {"Nicușor Dan", "Gabriela Firea", "Cristian Popescu Piedone"}
    filtered: List[Dict[str, Any]] = []

    for p in data:
        try:
            poll_date = date.fromisoformat(p.get("data", "1900-01-01"))
        except Exception:
            continue

        # folosim strict anul 2024 pentru alegerile PMB 2024
        if poll_date.year != 2024:
            continue

        procentaje = p.get("procentaje", {}) or {}

        # trebuie să aibă cel puțin unul dintre candidații PMB 2024
        if not any(c in procentaje for c in target_candidates):
            continue

        filtered.append(p)

    print(f"✔ Am găsit {len(filtered)} sondaje noi valide pentru PMB 2024")
    return filtered[:max_polls]


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
# MAIN
# =====================================================

def main():
    print("\n==============================")
    print("      AGENT — FULL AUTO 🤖")
    print("==============================")

    print("\n1️⃣  Fetch rezultate PMB 2024...")
    fetch_final_election_results()

    print("\n2️⃣  Fetch + merge sondaje PMB 2024...")
    update_polls_json()

    print("\n==============================")
    print("       ✔ AGENT FINALIZAT")
    print("==============================\n")


if __name__ == "__main__":
    main()
