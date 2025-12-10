import json
from datetime import date
from poll_aggregator import Poll, calculeaza_media_candidat


def load_polls(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        Poll(
            institut=item["institut"],
            data=date.fromisoformat(item["data"]),
            esantion=item["esantion"],
            metoda=item["metoda"],
            procentaje=item["procentaje"],
            marja_eroare=item["marja_eroare"],
        )
        for item in data
    ]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_demo():
    sondaje = load_polls("data/polls_buc.json")
    accuracy_db = load_json("data/accuracy_institutes.json")
    results_real = load_json("data/results_buc.json")

    azi = date(2024, 6, 1)

    estimate = {}

    for candidat in ["Nicușor Dan", "Gabriela Firea", "Cristian Popescu Piedone"]:
        rezultat = calculeaza_media_candidat(
            sondaje,
            candidat=candidat,
            accuracy_db=accuracy_db,
            max_age_days=40,
            lambda_time_decay=0.04,
            azi=azi
        )

        estimate[candidat] = rezultat["media"]

        print("\n----------------------------")
        print("Candidat:", candidat)
        print("Estimare agregată:", f"{rezultat['media']:.2f}%")
        print("Marja de eroare:", f"±{rezultat['marja_eroare']:.2f}%")
        print("Sondaje folosite:", rezultat['numar_sondaje'])
        print("----------------------------")

    # 🔥 TOP 3 ESTIMĂRI
    print("\n===== TOP 3 AGREGARE =====")
    top_est = sorted(estimate.items(), key=lambda x: x[1], reverse=True)
    for i, (name, val) in enumerate(top_est, 1):
        print(f"{i}. {name} — {val:.2f}%")

    # 🔥 TOP 3 REZULTATE REALE
    print("\n===== TOP 3 REZULTATE FINALE =====")
    top_real = sorted(results_real.items(), key=lambda x: x[1], reverse=True)
    for i, (name, val) in enumerate(top_real, 1):
        print(f"{i}. {name} — {val:.2f}%")


if __name__ == "__main__":
    run_demo()
