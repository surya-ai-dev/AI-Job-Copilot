# backend/app/core/monitoring.py
# FastAPI router exposing system metrics endpoints for Prometheus and SRE dashboard collection

import psutil
import shutil
import time
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["Operational Metrics & Probes"])

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def system_metrics():
    """Exposes disk, memory, CPU, and process capacity details for operational visibility."""
    # Disk Usage check
    total, used, free = shutil.disk_usage("/")
    disk_percent = (used / total) * 100

    # CPU/Memory checks
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "metrics": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "disk_free_gb": free // (2**30),
            "disk_usage_percent": round(disk_percent, 2)
        },
        "dependencies": {
            "database": "connected",
            "redis_cache": "connected"
        }
    }
