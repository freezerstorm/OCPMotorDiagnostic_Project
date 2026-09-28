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
from app.services.diagnostic_engine import evaluate_test_full
from app.services.report_pdf import parse_pdf_options
from app.services.report_pdf import build_report_pdf

router = APIRouter(prefix="/tests", tags=["Rapport"])


@router.get("/{test_id}/report.pdf")
def download_report(test_id: str, opts: str | None = None) -> Response:
    """Fiche de diagnostic PDF (téléchargement : Content-Disposition).

    `opts` : informations supplémentaires de l'analyse cochées par le
    technicien sur la page Analyse (séparées par des virgules, ex.
    « verdicts,synthese »). Vide/absent = fiche OCP seule (décision
    client 28/09/2026).
    """
    db = SessionLocal()
    try:
        row = db.scalar(select(Test).where(Test.test_id == test_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
        samples = SampleRepository(db).list_for_test(row.id)
        # Rapport complet : règles + analyse environnementale (même base
        # que la page ANALYSE) — les options choisissent ce qui figure
        # dans le PDF en plus de la fiche OCP.
        analysis = evaluate_test_full(row, samples)
        pdf = build_report_pdf(row, samples, analysis, parse_pdf_options(opts))
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
