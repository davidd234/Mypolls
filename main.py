import json
from datetime import date
from poll_aggregator import Poll, calculeaza_media_candidat


def load_polls(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    polls = []
    for item in data:
        polls.append(
            Poll(
                institut=item["institut"],
                data=date.fromisoformat(item["data"]),
                esantion=item["esantion"],
                metoda=item["metoda"],
                procentaje=item["procentaje"],
                marja_eroare=item["marja_eroare"],
            )
        )
    return polls


def load_accuracy_db(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_demo():
    sondaje = load_polls("data/polls_buc.json")
    accuracy_db = load_accuracy_db("data/accuracy_institutes.json")

    azi = date(2024, 6, 1)

    for candidat in ["Nicușor Dan", "Gabriela Firea", "Cristian Popescu Piedone"]:
        rezultat = calculeaza_media_candidat(
            sondaje,
            candidat=candidat,
            accuracy_db=accuracy_db,
            max_age_days=40,
            lambda_time_decay=0.04,
            azi=azi
        )

        print("\n----------------------------")
        print("Candidat:", candidat)
        print("Estimare agregată:", f"{rezultat['media']:.2f}%")
        print("Marja de eroare:", f"±{rezultat['marja_eroare']:.2f}%")
        print("Sondaje folosite:", rezultat['numar_sondaje'])
        print("----------------------------")

    print("\nRezultate reale (pentru comparație):")
    print("Nicușor Dan        47.2%")
    print("Gabriela Firea     22.3%")
    print("Piedone            27.1%")


if __name__ == "__main__":
    run_demo()
