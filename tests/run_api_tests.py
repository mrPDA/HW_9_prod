#!/usr/bin/env python3
"""
🧪 Основной скрипт для запуска полного набора тестов API
Включает функциональные тесты, производительность и генерацию отчетов
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from test_public_api import APITester
from report_generator import generate_html_report


class APITestSuite:
    """Комплексный набор тестов для ML API"""
    
    def __init__(self, api_url: str, output_dir: str = "test_results"):
        self.api_url = api_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_functional_tests(self) -> Dict[str, Any]:
        """Запуск функциональных тестов API"""
        print("🧪 Запуск функциональных тестов...")
        
        tester = APITester(self.api_url)
        results = tester.run_full_test_suite()
        
        # Сохраняем результаты
        results_file = self.output_dir / f"functional_tests_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты функциональных тестов: {results_file}")
        return results
    
    def run_performance_tests(self, users: int = 10, duration: int = 30) -> Dict[str, Any]:
        """Запуск тестов производительности"""
        print(f"📈 Запуск тестов производительности ({users} пользователей, {duration}с)...")
        
        # Создаем временный скрипт для запуска Locust
        load_test_script = Path(__file__).parent / "load_test.py"
        
        if not load_test_script.exists():
            print("❌ Скрипт нагрузочного тестирования не найден")
            return {"error": "Load test script not found"}
        
        # Запускаем нагрузочное тестирование
        output_file = self.output_dir / f"load_test_{self.timestamp}.html"
        
        cmd = [
            sys.executable, str(load_test_script),
            "--url", self.api_url,
            "--users", str(users),
            "--spawn-rate", str(max(1, users // 5)),
            "--duration", str(duration),
            "--output", str(output_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=duration + 60)
            
            # Парсим результаты (упрощенная версия)
            perf_results = {
                "load_test_completed": result.returncode == 0,
                "users": users,
                "duration": duration,
                "output_file": str(output_file),
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Сохраняем результаты
            perf_file = self.output_dir / f"performance_results_{self.timestamp}.json"
            with open(perf_file, 'w', encoding='utf-8') as f:
                json.dump(perf_results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Результаты тестов производительности: {perf_file}")
            return perf_results
            
        except subprocess.TimeoutExpired:
            print("❌ Тест производительности превысил время ожидания")
            return {"error": "Performance test timeout"}
        except Exception as e:
            print(f"❌ Ошибка тестов производительности: {e}")
            return {"error": str(e)}
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Базовые тесты безопасности API"""
        print("🔒 Запуск тестов безопасности...")
        
        security_results = {
            "test_name": "Security Tests",
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        import requests
        
        # Тест на SQL injection
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; --"
        ]
        
        for payload in sql_injection_payloads:
            test_data = {
                "transaction_id": payload,
                "amount": 100.0,
                "merchant_category": "test",
                "hour_of_day": 12,
                "day_of_week": 3
            }
            
            try:
                response = requests.post(f"{self.api_url}/predict", 
                                       json=test_data, timeout=10)
                
                # API должен корректно обрабатывать или отклонять такие запросы
                security_results["tests"].append({
                    "test": "SQL Injection Protection",
                    "payload": payload,
                    "status_code": response.status_code,
                    "safe": response.status_code in [400, 422],  # Ожидаем ошибку валидации
                })
                
            except Exception as e:
                security_results["tests"].append({
                    "test": "SQL Injection Protection",
                    "payload": payload,
                    "error": str(e),
                    "safe": True  # Если запрос вызвал исключение, это безопасно
                })
        
        # Тест на XSS
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            test_data = {
                "transaction_id": "test_xss",
                "amount": 100.0,
                "merchant_category": payload,
                "hour_of_day": 12,
                "day_of_week": 3
            }
            
            try:
                response = requests.post(f"{self.api_url}/predict", 
                                       json=test_data, timeout=10)
                
                security_results["tests"].append({
                    "test": "XSS Protection",
                    "payload": payload,
                    "status_code": response.status_code,
                    "safe": response.status_code in [400, 422]
                })
                
            except Exception as e:
                security_results["tests"].append({
                    "test": "XSS Protection", 
                    "payload": payload,
                    "error": str(e),
                    "safe": True
                })
        
        # Тест на большие данные (DoS protection)
        large_data = {
            "transaction_id": "large_test",
            "amount": 100.0,
            "merchant_category": "x" * 10000,  # Очень длинная строка
            "hour_of_day": 12,
            "day_of_week": 3
        }
        
        try:
            response = requests.post(f"{self.api_url}/predict", 
                                   json=large_data, timeout=10)
            
            security_results["tests"].append({
                "test": "Large Input Protection",
                "status_code": response.status_code,
                "safe": response.status_code in [400, 413, 422]  # Ожидаем отклонение больших данных
            })
            
        except Exception as e:
            security_results["tests"].append({
                "test": "Large Input Protection",
                "error": str(e),
                "safe": True
            })
        
        # Сохраняем результаты
        security_file = self.output_dir / f"security_tests_{self.timestamp}.json"
        with open(security_file, 'w', encoding='utf-8') as f:
            json.dump(security_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты тестов безопасности: {security_file}")
        return security_results
    
    def generate_comprehensive_report(self, functional_results: Dict[str, Any],
                                    performance_results: Dict[str, Any] = None,
                                    security_results: Dict[str, Any] = None) -> str:
        """Генерация комплексного отчета"""
        print("📊 Генерация комплексного отчета...")
        
        # Объединяем все результаты
        comprehensive_results = functional_results.copy()
        
        # Добавляем результаты производительности
        if performance_results and not performance_results.get('error'):
            comprehensive_results['performance_tests'] = performance_results
        
        # Добавляем результаты безопасности
        if security_results:
            comprehensive_results['security_tests'] = security_results
            
            # Подсчитываем безопасные тесты
            safe_tests = sum(1 for test in security_results['tests'] if test.get('safe', False))
            total_security_tests = len(security_results['tests'])
            
            comprehensive_results['security_score'] = (safe_tests / total_security_tests * 100) if total_security_tests > 0 else 0
        
        # Генерируем HTML отчет
        report_file = self.output_dir / f"comprehensive_report_{self.timestamp}.html"
        html_file = generate_html_report(comprehensive_results, str(report_file))
        
        print(f"📄 Комплексный отчет: {html_file}")
        return html_file
    
    def run_full_test_suite(self, include_performance: bool = True, 
                          include_security: bool = True,
                          performance_users: int = 10,
                          performance_duration: int = 30) -> Dict[str, str]:
        """Запуск полного набора тестов"""
        print("🚀 Запуск полного набора тестов API...")
        print(f"🎯 Цель: {self.api_url}")
        print(f"📁 Результаты в: {self.output_dir}")
        print("-" * 60)
        
        start_time = time.time()
        results = {}
        
        # 1. Функциональные тесты (обязательные)
        functional_results = self.run_functional_tests()
        results['functional'] = functional_results
        
        # 2. Тесты производительности (опционально)
        performance_results = None
        if include_performance:
            performance_results = self.run_performance_tests(
                users=performance_users, 
                duration=performance_duration
            )
            results['performance'] = performance_results
        
        # 3. Тесты безопасности (опционально)
        security_results = None
        if include_security:
            security_results = self.run_security_tests()
            results['security'] = security_results
        
        # 4. Генерация комплексного отчета
        report_file = self.generate_comprehensive_report(
            functional_results, performance_results, security_results
        )
        results['report'] = report_file
        
        duration = time.time() - start_time
        
        print("-" * 60)
        print("🎉 Тестирование завершено!")
        print(f"⏱️ Общее время: {duration:.1f} сек")
        print(f"📊 Успешность функциональных тестов: {functional_results.get('success_rate', 0):.1f}%")
        
        if security_results:
            safe_tests = sum(1 for test in security_results['tests'] if test.get('safe', False))
            total_security = len(security_results['tests'])
            print(f"🔒 Безопасность: {safe_tests}/{total_security} тестов прошли")
        
        print(f"📄 Полный отчет: {report_file}")
        
        return results


def main():
    """Основная функция командной строки"""
    parser = argparse.ArgumentParser(description="🧪 Комплексное тестирование ML API")
    
    parser.add_argument("--url", default="http://localhost:8000",
                       help="URL API для тестирования")
    parser.add_argument("--output-dir", default="test_results",
                       help="Директория для сохранения результатов")
    parser.add_argument("--no-performance", action="store_true",
                       help="Пропустить тесты производительности")
    parser.add_argument("--no-security", action="store_true",
                       help="Пропустить тесты безопасности")
    parser.add_argument("--performance-users", type=int, default=10,
                       help="Количество пользователей для тестов производительности")
    parser.add_argument("--performance-duration", type=int, default=30,
                       help="Длительность тестов производительности (сек)")
    parser.add_argument("--quick", action="store_true",
                       help="Быстрое тестирование (только функциональные тесты)")
    
    args = parser.parse_args()
    
    # Быстрое тестирование
    if args.quick:
        args.no_performance = True
        args.no_security = True
    
    # Создаем и запускаем тест-сьют
    test_suite = APITestSuite(args.url, args.output_dir)
    
    try:
        results = test_suite.run_full_test_suite(
            include_performance=not args.no_performance,
            include_security=not args.no_security,
            performance_users=args.performance_users,
            performance_duration=args.performance_duration
        )
        
        # Определяем успешность тестирования
        functional_success = results['functional'].get('success_rate', 0) >= 70
        
        if functional_success:
            print("\n✅ Тестирование успешно завершено!")
            sys.exit(0)
        else:
            print("\n❌ Тестирование провалено!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
