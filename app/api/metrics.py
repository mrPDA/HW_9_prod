"""
📊 Metrics Endpoints
===================

Эндпоинты для экспорта метрик в Prometheus формате
и предоставления статистики о работе сервиса.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil

from fastapi import APIRouter, Response
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()


class ServiceMetrics(BaseModel):
    """Схема метрик сервиса"""
    service_name: str
    version: str
    environment: str
    uptime_seconds: float
    memory_usage_mb: float
    memory_usage_percent: float
    cpu_usage_percent: float
    timestamp: datetime


class ModelMetrics(BaseModel):
    """Схема метрик модели"""
    model_name: str
    model_version: str
    model_alias: str
    is_loaded: bool
    load_time_ms: float
    predictions_total: int
    avg_prediction_time_ms: float
    timestamp: datetime


# Время запуска для расчета uptime
from app.api.health import SERVICE_START_TIME


@router.get("/prometheus")
async def prometheus_metrics():
    """
    📈 Экспорт метрик в формате Prometheus
    
    Возвращает все зарегистрированные метрики в формате,
    совместимом с Prometheus scraping.
    """
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/service", response_model=ServiceMetrics)
async def service_metrics():
    """
    🔧 Метрики сервиса
    
    Информация о производительности и использовании ресурсов.
    """
    uptime = (datetime.utcnow() - SERVICE_START_TIME).total_seconds()
    
    # Получаем информацию о ресурсах
    memory_info = psutil.virtual_memory()
    process = psutil.Process()
    process_memory = process.memory_info()
    
    return ServiceMetrics(
        service_name=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
        uptime_seconds=round(uptime, 2),
        memory_usage_mb=round(process_memory.rss / (1024 * 1024), 2),
        memory_usage_percent=round(memory_info.percent, 2),
        cpu_usage_percent=round(psutil.cpu_percent(interval=0.1), 2),
        timestamp=datetime.utcnow()
    )


@router.get("/model", response_model=ModelMetrics)
async def model_metrics():
    """
    🤖 Метрики ML модели
    
    Статистика загруженной модели и ее производительности.
    """
    try:
        from app.main import ml_model
        
        if not ml_model or not ml_model.is_loaded:
            return ModelMetrics(
                model_name="unknown",
                model_version="unknown", 
                model_alias="unknown",
                is_loaded=False,
                load_time_ms=0.0,
                predictions_total=0,
                avg_prediction_time_ms=0.0,
                timestamp=datetime.utcnow()
            )
        
        # Получаем метрики из Prometheus counters
        from app.main import PREDICTION_COUNTER, PREDICTION_LATENCY
        
        predictions_total = int(PREDICTION_COUNTER._value._value)
        
        # Рассчитываем среднее время предсказания
        if PREDICTION_LATENCY._sum._value > 0 and PREDICTION_LATENCY._count._value > 0:
            avg_prediction_time = (PREDICTION_LATENCY._sum._value / PREDICTION_LATENCY._count._value) * 1000
        else:
            avg_prediction_time = 0.0
        
        return ModelMetrics(
            model_name=ml_model.model_name,
            model_version=ml_model.model_version or "unknown",
            model_alias=ml_model.model_alias,
            is_loaded=ml_model.is_loaded,
            load_time_ms=ml_model.load_time or 0.0,
            predictions_total=predictions_total,
            avg_prediction_time_ms=round(avg_prediction_time, 2),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        return ModelMetrics(
            model_name="error",
            model_version="error",
            model_alias="error", 
            is_loaded=False,
            load_time_ms=0.0,
            predictions_total=0,
            avg_prediction_time_ms=0.0,
            timestamp=datetime.utcnow()
        )


@router.get("/")
async def metrics_overview():
    """
    📊 Обзор всех метрик
    
    Сводная информация о состоянии сервиса и модели.
    """
    service_metrics_data = await service_metrics()
    model_metrics_data = await model_metrics()
    
    return {
        "service": service_metrics_data.dict(),
        "model": model_metrics_data.dict(),
        "endpoints": {
            "prometheus": "/metrics/prometheus",
            "service": "/metrics/service", 
            "model": "/metrics/model"
        },
        "timestamp": datetime.utcnow()
    }


@router.get("/debug")
async def debug_info():
    """
    🐛 Отладочная информация
    
    Подробная информация для диагностики проблем.
    Доступно только в development режиме.
    """
    if settings.is_production():
        return {"message": "Debug info not available in production"}
    
    import os
    import sys
    
    debug_data = {
        "environment": dict(os.environ),
        "python": {
            "version": sys.version,
            "path": sys.path[:5],  # Первые 5 путей
            "modules": list(sys.modules.keys())[:20]  # Первые 20 модулей
        },
        "process": {
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "user": os.getenv("USER", "unknown")
        },
        "settings": settings.dict(),
        "timestamp": datetime.utcnow()
    }
    
    return debug_data
