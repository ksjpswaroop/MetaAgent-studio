-- Migration 002: simulation, edge cases, prompts, packages, hill-climb, agent packs

CREATE TABLE IF NOT EXISTS edge_cases (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    agent_name TEXT,
    step_name TEXT,
    category TEXT NOT NULL
        CHECK (category IN ('timeout', 'partial_data', 'schema_drift', 'tool_failure', 'ambiguity', 'other')),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    input_fixture_json TEXT NOT NULL DEFAULT '{}',
    expected_behavior TEXT NOT NULL DEFAULT '',
    attached_scenario_id TEXT REFERENCES execution_scenarios(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_edge_cases_session ON edge_cases(session_id);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'passed', 'failed', 'partial')),
    scenario_ids_json TEXT NOT NULL DEFAULT '[]',
    edge_case_ids_json TEXT NOT NULL DEFAULT '[]',
    score_json TEXT NOT NULL DEFAULT '{}',
    summary TEXT NOT NULL DEFAULT '',
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_simulation_runs_session ON simulation_runs(session_id, created_at);

CREATE TABLE IF NOT EXISTS simulation_step_traces (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    agent_name TEXT,
    input_json TEXT NOT NULL DEFAULT '{}',
    output_json TEXT NOT NULL DEFAULT '{}',
    passed INTEGER NOT NULL DEFAULT 0 CHECK (passed IN (0, 1)),
    latency_ms INTEGER,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sim_traces_run ON simulation_step_traces(run_id, step_index);

CREATE TABLE IF NOT EXISTS coding_gap_prompts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    simulation_run_id TEXT REFERENCES simulation_runs(id) ON DELETE SET NULL,
    tool_target TEXT NOT NULL DEFAULT 'generic'
        CHECK (tool_target IN ('cursor', 'claude', 'codex', 'generic')),
    title TEXT NOT NULL,
    gap_description TEXT NOT NULL DEFAULT '',
    files_json TEXT NOT NULL DEFAULT '[]',
    acceptance_criteria TEXT NOT NULL DEFAULT '',
    prompt_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_coding_gap_prompts_session ON coding_gap_prompts(session_id);

CREATE TABLE IF NOT EXISTS packages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scaffold_job_id TEXT REFERENCES scaffold_jobs(id) ON DELETE SET NULL,
    output_dir TEXT NOT NULL,
    zip_path TEXT,
    manifest_json TEXT NOT NULL DEFAULT '{}',
    checksum_sha256 TEXT,
    pytest_passed INTEGER NOT NULL DEFAULT 0 CHECK (pytest_passed IN (0, 1)),
    verify_log TEXT,
    status TEXT NOT NULL DEFAULT 'built'
        CHECK (status IN ('built', 'verified', 'failed')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_packages_session ON packages(session_id);

CREATE TABLE IF NOT EXISTS package_files (
    id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    byte_size INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_package_files_package ON package_files(package_id);

CREATE TABLE IF NOT EXISTS improvement_iterations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    iteration_index INTEGER NOT NULL,
    simulation_run_id TEXT REFERENCES simulation_runs(id) ON DELETE SET NULL,
    package_id TEXT REFERENCES packages(id) ON DELETE SET NULL,
    score_before REAL,
    score_after REAL,
    plateau INTEGER NOT NULL DEFAULT 0 CHECK (plateau IN (0, 1)),
    notes TEXT NOT NULL DEFAULT '',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (session_id, iteration_index)
);

CREATE INDEX IF NOT EXISTS idx_improve_iters_session ON improvement_iterations(session_id);

CREATE TABLE IF NOT EXISTS agent_packs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_session_id TEXT REFERENCES studio_sessions(id) ON DELETE SET NULL,
    source_project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    package_id TEXT REFERENCES packages(id) ON DELETE SET NULL,
    blueprint_json TEXT NOT NULL DEFAULT '{}',
    best_score REAL NOT NULL DEFAULT 0,
    scores_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
