import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Any

# ----------------------------
# DETECTARE ROOT PROIECT (universală)
# ----------------------------
THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE

# urcăm în sus până găsim folderul "data"
while ROOT != ROOT.parent:
    if (ROOT / "data").exists():
        break
    ROOT = ROOT.parent

if not (ROOT / "data").exists():
    raise FileNotFoundError("❌ Nu am putut găsi folderul 'data' în niciun director părinte.")

# acum toate path-urile sunt 100% corecte, indiferent unde rulează scriptul
HISTORY_DIR = ROOT / "data" / "history"
POLLS_PATH = ROOT / "data" / "polls_buc.json"
ACCURACY_PATH = ROOT / "data" / "accuracy_institutes.json"

print(f"📁 ROOT detectat: {ROOT}")
print(f"📁 HISTORY_DIR: {HISTORY_DIR}")

# ----------------------------
# NORMALIZARE INSTITUTE (FULL)
# ----------------------------
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

def normalize_institute(name: str) -> str:
    """Normalizează numele tuturor institutele pentru consistență."""
    if not isinstance(name, str):
        return "necunoscut"
    return INSTITUTE_NORMALIZATION.get(name.strip(), name.strip())


# ----------------------------
# LOADING UTILITIES
# ----------------------------
def load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ EROARE la citirea {path}: {e}")
    return default


