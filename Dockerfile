# 🐳 Multi-stage Dockerfile for ML Fraud Detection API
# ===================================================

# 🏗️ Build stage
FROM python:3.11-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 🚀 Production stage
FROM python:3.11-slim as production

# Метаданные образа
LABEL maintainer="ML Team" \
      version="1.0.0" \
      description="Fraud Detection API Service"

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создание пользователя приложения (безопасность)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копирование виртуального окружения из builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Установка рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY app/ ./app/
COPY .env* ./

# Установка правильных разрешений
RUN chown -R appuser:appuser /app
USER appuser

# Переменные окружения
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Экспонируем порты
EXPOSE 8000 9090

# 🚀 Запуск приложения
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
