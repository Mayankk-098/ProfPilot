import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import Base, engine, ensure_schema

# Register all SQLAlchemy models before create_all()
from app.models import academic  # noqa: F401
from app.models import attendance  # noqa: F401

from app.routers import auth
from app.routers import attendance as attendance_router
from app.routers import schedule
from app.routers import context
from app.routers import courses
from app.routers import ai
from app.routers import memory
from app.routers import students
from app.routers import risk


Base.metadata.create_all(bind=engine)
ensure_schema(engine)


# Optional hosted-demo bootstrap. Disabled by default.
if os.getenv("DEMO_SEED_ON_STARTUP", "").strip().lower() == "true":
    from seed.seed_demo import seed_if_empty

    seed_if_empty()


app = FastAPI(
    title="ProfPilot API",
    version="0.2.0",
    description="Academic intelligence backend for ProfPilot",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication
app.include_router(auth.router)

# Existing ProfPilot v2 intelligence/data routes
app.include_router(context.router)
app.include_router(courses.router)
app.include_router(ai.router)
app.include_router(schedule.router)
app.include_router(memory.router)
app.include_router(students.router)

# Attendance and academic intelligence
app.include_router(attendance_router.router)
app.include_router(risk.router)


@app.get("/")
def root():
    return {
        "app": "ProfPilot",
        "status": "online",
        "version": "0.2.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
