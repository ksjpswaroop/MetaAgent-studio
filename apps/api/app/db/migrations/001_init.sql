-- Migration 001: initial schema
-- MetaAgent Studio — canonical SQLite schema
-- Single-user desktop app. No auth tables.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS app_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    schema_version INTEGER NOT NULL DEFAULT 1,
    install_id TEXT NOT NULL,
    app_version TEXT NOT NULL DEFAULT '0.1.0',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS license_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
    license_key_hash TEXT,
    license_key_last4 TEXT,
    status TEXT NOT NULL DEFAULT 'inactive'
        CHECK (status IN ('inactive', 'active', 'expired', 'revoked')),
    activated_at TEXT,
    expires_at TEXT,
    features_json TEXT NOT NULL DEFAULT '[]',
    last_validated_at TEXT,
    validation_error TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'flow_pending', 'approved', 'architected', 'scaffolded', 'archived')),
    export_path TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS studio_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    stage TEXT NOT NULL DEFAULT 'created'
        CHECK (stage IN (
            'created', 'discovery', 'scope_ready', 'flows', 'flow_approved',
            'allocated', 'architected', 'gated', 'scaffolded'
        )),
    raw_user_prompt TEXT NOT NULL DEFAULT '',
    flow_approved INTEGER NOT NULL DEFAULT 0 CHECK (flow_approved IN (0, 1)),
    state_json TEXT NOT NULL DEFAULT '{}',
    token_usage INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_studio_sessions_project_id ON studio_sessions(project_id);

CREATE TABLE IF NOT EXISTS session_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_session_events_session_created
    ON session_events(session_id, created_at);

CREATE TABLE IF NOT EXISTS discovery_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('assistant', 'user', 'system')),
    content TEXT NOT NULL,
    question_key TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_discovery_messages_session
    ON discovery_messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS scope_envelopes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES studio_sessions(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    primary_goal TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('webhook', 'cron', 'manual')),
    external_tools_json TEXT NOT NULL DEFAULT '[]',
    human_in_loop INTEGER NOT NULL DEFAULT 0 CHECK (human_in_loop IN (0, 1)),
    fallback_strategy TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS execution_scenarios (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('happy', 'ambiguity', 'failure')),
    title TEXT NOT NULL,
    ascii_flow TEXT NOT NULL DEFAULT '',
    mermaid_flow TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_approved INTEGER NOT NULL DEFAULT 0 CHECK (is_approved IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_execution_scenarios_session
    ON execution_scenarios(session_id);

CREATE TABLE IF NOT EXISTS scenario_steps (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL REFERENCES execution_scenarios(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    name TEXT NOT NULL,
    input_data_json TEXT NOT NULL DEFAULT '{}',
    processing_goal TEXT NOT NULL DEFAULT '',
    expected_output TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_scenario_steps_scenario
    ON scenario_steps(scenario_id, step_index);

CREATE TABLE IF NOT EXISTS flow_revision_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK (action IN ('accept', 'modify', 'add_fallback', 're_route')),
    before_json TEXT NOT NULL DEFAULT '{}',
    after_json TEXT NOT NULL DEFAULT '{}',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS step_allocations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    allocated_tier TEXT NOT NULL
        CHECK (allocated_tier IN ('TIER_1_CODE', 'TIER_2_CLASSICAL_ML', 'TIER_3_LLM_AGENT')),
    rationale TEXT NOT NULL DEFAULT '',
    suggested_tech TEXT NOT NULL DEFAULT '',
    user_override INTEGER NOT NULL DEFAULT 0 CHECK (user_override IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (session_id, step_id)
);

CREATE INDEX IF NOT EXISTS idx_step_allocations_session ON step_allocations(session_id);

CREATE TABLE IF NOT EXISTS architecture_blueprints (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES studio_sessions(id) ON DELETE CASCADE,
    agent_state_schema_json TEXT NOT NULL DEFAULT '{}',
    graph_topology_json TEXT NOT NULL DEFAULT '{}',
    model_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS agent_specs (
    id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL REFERENCES architecture_blueprints(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL DEFAULT '',
    tools_json TEXT NOT NULL DEFAULT '[]',
    model_recommendation TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tool_specs (
    id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL REFERENCES architecture_blueprints(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_side_effecting INTEGER NOT NULL DEFAULT 0 CHECK (is_side_effecting IN (0, 1)),
    side_effect_class TEXT NOT NULL DEFAULT 'read_only'
        CHECK (side_effect_class IN ('read_only', 'side_effecting')),
    parameters_json TEXT NOT NULL DEFAULT '{}',
    timeout_seconds REAL NOT NULL DEFAULT 30.0
);

CREATE TABLE IF NOT EXISTS gate_configs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    gate_type TEXT NOT NULL
        CHECK (gate_type IN ('schema', 'pii', 'cost_budget', 'rate_limit', 'custom')),
    phase TEXT NOT NULL CHECK (phase IN ('pre', 'post')),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    config_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS gate_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    gate_config_id TEXT REFERENCES gate_configs(id) ON DELETE SET NULL,
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS scaffold_jobs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'passed', 'failed')),
    output_dir TEXT,
    verification_passed INTEGER NOT NULL DEFAULT 0 CHECK (verification_passed IN (0, 1)),
    pytest_passed INTEGER NOT NULL DEFAULT 0 CHECK (pytest_passed IN (0, 1)),
    ruff_passed INTEGER NOT NULL DEFAULT 0 CHECK (ruff_passed IN (0, 1)),
    mypy_passed INTEGER NOT NULL DEFAULT 0 CHECK (mypy_passed IN (0, 1)),
    error_summary TEXT,
    file_map_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_scaffold_jobs_session_status
    ON scaffold_jobs(session_id, status);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scaffold_job_id TEXT REFERENCES scaffold_jobs(id) ON DELETE SET NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    byte_size INTEGER NOT NULL DEFAULT 0,
    content_text TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON artifacts(project_id);

CREATE TABLE IF NOT EXISTS llm_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
        CHECK (name IN ('ollama', 'anthropic', 'openai', 'deepseek')),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    base_url TEXT,
    api_key_env_var TEXT,
    priority INTEGER NOT NULL DEFAULT 100,
    default_model TEXT NOT NULL DEFAULT '',
    config_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS provider_health_checks (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    ok INTEGER NOT NULL CHECK (ok IN (0, 1)),
    latency_ms INTEGER,
    message TEXT NOT NULL DEFAULT '',
    checked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS template_cache (
    key TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
