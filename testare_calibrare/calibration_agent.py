import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Any

HISTORY_DIR = Path("data/history")
POLLS_PATH = Path("data/polls_buc.json")
ACCURACY_PATH = Path("data/accuracy_institutes.json")


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_history() -> Dict[str, Any]:
    if not HISTORY_DIR.exists():
        raise FileNotFoundError("Nu există niciun istoric de rulări în data/history.")

    run_files: List[Path] = sorted(
        HISTORY_DIR.glob("rezultate_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not run_files:
        raise FileNotFoundError("Nu am găsit fișiere de istoric în data/history.")

    latest_file = run_files[0]
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📂 Folosesc ultimul snapshot: {latest_file}")
    return data


def compute_institute_bonuses(
    final_results: Dict[str, float],
    election_date: date,
    max_age_days: int = 40,
    learning_rate: float = 0.3,
) -> Dict[str, Dict[str, Any]]:
    """
    Calibrează bonusurile de acuratețe pe baza ultimului snapshot:
    - ține cont DOAR de sondajele dinainte de alegeri (până la max_age_days)
    - calculează eroare globală per institut
    - calculează eroare per candidat per institut
    - aplică un learning rate peste bonusurile vechi (nu sare brusc)
    """

    polls = load_json(POLLS_PATH, [])
    if not polls:
        raise ValueError("Lipsește fișierul cu sondaje sau este gol.")

    # Erori globale și per candidat
    errors_global: Dict[str, List[float]] = defaultdict(list)
    errors_per_cand: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    for poll in polls:
        try:
            poll_date = date.fromisoformat(poll.get("data", "1900-01-01"))
        except Exception:
            continue

        # distanța dintre ALEGERI și sondaj
        age_days = (election_date - poll_date).days

        # ignorăm sondajele din viitor sau cu prea mult timp înainte de alegeri
        if age_days < 0 or age_days > max_age_days:
            continue

        institute = poll.get("institut", "necunoscut")
        procentaje = poll.get("procentaje", {}) or {}

        for candidate, real_value in final_results.items():
            polled_value = procentaje.get(candidate)
            if polled_value is None:
                continue
            diff = abs(polled_value - real_value)
            errors_global[institute].append(diff)
            errors_per_cand[institute][candidate].append(diff)

    if not any(errors_global.values()):
        raise ValueError("Nu am putut calcula erori pe baza sondajelor existente (după filtre).")

    # Erori medii globale
    mean_global_errors: Dict[str, float] = {
        inst: (sum(vals) / len(vals))
        for inst, vals in errors_global.items()
        if vals
    }

    max_err_global = max(mean_global_errors.values()) if mean_global_errors else 1.0

    # Erori medii per candidat
    mean_cand_errors: Dict[str, Dict[str, float]] = {}
    for inst, cand_dict in errors_per_cand.items():
        mean_cand_errors[inst] = {}
        for cand, vals in cand_dict.items():
            if not vals:
                continue
            mean_cand_errors[inst][cand] = sum(vals) / len(vals)

    # Încărcăm bonusurile anterioare pentru learning rate
    previous = load_json(ACCURACY_PATH, {})

    bonuses: Dict[str, Dict[str, Any]] = {}

    def clamp_bonus(x: float) -> float:
        # ținem bonusul într-un interval rezonabil
        return max(0.7, min(1.3, x))

    for inst, mean_err in mean_global_errors.items():
        # bonus brut pe baza erorii globale
        raw_global_bonus = 1.2 - 0.3 * (mean_err / max_err_global if max_err_global else 0.0)

        prev_inst = previous.get(inst, {}) or {}
        prev_global_bonus = prev_inst.get("bonus_greutate", 1.0)
        prev_global_err = prev_inst.get("eroare_medie", mean_err)

        # aplicăm learning rate
        new_global_bonus = (1.0 - learning_rate) * prev_global_bonus + learning_rate * raw_global_bonus
        new_global_err = (1.0 - learning_rate) * prev_global_err + learning_rate * mean_err

        new_global_bonus = clamp_bonus(new_global_bonus)

        cand_block: Dict[str, Any] = {}
        inst_cand_errs = mean_cand_errors.get(inst, {})

        prev_cand_block = prev_inst.get("cand", {}) or {}

        for cand, mean_err_cand in inst_cand_errs.items():
            raw_cand_bonus = 1.2 - 0.3 * (mean_err_cand / max_err_global if max_err_global else 0.0)

            prev_cand_info = prev_cand_block.get(cand, {}) or {}
            prev_cand_bonus = prev_cand_info.get("bonus_greutate", prev_global_bonus)
            prev_cand_err = prev_cand_info.get("eroare_medie", mean_err_cand)

            new_cand_bonus = (1.0 - learning_rate) * prev_cand_bonus + learning_rate * raw_cand_bonus
            new_cand_err = (1.0 - learning_rate) * prev_cand_err + learning_rate * mean_err_cand

            new_cand_bonus = clamp_bonus(new_cand_bonus)

            cand_block[cand] = {
                "bonus_greutate": round(new_cand_bonus, 3),
                "eroare_medie": round(new_cand_err, 3),
            }

        bonuses[inst] = {
            "bonus_greutate": round(new_global_bonus, 3),
            "eroare_medie": round(new_global_err, 3),
        }
        if cand_block:
            bonuses[inst]["cand"] = cand_block

    return bonuses


def save_accuracy(bonuses: Dict[str, Dict[str, Any]]):
    ACCURACY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ACCURACY_PATH, "w", encoding="utf-8") as f:
        json.dump(bonuses, f, ensure_ascii=False, indent=2)
    print(f"✔ Bonusurile recalibrate au fost salvate în {ACCURACY_PATH}")


def calibrate_from_latest_snapshot():
    snapshot = load_latest_history()
    final_results = snapshot.get("rezultate_complete") or {}
    if not final_results:
        raise ValueError("Snapshot-ul nu conține rezultate finale pentru calibrare.")

    # PMB 2024 — data alegerilor
    election_date = date(2024, 6, 9)
    bonuses = compute_institute_bonuses(
        final_results=final_results,
        election_date=election_date,
        max_age_days=40,      # exact fereastra folosită și de agregator
        learning_rate=0.3,    # învață treptat
    )
    save_accuracy(bonuses)

    print("\n==============================")
    print("  AGENT DE CALIBRARE FINALIZAT")
    print("==============================\n")


if __name__ == "__main__":
    calibrate_from_latest_snapshot()
