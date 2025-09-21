#!/usr/bin/env python3
"""
🚀 Нагрузочное тестирование ML API с помощью Locust
Автоматическое тестирование производительности под нагрузкой
"""

import random
import json
import time
from locust import HttpUser, task, between
from datetime import datetime


class MLAPIUser(HttpUser):
    """Пользователь для нагрузочного тестирования ML API"""
    
    wait_time = between(1, 3)  # Пауза между запросами 1-3 секунды
    
    def on_start(self):
        """Инициализация при запуске пользователя"""
        self.test_data_pool = self._generate_test_data_pool(100)
        
    def _generate_test_data_pool(self, size: int) -> list:
        """Генерация пула тестовых данных"""
        merchant_categories = [
            "restaurant", "grocery", "gas_station", "pharmacy", "retail",
            "electronics", "clothing", "entertainment", "travel", "online"
        ]
        
        data_pool = []
        for i in range(size):
            data = {
                "transaction_id": f"load_test_{i}_{int(time.time())}",
                "amount": round(random.uniform(1.0, 2000.0), 2),
                "merchant_category": random.choice(merchant_categories),
                "hour_of_day": random.randint(0, 23),
                "day_of_week": random.randint(0, 6),
                "user_age": random.randint(18, 80),
                "location_risk_score": round(random.uniform(0.0, 1.0), 3)
            }
            data_pool.append(data)
        
        return data_pool
    
    @task(3)
    def test_single_prediction(self):
        """Тест единичного предсказания (вес 3)"""
        test_data = random.choice(self.test_data_pool)
        test_data["transaction_id"] = f"single_{int(time.time())}_{random.randint(1000, 9999)}"
        
        with self.client.post("/predict", json=test_data, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Проверяем обязательные поля
                    required_fields = ['transaction_id', 'is_fraud', 'fraud_probability']
                    if all(field in result for field in required_fields):
                        response.success()
                    else:
                        response.failure(f"Missing required fields: {required_fields}")
                except Exception as e:
                    response.failure(f"Invalid JSON response: {e}")
            elif response.status_code == 422:
                response.failure("Validation error")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def test_batch_prediction(self):
        """Тест batch предсказаний (вес 1)"""
        batch_size = random.randint(2, 5)
        transactions = random.sample(self.test_data_pool, batch_size)
        
        # Обновляем transaction_id для уникальности
        for i, transaction in enumerate(transactions):
            transaction["transaction_id"] = f"batch_{int(time.time())}_{i}"
        
        batch_data = {"transactions": transactions}
        
        with self.client.post("/predict/batch", json=batch_data, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'predictions' in result and len(result['predictions']) == batch_size:
                        response.success()
                    else:
                        response.failure(f"Unexpected batch response structure")
                except Exception as e:
                    response.failure(f"Invalid JSON response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def test_health_check(self):
        """Тест health check (вес 1)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: HTTP {response.status_code}")
    
    @task(1)
    def test_api_root(self):
        """Тест корневого endpoint (вес 1)"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'service' in result:
                        response.success()
                    else:
                        response.failure("Missing service info in root response")
                except Exception as e:
                    response.failure(f"Invalid JSON response: {e}")
            else:
                response.failure(f"Root endpoint failed: HTTP {response.status_code}")


class StressTestUser(HttpUser):
    """Пользователь для стресс-тестирования с высокой нагрузкой"""
    
    wait_time = between(0.1, 0.5)  # Минимальная пауза для стресс-теста
    
    def on_start(self):
        """Инициализация стресс-тестирования"""
        self.stress_test_data = {
            "transaction_id": f"stress_{int(time.time())}",
            "amount": 100.0,
            "merchant_category": "test",
            "hour_of_day": 12,
            "day_of_week": 3
        }
    
    @task
    def stress_predict(self):
        """Стресс-тест предсказаний"""
        self.stress_test_data["transaction_id"] = f"stress_{int(time.time())}_{random.randint(1000, 9999)}"
        
        with self.client.post("/predict", json=self.stress_test_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Stress test failed: HTTP {response.status_code}")


def run_load_test_scenario(api_url: str, users: int = 10, spawn_rate: int = 2, 
                          duration: int = 60, output_file: str = None):
    """
    Запуск сценария нагрузочного тестирования
    
    Args:
        api_url: URL API для тестирования
        users: Количество виртуальных пользователей
        spawn_rate: Скорость появления пользователей (пользователей/сек)
        duration: Длительность теста в секундах
        output_file: Файл для сохранения результатов
    """
    import subprocess
    import os
    
    # Создаем команду для запуска Locust
    cmd = [
        "locust",
        "-f", __file__,
        "-H", api_url,
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", f"{duration}s",
        "--headless",
        "--only-summary"
    ]
    
    if output_file:
        cmd.extend(["--html", output_file])
    
    print(f"🚀 Запуск нагрузочного тестирования:")
    print(f"   🎯 URL: {api_url}")
    print(f"   👥 Пользователи: {users}")
    print(f"   📈 Скорость: {spawn_rate} пользователей/сек")
    print(f"   ⏱️ Длительность: {duration} сек")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 30)
        
        print("\n📊 Результаты нагрузочного тестирования:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ Предупреждения:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Тест превысил максимальное время выполнения")
        return False
    except Exception as e:
        print(f"❌ Ошибка выполнения теста: {e}")
        return False


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="🚀 Нагрузочное тестирование ML API")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL API (по умолчанию: http://localhost:8000)")
    parser.add_argument("--users", type=int, default=10,
                       help="Количество виртуальных пользователей (по умолчанию: 10)")
    parser.add_argument("--spawn-rate", type=int, default=2,
                       help="Скорость появления пользователей/сек (по умолчанию: 2)")
    parser.add_argument("--duration", type=int, default=60,
                       help="Длительность теста в секундах (по умолчанию: 60)")
    parser.add_argument("--output", 
                       help="Файл для сохранения HTML отчета")
    parser.add_argument("--mode", choices=["normal", "stress"], default="normal",
                       help="Режим тестирования (normal/stress)")
    
    args = parser.parse_args()
    
    if args.mode == "stress":
        print("⚡ Режим стресс-тестирования активирован")
        # Для стресс-тестирования увеличиваем нагрузку
        args.users = args.users * 2
        args.spawn_rate = args.spawn_rate * 3
    
    # Генерируем имя файла отчета если не указано
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"load_test_report_{timestamp}.html"
    
    success = run_load_test_scenario(
        api_url=args.url,
        users=args.users,
        spawn_rate=args.spawn_rate,
        duration=args.duration,
        output_file=args.output
    )
    
    if success:
        print(f"✅ Нагрузочное тестирование завершено успешно")
        if args.output:
            print(f"📊 Отчет сохранен: {args.output}")
        sys.exit(0)
    else:
        print("❌ Нагрузочное тестирование провалено")
        sys.exit(1)
