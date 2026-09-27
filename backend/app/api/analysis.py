"""Routes API du DIAGNOSTIC — analyse par règles.

- GET /api/v1/tests/{test_id}/analysis
    Applique les règles du package « diagnostic_rules/ » (modules
    courant / isolement / température + règles préparées) aux mesures
    du test et renvoie le rapport détaillé : pour chaque paramètre,
    valeur mesurée, référence, évaluation, interprétation, risque et
    recommandation éventuels.

La page Analyse (frontend) AFFICHE ce rapport. Aucune décision
automatique n'est prise ici : le technicien garde la main (§14).
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.test import Test
from app.repositories.sql.sample_repository import SampleRepository
from app.services.diagnostic_engine import evaluate_test_full

router = APIRouter(prefix="/tests", tags=["Diagnostic"])


@router.get("/{test_id}/analysis")
def analyse_test(test_id: str) -> dict:
    """Rapport de diagnostic d'un test : règles appliquées aux mesures,
    puis analyse environnementale (hypothèses de causes possibles)."""
    db = SessionLocal()
    try:
        row = db.scalar(select(Test).where(Test.test_id == test_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
        samples = SampleRepository(db).list_for_test(row.id)
        return evaluate_test_full(row, samples)
    finally:
        db.close()
