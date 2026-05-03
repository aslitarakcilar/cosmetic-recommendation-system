from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_all_tables
from .routers import analytics, auth, interactions, recommendations, users

create_all_tables()

app = FastAPI(
    title="Sephora Recommendation API",
    description=(
        "Kişiselleştirilmiş kozmetik öneri sistemi. "
        "Popularity, profil tabanlı, içerik tabanlı, "
        "collaborative filtering ve hybrid yaklaşımları karşılaştırır."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recommendations.router)
app.include_router(interactions.router)
app.include_router(analytics.router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}
