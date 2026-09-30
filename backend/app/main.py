from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import schedule
from app.routers import context
from app.database.db import Base, engine

from app.models import academic  # noqa: F401

from app.routers import courses
from app.routers import ai
from app.routers import memory


Base.metadata.create_all(bind=engine)


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

app.include_router(context.router)
app.include_router(courses.router)
app.include_router(ai.router)
app.include_router(schedule.router)
app.include_router(memory.router)


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