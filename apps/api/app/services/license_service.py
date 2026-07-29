from __future__ import annotations

import hashlib
import json
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LicenseState
from app.models.schemas import LicenseStatus
from app.utils.time import utc_now

# Local stub format: MAS-PRO-XXXX-XXXX-XXXX
LICENSE_RE = re.compile(r"^MAS-PRO-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", re.I)
PRO_FEATURES = ["teams", "deploy", "audits"]


def hash_license_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


def validate_key_format(key: str) -> bool:
    return bool(LICENSE_RE.match(key.strip()))


async def get_license_row(db: AsyncSession) -> LicenseState:
    row = await db.get(LicenseState, 1)
    if row is None:
        row = LicenseState(id=1, tier="free", status="inactive", features_json="[]")
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


def to_status(row: LicenseState) -> LicenseStatus:
    try:
        features = json.loads(row.features_json or "[]")
    except json.JSONDecodeError:
        features = []
    return LicenseStatus(
        tier=row.tier,
        status=row.status,
        license_key_last4=row.license_key_last4,
        activated_at=row.activated_at,
        expires_at=row.expires_at,
        features=features,
    )


async def activate_license(db: AsyncSession, key: str) -> LicenseStatus:
    if not validate_key_format(key):
        raise ValueError(
            "Invalid license key format. Expected MAS-PRO-XXXX-XXXX-XXXX"
        )
    row = await get_license_row(db)
    cleaned = key.strip().upper()
    row.license_key_hash = hash_license_key(cleaned)
    row.license_key_last4 = cleaned[-4:]
    row.tier = "pro"
    row.status = "active"
    row.activated_at = utc_now()
    row.expires_at = None
    row.features_json = json.dumps(PRO_FEATURES)
    row.last_validated_at = utc_now()
    row.validation_error = None
    await db.commit()
    await db.refresh(row)
    return to_status(row)


async def deactivate_license(db: AsyncSession) -> LicenseStatus:
    row = await get_license_row(db)
    row.tier = "free"
    row.status = "inactive"
    row.license_key_hash = None
    row.license_key_last4 = None
    row.activated_at = None
    row.expires_at = None
    row.features_json = "[]"
    row.last_validated_at = utc_now()
    row.validation_error = None
    await db.commit()
    await db.refresh(row)
    return to_status(row)


async def validate_license(db: AsyncSession) -> LicenseStatus:
    row = await get_license_row(db)
    row.last_validated_at = utc_now()
    if row.tier == "pro" and row.status == "active" and row.license_key_hash:
        row.validation_error = None
    elif row.tier == "pro":
        row.status = "inactive"
        row.validation_error = "Missing license hash"
    await db.commit()
    await db.refresh(row)
    return to_status(row)


async def is_pro_active(db: AsyncSession) -> bool:
    row = await db.scalar(select(LicenseState).where(LicenseState.id == 1))
    return bool(row and row.tier == "pro" and row.status == "active")
