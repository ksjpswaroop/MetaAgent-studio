from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppMeta(Base):
    __tablename__ = "app_meta"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    install_id: Mapped[str] = mapped_column(String, nullable=False)
    app_version: Mapped[str] = mapped_column(String, default="0.1.0")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class LicenseState(Base):
    __tablename__ = "license_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tier: Mapped[str] = mapped_column(String, default="free")
    license_key_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    license_key_last4: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="inactive")
    activated_at: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    features_json: Mapped[str] = mapped_column(Text, default="[]")
    last_validated_at: Mapped[str | None] = mapped_column(String, nullable=True)
    validation_error: Mapped[str | None] = mapped_column(String, nullable=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="draft")
    export_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    sessions: Mapped[list[StudioSession]] = relationship(back_populates="project")


class StudioSession(Base):
    __tablename__ = "studio_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    stage: Mapped[str] = mapped_column(String, default="created")
    raw_user_prompt: Mapped[str] = mapped_column(Text, default="")
    flow_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    state_json: Mapped[str] = mapped_column(Text, default="{}")
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    project: Mapped[Project] = relationship(back_populates="sessions")


class SessionEvent(Base):
    __tablename__ = "session_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class DiscoveryMessage(Base):
    __tablename__ = "discovery_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    question_key: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ScopeEnvelopeRow(Base):
    __tablename__ = "scope_envelopes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("studio_sessions.id", ondelete="CASCADE"), unique=True
    )
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    primary_goal: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    external_tools_json: Mapped[str] = mapped_column(Text, default="[]")
    human_in_loop: Mapped[bool] = mapped_column(Boolean, default=False)
    fallback_strategy: Mapped[str] = mapped_column(Text, default="")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ExecutionScenario(Base):
    __tablename__ = "execution_scenarios"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    ascii_flow: Mapped[str] = mapped_column(Text, default="")
    mermaid_flow: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    steps: Mapped[list[ScenarioStep]] = relationship(back_populates="scenario")


class ScenarioStep(Base):
    __tablename__ = "scenario_steps"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("execution_scenarios.id", ondelete="CASCADE")
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    input_data_json: Mapped[str] = mapped_column(Text, default="{}")
    processing_goal: Mapped[str] = mapped_column(Text, default="")
    expected_output: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    scenario: Mapped[ExecutionScenario] = relationship(back_populates="steps")


