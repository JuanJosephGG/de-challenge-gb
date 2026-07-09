from fastapi import FastAPI
from src.api.routers import admin, metrics, ingestion

app = FastAPI(
    title="Data Engineering Platform API",
    description="API for ingesting, validating, and analyzing HR data.",
    version="1.0.0"
)

app.include_router(ingestion.router)
app.include_router(metrics.router)
app.include_router(admin.router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API is running securely"}