# Feature: License and Pro

## Problem

Paid capabilities (team collab stubs, deploy stubs, audits) need a license gate without multi-user auth.

## User stories

- As a paid user, I paste a license key once; Studio unlocks Pro routes locally.
- As a free user, I still get full local design and scaffold.

## User flow

1. `GET /api/v1/license` → tier free, status inactive
2. `POST /api/v1/license/activate` with key
3. Key hashed (SHA-256); last4 stored; tier=pro; status=active
4. Pro routers succeed
5. `POST /api/v1/license/deactivate` returns to free

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/license` |
| POST | `/api/v1/license/activate` |
| POST | `/api/v1/license/deactivate` |
| POST | `/api/v1/license/validate` |

## Stub key format

Local validator accepts keys matching: `MAS-PRO-XXXX-XXXX-XXXX` (alphanumeric groups). Real license server is future work.

## Pro routers (gated)

- `/api/v1/teams`
- `/api/v1/deploy`
- `/api/v1/audits`

Return `402 Payment Required` when license is not active Pro.

## Tables

`license_state`

## Acceptance

- Plaintext key never persisted
- Free tier unrestricted for core routers
- Pro routers call `require_pro_license`
