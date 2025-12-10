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
# -----------------------------

def calculeaza_media_candidat(
    sondaje: List[Poll],
    candidat: str,
    accuracy_db: Dict[str, Dict[str, float]],
    max_age_days: int = 45,
    lambda_time_decay: float = 0.05,
    azi: date | None = None,
) -> Dict[str, Any]:
    """
    Calculează media ponderată a sondajelor pentru un candidat,
    incluzând bonus pentru institute, time-decay și mărimea eșantionului.
    """

    if azi is None:
        azi = date.today()

    valori = []
    greutati = []
    marje = []
    sondaje_folosite = []

    for s in sondaje:
        # 1. Elimină sondajele expirate
        age_days = (azi - s.data).days
        if age_days > max_age_days:
            continue

        # 2. Ignoră sondajele care nu conțin candidatul
        if candidat not in s.procentaje:
            continue

        # 3. Time-decay (sondajele noi contează mai mult)
        weight_time = exp(-lambda_time_decay * age_days)

        # 4. Greutate după mărimea eșantionului
        weight_sample = sqrt(max(s.esantion, 1))

        # 5. Bonus institut
        bonus = accuracy_db.get(s.institut, {}).get("bonus_greutate", 1.0)

        # 6. Greutatea finală
        w = weight_time * weight_sample * bonus

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
            "bonus_institut": bonus,
            "greutate_finala": w
        })

    if not valori:
        return {
            "candidat": candidat,
            "media": None,
            "marja_eroare": None,
            "mesaj": "Nu există sondaje valide pentru acest candidat.",
            "sondaje_folosite": []
        }

    # MEDIA PONDERATĂ
    media = sum(v * w for v, w in zip(valori, greutati)) / sum(greutati)

    # CALCULEAZĂ MARJA DE EROARE AGREGATĂ
    # Convertim MOE individuală în abatere standard
    ses = [(moe / 1.96) for moe in marje]

    se_agregat = sqrt(
        sum((w ** 2) * (se ** 2) for w, se in zip(greutati, ses))
        / (sum(greutati) ** 2)
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
            "lambda_time_decay": lambda_time_decay
        }
    }
