# 🛡️ ML Fraud Detection API

> **⚠️ ВНИМАНИЕ: Учебный проект для демонстрации MLOps практик**

Production-ready REST API сервис для детекции мошеннических транзакций с интеграцией MLflow Model Registry и развертыванием в Kubernetes.

**🔒 БЕЗОПАСНОСТЬ**: Все секретные данные заменены на примеры. Для production использования требуется настройка собственных ключей и сертификатов. См. раздел [Безопасность](#-безопасность).

## 🎯 Возможности

- **🔌 REST API** с эндпоинтами для предсказаний
- **🤖 MLflow интеграция** для загрузки моделей из Registry
- **📊 Prometheus метрики** для мониторинга
- **🏥 Health checks** для Kubernetes проб
- **☸️ Kubernetes ready** с манифестами для развертывания
- **🚀 CI/CD** автоматизация через GitHub Actions
- **🐳 Docker** контейнеризация с multi-stage сборкой

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Load Balancer  │───▶│  Fraud API Pod  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │◀───│   Kubernetes    │───▶│ MLflow Registry │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd ml-k8s-fraud-detection
```

2. **Установка зависимостей:**
```bash
pip install -r app/requirements.txt
```

3. **Настройка окружения:**
```bash
cp env.example .env
# Отредактируйте .env с вашими настройками
```

4. **Запуск сервиса:**
```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **Проверка работы:**
```bash
curl http://localhost:8000/health/
```

### Docker развертывание

1. **Сборка образа:**
```bash
docker build -t fraud-detection-api:latest .
```

2. **Запуск контейнера:**
```bash
docker run -d \
  --name fraud-api \
  -p 8000:8000 \
  -p 9090:9090 \
  -e MLFLOW_TRACKING_URI="http://your-mlflow:5000" \
  -e MODEL_NAME="fraud_detection_yandex_model" \
  fraud-detection-api:latest
```

## 📖 API Документация

### Основные эндпоинты

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Информация о сервисе |
| `/predict` | POST | Предсказание для одной транзакции |
| `/predict/batch` | POST | Batch предсказания (до 100 транзакций) |
| `/health/` | GET | Health check |
| `/health/ready` | GET | Readiness probe |
| `/health/live` | GET | Liveness probe |
| `/metrics/` | GET | Обзор метрик |
| `/metrics/prometheus` | GET | Prometheus метрики |
| `/docs` | GET | Swagger UI документация |

### Пример запроса

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_123456",
    "amount": 150.75,
    "merchant_category": "restaurant", 
    "hour_of_day": 14,
    "day_of_week": 2,
    "user_age": 35,
    "location_risk_score": 0.2
  }'
```

### Пример ответа

```json
{
  "transaction_id": "txn_123456",
  "is_fraud": false,
  "fraud_probability": 0.23,
  "confidence": "medium",
  "model_version": "1",
  "prediction_timestamp": "2025-09-17T08:00:00Z",
  "processing_time_ms": 12.5
}
```

## ☸️ Kubernetes развертывание

### Предварительные требования

- Kubernetes кластер (версия 1.20+)
- kubectl настроен для подключения к кластеру
- Container Registry для Docker образов

### Развертывание

1. **Создание namespace:**
```bash
kubectl create namespace fraud-detection
```

2. **Применение манифестов:**
```bash
kubectl apply -f k8s/ -n fraud-detection
```

3. **Проверка статуса:**
```bash
kubectl get pods -n fraud-detection
kubectl get services -n fraud-detection
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Юнит-тесты
pytest tests/ -v

# Тесты с покрытием
pytest tests/ --cov=app --cov-report=html

# Тесты API
pytest tests/test_api.py -v

# Тесты модели
pytest tests/test_model.py -v
```

### Нагрузочное тестирование

```bash
# Установка locust
pip install locust

# Запуск нагрузочного тестирования
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Мониторинг

### Prometheus метрики

Сервис экспортирует следующие метрики:

- `ml_predictions_total` - Общее количество предсказаний
- `ml_prediction_duration_seconds` - Время выполнения предсказаний
- `ml_prediction_errors_total` - Количество ошибок предсказаний

### Grafana Dashboard

Пример запросов для Grafana:

