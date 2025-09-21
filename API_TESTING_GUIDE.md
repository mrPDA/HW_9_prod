# 🧪 Руководство по тестированию ML API

## 📋 Содержание
- [Обзор системы тестирования](#обзор-системы-тестирования)
- [Быстрый старт](#быстрый-старт)
- [Типы тестов](#типы-тестов)
- [Генерация отчетов](#генерация-отчетов)
- [CI/CD интеграция](#cicd-интеграция)
- [Примеры использования](#примеры-использования)

## 🎯 Обзор системы тестирования

Наша система тестирования ML API включает:

### ✅ Комплексное тестирование
- **Функциональные тесты** - проверка корректности API endpoints
- **Тесты производительности** - нагрузочное тестирование с Locust
- **Тесты безопасности** - проверка на XSS, SQL injection, DoS
- **Интеграционные тесты** - проверка взаимодействия компонентов

### 📊 Автоматическая генерация отчетов
- **HTML отчеты** с красивой визуализацией
- **JSON отчеты** для интеграции с CI/CD
- **Метрики производительности** с графиками
- **Статистика безопасности** с детализацией

### 🚀 CI/CD интеграция
- **GitHub Actions** workflows
- **Автоматические тесты** при каждом commit
- **Deployment gates** на основе результатов тестирования
- **Уведомления** о результатах тестирования

## ⚡ Быстрый старт

### 1. Установка зависимостей
```bash
# Установка всех зависимостей
make install-dev

# Или установка только для тестирования
pip install -r tests/requirements.txt
```

### 2. Запуск быстрого тестирования
```bash
# Полное тестирование с автозапуском API
./run_api_tests.sh

# Быстрое тестирование (только функциональные тесты)
./run_api_tests.sh --quick

# Тестирование внешнего API
./run_api_tests.sh --url https://your-api.domain.com
```

### 3. Использование Makefile
```bash
# Комплексное тестирование
make test-api-public

# Тестирование с автозапуском API
make test-api-local

# Только производительность
make test-api-performance

# Только безопасность
make test-api-security

# Генерация отчетов
make test-api-reports
```

## 🧪 Типы тестов

### 1. Функциональные тесты
Проверяют корректность работы API endpoints:

```python
# Пример запуска
cd tests
python test_public_api.py

# Или через основной скрипт
python run_api_tests.py --url http://localhost:8000 --no-performance
```

**Что тестируется:**
- ✅ Доступность API (`/`, `/health`, `/docs`)
- ✅ Единичные предсказания (`/predict`)
- ✅ Batch предсказания (`/predict/batch`)
- ✅ Валидация входных данных
- ✅ Обработка ошибок
- ✅ Структура ответов

### 2. Тесты производительности
Нагрузочное тестирование с помощью Locust:

```bash
# Запуск нагрузочных тестов
cd tests
python load_test.py --url http://localhost:8000 --users 20 --duration 60

# Интерактивный режим
locust -f load_test.py --host http://localhost:8000
# Открыть http://localhost:8089 для веб-интерфейса
```

**Метрики производительности:**
- 📈 Среднее время отклика
- 📊 Пропускная способность (RPS)
- 🎯 Процент успешных запросов
- 📉 95-й и 99-й перцентили времени отклика

### 3. Тесты безопасности
Проверка на базовые уязвимости:

```python
# Запуск тестов безопасности
cd tests
python run_api_tests.py --url http://localhost:8000 --no-performance --no-security=false
```

**Что тестируется:**
- 🛡️ SQL injection защита
- 🔒 XSS (Cross-Site Scripting) защита
- 🚫 DoS защита от больших данных
- ✨ Валидация и санитизация входных данных

## 📊 Генерация отчетов

### HTML отчеты
Создаются автоматически для каждого запуска тестов:

```bash
# Генерация полного отчета
cd tests
python run_api_tests.py --url http://localhost:8000 --output-dir ../test_results

# Результат: test_results/comprehensive_report_YYYYMMDD_HHMMSS.html
```

**Структура HTML отчета:**
- 📋 Сводная статистика тестирования
- 📈 Метрики производительности с графиками
- 🧪 Детальные результаты по категориям
- 🔒 Отчет по безопасности
- ⏱️ Временные метрики

### JSON отчеты
Для интеграции с внешними системами:

```bash
# JSON отчеты создаются автоматически
ls test_results/
# functional_tests_YYYYMMDD_HHMMSS.json
# performance_results_YYYYMMDD_HHMMSS.json
# security_tests_YYYYMMDD_HHMMSS.json
```

### Пример отчета
```json
{
  "test_run_id": "api_test_1727649123",
  "start_time": "2024-09-30T10:15:23.456789",
  "end_time": "2024-09-30T10:17:45.789012",
  "api_url": "http://localhost:8000",
  "total_tests": 15,
  "passed_tests": 14,
  "failed_tests": 1,
  "success_rate": 93.3,
  "performance_stats": {
    "avg_response_time": 245.6,
    "min_response_time": 89.2,
    "max_response_time": 1203.4,
    "success_rate": 98.5
  }
}
```

## 🔄 CI/CD интеграция

### GitHub Actions
Автоматические тесты настроены в `.github/workflows/api-testing.yml`:

```yaml
# Запуск тестов при каждом push
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 9-17 * * 1-5'  # Каждый час в рабочее время
```

**Этапы CI/CD:**
1. 🚀 Подготовка и запуск API
2. 🧪 Функциональные тесты
3. 📈 Тесты производительности  
4. 🔒 Тесты безопасности
5. 📊 Генерация комплексного отчета
6. 🚨 Уведомления о результатах

### Deployment Gates
Развертывание блокируется если:
- ❌ Успешность функциональных тестов < 90%
- ❌ Среднее время отклика > 1000ms
- ❌ Критические уязвимости безопасности
- ❌ Процент успешных запросов < 95%

### Ручной запуск через GitHub Actions
```bash
# Через веб-интерфейс GitHub
# Actions -> API Testing & Reports -> Run workflow
# Параметры:
# - API URL: https://your-api.domain.com
# - Include performance: true
# - Performance users: 20
# - Performance duration: 60
```

## 🛠️ Примеры использования

### Локальная разработка
```bash
# Запуск API в одном терминале
cd app
python -m uvicorn main:app --reload

# Тестирование в другом терминале
./run_api_tests.sh --quick
```

### Тестирование staging окружения
```bash
./run_api_tests.sh \
  --url https://api-staging.yourdomain.com \
  --performance-users 5 \
  --duration 30 \
  --output staging_results
```

### Production health check
```bash
./run_api_tests.sh \
  --url https://api.yourdomain.com \
  --only-functional \
  --output production_health
```

### Нагрузочное тестирование
```bash
# Интенсивный тест
./run_api_tests.sh \
  --url http://localhost:8000 \
  --only-performance \
  --performance-users 50 \
  --duration 300  # 5 минут
```

### Regression тестирование
```bash
# Полное тестирование перед релизом
./run_api_tests.sh \
  --url https://api-staging.yourdomain.com \
  --performance-users 20 \
  --duration 120 \
  --output regression_test_$(date +%Y%m%d)
```

## 📈 Интерпретация результатов

### Успешное тестирование
```
✅ Пройдено: 15
❌ Провалено: 0
🔴 Ошибки: 0
📈 Успешность: 100.0%
```

### Метрики производительности
- **< 200ms** - Отлично 🟢
- **200-500ms** - Хорошо 🟡
- **500-1000ms** - Приемлемо 🟠
- **> 1000ms** - Требует оптимизации 🔴

### Безопасность
- **100% безопасных тестов** - Отлично 🟢
- **90-99%** - Хорошо, требует внимания 🟡
- **< 90%** - Критично, требует исправления 🔴

## 🔧 Конфигурация

### Переменные окружения
```bash
# API настройки
export API_URL="http://localhost:8000"
export API_TIMEOUT="30"

# Настройки тестирования
export PERFORMANCE_USERS="10"
export PERFORMANCE_DURATION="30"
export OUTPUT_DIR="test_results"

# Режим тестирования
export QUICK_MODE="false"
export INCLUDE_SECURITY="true"
export INCLUDE_PERFORMANCE="true"
```

### Кастомизация тестов
Настройте параметры в `tests/run_api_tests.py`:

```python
# Количество запросов для performance тестов
DEFAULT_PERFORMANCE_REQUESTS = 100

# Таймауты
API_TIMEOUT = 30
HEALTH_CHECK_TIMEOUT = 10

# Пороги успешности
MIN_SUCCESS_RATE = 70
MAX_AVG_RESPONSE_TIME = 1000
```

## 🆘 Troubleshooting

### Проблема: API не запускается
```bash
# Проверка порта
lsof -i :8000

# Проверка логов
cd app && python -m uvicorn main:app --log-level debug

# Проверка зависимостей
pip install -r app/requirements.txt
```

### Проблема: Тесты падают с timeout
```bash
# Увеличьте таймауты
./run_api_tests.sh --url http://localhost:8000 --duration 10

# Проверьте нагрузку на систему
htop
```

### Проблема: Низкая производительность
```bash
# Проверьте конфигурацию API
cd app && python -m uvicorn main:app --workers 2

# Мониторинг ресурсов
docker stats  # если используете Docker
```

## 📞 Поддержка

### Логи тестирования
```bash
# Детальные логи
./run_api_tests.sh --url http://localhost:8000 2>&1 | tee test.log

# Анализ производительности
cd tests && python load_test.py --help
```

### Отладка
```bash
# Запуск конкретного теста
cd tests
python -m pytest test_public_api.py::test_single_prediction -v

# Интерактивный режим
python -i run_api_tests.py
```

---

## 🎉 Заключение

Система тестирования ML API обеспечивает:
- ✅ **Качество** - комплексная проверка функциональности
- 📊 **Производительность** - мониторинг под нагрузкой  
- 🔒 **Безопасность** - защита от основных угроз
- 📈 **Мониторинг** - подробные отчеты и метрики
- 🚀 **CI/CD** - автоматизация в процессе разработки

**Готово к production использованию!** 🚀
