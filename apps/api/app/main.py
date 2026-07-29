from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.db.init import init_db
from app.routers import (
    allocation,
    architecture,
    artifacts,
    discovery,
    edge_cases,
    events,
    flows,
    gates,
    health,
    improve,
    license,
    package,
    pro,
    projects,
    prompts,
    providers,
    scaffold,
    sessions,
    settings as settings_router,
    simulate,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="MetaAgent Studio Local API",
    version=__version__,
    description=(
        "Local-first core API for MetaAgent Studio. "
        "LLM-backed design stages, simulation, packaging, and hill-climb improvement."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(license.router)
app.include_router(projects.router)
app.include_router(sessions.router)
app.include_router(discovery.router)
app.include_router(flows.router)
app.include_router(allocation.router)
app.include_router(architecture.router)
app.include_router(gates.router)
app.include_router(scaffold.router)
app.include_router(artifacts.router)
app.include_router(providers.router)
app.include_router(settings_router.router)
app.include_router(events.router)
app.include_router(pro.router)
app.include_router(edge_cases.router)
app.include_router(simulate.router)
app.include_router(prompts.router)
app.include_router(package.router)
app.include_router(improve.router)
