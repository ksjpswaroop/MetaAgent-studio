# Feature: Artifacts and Export

## Problem

Users need a durable log of generated files with content hashes for audit and reopen.

## User stories

- As a developer, I list artifacts for a project, fetch file content, and download a zip.

## User flow

1. After scaffold, list artifacts by `project_id`
2. GET single artifact content
3. Download zip of job output

## API

| Method | Path |
|--------|------|
| GET | `/api/v1/artifacts?project_id=` |
| GET | `/api/v1/artifacts/{id}` |
| GET | `/api/v1/artifacts/jobs/{job_id}/download` |

## Tables

`artifacts`, `scaffold_jobs`

## Acceptance

- Each artifact has `content_hash` and `file_path`
- Download returns application/zip (stub may return JSON manifest if no disk files)