class FlowRevisionLog(Base):
    __tablename__ = "flow_revision_log"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String, nullable=False)
    before_json: Mapped[str] = mapped_column(Text, default="{}")
    after_json: Mapped[str] = mapped_column(Text, default="{}")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class StepAllocation(Base):
    __tablename__ = "step_allocations"
    __table_args__ = (UniqueConstraint("session_id", "step_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    step_id: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    allocated_tier: Mapped[str] = mapped_column(String, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="")
    suggested_tech: Mapped[str] = mapped_column(String, default="")
    user_override: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class ArchitectureBlueprint(Base):
    __tablename__ = "architecture_blueprints"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("studio_sessions.id", ondelete="CASCADE"), unique=True
    )
    agent_state_schema_json: Mapped[str] = mapped_column(Text, default="{}")
    graph_topology_json: Mapped[str] = mapped_column(Text, default="{}")
    model_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    agents: Mapped[list[AgentSpec]] = relationship(back_populates="blueprint")
    tools: Mapped[list[ToolSpec]] = relationship(back_populates="blueprint")


class AgentSpec(Base):
    __tablename__ = "agent_specs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    blueprint_id: Mapped[str] = mapped_column(
        ForeignKey("architecture_blueprints.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    tools_json: Mapped[str] = mapped_column(Text, default="[]")
    model_recommendation: Mapped[str] = mapped_column(String, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    blueprint: Mapped[ArchitectureBlueprint] = relationship(back_populates="agents")


class ToolSpec(Base):
    __tablename__ = "tool_specs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    blueprint_id: Mapped[str] = mapped_column(
        ForeignKey("architecture_blueprints.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_side_effecting: Mapped[bool] = mapped_column(Boolean, default=False)
    side_effect_class: Mapped[str] = mapped_column(String, default="read_only")
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    timeout_seconds: Mapped[float] = mapped_column(Float, default=30.0)
    blueprint: Mapped[ArchitectureBlueprint] = relationship(back_populates="tools")


class GateConfig(Base):
    __tablename__ = "gate_configs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    gate_type: Mapped[str] = mapped_column(String, nullable=False)
    phase: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class GateRun(Base):
    __tablename__ = "gate_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    gate_config_id: Mapped[str | None] = mapped_column(
        ForeignKey("gate_configs.id", ondelete="SET NULL"), nullable=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ScaffoldJob(Base):
    __tablename__ = "scaffold_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="queued")
    output_dir: Mapped[str | None] = mapped_column(String, nullable=True)
    verification_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    pytest_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    ruff_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    mypy_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_map_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[str | None] = mapped_column(String, nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    scaffold_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("scaffold_jobs.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class LlmProvider(Base):
    __tablename__ = "llm_providers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key_env_var: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    default_model: Mapped[str] = mapped_column(String, default="")
    config_json: Mapped[str] = mapped_column(Text, default="{}")


class ProviderHealthCheck(Base):
    __tablename__ = "provider_health_checks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("llm_providers.id", ondelete="CASCADE"))
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    checked_at: Mapped[str] = mapped_column(String, nullable=False)


class TemplateCache(Base):
    __tablename__ = "template_cache"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class EdgeCase(Base):
    __tablename__ = "edge_cases"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    agent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    step_name: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    input_fixture_json: Mapped[str] = mapped_column(Text, default="{}")
    expected_behavior: Mapped[str] = mapped_column(Text, default="")
    attached_scenario_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_scenarios.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="queued")
    scenario_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    edge_case_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    score_json: Mapped[str] = mapped_column(Text, default="{}")
    summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[str | None] = mapped_column(String, nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class SimulationStepTrace(Base):
    __tablename__ = "simulation_step_traces"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"))
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class CodingGapPrompt(Base):
    __tablename__ = "coding_gap_prompts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    simulation_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True
    )
    tool_target: Mapped[str] = mapped_column(String, default="generic")
    title: Mapped[str] = mapped_column(String, nullable=False)
    gap_description: Mapped[str] = mapped_column(Text, default="")
    files_json: Mapped[str] = mapped_column(Text, default="[]")
    acceptance_criteria: Mapped[str] = mapped_column(Text, default="")
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Package(Base):
    __tablename__ = "packages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    scaffold_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("scaffold_jobs.id", ondelete="SET NULL"), nullable=True
    )
    output_dir: Mapped[str] = mapped_column(String, nullable=False)
    zip_path: Mapped[str | None] = mapped_column(String, nullable=True)
    manifest_json: Mapped[str] = mapped_column(Text, default="{}")
    checksum_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    pytest_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="built")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class PackageFile(Base):
    __tablename__ = "package_files"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, default=0)


class ImprovementIteration(Base):
    __tablename__ = "improvement_iterations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("studio_sessions.id", ondelete="CASCADE"))
    iteration_index: Mapped[int] = mapped_column(Integer, nullable=False)
    simulation_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True
    )
    package_id: Mapped[str | None] = mapped_column(
        ForeignKey("packages.id", ondelete="SET NULL"), nullable=True
    )
    score_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    plateau: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class AgentPack(Base):
    __tablename__ = "agent_packs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("studio_sessions.id", ondelete="SET NULL"), nullable=True
    )
    source_project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    package_id: Mapped[str | None] = mapped_column(
        ForeignKey("packages.id", ondelete="SET NULL"), nullable=True
    )
    blueprint_json: Mapped[str] = mapped_column(Text, default="{}")
    best_score: Mapped[float] = mapped_column(Float, default=0.0)
    scores_json: Mapped[str] = mapped_column(Text, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
