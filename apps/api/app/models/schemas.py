from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TierType(str, Enum):
    TIER_1_CODE = "TIER_1_CODE"
    TIER_2_CLASSICAL_ML = "TIER_2_CLASSICAL_ML"
    TIER_3_LLM_AGENT = "TIER_3_LLM_AGENT"


class ProjectStatus(str, Enum):
    draft = "draft"
    flow_pending = "flow_pending"
    approved = "approved"
    architected = "architected"
    scaffolded = "scaffolded"
    archived = "archived"


class SessionStage(str, Enum):
    created = "created"
    discovery = "discovery"
    scope_ready = "scope_ready"
    flows = "flows"
    flow_approved = "flow_approved"
    allocated = "allocated"
    architected = "architected"
    gated = "gated"
    scaffolded = "scaffolded"


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    version: str
    db_ok: bool
    providers_reachable: bool = False


class LicenseStatus(BaseModel):
    tier: str
    status: str
    license_key_last4: str | None = None
    activated_at: str | None = None
    expires_at: str | None = None
    features: list[str] = Field(default_factory=list)


class LicenseActivateRequest(BaseModel):
    license_key: str = Field(min_length=8)


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    export_path: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    export_path: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    export_path: str | None
    created_at: str
    updated_at: str


class SessionCreate(BaseModel):
    project_id: str
    raw_user_prompt: str


class StudioSessionOut(BaseModel):
    id: str
    project_id: str
    stage: str
    raw_user_prompt: str
    flow_approved: bool
    state: dict[str, Any] = Field(default_factory=dict)
    token_usage: int = 0
    created_at: str
    updated_at: str


class SessionEventOut(BaseModel):
    id: str
    session_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class DiscoveryAnswerRequest(BaseModel):
    question_key: str
    answer: str


class DiscoveryMessageOut(BaseModel):
    id: str
    role: str
    content: str
    question_key: str | None = None
    created_at: str


class ScopeEnvelope(BaseModel):
    project_name: str
    primary_goal: str
    trigger_type: str
    external_tools: list[str] = Field(default_factory=list)
    human_in_loop: bool = False
    fallback_strategy: str = ""


class ScopeFinalizeRequest(BaseModel):
    scope: ScopeEnvelope | None = None


class ScenarioStepOut(BaseModel):
    step_index: int
    name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    processing_goal: str = ""
    expected_output: str = ""
    notes: str = ""


class ExecutionScenarioOut(BaseModel):
    id: str
    kind: str
    title: str
    ascii_flow: str = ""
    mermaid_flow: str = ""
    sort_order: int = 0
    is_approved: bool = False
    steps: list[ScenarioStepOut] = Field(default_factory=list)


class FlowModifyRequest(BaseModel):
    step_index: int
    changes: dict[str, Any] = Field(default_factory=dict)
    note: str = ""


class StepAllocationOut(BaseModel):
    step_id: int
    step_name: str
    description: str = ""
    allocated_tier: TierType
    rationale: str = ""
    suggested_tech: str = ""
    user_override: bool = False


class AllocationOverride(BaseModel):
    allocated_tier: TierType
    rationale: str = "User override"


