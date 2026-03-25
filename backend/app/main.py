from fastapi import FastAPI

from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.problems import router as problems_router
from app.routes.submissions import router as submissions_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health_router)
app.include_router(problems_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
