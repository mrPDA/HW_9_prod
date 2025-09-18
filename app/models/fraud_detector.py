"""
🤖 Fraud Detection Model
========================

Класс для загрузки и использования ML модели из MLflow Registry
для детекции мошеннических транзакций.
"""

import asyncio
import time
import pickle
import tempfile
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging

import pandas as pd
import numpy as np
import mlflow
import mlflow.pyfunc
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import structlog

from app.core.logging import log_model_metrics, log_error

logger = structlog.get_logger(__name__)


class FraudDetectionModel:
    """
    🛡️ Модель детекции мошенничества с интеграцией MLflow
    
    Поддерживает:
    - Загрузку модели из MLflow Registry
    - Асинхронное выполнение предсказаний
    - Batch обработку
    - Кеширование модели
    - Метрики производительности
    """
    
    def __init__(
        self, 
        mlflow_uri: str,
        model_name: str,
        model_alias: str = "champion",
        model_stage: str = "Production"
    ):
        self.mlflow_uri = mlflow_uri
        self.model_name = model_name
        self.model_alias = model_alias
        self.model_stage = model_stage
        
        self.model = None
        self.model_version = None
        self.model_metadata = {}
        self.feature_names = []
        self.is_loaded = False
        self.load_time = None
        
        # MLflow client
        self.client = None
        
        logger.info(
            "🤖 Initializing FraudDetectionModel",
            mlflow_uri=mlflow_uri,
            model_name=model_name,
            model_alias=model_alias,
            model_stage=model_stage
        )
    
    async def load_model(self) -> None:
        """
        Асинхронная загрузка модели из MLflow Registry
        """
        start_time = time.time()
        
        try:
            logger.info("📥 Loading model from MLflow Registry...")
            
            # Настраиваем MLflow
            mlflow.set_tracking_uri(self.mlflow_uri)
            self.client = MlflowClient(self.mlflow_uri)
            
            # Получаем информацию о модели
            model_info = await self._get_model_info()
            self.model_version = model_info["version"]
            self.model_metadata = model_info["metadata"]
            
            # Загружаем модель
            model_uri = f"models:/{self.model_name}@{self.model_alias}"
            logger.info(f"📦 Loading model from URI: {model_uri}")
            
            # Загружаем в отдельном потоке чтобы не блокировать event loop
            self.model = await asyncio.get_event_loop().run_in_executor(
                None,
                mlflow.pyfunc.load_model,
                model_uri
            )
            
            # Получаем метаданные о фичах
            self.feature_names = self._extract_feature_names()
            
            load_time_ms = (time.time() - start_time) * 1000
            self.load_time = load_time_ms
            self.is_loaded = True
            
            # Логируем метрики загрузки
            log_model_metrics(
                model_name=self.model_name,
                model_version=self.model_version,
                load_time_ms=load_time_ms,
                model_size_mb=self._estimate_model_size()
            )
            
            logger.info(
                "✅ Model loaded successfully",
                model_version=self.model_version,
                load_time_ms=round(load_time_ms, 2),
                feature_count=len(self.feature_names)
            )
            
        except Exception as e:
            self.is_loaded = False
            log_error(
                error_type="ModelLoadError",
                error_message=f"Failed to load model: {str(e)}",
                context={
                    "model_name": self.model_name,
                    "model_alias": self.model_alias,
                    "mlflow_uri": self.mlflow_uri
                },
                exception=e
            )
            raise
    
    async def _get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели из Registry"""
        
        try:
            # Получаем модель по алиасу
            model_version = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.get_model_version_by_alias,
                self.model_name,
                self.model_alias
            )
            
            return {
                "version": model_version.version,
                "stage": model_version.current_stage,
                "metadata": {
                    "run_id": model_version.run_id,
                    "creation_timestamp": model_version.creation_timestamp,
                    "last_updated_timestamp": model_version.last_updated_timestamp,
                    "description": model_version.description,
                    "tags": {tag.key: tag.value for tag in model_version.tags} if model_version.tags else {}
                }
            }
            
        except Exception as e:
            # Fallback: поиск по стадии
            logger.warning(f"Alias '{self.model_alias}' not found, trying stage '{self.model_stage}'")
            
            latest_versions = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.get_latest_versions,
                self.model_name,
                [self.model_stage]
            )
            
            if not latest_versions:
                raise ValueError(f"No model found for {self.model_name} in stage {self.model_stage}")
            
            model_version = latest_versions[0]
            return {
                "version": model_version.version,
                "stage": model_version.current_stage,
                "metadata": {
                    "run_id": model_version.run_id,
                    "creation_timestamp": model_version.creation_timestamp,
                    "last_updated_timestamp": model_version.last_updated_timestamp,
                    "description": model_version.description,
                    "tags": {}
                }
            }
    
    def _extract_feature_names(self) -> List[str]:
        """Извлечение имен фичей из модели"""
        
        try:
            # Для scikit-learn моделей
            if hasattr(self.model, '_model_impl') and hasattr(self.model._model_impl, 'feature_names_in_'):
                return list(self.model._model_impl.feature_names_in_)
            
            # Для других типов моделей - стандартный набор фичей
            return [
                "amount", "merchant_category", "hour_of_day", 
                "day_of_week", "user_age", "location_risk_score"
            ]
            
        except Exception as e:
            logger.warning(f"Could not extract feature names: {e}")
            return ["feature_" + str(i) for i in range(6)]  # Default features
    
    def _estimate_model_size(self) -> float:
        """Оценка размера модели в MB"""
        try:
            # Приблизительная оценка через сериализацию
            with tempfile.NamedTemporaryFile() as tmp:
                pickle.dump(self.model, tmp)
                size_bytes = tmp.tell()
                return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0
    
    async def predict(self, transaction_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Предсказание для одной транзакции
        
        Args:
            transaction_data: DataFrame с данными транзакции
            
        Returns:
            Dict с результатами предсказания
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Предобработка данных
            processed_data = self._preprocess_data(transaction_data)
            
            # Предсказание в отдельном потоке
            start_time = time.time()
            prediction = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.predict,
                processed_data
            )
            prediction_time = time.time() - start_time
            
            # Получаем вероятности если доступны
            try:
                probabilities = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.model.predict_proba,
                    processed_data
                )
                fraud_probability = float(probabilities[0][1])  # Вероятность класса "fraud"
            except:
                # Fallback: если predict_proba недоступен
                fraud_probability = float(prediction[0]) if prediction[0] in [0, 1] else 0.5
            
            is_fraud = bool(prediction[0]) if len(prediction) > 0 else fraud_probability > 0.5
            
            return {
                "is_fraud": is_fraud,
                "fraud_probability": fraud_probability,
                "prediction_time_ms": round(prediction_time * 1000, 2),
                "model_version": self.model_version,
                "features_used": list(processed_data.columns)
            }
            
        except Exception as e:
            log_error(
                error_type="PredictionError",
                error_message=f"Prediction failed: {str(e)}",
                context={"transaction_data": transaction_data.to_dict()},
                exception=e
            )
            raise
    
    async def predict_batch(self, transactions_data: pd.DataFrame) -> pd.DataFrame:
        """
        Batch предсказание для множества транзакций
        
        Args:
            transactions_data: DataFrame с данными транзакций
            
        Returns:
            DataFrame с результатами предсказаний
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Предобработка данных
            processed_data = self._preprocess_data(transactions_data)
            
            # Batch предсказание
            start_time = time.time()
            predictions = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.predict,
                processed_data
            )
            
            # Получаем вероятности
            try:
                probabilities = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.model.predict_proba,
                    processed_data
                )
                fraud_probabilities = probabilities[:, 1]  # Вероятности класса "fraud"
            except:
                fraud_probabilities = predictions.astype(float)
            
            prediction_time = time.time() - start_time
            
            # Формируем результат
            results = pd.DataFrame({
                "is_fraud": predictions.astype(bool),
                "fraud_probability": fraud_probabilities,
                "prediction_time_ms": round(prediction_time * 1000 / len(transactions_data), 2),
                "model_version": self.model_version
            })
            
            return results
            
        except Exception as e:
            log_error(
                error_type="BatchPredictionError", 
                error_message=f"Batch prediction failed: {str(e)}",
                context={"batch_size": len(transactions_data)},
                exception=e
            )
            raise
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Предобработка данных перед предсказанием
        
        Args:
            data: Исходные данные
            
        Returns:
            Обработанные данные готовые для модели
        """
        processed = data.copy()
        
        # Заполняем пропущенные значения
        if 'user_age' in processed.columns:
            processed['user_age'] = processed['user_age'].fillna(35)  # Средний возраст
        
        if 'location_risk_score' in processed.columns:
            processed['location_risk_score'] = processed['location_risk_score'].fillna(0.5)
        
        # Кодируем категориальные переменные
        if 'merchant_category' in processed.columns:
            # Простое ordinal encoding для демо
            category_map = {
                'grocery': 0, 'gas_station': 1, 'restaurant': 2,
                'retail': 3, 'online': 4, 'electronics': 5,
                'pharmacy': 6, 'other': 7
            }
            processed['merchant_category'] = processed['merchant_category'].map(
                lambda x: category_map.get(x, 7)
            )
        
        # Убеждаемся что все колонки числовые
        numeric_columns = ['amount', 'merchant_category', 'hour_of_day', 'day_of_week']
        if 'user_age' in processed.columns:
            numeric_columns.append('user_age')
        if 'location_risk_score' in processed.columns:
            numeric_columns.append('location_risk_score')
        
        # Оставляем только нужные колонки и приводим к float
        processed = processed[numeric_columns].astype(float)
        
        return processed
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о загруженной модели"""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_alias": self.model_alias,
            "is_loaded": self.is_loaded,
            "load_time_ms": self.load_time,
            "feature_names": self.feature_names,
            "metadata": self.model_metadata
        }
