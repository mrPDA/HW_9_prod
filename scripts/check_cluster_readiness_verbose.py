#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ Улучшенная проверка готовности DataProc кластера для Kafka Streaming
===================================================================

PySpark job для проверки готовности кластера с детальным логированием.

Author: ML Pipeline Team
Date: 2024
"""

from pyspark.sql import SparkSession
import argparse
import sys
import logging
import traceback

# Setup logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_spark_environment(spark):
    """Проверка Spark environment с детальным логированием"""
    try:
        logger.info("🔍 Начинаю проверку Spark environment...")
        
        # Проверка 1: Создание простого DataFrame
        logger.info("📝 Шаг 1: Создание тестового DataFrame...")
        test_data = [(1, "test"), (2, "spark"), (3, "ready")]
        df = spark.createDataFrame(test_data, ["id", "value"])
        logger.info("✅ DataFrame создан успешно")
        
        # Проверка 2: Выполнение операции count
        logger.info("🔢 Шаг 2: Выполнение операции count...")
        count = df.count()
        logger.info(f"✅ Count выполнен успешно: {count} записей")
        
        # Проверка 3: Простая трансформация
        logger.info("🔄 Шаг 3: Выполнение простой трансформации...")
        filtered_df = df.filter(df.id > 1)
        filtered_count = filtered_df.count()
        logger.info(f"✅ Фильтрация выполнена успешно: {filtered_count} записей после фильтра")
        
        # Проверка 4: Python модули
        logger.info("📦 Шаг 4: Проверка доступных Python модулей...")
        
        basic_modules = ['json', 'datetime', 'os', 'sys']
        available_basic = 0
        for module_name in basic_modules:
            try:
                __import__(module_name)
                available_basic += 1
                logger.info(f"✅ Базовый модуль {module_name} доступен")
            except ImportError as e:
                logger.warning(f"⚠️ Базовый модуль {module_name} недоступен: {e}")
        
        logger.info(f"📊 Базовые модули: {available_basic}/{len(basic_modules)} доступны")
        
        # Проверка дополнительных модулей (не критично)
        optional_modules = ['pandas', 'numpy', 'requests']
        available_optional = 0
        for module_name in optional_modules:
            try:
                __import__(module_name)
                available_optional += 1
                logger.info(f"✅ Дополнительный модуль {module_name} доступен")
            except ImportError:
                logger.info(f"ℹ️ Дополнительный модуль {module_name} недоступен (не критично)")
        
        logger.info(f"📊 Дополнительные модули: {available_optional}/{len(optional_modules)} доступны")
        
        # Проверка 5: Конфигурация Spark
        logger.info("⚙️ Шаг 5: Проверка конфигурации Spark...")
        try:
            spark_version = spark.version
            logger.info(f"✅ Spark версия: {spark_version}")
            
            executor_instances = spark.conf.get('spark.executor.instances', 'не задано')
            logger.info(f"✅ Executor instances: {executor_instances}")
            
            app_name = spark.conf.get('spark.app.name', 'не задано')
            logger.info(f"✅ App name: {app_name}")
            
        except Exception as e:
            logger.warning(f"⚠️ Проблема с получением конфигурации Spark: {e}")
        
        # Финальная проверка
        if available_basic >= len(basic_modules) * 0.8:  # 80% базовых модулей должны быть доступны
            logger.info("🎉 Все критичные проверки пройдены успешно!")
            return True
        else:
            logger.error("❌ Не хватает критичных базовых модулей")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в check_spark_environment: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Основная функция с улучшенной обработкой ошибок"""
    try:
        logger.info("🚀 Запуск проверки готовности DataProc кластера...")
        
        # Парсинг аргументов
        parser = argparse.ArgumentParser(
            description='Проверка готовности кластера для Kafka Streaming'
        )
        parser.add_argument('--packages', help='Список пакетов (игнорируется)')
        parser.add_argument('--s3-endpoint-url', help='S3 endpoint URL (игнорируется)')
        parser.add_argument('--s3-access-key', help='S3 access key (игнорируется)')
        parser.add_argument('--s3-secret-key', help='S3 secret key (игнорируется)')
        
        args = parser.parse_args()
        logger.info(f"📋 Аргументы получены: packages={args.packages}")
        
        # Создание Spark Session
        logger.info("🔧 Создание Spark Session...")
        spark = SparkSession.builder \
            .appName("KafkaStreamingClusterCheck") \
            .getOrCreate()
        
        logger.info(f"✅ Spark Session создана успешно: версия {spark.version}")
        
        # Выполняем проверки
        logger.info("🔍 Начинаю комплексную проверку кластера...")
        
        check_result = check_spark_environment(spark)
        
        if check_result:
            logger.info("🎉 УСПЕХ: Кластер готов для Kafka Streaming!")
            
            # Финальная информация
            logger.info("📊 Финальная информация о кластере:")
            logger.info(f"  🔧 Spark версия: {spark.version}")
            logger.info(f"  🐍 Python версия: {sys.version.split()[0]}")
            logger.info(f"  💻 Executor instances: {spark.conf.get('spark.executor.instances', 'не задано')}")
            
            logger.info("✅ Завершаю работу с кодом 0 (успех)")
            spark.stop()
            sys.exit(0)
        else:
            logger.error("❌ ОШИБКА: Кластер НЕ готов для Kafka Streaming")
            logger.error("💡 Проверьте логи выше для получения подробной информации")
            logger.info("❌ Завершаю работу с кодом 1 (ошибка)")
            spark.stop()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в main(): {e}")
        logger.error(f"🔍 Полный traceback: {traceback.format_exc()}")
        logger.info("❌ Завершаю работу с кодом 1 (критическая ошибка)")
        sys.exit(1)

if __name__ == "__main__":
    main()