```promql
# Количество предсказаний в секунду
rate(ml_predictions_total[5m])

# Среднее время предсказания
rate(ml_prediction_duration_seconds_sum[5m]) / rate(ml_prediction_duration_seconds_count[5m])

# Частота ошибок
rate(ml_prediction_errors_total[5m]) / rate(ml_predictions_total[5m])
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `MLFLOW_TRACKING_URI` | URI MLflow сервера | `http://localhost:5000` |
| `MODEL_NAME` | Название модели в Registry | `fraud_detection_yandex_model` |
| `MODEL_ALIAS` | Алиас модели | `champion` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `ENABLE_METRICS` | Включить Prometheus метрики | `true` |
| `MAX_BATCH_SIZE` | Максимальный размер batch | `100` |

### MLflow модель

Сервис ожидает модель в MLflow Registry с:
- **Входные фичи:** `amount`, `merchant_category`, `hour_of_day`, `day_of_week`, `user_age`, `location_risk_score`
- **Выходные данные:** Вероятность мошенничества (0-1) или бинарная классификация
- **Методы:** `predict()` и опционально `predict_proba()`

## 🔧 Разработка

### Структура проекта

```
ml-k8s-fraud-detection/
├── app/                    # Основное приложение
│   ├── main.py            # FastAPI приложение
│   ├── core/              # Конфигурация и утилиты
│   ├── api/               # API роутеры
│   ├── models/            # ML модели
│   └── requirements.txt   # Python зависимости
├── tests/                 # Тесты
├── k8s/                   # Kubernetes манифесты
├── .github/workflows/     # CI/CD пайплайны
├── Dockerfile             # Docker образ
└── README.md             # Эта документация
```

### Добавление новых фичей

1. Создайте feature ветку
2. Добавьте код и тесты
3. Убедитесь что тесты проходят
4. Создайте Pull Request

### Code Style

Проект использует:
- **Black** для форматирования
- **isort** для сортировки импортов  
- **flake8** для линтинга
- **mypy** для проверки типов

## 🚨 Troubleshooting

### Частые проблемы

**Модель не загружается:**
- Проверьте доступность MLflow сервера
- Убедитесь что модель существует в Registry
- Проверьте правильность алиаса/стадии модели

**Высокое потребление памяти:**
- Уменьшите размер batch запросов
- Проверьте размер модели
- Рассмотрите использование CPU/memory limits в K8s

**Медленные предсказания:**
- Проверьте производительность модели
- Рассмотрите кеширование предсказаний
- Увеличьте количество реплик в K8s

### Логи и отладка

```bash
# Просмотр логов в K8s
kubectl logs -f deployment/fraud-detection-api -n fraud-detection

# Отладочная информация
curl http://localhost:8000/metrics/debug

# Проверка health checks
curl http://localhost:8000/health/ready
```

## 📋 TODO

- [ ] Добавить аутентификацию API
- [ ] Реализовать кеширование предсказаний
- [ ] Добавить A/B тестирование моделей
- [ ] Интеграция с Kafka для streaming
- [ ] Добавить distributed tracing

## 🔒 Безопасность

### ⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ ДЛЯ ПУБЛИЧНОГО РЕПОЗИТОРИЯ

Этот репозиторий подготовлен для публичного доступа. **ВСЕ СЕКРЕТНЫЕ ДАННЫЕ УДАЛЕНЫ** и заменены на примеры.

#### 🚫 Удаленные файлы (НЕ включайте в публичный репозиторий):
- `github-actions-key.json` - Приватный ключ сервисного аккаунта
- `kubeconfig-github-actions.yaml` - Kubeconfig с сертификатами  
- `terraform.tfstate*` - Terraform state с чувствительными данными

#### 📝 Example файлы (безопасные для публикации):
- `env.example` - Шаблон конфигурации
- `terraform.tfvars.example` - Пример настроек Terraform
- `github-actions-setup.example.json` - Инструкции по настройке CI/CD
- `kubeconfig.example.yaml` - Пример kubeconfig

### 🛡️ Настройка безопасности для production

1. **Переменные окружения**:
   ```bash
   cp env.example .env
   # Отредактируйте .env с РЕАЛЬНЫМИ значениями
   ```

2. **GitHub Secrets** (для CI/CD):
   - `YC_KEY` - Содержимое service account key
   - `YC_REGISTRY_ID` - ID Container Registry  
   - `KUBECONFIG_STAGING` - Base64 encoded kubeconfig

3. **Рекомендации**:
   - ✅ Используйте сильные пароли
   - ✅ Регулярно ротируйте секреты
   - ❌ НИКОГДА не коммитьте секреты в Git

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 👥 Авторы

- **ML Team** - Разработка и поддержка

---

⭐ **Если проект оказался полезным, поставьте звезду!**
