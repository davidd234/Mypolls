import subprocess
import sys
import time


def run_script(name, file):
    print(f"\n==============================")
    print(f"▶ RULARE: {name}")
    print(f"==============================\n")

    result = subprocess.run([sys.executable, file])

    print("\n--- FINALIZAT ---\n")
    time.sleep(1)

    return result.returncode


def main():
    print("\n=======================================")
    print("   SISTEM COMPLET MY POLLS – FULL ML ")
    print("=======================================\n")

    # 1️⃣ Agent AI – fetch rezultate + sondaje
    code = run_script("AGENT (agent_update.py)", "agent_update.py")
    if code != 0:
        print("❌ Agentul a eșuat. Oprim execuția.")
        return

    # 2️⃣ Train ML
    code = run_script("ML TRAIN (ml_train.py)", "ml_train.py")
    if code != 0:
        print("❌ ML train a eșuat. Oprim execuția.")
        return

    # 3️⃣ Predict ML + snapshot
    code = run_script("ML PREDICT (ml_predict.py)", "ml_predict.py")
    if code != 0:
        print("❌ ML predict a eșuat.")
        return

    print("\n=======================================")
    print("       ✔ FULL ML PIPELINE GATA")
    print("=======================================\n")


if __name__ == "__main__":
    main()
