"""Route du RAPPORT PDF — Étape 12.

- GET /api/v1/tests/{test_id}/report.pdf
    Construit et renvoie la fiche de diagnostic PDF (téléchargement).
    Même rapport pour les deux modes ; données = base + moteur de règles.
"""

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.test import Test
from app.repositories.sql.sample_repository import SampleRepository
from app.services.diagnostic_engine import evaluate_test
from app.services.report_pdf import build_report_pdf

router = APIRouter(prefix="/tests", tags=["Rapport"])


@router.get("/{test_id}/report.pdf")
def download_report(test_id: str) -> Response:
    """Fiche de diagnostic PDF (téléchargement : Content-Disposition)."""
    db = SessionLocal()
    try:
        row = db.scalar(select(Test).where(Test.test_id == test_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
        samples = SampleRepository(db).list_for_test(row.id)
        analysis = evaluate_test(row, samples)
        pdf = build_report_pdf(row, samples, analysis)
    finally:
        db.close()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="fiche-essai-{test_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )
