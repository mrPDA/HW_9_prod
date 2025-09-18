#!/usr/bin/env python3
"""
🚀 ML Fraud Detection API Service
===================================

Production-ready FastAPI сервис для детекции мошенничества
с интеграцией MLflow Model Registry и Kubernetes.

Автор: ML Team
Версия: 1.0.0
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server
from pydantic import BaseModel, Field
import pandas as pd

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.models.fraud_detector import FraudDetectionModel
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Prometheus метрики
PREDICTION_COUNTER = Counter('ml_predictions_total', 'Total ML predictions made')
PREDICTION_LATENCY = Histogram('ml_prediction_duration_seconds', 'ML prediction latency')
ERROR_COUNTER = Counter('ml_prediction_errors_total', 'Total ML prediction errors')

# Получаем настройки
settings = get_settings()

# Создаем FastAPI приложение
app = FastAPI(
    title="🛡️ Fraud Detection API",
    description="Production ML API для детекции мошеннических транзакций",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальная переменная для модели
ml_model: Optional[FraudDetectionModel] = None


class TransactionRequest(BaseModel):
    """Схема запроса для предсказания мошенничества"""
    
    transaction_id: str = Field(..., description="Уникальный ID транзакции")
    amount: float = Field(..., ge=0, description="Сумма транзакции")
    merchant_category: str = Field(..., description="Категория продавца")
    hour_of_day: int = Field(..., ge=0, le=23, description="Час дня (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="День недели (0-6)")
    user_age: Optional[int] = Field(None, ge=0, le=120, description="Возраст пользователя")
    location_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Риск локации (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "txn_123456",
                "amount": 150.75,
                "merchant_category": "restaurant",
                "hour_of_day": 14,
                "day_of_week": 2,
                "user_age": 35,
                "location_risk_score": 0.2
            }
        }


class PredictionResponse(BaseModel):
    """Схема ответа с предсказанием"""
    
    transaction_id: str
    is_fraud: bool
    fraud_probability: float = Field(..., ge=0, le=1)
    confidence: str
    model_version: str
    prediction_timestamp: datetime
    processing_time_ms: float


class BatchPredictionRequest(BaseModel):
    """Схема для batch предсказаний"""
    
    transactions: List[TransactionRequest]
    
    class Config:
        schema_extra = {
            "example": {
                "transactions": [
                    {
                        "transaction_id": "txn_001",
                        "amount": 50.0,
                        "merchant_category": "grocery",
                        "hour_of_day": 10,
                        "day_of_week": 1
                    },
                    {
                        "transaction_id": "txn_002", 
                        "amount": 999.99,
                        "merchant_category": "electronics",
                        "hour_of_day": 23,
                        "day_of_week": 6
                    }
                ]
            }
        }


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервиса"""
    global ml_model
    
    logger.info("🚀 Starting Fraud Detection API Service...")
    logger.info(f"📊 MLflow URI: {settings.mlflow_tracking_uri}")
    logger.info(f"🤖 Model: {settings.model_name}@{settings.model_alias}")
    
    try:
        # Загружаем ML модель
        ml_model = FraudDetectionModel(
            mlflow_uri=settings.mlflow_tracking_uri,
            model_name=settings.model_name,
            model_alias=settings.model_alias
        )
        
        await ml_model.load_model()
        logger.info("✅ ML model loaded successfully")
        
        # Запускаем Prometheus metrics сервер
        if settings.enable_metrics:
            start_http_server(settings.metrics_port)
            logger.info(f"📈 Prometheus metrics server started on port {settings.metrics_port}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown"""
    logger.info("🔄 Shutting down Fraud Detection API Service...")


def get_model() -> FraudDetectionModel:
    """Dependency для получения модели"""
    if ml_model is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded. Service unavailable."
        )
    return ml_model


@app.post("/predict", response_model=PredictionResponse)
async def predict_fraud(
    request: TransactionRequest,
    background_tasks: BackgroundTasks,
    model: FraudDetectionModel = Depends(get_model)
):
    """
    🎯 Предсказание мошенничества для одной транзакции
    
    Анализирует транзакцию и возвращает:
    - Вероятность мошенничества (0-1)
    - Бинарное решение (fraud/not fraud)
    - Уровень уверенности
    """
    start_time = time.time()
    PREDICTION_COUNTER.inc()
    
    try:
        # Преобразуем запрос в DataFrame
        transaction_data = pd.DataFrame([request.dict()])
        
        # Делаем предсказание
        prediction_result = await model.predict(transaction_data)
        
        # Вычисляем время обработки
        processing_time = (time.time() - start_time) * 1000
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        # Определяем уровень уверенности
        confidence = "high" if abs(prediction_result['fraud_probability'] - 0.5) > 0.3 else "medium"
        if abs(prediction_result['fraud_probability'] - 0.5) > 0.4:
            confidence = "very_high"
        
        response = PredictionResponse(
            transaction_id=request.transaction_id,
            is_fraud=prediction_result['is_fraud'],
            fraud_probability=prediction_result['fraud_probability'],
            confidence=confidence,
            model_version=model.model_version,
            prediction_timestamp=datetime.utcnow(),
            processing_time_ms=round(processing_time, 2)
        )
        
        # Логируем предсказание в фоне
        background_tasks.add_task(
            log_prediction,
            request.transaction_id,
            prediction_result['fraud_probability'],
            confidence
        )
        
        return response
        
    except Exception as e:
        ERROR_COUNTER.inc()
        logger.error(f"❌ Prediction error for {request.transaction_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch")
async def predict_fraud_batch(
    request: BatchPredictionRequest,
    model: FraudDetectionModel = Depends(get_model)
):
    """
    📦 Batch предсказание для множества транзакций
    
    Обрабатывает до 100 транзакций за раз для оптимальной производительности.
    """
    start_time = time.time()
    
    if len(request.transactions) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size too large. Maximum 100 transactions per request."
        )
    
    try:
        # Преобразуем в DataFrame
        transactions_df = pd.DataFrame([t.dict() for t in request.transactions])
        
        # Batch предсказание
        predictions = await model.predict_batch(transactions_df)
        
        # Формируем ответы
        responses = []
        for i, transaction in enumerate(request.transactions):
            pred = predictions.iloc[i]
            confidence = "high" if abs(pred['fraud_probability'] - 0.5) > 0.3 else "medium"
            
            responses.append(PredictionResponse(
                transaction_id=transaction.transaction_id,
                is_fraud=pred['is_fraud'],
                fraud_probability=pred['fraud_probability'],
                confidence=confidence,
                model_version=model.model_version,
                prediction_timestamp=datetime.utcnow(),
                processing_time_ms=round((time.time() - start_time) * 1000 / len(request.transactions), 2)
            ))
        
        PREDICTION_COUNTER.inc(len(request.transactions))
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return {
            "predictions": responses,
            "batch_size": len(responses),
            "total_processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
    except Exception as e:
        ERROR_COUNTER.inc()
        logger.error(f"❌ Batch prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )


async def log_prediction(transaction_id: str, fraud_prob: float, confidence: str):
    """Асинхронное логирование предсказаний"""
    logger.info(
        f"🎯 Prediction: {transaction_id} | "
        f"Fraud: {fraud_prob:.3f} | "
        f"Confidence: {confidence}"
    )


# Подключаем дополнительные роутеры
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])


@app.get("/")
async def root():
    """Корневой endpoint с информацией о сервисе"""
    return {
        "service": "🛡️ Fraud Detection API",
        "version": "1.0.0",
        "status": "healthy",
        "model": {
            "name": settings.model_name,
            "alias": settings.model_alias,
            "version": ml_model.model_version if ml_model else "not_loaded"
        },
        "endpoints": {
            "predict": "/predict",
            "batch_predict": "/predict/batch", 
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    # Локальный запуск для разработки
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
