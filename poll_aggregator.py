from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from math import exp, sqrt
from typing import Dict, List, Any


# -----------------------------
# 1. MODELUL DE DATE PENTRU SONDAJE
# -----------------------------

@dataclass
class Poll:
    institut: str
    data: date
    esantion: int
    metoda: str
    procentaje: Dict[str, float]
    marja_eroare: float


# -----------------------------
# 2. FUNCȚIA DE AGREGARE COMPLETĂ
#    - time-decay
#    - mărimea eșantionului
#    - bonus per institut + per candidat
#    - penalizare pe baza erorii medii
#    - ignoră sondajele din viitor
# -----------------------------

def calculeaza_media_candidat(
    sondaje: List[Poll],
    candidat: str,
    accuracy_db: Dict[str, Dict[str, Any]],
    max_age_days: int = 45,
    lambda_time_decay: float = 0.05,
    azi: date | None = None,
) -> Dict[str, Any]:

    if azi is None:
        azi = date.today()

    valori: List[float] = []
    greutati: List[float] = []
    marje: List[float] = []
    sondaje_folosite: List[Dict[str, Any]] = []

    for s in sondaje:
        # 1. Calculăm vechimea sondajului față de "azi" (de ex. 2024-06-01)
        age_days = (azi - s.data).days

        # ❗ Ignorăm sondajele din viitor și cele prea vechi
        if age_days < 0:
            continue
        if age_days > max_age_days:
            continue

        # 2. Ignorăm sondajele care nu conțin candidatul
        if candidat not in s.procentaje:
            continue

        # ----------------------------
        # COMPONENTELE GREUTĂȚII
        # ----------------------------

        # A) Time-decay — sondajele mai noi au greutate mai mare
        weight_time = exp(-lambda_time_decay * age_days)

        # B) Mărimea eșantionului — sondajele cu eșantion mare cântăresc mai mult
        weight_sample = sqrt(max(s.esantion, 1))

        # C) Bonus institut + per candidat (din accuracy_institutes.json)
        inst_info = accuracy_db.get(s.institut, {}) or {}

        global_bonus = inst_info.get("bonus_greutate", 1.0)
        global_err = inst_info.get("eroare_medie")

        cand_info = {}
        cand_block = inst_info.get("cand")
        if isinstance(cand_block, dict):
            cand_info = cand_block.get(candidat, {}) or {}

        cand_bonus = cand_info.get("bonus_greutate", global_bonus)
        cand_err = cand_info.get("eroare_medie", global_err)

        # Bonus efectiv = combinăm bonusul global cu cel pe candidat
        bonus_effectiv = global_bonus * cand_bonus

        # D) Penalizare pe baza erorii medii (globală + per candidat)
        erori_pentru_penalizare = [
            e for e in [global_err, cand_err] if isinstance(e, (int, float))
        ]
        if erori_pentru_penalizare:
            eroare_medie_pentru_penalizare = sum(erori_pentru_penalizare) / len(erori_pentru_penalizare)
            penalizare_eroare = 1.0 / (1.0 + eroare_medie_pentru_penalizare)
        else:
            penalizare_eroare = 1.0

        # ----------------------------
        # GREUTATEA FINALĂ
        # ----------------------------
        w = weight_time * weight_sample * bonus_effectiv * penalizare_eroare

        valori.append(s.procentaje[candidat])
        greutati.append(w)
        marje.append(s.marja_eroare)

        sondaje_folosite.append({
            "institut": s.institut,
            "data": s.data.isoformat(),
            "esantion": s.esantion,
            "metoda": s.metoda,
            "procent": s.procentaje[candidat],
            "moe": s.marja_eroare,
            "greutate_time": weight_time,
            "greutate_esantion": weight_sample,
            "bonus_global": global_bonus,
            "eroare_medie_global": global_err,
            "bonus_candidat": cand_bonus,
            "eroare_medie_candidat": cand_err,
            "bonus_effectiv": bonus_effectiv,
            "penalizare_eroare": penalizare_eroare,
            "greutate_finala": w
        })

    # Dacă nu există sondaje valide
    if not valori:
        return {
            "candidat": candidat,
            "media": None,
            "marja_eroare": None,
            "mesaj": "Nu există sondaje valide pentru acest candidat.",
            "sondaje_folosite": []
        }

    # ----------------------------
    # MEDIA PONDERATĂ FINALĂ
    # ----------------------------
    suma_greutati = sum(greutati)
    media = sum(v * w for v, w in zip(valori, greutati)) / suma_greutati

    # ----------------------------
    # CALCUL MOE AGREGATĂ
    # ----------------------------
    ses = [(moe / 1.96) for moe in marje]

    se_agregat = sqrt(
        sum((w ** 2) * (se ** 2) for w, se in zip(greutati, ses))
        / (suma_greutati ** 2)
    )

    moe_agregat = 1.96 * se_agregat

    return {
        "candidat": candidat,
        "media": media,
        "marja_eroare": moe_agregat,
        "numar_sondaje": len(valori),
        "sondaje_folosite": sondaje_folosite,
        "parametri": {
            "max_age_days": max_age_days,
            "lambda_time_decay": lambda_time_decay,
            "azi": azi.isoformat()
        }
    }
