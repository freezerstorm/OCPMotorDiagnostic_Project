"""Jeu de données de DÉMONSTRATION — 100 % FICTIF, étiqueté « démo ».

Recrée : 4 moteurs fictifs (M-1042, M-0871, M-2001, M-5000) et 6 tests
(4 manuels + T-0005 automatique brouillon + T-0006 automatique terminé
avec 24 échantillons synthétiques déterministes).

ATTENTION : efface TOUTES les données existantes (TRUNCATE).
Usage (depuis backend/) :  python tools/seed_demo.py

Cohérence avec la seule règle définie (courant à vide entre ⅓ et ⅔ In) :
- T-0001, T-0002, T-0004 : courant DANS la plage  → contrôles « pass » ;
- T-0003 : courant volontairement HORS plage (et isolement dégradé)
  → défaut cohérent avec la décision « envoyé en réparation » ;
- T-0006 : série du kit volontairement absurde (≈ 27,9 A pour un In de
  3,5 A) → servira d'exemple d'ANOMALIE détectée par le moteur.
"""

import math
import random
import sys
from pathlib import Path

# Permet de lancer « python tools/seed_demo.py » depuis backend/
# (ajoute le dossier backend/ au chemin de recherche des modules).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.motor import Motor  # noqa: E402
from app.models.sample import AcquisitionSample  # noqa: E402
from app.models.test import Measurements, Test  # noqa: E402
from sqlalchemy import text  # noqa: E402

db = SessionLocal()

# --- Nettoyage complet ---
db.execute(text("TRUNCATE acquisition_samples, measurements, tests, motors RESTART IDENTITY CASCADE"))
db.execute(text("SELECT setval('test_id_seq', 1, false)"))
db.commit()

# --- Moteurs fictifs (plaques plausibles, données démo) ---
motors = [
    dict(motor_id="M-1042", designation="Pompe eau process (démo)", brand="SEG", model="92X2-2",
         rated_power_kw=45.0, rated_voltage_v=380.0, rated_current_a=78.0, rated_speed_rpm=2900,
         coupling="direct", service="Laverie / Lavage / Décantation"),
    dict(motor_id="M-0871", designation="Convoyeur A (démo)", brand="ABB", model="M3BP 160",
         rated_power_kw=15.0, rated_voltage_v=380.0, rated_current_a=29.0, rated_speed_rpm=1465,
         coupling="courroie", service="Concassage / Criblage"),
    dict(motor_id="M-2001", designation="Compresseur atelier (démo)", brand="Leroy-Somer", model="LS 225",
         rated_power_kw=55.0, rated_voltage_v=380.0, rated_current_a=100.0, rated_speed_rpm=1470,
         coupling="direct", service="Sécherie / Fours rotatifs"),
    dict(motor_id="M-5000", designation="Moteur ventilateur atelier (démo auto)", brand="SEG", model="90L-4",
         rated_power_kw=1.5, rated_voltage_v=380.0, rated_current_a=3.5, rated_speed_rpm=1400,
         coupling="direct", service="Parc de stockage et reprise"),
]
for m in motors:
    db.add(Motor(**m))
db.commit()

# --- Fiches manuelles de démonstration ---
def add_manual(test_id, motor_id, status, decision, observation, iso, r, cur, vib, voltage,
               continuity=True, temp_de=None, temp_nde=None):
    t = Test(test_id=test_id, mode="manual", status=status, decision=decision,
             observation=observation, motor_id=motor_id)
    db.add(t)
    db.flush()
    db.add(Measurements(
        test_id=t.id,
        insulation_test_voltage_v=voltage,
        ph1_ph2_mohm=iso[0], ph2_ph3_mohm=iso[1], ph3_ph1_mohm=iso[2],
        ph1_ground_mohm=iso[3], ph2_ground_mohm=iso[4], ph3_ground_mohm=iso[5],
        r12_ohm=r[0], r23_ohm=r[1], r31_ohm=r[2],
        # É16 : continuité globale + températures paliers (règle < 70 °C)
        continuity_ok=continuity,
        temp_bearing_de_c=temp_de, temp_bearing_nde_c=temp_nde,
        current_a=cur, vibration_mm_s=vib,
    ))

# T-0001 : moteur sain — courant 41,0 A = 0,53 In → dans la plage à vide (26–52 A)
# Isolement : Vtest 1000 V → Rmin 1 MΩ ; toutes les mesures ≥ 138 MΩ → conforme
add_manual("T-0001", "M-1042", "completed", "serviced",
           "RAS — remis en service (démo)",
           [145.0, 138.0, 141.0, 310.0, 298.0, 305.0],
           [0.152, 0.152, 0.152], 41.0, 1.6, 1000,
           temp_de=48.5, temp_nde=51.2)
