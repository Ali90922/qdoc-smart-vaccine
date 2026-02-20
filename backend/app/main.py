from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routers import auth, profile, dashboard, schedule, reminders

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QDoc Vaccine System",
    description="Smart vaccine eligibility and reminder system for Manitoba patients.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # React Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/auth",      tags=["Auth"])
app.include_router(profile.router,    prefix="/api/profile",   tags=["Profile"])
app.include_router(dashboard.router,  prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(schedule.router,   prefix="/api/schedule",  tags=["Schedule"])
app.include_router(reminders.router,  prefix="/api/reminders", tags=["Reminders"])


@app.get("/")
def root():
    return {"message": "QDoc Vaccine API is running."}
