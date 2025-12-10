import subprocess
import sys
import time


def run_script(name, file):
    print(f"\n==============================")
    print(f"▶ RULARE: {name}")
    print(f"==============================\n")

    result = subprocess.run([sys.executable, file])

    print("\n--- FINALIZAT ---\n")
    time.sleep(1)  # doar ca să fie outputul mai elegant

    return result.returncode


def main():

    print("\n=======================================")
    print("     SISTEM COMPLET MY POLLS – RUN ALL ")
    print("=======================================\n")

    # 1️⃣ RULĂM AGENTUL AI
    code = run_script("AGENT (agent_update.py)", "agent_update.py")
    if code != 0:
        print("❌ Agentul a eșuat. Oprim execuția.")
        return

    # 2️⃣ RULĂM AGREGATORUL
    code = run_script("AGREGATOR (main.py)", "main.py")
    if code != 0:
        print("❌ Agregatorul a eșuat.")
        return

    print("\n=======================================")
    print("          TOTUL A FOST RULAT!")
    print("=======================================\n")


if __name__ == "__main__":
    main()
