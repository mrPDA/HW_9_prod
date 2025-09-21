#!/usr/bin/env python3
"""
📊 Генератор HTML отчетов для тестирования API
Создает красивые отчеты с графиками и статистикой
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import base64
from io import BytesIO


def generate_html_report(test_results: Dict[str, Any], output_file: str = None) -> str:
    """Генерация HTML отчета по результатам тестирования"""
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"api_test_report_{timestamp}.html"
    
    # Подготовка данных для отчета
    total_tests = test_results.get('total_tests', 0)
    passed_tests = test_results.get('passed_tests', 0)
    failed_tests = test_results.get('failed_tests', 0)
    error_tests = test_results.get('error_tests', 0)
    success_rate = test_results.get('success_rate', 0)
    
    # Группировка результатов по категориям
    test_categories = {}
    for result in test_results.get('detailed_results', []):
        test_name = result['test_name']
        category = 'Other'
        
        if 'Health Check' in test_name:
            category = 'Health Checks'
        elif 'Prediction' in test_name:
            category = 'ML Predictions'
        elif 'Validation' in test_name:
            category = 'Input Validation'
        elif 'Performance' in test_name:
            category = 'Performance'
        elif 'Documentation' in test_name:
            category = 'Documentation'
        elif 'API Availability' in test_name:
            category = 'Availability'
            
        if category not in test_categories:
            test_categories[category] = []
        test_categories[category].append(result)
    
    # Статистика производительности
    perf_stats = test_results.get('performance_stats', {})
    
    # HTML шаблон
    html_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ ML API Testing Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .danger { color: #dc3545; }
        .info { color: #17a2b8; }
        
        .content {
            padding: 30px;
        }
        
        .test-category {
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .category-header {
            background: #343a40;
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .test-list {
            padding: 20px;
        }
        
        .test-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #dee2e6;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .test-item.pass { border-left-color: #28a745; }
        .test-item.fail { border-left-color: #dc3545; }
        .test-item.error { border-left-color: #ffc107; }
        
        .test-name {
            font-weight: 600;
        }
        
        .test-status {
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .test-status.pass {
            background: #d4edda;
            color: #155724;
        }
        
        .test-status.fail {
            background: #f8d7da;
            color: #721c24;
        }
        
        .test-status.error {
            background: #fff3cd;
            color: #856404;
        }
        
        .test-time {
            color: #666;
            font-size: 0.9em;
        }
        
        .performance-section {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .performance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .perf-metric {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .perf-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #1565c0;
        }
        
        .perf-label {
            color: #666;
            font-size: 0.8em;
            margin-top: 5px;
        }
        
        .footer {
            background: #343a40;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.8em;
        }
        
        .api-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .summary {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .container {
                margin: 10px;
                border-radius: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ ML Fraud Detection API</h1>
            <div class="subtitle">Отчет о тестировании • {{test_date}}</div>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value success">{{total_tests}}</div>
                <div class="metric-label">Всего тестов</div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">{{passed_tests}}</div>
                <div class="metric-label">Пройдено</div>
            </div>
            <div class="metric-card">
                <div class="metric-value danger">{{failed_tests}}</div>
                <div class="metric-label">Провалено</div>
            </div>
            <div class="metric-card">
                <div class="metric-value warning">{{error_tests}}</div>
                <div class="metric-label">Ошибки</div>
            </div>
            <div class="metric-card">
                <div class="metric-value info">{{success_rate}}%</div>
                <div class="metric-label">Успешность</div>
            </div>
        </div>
        
        <div class="content">
            <div class="api-info">
                <strong>🔗 API URL:</strong> {{api_url}}<br>
                <strong>⏱️ Время выполнения:</strong> {{duration}} сек<br>
                <strong>🆔 Test Run ID:</strong> {{test_run_id}}
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{success_rate}}%;">
                    {{success_rate}}% успешных тестов
                </div>
            </div>
            
            {{performance_section}}
            
            {{test_categories_html}}
        </div>
        
        <div class="footer">
            Сгенерировано автоматически • ML DevOps Pipeline • {{timestamp}}
        </div>
    </div>
</body>
</html>
    """
    
    # Генерация секции производительности
    performance_section = ""
    if perf_stats:
        performance_section = f"""
        <div class="performance-section">
            <h3>📈 Производительность API</h3>
            <div class="performance-grid">
                <div class="perf-metric">
                    <div class="perf-value">{perf_stats.get('avg_response_time', 0):.1f}</div>
                    <div class="perf-label">Среднее время (мс)</div>
                </div>
                <div class="perf-metric">
                    <div class="perf-value">{perf_stats.get('min_response_time', 0):.1f}</div>
                    <div class="perf-label">Минимальное (мс)</div>
                </div>
                <div class="perf-metric">
                    <div class="perf-value">{perf_stats.get('max_response_time', 0):.1f}</div>
                    <div class="perf-label">Максимальное (мс)</div>
                </div>
                <div class="perf-metric">
                    <div class="perf-value">{perf_stats.get('success_rate', 0):.1f}%</div>
                    <div class="perf-label">Успешность</div>
                </div>
                <div class="perf-metric">
                    <div class="perf-value">{perf_stats.get('total_requests', 0)}</div>
                    <div class="perf-label">Всего запросов</div>
                </div>
            </div>
        </div>
        """
    
    # Генерация секций по категориям
    test_categories_html = ""
    for category, tests in test_categories.items():
        category_html = f"""
        <div class="test-category">
            <div class="category-header">📋 {category}</div>
            <div class="test-list">
        """
        
        for test in tests:
            status_class = "pass"
            if "FAIL" in test['status']:
                status_class = "fail"
            elif "ERROR" in test['status']:
                status_class = "error"
            
            response_time_html = ""
            if test.get('response_time_ms'):
                response_time_html = f'<span class="test-time">({test["response_time_ms"]:.1f}ms)</span>'
            
            category_html += f"""
                <div class="test-item {status_class}">
                    <div class="test-name">{test['test_name']}</div>
                    <div>
                        <span class="test-status {status_class}">{test['status']}</span>
                        {response_time_html}
                    </div>
                </div>
            """
        
        category_html += """
            </div>
        </div>
        """
        test_categories_html += category_html
    
    # Заполнение шаблона
    html_content = html_template.replace("{{test_date}}", datetime.fromtimestamp(int(test_results.get('test_run_id', 'test').split('_')[-1])).strftime("%d.%m.%Y %H:%M"))
    html_content = html_content.replace("{{total_tests}}", str(total_tests))
    html_content = html_content.replace("{{passed_tests}}", str(passed_tests))
    html_content = html_content.replace("{{failed_tests}}", str(failed_tests))
    html_content = html_content.replace("{{error_tests}}", str(error_tests))
    html_content = html_content.replace("{{success_rate}}", f"{success_rate:.1f}")
    html_content = html_content.replace("{{api_url}}", test_results.get('api_url', 'Unknown'))
    html_content = html_content.replace("{{duration}}", f"{test_results.get('duration_seconds', 0):.1f}")
    html_content = html_content.replace("{{test_run_id}}", test_results.get('test_run_id', 'Unknown'))
    html_content = html_content.replace("{{performance_section}}", performance_section)
    html_content = html_content.replace("{{test_categories_html}}", test_categories_html)
    html_content = html_content.replace("{{timestamp}}", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    
    # Сохранение HTML файла
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(output_path.absolute())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Использование: python report_generator.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            test_results = json.load(f)
        
        html_file = generate_html_report(test_results, output_file)
        print(f"✅ HTML отчет сгенерирован: {html_file}")
        
    except Exception as e:
        print(f"❌ Ошибка генерации отчета: {e}")
        sys.exit(1)
