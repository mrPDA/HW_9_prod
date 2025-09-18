"""
📝 Logging Configuration
========================

Настройка структурированного логирования для production среды
с поддержкой JSON формата и интеграцией с Kubernetes.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Настройка системы логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_format: Формат логов (json, text)
    """
    
    # Основная конфигурация
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "structlog.stdlib.ProcessorFormatter",
                "processor": structlog.dev.JSONProcessor(),
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                ],
            },
            "text": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": log_format,
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO", 
                "propagate": False,
            },
        },
    }
    
    # Применяем конфигурацию
    logging.config.dictConfig(logging_config)
    
    # Настраиваем structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Получение структурированного логгера"""
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """Middleware для логирования HTTP запросов"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("request")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = datetime.utcnow()
        
        # Извлекаем информацию о запросе
        request_info = {
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope.get("query_string", b"").decode(),
            "client_ip": scope.get("client", ["unknown", None])[0],
            "user_agent": "",
        }
        
        # Ищем User-Agent в заголовках
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"user-agent":
                request_info["user_agent"] = header_value.decode()
                break
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Логируем после получения статуса ответа
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                self.logger.info(
                    "HTTP Request",
                    **request_info,
                    status_code=message["status"],
                    duration_ms=round(duration_ms, 2),
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def log_prediction_metrics(
    transaction_id: str,
    fraud_probability: float,
    is_fraud: bool,
    model_version: str,
    processing_time_ms: float,
    confidence: str,
) -> None:
    """Логирование метрик предсказаний для мониторинга"""
    
    logger = get_logger("predictions")
    logger.info(
        "Prediction made",
        transaction_id=transaction_id,
        fraud_probability=fraud_probability,
        is_fraud=is_fraud,
        model_version=model_version,
        processing_time_ms=processing_time_ms,
        confidence=confidence,
        timestamp=datetime.utcnow().isoformat(),
    )


def log_model_metrics(
    model_name: str,
    model_version: str,
    load_time_ms: float,
    model_size_mb: float,
) -> None:
    """Логирование метрик модели"""
    
    logger = get_logger("model")
    logger.info(
        "Model loaded",
        model_name=model_name,
        model_version=model_version,
        load_time_ms=load_time_ms,
        model_size_mb=model_size_mb,
        timestamp=datetime.utcnow().isoformat(),
    )


def log_error(
    error_type: str,
    error_message: str,
    context: Dict[str, Any] = None,
    exception: Exception = None,
) -> None:
    """Структурированное логирование ошибок"""
    
    logger = get_logger("errors")
    
    error_data = {
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if context:
        error_data.update(context)
    
    if exception:
        error_data["exception_type"] = type(exception).__name__
        error_data["exception_details"] = str(exception)
    
    logger.error("Application error", **error_data)
