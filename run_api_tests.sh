#!/bin/bash
# 🧪 Быстрый запуск тестирования ML API
# Скрипт для автоматизации процесса тестирования и генерации отчетов

set -e  # Остановка при первой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация по умолчанию
API_URL="${API_URL:-http://localhost:8000}"
OUTPUT_DIR="${OUTPUT_DIR:-test_results}"
PERFORMANCE_USERS="${PERFORMANCE_USERS:-10}"
PERFORMANCE_DURATION="${PERFORMANCE_DURATION:-30}"
QUICK_MODE="${QUICK_MODE:-false}"

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Функция проверки зависимостей
check_dependencies() {
    log "Проверка зависимостей..."
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 не найден. Установите Python 3.11+"
        exit 1
    fi
    
    # Проверяем pip
    if ! command -v pip &> /dev/null; then
        error "pip не найден. Установите pip"
        exit 1
    fi
    
    # Устанавливаем зависимости если нужно
    if [ ! -d "tests/__pycache__" ] || [ ! -f "tests/requirements.txt" ]; then
        log "Установка зависимостей для тестирования..."
        pip install -r tests/requirements.txt
    fi
    
    success "Зависимости проверены"
}

# Функция запуска API в фоне
start_api() {
    log "Запуск ML API на $API_URL..."
    
    # Проверяем доступность порта
    if curl -f "$API_URL/health" &> /dev/null; then
        warning "API уже запущен на $API_URL"
        return 0
    fi
    
    # Запускаем API в фоне
    cd app
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    cd ..
    
    # Ждем запуска API
    log "Ожидание запуска API..."
    for i in {1..30}; do
        if curl -f "$API_URL/health" &> /dev/null; then
            success "API успешно запущен (PID: $API_PID)"
            echo $API_PID > api.pid
            return 0
        fi
        sleep 2
    done
    
    error "Не удалось запустить API за 60 секунд"
    exit 1
}

# Функция остановки API
stop_api() {
    if [ -f "api.pid" ]; then
        API_PID=$(cat api.pid)
        log "Остановка API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        rm -f api.pid
        success "API остановлен"
    fi
}

# Функция запуска функциональных тестов
run_functional_tests() {
    log "Запуск функциональных тестов..."
    
    cd tests
    if $QUICK_MODE; then
        python run_api_tests.py \
            --url "$API_URL" \
            --output-dir "$OUTPUT_DIR" \
            --quick
    else
        python run_api_tests.py \
            --url "$API_URL" \
            --output-dir "$OUTPUT_DIR" \
            --no-performance
    fi
    cd ..
    
    success "Функциональные тесты завершены"
}

# Функция запуска тестов производительности
run_performance_tests() {
    if $QUICK_MODE; then
        warning "Тесты производительности пропущены (быстрый режим)"
        return 0
    fi
    
    log "Запуск тестов производительности ($PERFORMANCE_USERS пользователей, ${PERFORMANCE_DURATION}с)..."
    
    cd tests
    python load_test.py \
        --url "$API_URL" \
        --users "$PERFORMANCE_USERS" \
        --duration "$PERFORMANCE_DURATION" \
        --output "${OUTPUT_DIR}/performance_report.html"
    cd ..
    
    success "Тесты производительности завершены"
}

# Функция генерации комплексного отчета
generate_comprehensive_report() {
    log "Генерация комплексного отчета..."
    
    cd tests
    python run_api_tests.py \
        --url "$API_URL" \
        --output-dir "$OUTPUT_DIR" \
        --performance-users $(( PERFORMANCE_USERS / 2 )) \
        --performance-duration 15
    cd ..
    
    success "Комплексный отчет сгенерирован"
}