class AgentSpecOut(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    model_recommendation: str = ""


class ToolSpecOut(BaseModel):
    id: str
    name: str
    description: str
    is_side_effecting: bool
    side_effect_class: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0


class ArchitectureBlueprintOut(BaseModel):
    id: str
    session_id: str
    agent_state_schema: dict[str, Any]
    graph_topology: dict[str, Any]
    model_notes: str = ""
    agents: list[AgentSpecOut] = Field(default_factory=list)
    tools: list[ToolSpecOut] = Field(default_factory=list)


class GateConfigOut(BaseModel):
    id: str
    gate_type: str
    phase: str
    enabled: bool
    config: dict[str, Any] = Field(default_factory=dict)


class GateUpdate(BaseModel):
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class GateRunOut(BaseModel):
    id: str
    gate_config_id: str | None
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ScaffoldRunRequest(BaseModel):
    write_to_disk: bool = False
    output_dir: str | None = None


class ScaffoldJobOut(BaseModel):
    id: str
    session_id: str
    project_id: str
    status: str
    output_dir: str | None = None
    verification_passed: bool = False
    pytest_passed: bool = False
    ruff_passed: bool = False
    mypy_passed: bool = False
    error_summary: str | None = None
    file_map: dict[str, str] = Field(default_factory=dict)
    started_at: str | None = None
    finished_at: str | None = None


class ArtifactOut(BaseModel):
    id: str
    project_id: str
    scaffold_job_id: str | None
    file_path: str
    content_hash: str
    byte_size: int
    content_text: str | None = None
    created_at: str


class ProviderOut(BaseModel):
    id: str
    name: str
    enabled: bool
    base_url: str | None
    api_key_env_var: str | None
    priority: int
    default_model: str
    config: dict[str, Any] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    enabled: bool | None = None
    base_url: str | None = None
    api_key_env_var: str | None = None
    priority: int | None = None
    default_model: str | None = None
    config: dict[str, Any] | None = None


class ProviderHealthOut(BaseModel):
    ok: bool
    latency_ms: int | None = None
    message: str = ""


class ProviderOrderRequest(BaseModel):
    provider_ids: list[str]


class ProStubResponse(BaseModel):
    message: str
    maturity: str = "future"


class EdgeCaseOut(BaseModel):
    id: str
    session_id: str
    agent_name: str | None = None
    step_name: str | None = None
    category: str
    title: str
    description: str = ""
    input_fixture: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: str = ""
    attached_scenario_id: str | None = None
    created_at: str


class EdgeCaseGenerateRequest(BaseModel):
    count: int = 5
    categories: list[str] = Field(
        default_factory=lambda: [
            "timeout",
            "partial_data",
            "schema_drift",
            "tool_failure",
        ]
    )


class SimulationRunRequest(BaseModel):
    scenario_ids: list[str] = Field(default_factory=list)
    edge_case_ids: list[str] = Field(default_factory=list)
    include_all_scenarios: bool = True


class SimulationTraceOut(BaseModel):
    id: str
    step_index: int
    step_name: str
    agent_name: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    passed: bool
    latency_ms: int | None = None
    error: str | None = None


class SimulationScore(BaseModel):
    overall: float = 0.0
    correctness: float = 0.0
    gate_pass_rate: float = 0.0
    latency_budget: float = 0.0
    tier_efficiency: float = 0.0


class SimulationRunOut(BaseModel):
    id: str
    session_id: str
    status: str
    scenario_ids: list[str] = Field(default_factory=list)
    edge_case_ids: list[str] = Field(default_factory=list)
    score: SimulationScore = Field(default_factory=SimulationScore)
    summary: str = ""
    traces: list[SimulationTraceOut] = Field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str


class PromptGenerateRequest(BaseModel):
    simulation_run_id: str | None = None
    tool_target: str = "cursor"


class CodingGapPromptOut(BaseModel):
    id: str
    session_id: str
    simulation_run_id: str | None = None
    tool_target: str
    title: str
    gap_description: str = ""
    files: list[str] = Field(default_factory=list)
    acceptance_criteria: str = ""
    prompt_text: str
    created_at: str


class PackageBuildRequest(BaseModel):
    output_dir: str | None = None
    run_verify: bool = True


class PackageFileOut(BaseModel):
    file_path: str
    content_hash: str
    byte_size: int


class PackageOut(BaseModel):
    id: str
    session_id: str
    project_id: str
    scaffold_job_id: str | None = None
    output_dir: str
    zip_path: str | None = None
    checksum_sha256: str | None = None
    pytest_passed: bool = False
    verify_log: str | None = None
    status: str
    files: list[PackageFileOut] = Field(default_factory=list)
    created_at: str


class ImproveIterateRequest(BaseModel):
    auto_attach_edge_cases: bool = True
    generate_prompts: bool = True
    tool_target: str = "cursor"


class ImprovementIterationOut(BaseModel):
    id: str
    session_id: str
    iteration_index: int
    simulation_run_id: str | None = None
    package_id: str | None = None
    score_before: float | None = None
    score_after: float | None = None
    plateau: bool = False
    notes: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class PublishPackRequest(BaseModel):
    name: str
    package_id: str | None = None


class AgentPackOut(BaseModel):
    id: str
    name: str
    source_session_id: str | None = None
    source_project_id: str | None = None
    package_id: str | None = None
    blueprint: dict[str, Any] = Field(default_factory=dict)
    best_score: float = 0.0
    scores: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ForkPackRequest(BaseModel):
    project_name: str | None = None
    raw_user_prompt: str | None = None