def load_latest_history() -> Dict[str, Any]:
    """Încarcă ultimul snapshot din data/history"""
    if not HISTORY_DIR.exists():
        raise FileNotFoundError("❌ Nu există directorul data/history.")

    run_files = sorted(
        HISTORY_DIR.glob("rezultate_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not run_files:
        raise FileNotFoundError("❌ Nu există fișiere de tip rezultate_*.json în history.")

    latest = run_files[0]
    print(f"📂 Folosesc snapshotul: {latest.name}")

    return load_json(latest, {})


# ----------------------------
# CALCUL BONUSURI
# ----------------------------
def compute_institute_bonuses(
    final_results: Dict[str, float],
    election_date: date,
    max_age_days: int = 40,
    learning_rate_bonus: float = 0.3,
    learning_rate_coef_global: float = 0.7,
    learning_rate_coef_cand: float = 0.7,
) -> Dict[str, Dict[str, Any]]:

    # încărcăm sondaje brute
    polls = load_json(POLLS_PATH, [])
    previous = load_json(ACCURACY_PATH, {})

    if not polls:
        raise ValueError("❌ polls_buc.json este gol sau nu există.")

    # colectoare de erori
    errors_global = defaultdict(list)
    errors_per_cand = defaultdict(lambda: defaultdict(list))
    ratios_global = defaultdict(list)
    ratios_per_cand = defaultdict(lambda: defaultdict(list))

    # pondere institut vs candidat
    GAMMA_INST_COEF = 0.7
    GAMMA_CAND_COEF = 0.3

    # procesăm fiecare sondaj
    for poll in polls:

        # validare minimă
        if "institut" not in poll or "procentaje" not in poll or "data" not in poll:
            print("⚠️ Sondaj corupt ignorat:", poll)
            continue

        # normalizare nume institut
        inst = normalize_institute(poll["institut"])
        procentaje = poll.get("procentaje", {})

        # validare dată
        try:
            poll_date = date.fromisoformat(poll["data"])
        except:
            print(f"⚠️ Dată invalidă în sondaj: {poll}")
            continue

        # ignorăm sondaje în afara ferestrei
        age_days = (election_date - poll_date).days
        if age_days < 0 or age_days > max_age_days:
            continue

        # coeficienții anteriori
        prev_inst = previous.get(inst, {})
        prev_global_coef = float(prev_inst.get("coeficient_procente", 1.0))
        prev_cand_block = prev_inst.get("cand", {}) or {}

        # analizăm fiecare candidat
        for cand, real in final_results.items():

            if cand not in procentaje:
                continue
            raw = procentaje[cand]

            prev_cand_info = prev_cand_block.get(cand, {})
            prev_cand_coef = float(prev_cand_info.get("coeficient_procente", 1.0))

            # coeficient efectiv folosit în iteratia anterioară
            effective_coef = (prev_global_coef**GAMMA_INST_COEF) * (prev_cand_coef**GAMMA_CAND_COEF)
            adjusted = raw * effective_coef

            # erori
            diff = abs(adjusted - real)
            errors_global[inst].append(diff)
            errors_per_cand[inst][cand].append(diff)

            # raport real/ajustat
            if adjusted > 0:
                ratios_global[inst].append(real / adjusted)
                ratios_per_cand[inst][cand].append(real / adjusted)

    # dacă nu există erori — nu putem calibra
    if not any(errors_global.values()):
        raise ValueError("❌ Nu am putut calcula erori. Probabil nu sunt sondaje valide.")

    # ----------------------
    # Calcule errori & ratio
    # ----------------------
    mean_global_err = {inst: sum(v)/len(v) for inst, v in errors_global.items()}
    max_err = max(mean_global_err.values())

    mean_cand_err = {
        inst: {cand: sum(vals)/len(vals) for cand, vals in cand_dict.items()}
        for inst, cand_dict in errors_per_cand.items()
    }

    mean_ratio_global = {
        inst: sum(v)/len(v) for inst, v in ratios_global.items()
    }

    mean_ratio_cand = {
        inst: {cand: sum(vv)/len(vv) for cand, vv in ratios_per_cand[inst].items()}
        for inst in ratios_per_cand
    }

    # ----------------------
    # CLAMP-uri ultra-robuste
    # ----------------------
    def clamp_bonus(x): return max(0.7, min(1.3, x))
    def clamp_global(x): return max(0.6, min(1.4, x))
    def clamp_cand(x):   return max(0.5, min(1.6, x))

    # ----------------------
    # Generăm noul accuracy_institutes
    # ----------------------
    bonuses = {}

    for inst, err_inst in mean_global_err.items():

        prev_inst = previous.get(inst, {})

        # bonus greutate global
        raw_bonus_g = 1.2 - 0.3 * (err_inst / max_err)
        new_bonus_g = (
            (1-learning_rate_bonus) * float(prev_inst.get("bonus_greutate", 1.0))
            + learning_rate_bonus * raw_bonus_g
        )
        new_bonus_g = clamp_bonus(new_bonus_g)

        # coeficient global procente
        ratio_g = mean_ratio_global.get(inst, 1.0)
        prev_coef_g = float(prev_inst.get("coeficient_procente", 1.0))
        raw_coef_g = prev_coef_g * ratio_g
        new_coef_g = (1-learning_rate_coef_global)*prev_coef_g + learning_rate_coef_global*raw_coef_g
        new_coef_g = clamp_global(new_coef_g)

        # PREGĂTIM blocul de candidați
        cand_block = {}
        prev_cand_block = prev_inst.get("cand", {})

        for cand, err_c in mean_cand_err.get(inst, {}).items():
            # bonus candidat
            raw_bonus_c = 1.2 - 0.3 * (err_c / max_err)
            prev_bonus_c = float(prev_cand_block.get(cand, {}).get("bonus_greutate", new_bonus_g))
            new_bonus_c = (1-learning_rate_bonus)*prev_bonus_c + learning_rate_bonus*raw_bonus_c
            new_bonus_c = clamp_bonus(new_bonus_c)

            # coeficient candidat
            prev_coef_c = float(prev_cand_block.get(cand, {}).get("coeficient_procente", 1.0))
            ratio_c = mean_ratio_cand.get(inst, {}).get(cand, 1.0)
            raw_coef_c = prev_coef_c * ratio_c
            new_coef_c = (1-learning_rate_coef_cand)*prev_coef_c + learning_rate_coef_cand*raw_coef_c
            new_coef_c = clamp_cand(new_coef_c)

            cand_block[cand] = {
                "bonus_greutate": round(new_bonus_c,3),
                "eroare_medie": round(err_c,3),
                "coeficient_procente": round(new_coef_c,4)
            }

        # salvăm institutul
        bonuses[inst] = {
            "bonus_greutate": round(new_bonus_g,3),
            "eroare_medie": round(err_inst,3),
            "coeficient_procente": round(new_coef_g,4)
        }
        if cand_block:
            bonuses[inst]["cand"] = cand_block

    return bonuses


# ----------------------------
# SALVARE CU NORMALIZARE FINALĂ
# ----------------------------
def save_accuracy(bonuses: Dict[str, Dict[str, Any]]):

    merged = {}

    # combinăm institute duplicate după normalizare
    for raw_inst, data in bonuses.items():
        inst = normalize_institute(raw_inst)

        if inst not in merged:
            merged[inst] = data
        else:
            # media bonusurilor dacă existau dubluri
            merged[inst]["bonus_greutate"] = round(
                (merged[inst]["bonus_greutate"] + data["bonus_greutate"]) / 2, 3
            )
            merged[inst]["eroare_medie"] = round(
                (merged[inst]["eroare_medie"] + data["eroare_medie"]) / 2, 3
            )
            merged[inst]["coeficient_procente"] = round(
                (merged[inst]["coeficient_procente"] + data["coeficient_procente"]) / 2, 4
            )

    ACCURACY_PATH.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("✔ accuracy_institutes.json salvat (normalizat + curățat)")


# ----------------------------
# RUN
# ----------------------------
def calibrate_from_latest_snapshot():
    snapshot = load_latest_history()
    final_results = snapshot.get("rezultate_complete")

    if not final_results:
        raise ValueError("❌ Snapshot-ul nu are câmpul 'rezultate_complete'.")

    bonuses = compute_institute_bonuses(
        final_results=final_results,
        election_date=date(2024,6,9),
        max_age_days=40
    )
    save_accuracy(bonuses)

    print("\n==============================")
    print("  ✔ AGENTUL DE CALIBRARE A RULAT CU SUCCES")
    print("==============================\n")


if __name__ == "__main__":
    calibrate_from_latest_snapshot()
