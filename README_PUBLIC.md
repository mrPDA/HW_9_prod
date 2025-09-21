# 🛡️ ML Fraud Detection API

> **Производственный REST API для детекции мошеннических транзакций с полным CI/CD и облачным развертыванием**

[![GitHub Actions](https://github.com/username/repo/workflows/CI%2FCD/badge.svg)](https://github.com/username/repo/actions)
[![Security](https://github.com/username/repo/workflows/Security/badge.svg)](https://github.com/username/repo/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Описание

Комплексное решение для детекции мошенничества в реальном времени, включающее:

- 🚀 **REST API** на FastAPI с полной валидацией
- 🤖 **MLflow интеграция** для управления ML моделями  
- ☸️ **Kubernetes развертывание** с автоскейлингом
- 🔄 **CI/CD pipeline** с автоматическими тестами
- 📊 **Мониторинг** с Prometheus/Grafana
- 🧪 **Комплексное тестирование** включая нагрузочные тесты
- 🔒 **Security-first** подход с защитой секретов

## ✨ Особенности

### 🚀 Production-Ready API
- **FastAPI** с автоматической документацией
- **Единичные и batch предсказания** 
- **Валидация данных** через Pydantic
- **Graceful shutdown** и health checks
- **Структурированное логирование**

### 🤖 ML Pipeline
- Интеграция с **MLflow Model Registry**
- Загрузка моделей по алиасам (`champion`, `staging`)
- Кэширование моделей для производительности
- Метрики качества и производительности

### ☸️ Cloud-Native
- **Kubernetes манифесты** с best practices
- **Horizontal Pod Autoscaling**
- **Service mesh ready**
- **Multi-environment** поддержка

### 🔄 DevOps Excellence
- **GitHub Actions** CI/CD
- **Multi-stage Docker** сборка
- **Security scanning** 
- **Automated testing** и отчеты
- **Infrastructure as Code** с Terraform

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/ml-fraud-detection-api.git
cd ml-fraud-detection-api

# Установка зависимостей
make install-dev
```

### 2. Локальный запуск

```bash
# Копирование конфигурации
cp env.example .env
# Отредактируйте .env файл с вашими настройками

# Запуск API
make run

# API доступен по адресу: http://localhost:8000
# Документация: http://localhost:8000/docs
```

### 3. Docker Compose (рекомендуется)

```bash
# Запуск полного окружения
make dev-up

# Включает:
# - ML API (http://localhost:8000)
# - MLflow (http://localhost:5001) 
# - Prometheus (http://localhost:9090)
# - Grafana (http://localhost:3000)
```

## 🧪 Тестирование

### Быстрые тесты
```bash
# Функциональные тесты
make test-api-local

# Полное тестирование с отчетами
./run_api_tests.sh --quick
```

### Комплексное тестирование
```bash
# Полное тестирование включая производительность
./run_api_tests.sh

# Нагрузочное тестирование
make test-api-performance

# Тесты безопасности
make test-api-security
```

### Использование API

```bash
# Health check
curl http://localhost:8000/health

# Предсказание
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_123",
    "amount": 150.75,
    "merchant_category": "restaurant", 
    "hour_of_day": 14,
    "day_of_week": 2,
    "user_age": 35,
    "location_risk_score": 0.2
  }'
```

## ☸️ Развертывание

### Kubernetes (рекомендуется)

```bash
# Настройка kubectl для вашего кластера
kubectl config use-context your-cluster

# Развертывание
kubectl apply -f k8s/

# Проверка статуса
kubectl get pods -n fraud-detection
```

### Terraform Infrastructure

```bash
# Инициализация
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Отредактируйте terraform.tfvars

# Развертывание инфраструктуры
terraform init
terraform plan
terraform apply
```

## 🔧 Конфигурация

### Переменные окружения

Ключевые настройки в `.env`:

```bash
# MLflow
MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
MODEL_NAME=your_model_name
MODEL_ALIAS=champion

# Security
API_KEY=your_secure_api_key
JWT_SECRET=your_jwt_secret

# Cloud (Yandex Cloud)
YC_TOKEN=your_token
YC_CLOUD_ID=your_cloud_id
YC_FOLDER_ID=your_folder_id
```

### Kubernetes Secrets

```bash
# Создание секретов
kubectl create secret generic api-secrets \
  --from-literal=api-key=your_api_key \
  --from-literal=mlflow-password=your_password \
  -n fraud-detection
```

## 📊 Мониторинг

### Метрики Prometheus
- `ml_predictions_total` - Общее количество предсказаний
- `ml_prediction_duration_seconds` - Время обработки запросов
- `ml_prediction_errors_total` - Количество ошибок

### Health Checks
- `/health` - Общий статус
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe

### Логирование
Структурированные JSON логи с поддержкой:
- Трейсинга запросов
- Метрик производительности
- Аудита безопасности

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Секреты**: Используйте переменные окружения или K8s secrets
2. **HTTPS**: Всегда используйте TLS в production
3. **API Keys**: Ротируйте ключи регулярно
4. **Network**: Используйте Network Policies в K8s
5. **Scanning**: Регулярно сканируйте на уязвимости

### Security Headers
API автоматически добавляет security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## 📁 Структура проекта

```
ml-fraud-detection-api/
├── app/                    # FastAPI приложение
│   ├── main.py            # Основной файл API
│   ├── core/              # Конфигурация и утилиты
│   ├── models/            # ML модели
│   └── api/               # API endpoints
├── k8s/                   # Kubernetes манифесты
├── terraform/             # Infrastructure as Code
├── tests/                 # Тесты и отчеты
├── .github/workflows/     # CI/CD pipeline
├── monitoring/            # Конфигурация мониторинга
└── docs/                  # Документация
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

1. **Testing** - Функциональные, производительность, безопасность
2. **Building** - Docker image сборка и публикация
3. **Security** - Сканирование уязвимостей  
4. **Deployment** - Автоматическое развертывание

### Deployment Strategy
- **Staging** - Автоматически из `develop` ветки
- **Production** - По тегам версий (`v1.0.0`)
- **Rollback** - Автоматический откат при ошибках

## 📚 Документация

- [🧪 API Testing Guide](API_TESTING_GUIDE.md) - Подробное руководство по тестированию
- [🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Развертывание в production
- [🔧 Configuration Guide](docs/CONFIG_GUIDE.md) - Настройка и конфигурация
- [🔒 Security Guide](docs/SECURITY_GUIDE.md) - Рекомендации по безопасности

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

### Development Guidelines

- Следуйте [PEP 8](https://pep8.org/) для Python кода
- Добавляйте тесты для новой функциональности
- Обновляйте документацию
- Проверяйте безопасность (`make security`)

## 📝 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).

## 🆘 Поддержка

- 📖 [Документация](docs/)
- 🐛 [Issues](https://github.com/your-username/repo/issues)
- 💬 [Discussions](https://github.com/your-username/repo/discussions)

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) за отличный фреймворк
- [MLflow](https://mlflow.org/) за ML lifecycle management
- [Yandex Cloud](https://cloud.yandex.com/) за облачную инфраструктуру

---

**⭐ Если проект был полезен, поставьте звездочку!**
