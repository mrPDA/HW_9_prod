"""
🏥 Health Check Endpoints
========================

Эндпоинты для проверки состояния сервиса и его компонентов.
Используется для Kubernetes liveness и readiness проб.
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()

# Время запуска сервиса
SERVICE_START_TIME = datetime.utcnow()
settings = get_settings()


class HealthResponse(BaseModel):
    """Схема ответа health check"""
    status: str
    timestamp: datetime
    uptime_seconds: float
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Схема ответа readiness check"""
    status: str
    checks: Dict[str, Any]
    timestamp: datetime


class LivenessResponse(BaseModel):
    """Схема ответа liveness check"""
    status: str
    timestamp: datetime
    memory_usage_percent: float
    cpu_usage_percent: float


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    🩺 Основной health check
    
    Простая проверка что сервис запущен и работает.
    Используется для базовой проверки доступности.
    """
    uptime = (datetime.utcnow() - SERVICE_START_TIME).total_seconds()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        uptime_seconds=round(uptime, 2),
        version=settings.service_version,
        environment=settings.environment
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    ✅ Readiness probe для Kubernetes
    
    Проверяет готовность сервиса принимать трафик:
    - ML модель загружена
    - MLflow доступен
    - Основные зависимости работают
    """
    checks = {}
    overall_status = "ready"
    
    # Проверка загрузки ML модели
    try:
        from app.main import ml_model
        if ml_model and ml_model.is_loaded:
            checks["ml_model"] = {
                "status": "ready",
                "model_name": ml_model.model_name,
                "model_version": ml_model.model_version,
                "load_time_ms": ml_model.load_time
            }
        else:
            checks["ml_model"] = {"status": "not_ready", "reason": "Model not loaded"}
            overall_status = "not_ready"
    except Exception as e:
        checks["ml_model"] = {"status": "error", "error": str(e)}
        overall_status = "not_ready"
    
    # Проверка MLflow доступности
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        
        start_time = time.time()
        client = MlflowClient(settings.mlflow_tracking_uri)
        # Простая проверка доступности
        experiments = client.search_experiments(max_results=1)
        response_time = (time.time() - start_time) * 1000
        
        checks["mlflow"] = {
            "status": "ready",
            "uri": settings.mlflow_tracking_uri,
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        checks["mlflow"] = {
            "status": "error", 
            "uri": settings.mlflow_tracking_uri,
            "error": str(e)
        }
        overall_status = "not_ready"
    
    # Проверка ресурсов системы
    try:
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if memory_percent > 90 or cpu_percent > 95:
            checks["system_resources"] = {
                "status": "warning",
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "reason": "High resource usage"
            }
        else:
            checks["system_resources"] = {
                "status": "ready",
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent
            }
    except Exception as e:
        checks["system_resources"] = {"status": "error", "error": str(e)}
    
    if overall_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": overall_status, "checks": checks}
        )
    
    return ReadinessResponse(
        status=overall_status,
        checks=checks,
        timestamp=datetime.utcnow()
    )


@router.get("/live", response_model=LivenessResponse)
async def liveness_check():
    """
    💓 Liveness probe для Kubernetes
    
    Проверяет что процесс сервиса жив и отвечает.
    При неудаче Kubernetes перезапустит pod.
    """
    try:
        # Проверка использования ресурсов
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Критические пороги для liveness
        if memory_percent > 95:
            logger.error(f"Critical memory usage: {memory_percent}%")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Critical memory usage: {memory_percent}%"
            )
        
        return LivenessResponse(
            status="alive",
            timestamp=datetime.utcnow(),
            memory_usage_percent=round(memory_percent, 2),
            cpu_usage_percent=round(cpu_percent, 2)
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Liveness check failed"
        )


@router.get("/startup")
async def startup_check():
    """
    🚀 Startup probe для Kubernetes
    
    Проверяет что сервис полностью инициализирован.
    Более медленная альтернатива readiness для начального запуска.
    """
    uptime = (datetime.utcnow() - SERVICE_START_TIME).total_seconds()
    
    # Даем время на инициализацию модели
    if uptime < 30:  # 30 секунд на startup
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service still starting up. Uptime: {uptime:.1f}s"
        )
    
    # Проверяем что все готово
    try:
        await readiness_check()
        return {
            "status": "started",
            "timestamp": datetime.utcnow(),
            "uptime_seconds": round(uptime, 2)
        }
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies not ready"
        )