# Функция отображения результатов
show_results() {
    log "Результаты тестирования:"
    echo ""
    
    if [ -d "$OUTPUT_DIR" ]; then
        echo "📁 Файлы отчетов в директории: $OUTPUT_DIR"
        find "$OUTPUT_DIR" -name "*.html" -o -name "*.json" | while read file; do
            echo "  📄 $(basename "$file")"
        done
        echo ""
        
        # Ищем основной HTML отчет
        MAIN_REPORT=$(find "$OUTPUT_DIR" -name "*comprehensive_report*.html" | head -1)
        if [ -n "$MAIN_REPORT" ]; then
            success "Основной отчет: $MAIN_REPORT"
            
            # Пытаемся открыть в браузере (macOS/Linux)
            if command -v open &> /dev/null; then
                log "Открытие отчета в браузере..."
                open "$MAIN_REPORT"
            elif command -v xdg-open &> /dev/null; then
                log "Открытие отчета в браузере..."
                xdg-open "$MAIN_REPORT"
            else
                log "Откройте отчет вручную: file://$(pwd)/$MAIN_REPORT"
            fi
        fi
    else
        warning "Директория с результатами не найдена"
    fi
}

# Функция очистки
cleanup() {
    log "Очистка..."
    stop_api
    success "Очистка завершена"
}

# Обработка сигналов
trap cleanup EXIT INT TERM

# Функция показа помощи
show_help() {
    cat << EOF
🧪 ML API Testing Script

Использование: $0 [OPTIONS]

Опции:
  -u, --url URL              API URL для тестирования (по умолчанию: http://localhost:8000)
  -o, --output DIR           Директория для результатов (по умолчанию: test_results)
  -q, --quick               Быстрый режим (только функциональные тесты)
  -p, --performance-users N  Количество пользователей для нагрузочного тестирования (по умолчанию: 10)
  -d, --duration N          Длительность нагрузочного тестирования в секундах (по умолчанию: 30)
  --no-start-api            Не запускать API автоматически
  --only-functional         Только функциональные тесты
  --only-performance        Только тесты производительности
  --only-report             Только генерация отчета
  -h, --help               Показать эту справку

Переменные окружения:
  API_URL                   URL API
  OUTPUT_DIR               Директория результатов
  PERFORMANCE_USERS        Количество пользователей
  PERFORMANCE_DURATION     Длительность тестирования
  QUICK_MODE               Быстрый режим (true/false)

Примеры:
  $0                       # Полное тестирование локального API
  $0 --quick              # Быстрое тестирование
  $0 -u http://prod-api:8000  # Тестирование production API
  $0 --only-performance   # Только нагрузочные тесты
EOF
}

# Обработка аргументов командной строки
ONLY_FUNCTIONAL=false
ONLY_PERFORMANCE=false
ONLY_REPORT=false
START_API=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -p|--performance-users)
            PERFORMANCE_USERS="$2"
            shift 2
            ;;
        -d|--duration)
            PERFORMANCE_DURATION="$2"
            shift 2
            ;;
        --no-start-api)
            START_API=false
            shift
            ;;
        --only-functional)
            ONLY_FUNCTIONAL=true
            shift
            ;;
        --only-performance)
            ONLY_PERFORMANCE=true
            shift
            ;;
        --only-report)
            ONLY_REPORT=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Основная логика
main() {
    echo ""
    echo "🧪 ML Fraud Detection API Testing"
    echo "=================================="
    echo "🎯 API URL: $API_URL"
    echo "📁 Результаты: $OUTPUT_DIR"
    echo "⚡ Режим: $([ "$QUICK_MODE" = true ] && echo "Быстрый" || echo "Полный")"
    echo ""
    
    # Проверяем зависимости
    check_dependencies
    
    # Создаем директорию для результатов
    mkdir -p "$OUTPUT_DIR"
    
    # Запускаем API если нужно
    if $START_API; then
        start_api
    fi
    
    # Выполняем тестирование
    if $ONLY_PERFORMANCE; then
        run_performance_tests
    elif $ONLY_REPORT; then
        generate_comprehensive_report
    elif $ONLY_FUNCTIONAL; then
        run_functional_tests
    else
        # Полное тестирование
        run_functional_tests
        run_performance_tests
        generate_comprehensive_report
    fi
    
    # Показываем результаты
    show_results
    
    success "Тестирование завершено успешно! 🎉"
}

# Запуск основной функции
main
