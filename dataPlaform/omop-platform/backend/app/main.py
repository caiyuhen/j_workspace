from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sources, ingestion, dicom, monitor
from app.db.database import engine, Base
from app.models import models

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OMOP Data Platform API",
    description="Backend API for OMOP Data Cleaning and Governance Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(ingestion.router, prefix="/api/v1/ingestion", tags=["ingestion"])
app.include_router(dicom.router, prefix="/api/v1/dicom", tags=["dicom"])
app.include_router(monitor.router, prefix="/api/v1/monitor", tags=["monitor"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to OMOP Data Platform API"}
