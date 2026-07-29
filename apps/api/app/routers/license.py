from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import LicenseActivateRequest, LicenseStatus
from app.services import license_service

router = APIRouter(prefix="/api/v1/license", tags=["license"])


@router.get("", response_model=LicenseStatus)
async def get_license(db: AsyncSession = Depends(get_db)) -> LicenseStatus:
    row = await license_service.get_license_row(db)
    return license_service.to_status(row)


@router.post("/activate", response_model=LicenseStatus)
async def activate(
    body: LicenseActivateRequest, db: AsyncSession = Depends(get_db)
) -> LicenseStatus:
    try:
        return await license_service.activate_license(db, body.license_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/deactivate", response_model=LicenseStatus)
async def deactivate(db: AsyncSession = Depends(get_db)) -> LicenseStatus:
    return await license_service.deactivate_license(db)


@router.post("/validate", response_model=LicenseStatus)
async def validate(db: AsyncSession = Depends(get_db)) -> LicenseStatus:
    return await license_service.validate_license(db)
