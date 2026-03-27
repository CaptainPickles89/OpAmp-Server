"""REST API router for OpAMP Server management endpoints.

Provides /api/v1/* endpoints for operator-facing config management.
The OpAMP protocol endpoint (/v1/opamp) is mounted separately in main.py.
"""
from fastapi import APIRouter

from opamp_server.api import config as config_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(config_router.router)
