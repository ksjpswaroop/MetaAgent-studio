from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import require_pro_license
from app.models.schemas import ProStubResponse

router = APIRouter(prefix="/api/v1", tags=["pro"], dependencies=[Depends(require_pro_license)])


@router.get("/teams", response_model=ProStubResponse)
async def list_teams() -> ProStubResponse:
    return ProStubResponse(
        message="Team collaboration is a future Pro feature stub.",
        maturity="future",
    )


@router.post("/deploy", response_model=ProStubResponse)
async def create_deploy() -> ProStubResponse:
    return ProStubResponse(
        message="One-click deploy (ECS/Modal/Fly) is a future Pro feature stub.",
        maturity="future",
    )


@router.get("/audits", response_model=ProStubResponse)
async def list_audits() -> ProStubResponse:
    return ProStubResponse(
        message="Automated security audits are a future Pro feature stub.",
        maturity="future",
    )
