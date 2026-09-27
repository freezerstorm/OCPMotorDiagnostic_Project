"""LANCEUR DES TESTS SIMPLES — Étape 14.

Exécute les trois suites (règles, environnement, cas limites) et
s'arrête à la première en échec. Usage (depuis backend/) :

    python tools/run_tests.py
"""

import subprocess
import sys
from pathlib import Path

SUITES = ["test_rules.py", "test_environment.py", "test_edge_cases.py", "test_registre.py"]
TOOLS = Path(__file__).resolve().parent

for suite in SUITES:
    print(f"\n{'=' * 60}\n>>> {suite}\n{'=' * 60}")
    result = subprocess.run([sys.executable, str(TOOLS / suite)])
    if result.returncode != 0:
        print(f"\nÉCHEC de la suite {suite} — arrêt.")
        sys.exit(result.returncode)

print(f"\nToutes les suites sont passées : {', '.join(SUITES)}")