# T-0002 : entretien — courant 15,8 A = 0,55 In → dans la plage à vide (9,7–19,3 A)
# Isolement : Vtest 500 V → Rmin 0,5 MΩ ; mesures ≥ 88 MΩ → conforme
add_manual("T-0002", "M-0871", "completed", "serviced",
           "Nettoyage + resserrage des connexions du bornier (démo)",
           [88.0, 92.0, 90.0, 190.0, 185.0, 188.0],
           [0.61, 0.61, 0.61], 15.8, 2.4, 500,
           temp_de=55.0, temp_nde=57.3)
# T-0003 : isolement dégradé + courant 108 A hors plage (33–67 A) → réparation
# Isolement : Vtest 5000 V → Rmin 5 MΩ ; phase-phase ≥ 89 MΩ → conforme,
# phase-masse ≤ 1,1 MΩ → PROBLÉMATIQUE (cohérent avec l'observation).
add_manual("T-0003", "M-2001", "archived", "repair",
           "Isolation dégradée (phase-terre) — envoyé atelier (démo)",
           [95.0, 91.0, 89.0, 1.1, 0.9, 1.0],
           [0.088, 0.089, 0.088], 108.0, 5.8, 5000,
           continuity=True, temp_de=84.0, temp_nde=71.5)
# T-0004 : contrôle périodique — courant 40,5 A = 0,52 In → dans la plage
# Isolement : Vtest 1000 V → Rmin 1 MΩ ; mesures ≥ 147 MΩ → conforme
add_manual("T-0004", "M-1042", "completed", "serviced",
           "Contrôle périodique — conforme (démo)",
           [150.0, 147.0, 149.0, 320.0, 315.0, 318.0],
           [0.150, 0.150, 0.150], 40.5, 1.5, 1000,
           temp_de=47.8, temp_nde=49.0)

# T-0005 : test automatique laissé en brouillon (aucune mesure)
db.add(Test(test_id="T-0005", mode="auto", status="draft", motor_id="M-1042"))

# T-0006 : test automatique TERMINÉ avec 24 échantillons (seed déterministe).
# Courant volontairement absurde (≈ 27,9 A pour In = 3,5 A) → anomalie à détecter.
t6 = Test(test_id="T-0006", mode="auto", status="completed", motor_id="M-5000")
db.add(t6)
db.flush()

rng = random.Random(42)
n = 24
for i in range(n):
    t_s = round(0.35 + i * 0.5, 2)          # 0,35 → 11,85 s
    p = i / (n - 1)
    temp = 29.5 + p * (32.21 - 29.5) + rng.uniform(-0.15, 0.15)
    cur = 27.2 + p * (27.91 - 27.2) + rng.uniform(-0.12, 0.12)
    v = 1.28 + p * (1.40 - 1.28) + rng.uniform(-0.03, 0.03)
    x = abs(v / math.sqrt(3) + rng.uniform(-0.02, 0.02))
    y = abs(v / math.sqrt(3) + rng.uniform(-0.02, 0.02))
    z = abs(v / math.sqrt(3) + rng.uniform(-0.02, 0.02))
    if i == n - 1:                           # dernier échantillon = valeurs de référence
        temp, cur = 32.21, 27.91
        x, y, z = 0.808, 0.809, 0.809        # norme ≈ 1,40 mm/s
    db.add(AcquisitionSample(
        test_id=t6.id, t_s=t_s,
        temperature_c=round(temp, 2), current_a=round(cur, 2),
        vib_x_mm_s=round(x, 4), vib_y_mm_s=round(y, 4), vib_z_mm_s=round(z, 4),
        vib_global_mm_s=round(math.sqrt(x * x + y * y + z * z), 4),
    ))

# Synthèse « instantanée » du test auto = dernières valeurs reçues
db.add(Measurements(test_id=t6.id, temperature_c=32.21, current_a=27.91,
                    vibration_mm_s=None))

db.execute(text("SELECT setval('test_id_seq', 6, true)"))
db.commit()

print("Motors :", db.scalar(text("SELECT count(*) FROM motors")))
print("Tests  :", db.scalar(text("SELECT count(*) FROM tests")))
print("Samples:", db.scalar(text("SELECT count(*) FROM acquisition_samples")))
print("T-0006 :", db.execute(text(
    "SELECT test_id, mode, status FROM tests WHERE test_id='T-0006'")).fetchone())
db.close()
print("SEED OK")
