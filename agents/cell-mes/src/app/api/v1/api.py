"""API v1 router configuration."""

from fastapi import APIRouter

from .endpoints import (
    auth,
    masters,
    equipments,
    routings,
    scenarios,
    production,
    scheduler,
    analytics,
    nlm,
    quality,
    downtime,
    alarms,
    process_categories,
    cells,
    converters,
    dtp,
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Master data
api_router.include_router(masters.router, prefix="/masters", tags=["Master Data"])
api_router.include_router(
    process_categories.router, prefix="/masters/process-categories", tags=["Process Categories"]
)
api_router.include_router(cells.router, prefix="/masters/cells", tags=["Cells"])
api_router.include_router(equipments.router, prefix="/masters/equipments", tags=["Equipments"])
api_router.include_router(routings.router, prefix="/masters/products", tags=["Routings"])
api_router.include_router(scenarios.router, prefix="/masters/scenarios", tags=["Scenarios"])
api_router.include_router(converters.router, prefix="/converters", tags=["n8n Converters"])
api_router.include_router(dtp.router, prefix="/integrations/dtp", tags=["DTP Integration"])

# Production
api_router.include_router(production.router, prefix="/production", tags=["Production"])

# Scheduler Integration
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler Integration"])

# Analytics (NL-Driven MES)
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# NLM (Natural Language MES) - AI Assistant
api_router.include_router(nlm.router, prefix="/nlm", tags=["NLM AI Assistant"])

# Quality Management
api_router.include_router(quality.router, tags=["Quality Management"])

# Downtime Management
api_router.include_router(downtime.router, prefix="/downtime", tags=["Downtime Management"])

# Alarm Management
api_router.include_router(alarms.router, prefix="/alarms", tags=["Alarm Management"])
