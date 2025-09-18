"""
⚙️ Configuration Management
===========================

Централизованное управление настройками приложения с поддержкой
переменных окружения и валидацией через Pydantic.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения с автоматической загрузкой из environment"""
    
    # 🚀 Основные настройки сервиса
    service_name: str = Field(default="fraud-detection-api", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 🌐 Сетевые настройки
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # 🤖 MLflow настройки
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        env="MLFLOW_TRACKING_URI",
        description="MLflow Tracking Server URI"
    )
    mlflow_username: Optional[str] = Field(default=None, env="MLFLOW_TRACKING_USERNAME")
    mlflow_password: Optional[str] = Field(default=None, env="MLFLOW_TRACKING_PASSWORD")
    
    # 🎯 Модель настройки
    model_name: str = Field(
        default="fraud_detection_yandex_model",
        env="MODEL_NAME",
        description="Название модели в MLflow Registry"
    )
    model_alias: str = Field(
        default="champion",
        env="MODEL_ALIAS", 
        description="Алиас модели (champion, challenger, staging)"
    )
    model_stage: str = Field(
        default="Production",
        env="MODEL_STAGE",
        description="Стадия модели (Production, Staging, Archived)"
    )
    
    # 📊 Мониторинг и метрики
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # 📝 Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json, text
    
    # 🔐 Безопасность
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # 🗄️ База данных (для логирования предсказаний)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # ⚡ Производительность
    max_batch_size: int = Field(default=100, env="MAX_BATCH_SIZE")
    prediction_timeout: int = Field(default=30, env="PREDICTION_TIMEOUT")  # секунды
    model_cache_ttl: int = Field(default=3600, env="MODEL_CACHE_TTL")  # секунды
    
    # 🌐 Kubernetes настройки
    k8s_namespace: str = Field(default="default", env="K8S_NAMESPACE")
    k8s_service_name: str = Field(default="fraud-detection", env="K8S_SERVICE_NAME")
    k8s_pod_name: Optional[str] = Field(default=None, env="HOSTNAME")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Примеры для документации
        schema_extra = {
            "example": {
                "mlflow_tracking_uri": "http://mlflow.example.com:5000",
                "model_name": "fraud_detection_model",
                "model_alias": "champion",
                "log_level": "INFO",
                "enable_metrics": True,
                "environment": "production"
            }
        }
    
    def is_production(self) -> bool:
        """Проверка production окружения"""
        return self.environment.lower() in ("production", "prod")
    
    def is_development(self) -> bool:
        """Проверка development окружения"""
        return self.environment.lower() in ("development", "dev", "local")
    
    def get_cors_origins(self) -> list:
        """Получение списка CORS origins"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Получение настроек с кешированием
    
    Используется lru_cache для оптимизации - настройки загружаются
    только один раз и кешируются в памяти.
    """
    return Settings()


# Для удобства импорта
settings = get_settings()
