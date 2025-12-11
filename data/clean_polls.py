import json
from pathlib import Path
from datetime import date

# detectăm root-ul proiectului (folderul care conține "data")
THIS = Path(__file__).resolve()
ROOT = THIS.parent.parent
POLL_PATH = ROOT / "data" / "polls_buc.json"

# Institutele normalizate (nume scurt → unic)
INSTITUTE_NORMALIZATION = {
    "CURS": "CURS",
    "Centrul de Sociologie Urbană și Regională (CURS)": "CURS",
    "Centrul de Sociologie Urbană și Regională": "CURS",
    "Centrul de Sociologie Urbana si Regionala (CURS)": "CURS",

    "INSCOP": "INSCOP",
    "Inscop Research": "INSCOP",

    "AtlasIntel": "AtlasIntel",
    "Atlas Intel": "AtlasIntel",

    "Avangarde": "Avangarde",
    "Novel Research": "Novel Research",
    "IPSOS": "IPSOS",
}

# Candidații oficiali PMB 2024
VALID_CANDIDATES = {
    "Nicușor Dan",
    "Gabriela Firea",
    "Cristian Popescu Piedone",
    # Dacă ai și alții în sondaje PMB 2024, îi poți adăuga aici
}


def normalize_inst(name: str) -> str:
    name = name.strip()
    return INSTITUTE_NORMALIZATION.get(name, name)


def load_polls():
    if not POLL_PATH.exists():
        print("❌ polls_buc.json nu există.")
        return []
    return json.loads(POLL_PATH.read_text(encoding="utf-8"))


def save_polls(polls):
    POLL_PATH.write_text(json.dumps(polls, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✔ polls_buc.json a fost curățat și salvat.")


def clean_polls():
    polls = load_polls()
    cleaned = []

    seen = set()

    for poll in polls:
        inst_raw = poll.get("institut", "")
        inst = normalize_inst(inst_raw)

        # EXCLUDERE: sondaje în afara anului 2024
        try:
            poll_date = date.fromisoformat(poll.get("data"))
        except:
            continue

        if poll_date.year != 2024:
            continue

        # EXCLUDERE: duplicate (institut + data)
        key = (inst, poll.get("data"))
        if key in seen:
            continue
        seen.add(key)

        # CURĂȚARE: păstrăm doar candidații PMB 2024
        procentaje = poll.get("procentaje", {})
        procentaje = {k: v for k, v in procentaje.items() if k in VALID_CANDIDATES}

        if not procentaje:
            # sondaj care nu conține PMB 2024 → ignorăm
            continue

        poll["institut"] = inst
        poll["procentaje"] = procentaje
        cleaned.append(poll)

    save_polls(cleaned)
    print(f"✔ Total sondaje păstrate: {len(cleaned)}")


if __name__ == "__main__":
    clean_polls()
