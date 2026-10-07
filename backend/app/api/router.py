from fastapi import APIRouter

from app.api.routes import agents, health, templates, tools, workflows

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(workflows.router)
api_router.include_router(agents.router)
api_router.include_router(tools.router)
api_router.include_router(templates.router)
