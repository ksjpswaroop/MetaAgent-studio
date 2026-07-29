# Feature: Code Scaffolding

## Problem

Manual LangGraph boilerplate is slow and error-prone; exports must be runnable with tests.

## User stories

- As a developer, I generate a full project directory with state, agents, tools, gates, graph, pytest, Dockerfile, README.

## User flow

1. Start scaffold job for approved architecture
2. Poll job status (verification / pytest flags)
3. List artifacts; download zip or open export path

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/scaffold/{session_id}/run` |
| GET | `/api/v1/scaffold/{session_id}/jobs` |
| GET | `/api/v1/scaffold/jobs/{job_id}` |

## Tables

`scaffold_jobs`, `artifacts`

## Acceptance

- Stub returns a `FileMap` of expected paths
- Job status transitions queued → running → passed/failed
- Side-effecting write is gated (documented; stub does not write real trees by default unless `write_to_disk=true`)
