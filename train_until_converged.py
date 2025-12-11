import subprocess
import sys
import time
import json
from pathlib import Path

HISTORY_DIR = Path("data/history")
RESULTS_PATH = Path("data/results_buc.json")

TOLERANTA = 3.0  # ±3%
MAX_ITERATII = 50  # ca să nu intre în buclă infinită accidental


def load_latest_snapshot():
    """Încarcă ultimul fișier rezultate_*.json din istoricul agregatorului."""
    files = sorted(HISTORY_DIR.glob("rezultate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("Nu există snapshot-uri în data/history!")
    with open(files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def ruleaza(script):
    """Rulează un script Python."""
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"❌ Scriptul {script} a eșuat. Oprire...")
        sys.exit(1)


def diferenta_maxima(estimari, rezultate):
    """Calculează diferența maximă absolută între estimări și rezultate reale."""
    diffs = []
    for cand in rezultate:
        if cand not in estimari:
            continue
        diffs.append(abs(estimari[cand] - rezultate[cand]))
    return max(diffs) if diffs else 999


def main():

    rezultate_reale = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    print("📌 Rezultatele reale PMB:", rezultate_reale)

    for i in range(1, MAX_ITERATII + 1):

        print(f"\n==============================")
        print(f"   ITERAȚIA #{i}")
        print(f"==============================")

        # 1️⃣ Fetch sondaje + rezultate (nu mai rescrie rezultatele finale)
        ruleaza("agent_update.py")

        # 2️⃣ Agregatorul calculează estimări + snapshot
        ruleaza("main.py")

        # 3️⃣ Calibration agent ajustează bonusurile
        ruleaza("testare_calibrare/calibration_agent.py")

        # 4️⃣ Luăm ultimul snapshot
        snapshot = load_latest_snapshot()
        estimari = snapshot.get("estimari_complete", {})

        print("🔍 Estimări curente:", estimari)

        diff = diferenta_maxima(estimari, rezultate_reale)

        print(f"📉 Diferența maximă față de rezultate reale: {diff:.2f}%")

        if diff <= TOLERANTA:
            print("\n🎉 MODELUL A AJUNS ÎN TOLERANȚA CERUTĂ!")
            print("✔ Sistem convergent ✔")
            return

        time.sleep(1)

    print("\n⚠️ A fost atins numărul maxim de iterații fără convergență.")


if __name__ == "__main__":
    main()
