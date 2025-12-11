from datetime import datetime
from pathlib import Path
import json

from ml_core import predict_aggregated, RESULTS_PATH, ROOT


# putem reutiliza exact formatul din main.py (save_run_snapshot):contentReference[oaicite:3]{index=3}
def save_run_snapshot(estimate, results_real, history_dir="data/history"):
    history_path = Path(ROOT / history_dir)
    history_path.mkdir(parents=True, exist_ok=True)

    top_est = sorted(
        {k: v for k, v in estimate.items() if v is not None}.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    top_real = sorted(results_real.items(), key=lambda x: x[1], reverse=True)

    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "top_3_agregare": [
            {"candidat": name, "procent": val} for name, val in top_est[:3]
        ],
        "top_3_rezultate_finale": [
            {"candidat": name, "procent": val} for name, val in top_real[:3]
        ],
        "estimari_complete": estimate,
        "rezultate_complete": results_real,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = history_path / f"rezultate_{timestamp}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"📁 Rezultatele au fost salvate în {file_path}")
    return top_est, top_real


def main():
    print("\n==============================")
    print("      ML PREDICT PIPELINE")
    print("==============================\n")

    estimari = predict_aggregated(verbose=True)
    rezultate_reale = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    print("\n===== COMPARAȚIE CU REZULTATE REALE =====")
    for cand, real in rezultate_reale.items():
        est = estimari.get(cand)
        if est is None:
            print(f"{cand}: estimare N/A, real {real:.2f}%")
        else:
            diff = est - real
            print(f"{cand}: est {est:.2f}% vs real {real:.2f}% (diferență {diff:+.2f}p)")

    save_run_snapshot(estimari, rezultate_reale)

    print("\n==============================")
    print("   ✔ PREDICȚIE ML FINALIZATĂ")
    print("==============================\n")


if __name__ == "__main__":
    main()
