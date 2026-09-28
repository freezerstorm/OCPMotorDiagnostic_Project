"""Routes API des SERVICES — catalogue du champ « Service ».

- GET  /api/v1/services : liste des désignations proposées par le
  formulaire d'identification du moteur (ordre du catalogue) ;
- POST /api/v1/services : ajoute une nouvelle désignation saisie par le
  technicien (elle devient disponible dans les futures listes
  déroulantes). 409 si elle existe déjà.

Le contexte environnemental utilisé par l'analyse vit dans
« diagnostic_rules/environment_knowledge.py » : ce catalogue ne stocke
QUE les désignations (une désignation ajoutée par un technicien qui
n'est pas dans la base de connaissances donne simplement « service non
répertorié » dans l'analyse — aucune hypothèse inventée).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_service_repository
from app.repositories.sql.service_repository import ServiceRepository
from app.schemas.services import ServiceCreate, ServiceRead

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=list[ServiceRead])
def list_services(repo: ServiceRepository = Depends(get_service_repository)) -> list[ServiceRead]:
    """Liste des désignations de services (ordre du catalogue)."""
    return [ServiceRead.model_validate(s) for s in repo.list()]


@router.post("", status_code=201, response_model=ServiceRead)
def create_service(
    payload: ServiceCreate, repo: ServiceRepository = Depends(get_service_repository)
) -> ServiceRead:
    """Ajoute une désignation au catalogue (409 si déjà présente)."""
    try:
        service = repo.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ServiceRead.model_validate(service)
