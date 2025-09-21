#!/usr/bin/env python3
"""
🧪 Комплексное тестирование публичного ML API
Автоматизированное тестирование с генерацией отчетов
"""

import os
import json
import time
import requests
import pytest
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from jinja2 import Template
from pathlib import Path


class APITester:
    """Класс для комплексного тестирования ML API"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def log_test_result(self, test_name: str, status: str, 
                       response_time: float = None, details: Dict = None):
        """Логирование результата теста"""
        result = {
            'test_name': test_name,
            'status': status,
            'response_time_ms': response_time,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        print(f"📋 {test_name}: {status} ({response_time:.2f}ms)" if response_time else f"📋 {test_name}: {status}")
        
    def test_api_availability(self) -> bool:
        """Тест доступности API"""
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/", timeout=10)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                self.log_test_result("API Availability", "✅ PASS", response_time, 
                                   {"status_code": 200, "response": response.json()})
                return True
            else:
                self.log_test_result("API Availability", "❌ FAIL", response_time,
                                   {"status_code": response.status_code})
                return False
                
        except Exception as e:
            self.log_test_result("API Availability", "❌ ERROR", details={"error": str(e)})
            return False
    
    def test_health_endpoints(self) -> Dict[str, bool]:
        """Тест health check endpoints"""
        health_endpoints = ['/health', '/health/live', '/health/ready']
        results = {}
        
        for endpoint in health_endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                response_time = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    self.log_test_result(f"Health Check {endpoint}", "✅ PASS", 
                                       response_time, {"response": response.json()})
                    results[endpoint] = True
                else:
                    self.log_test_result(f"Health Check {endpoint}", "❌ FAIL", 
                                       response_time, {"status_code": response.status_code})
                    results[endpoint] = False
                    
            except Exception as e:
                self.log_test_result(f"Health Check {endpoint}", "❌ ERROR", 
                                   details={"error": str(e)})
                results[endpoint] = False
                
        return results
    
    def test_single_prediction(self) -> bool:
        """Тест единичного предсказания"""
        test_data = {
            "transaction_id": "test_001",
            "amount": 150.75,
            "merchant_category": "restaurant",
            "hour_of_day": 14,
            "day_of_week": 2,
            "user_age": 35,
            "location_risk_score": 0.2
        }
        
        try:
            start = time.time()
            response = requests.post(f"{self.base_url}/predict", 
                                   json=test_data, timeout=30)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                result = response.json()
                # Проверяем структуру ответа
                required_fields = ['transaction_id', 'is_fraud', 'fraud_probability', 
                                 'confidence', 'model_version', 'prediction_timestamp']
                
                if all(field in result for field in required_fields):
                    self.log_test_result("Single Prediction", "✅ PASS", response_time,
                                       {"prediction": result})
                    return True
                else:
                    missing_fields = [f for f in required_fields if f not in result]
                    self.log_test_result("Single Prediction", "❌ FAIL", response_time,
                                       {"missing_fields": missing_fields})
                    return False
            else:
                self.log_test_result("Single Prediction", "❌ FAIL", response_time,
                                   {"status_code": response.status_code, 
                                    "response": response.text})
                return False
                
        except Exception as e:
            self.log_test_result("Single Prediction", "❌ ERROR", 
                               details={"error": str(e)})
            return False
    
    def test_batch_prediction(self) -> bool:
        """Тест batch предсказаний"""
        test_data = {
            "transactions": [
                {
                    "transaction_id": "batch_001",
                    "amount": 50.0,
                    "merchant_category": "grocery",
                    "hour_of_day": 10,
                    "day_of_week": 1
                },
                {
                    "transaction_id": "batch_002",
                    "amount": 999.99,
                    "merchant_category": "electronics",
                    "hour_of_day": 23,
                    "day_of_week": 6
                }
            ]
        }
        
        try:
            start = time.time()
            response = requests.post(f"{self.base_url}/predict/batch", 
                                   json=test_data, timeout=30)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                if 'predictions' in result and len(result['predictions']) == 2:
                    self.log_test_result("Batch Prediction", "✅ PASS", response_time,
                                       {"batch_size": len(result['predictions'])})
                    return True
                else:
                    self.log_test_result("Batch Prediction", "❌ FAIL", response_time,
                                       {"response": result})
                    return False
            else:
                self.log_test_result("Batch Prediction", "❌ FAIL", response_time,
                                   {"status_code": response.status_code})
                return False
                
        except Exception as e:
            self.log_test_result("Batch Prediction", "❌ ERROR", 
                               details={"error": str(e)})
            return False
    
    def test_input_validation(self) -> Dict[str, bool]:
        """Тест валидации входных данных"""
        test_cases = {
            "missing_required_field": {
                "amount": 100.0,
                "merchant_category": "test"
                # transaction_id отсутствует
            },
            "invalid_data_types": {
                "transaction_id": "test_002",
                "amount": "invalid_amount",  # строка вместо числа
                "merchant_category": "test",
                "hour_of_day": 14,
                "day_of_week": 2
            },
            "out_of_range_values": {
                "transaction_id": "test_003",
                "amount": -100.0,  # отрицательная сумма
                "merchant_category": "test",
                "hour_of_day": 25,  # час > 23
                "day_of_week": 8    # день > 6
            }
        }
        
        results = {}
        for test_name, test_data in test_cases.items():
            try:
                start = time.time()
                response = requests.post(f"{self.base_url}/predict", 
                                       json=test_data, timeout=10)
                response_time = (time.time() - start) * 1000
                
                # Ожидаем 422 (Validation Error) для некорректных данных
                if response.status_code == 422:
                    self.log_test_result(f"Validation {test_name}", "✅ PASS", 
                                       response_time, {"expected_error": True})
                    results[test_name] = True
                else:
                    self.log_test_result(f"Validation {test_name}", "❌ FAIL", 
                                       response_time, 
                                       {"unexpected_status": response.status_code})
                    results[test_name] = False
                    
            except Exception as e:
                self.log_test_result(f"Validation {test_name}", "❌ ERROR", 
                                   details={"error": str(e)})
                results[test_name] = False
                
        return results
    
    def test_performance(self, num_requests: int = 10) -> Dict[str, float]:
        """Тест производительности API"""
        response_times = []
        successful_requests = 0
        
        test_data = {
            "transaction_id": "perf_test",
            "amount": 100.0,
            "merchant_category": "test",
            "hour_of_day": 12,
            "day_of_week": 3
        }
        
        print(f"🚀 Запуск performance теста ({num_requests} запросов)...")
        
        for i in range(num_requests):
            try:
                start = time.time()
                response = requests.post(f"{self.base_url}/predict", 
                                       json={**test_data, "transaction_id": f"perf_{i}"}, 
                                       timeout=30)
                response_time = (time.time() - start) * 1000
                response_times.append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                    
            except Exception as e:
                print(f"❌ Request {i} failed: {e}")
        
        if response_times:
            stats = {
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "success_rate": (successful_requests / num_requests) * 100,
                "total_requests": num_requests,
                "successful_requests": successful_requests
            }
            
            self.log_test_result("Performance Test", "✅ COMPLETED", 
                               stats["avg_response_time"], stats)
            return stats
        else:
            self.log_test_result("Performance Test", "❌ FAILED", 
                               details={"error": "No successful requests"})
            return {}
    
    def test_documentation_endpoints(self) -> Dict[str, bool]:
        """Тест endpoints документации"""
        doc_endpoints = ['/docs', '/redoc', '/openapi.json']
        results = {}
        
        for endpoint in doc_endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    self.log_test_result(f"Documentation {endpoint}", "✅ PASS", 
                                       response_time)
                    results[endpoint] = True
                else:
                    self.log_test_result(f"Documentation {endpoint}", "❌ FAIL", 
                                       response_time, {"status_code": response.status_code})
                    results[endpoint] = False
                    
            except Exception as e:
                self.log_test_result(f"Documentation {endpoint}", "❌ ERROR", 
                                   details={"error": str(e)})
                results[endpoint] = False
                
        return results
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Запуск полного набора тестов"""
        print("🧪 Начинаем комплексное тестирование API...")
        self.start_time = datetime.now()
        
        # Запуск всех тестов
        api_available = self.test_api_availability()
        
        if not api_available:
            print("❌ API недоступен, останавливаем тестирование")
            return {"error": "API unavailable"}
        
        health_results = self.test_health_endpoints()
        single_pred_result = self.test_single_prediction()
        batch_pred_result = self.test_batch_prediction()
        validation_results = self.test_input_validation()
        performance_stats = self.test_performance()
        doc_results = self.test_documentation_endpoints()
        
        self.end_time = datetime.now()
        
        # Сводная статистика
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == '✅ PASS' or r['status'] == '✅ COMPLETED'])
        failed_tests = len([r for r in self.results if r['status'] == '❌ FAIL'])
        error_tests = len([r for r in self.results if r['status'] == '❌ ERROR'])
        
        summary = {
            "test_run_id": f"api_test_{int(time.time())}",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "api_url": self.base_url,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "detailed_results": self.results,
            "performance_stats": performance_stats
        }
        
        print(f"\n📊 Тестирование завершено:")
        print(f"   ✅ Пройдено: {passed_tests}")
        print(f"   ❌ Провалено: {failed_tests}")  
        print(f"   🔴 Ошибки: {error_tests}")
        print(f"   📈 Успешность: {summary['success_rate']:.1f}%")
        
        return summary


def test_public_api_comprehensive():
    """Pytest функция для запуска комплексного тестирования"""
    # Определяем URL API из переменных окружения или используем дефолтный
    api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    tester = APITester(api_url)
    results = tester.run_full_test_suite()
    
    # Сохраняем результаты в JSON
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"api_test_results_{int(time.time())}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Результаты сохранены в: {results_file}")
    
    # Проверяем что основные тесты прошли
    assert results.get('success_rate', 0) >= 70, f"Success rate too low: {results.get('success_rate', 0)}%"


if __name__ == "__main__":
    # Запуск как standalone скрипт
    import sys
    
    api_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
    
    tester = APITester(api_url)
    results = tester.run_full_test_suite()
    
    # Сохраняем результаты
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"api_test_results_{int(time.time())}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в: {results_file}")
    
    # Возвращаем код выхода на основе результатов
    if results.get('success_rate', 0) >= 70:
        print("🎉 Тестирование успешно завершено!")
        sys.exit(0)
    else:
        print("❌ Тестирование провалено!")
        sys.exit(1)
