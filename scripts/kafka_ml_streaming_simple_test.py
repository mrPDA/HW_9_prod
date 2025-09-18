#!/usr/bin/env python3
"""
Максимально простой тест Kafka ML Streaming
"""
import argparse
import sys
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 ПРОСТОЙ ТЕСТ: Запуск...")
    
    try:
        # Парсинг аргументов - принимаем все, но не обязательно
        parser = argparse.ArgumentParser(description='Simple Test')
        parser.add_argument('--kafka-brokers', default='test:9092')
        parser.add_argument('--input-topic', default='test')
        parser.add_argument('--output-topic', default='test')
        parser.add_argument('--metrics-topic', default='test')
        parser.add_argument('--mlflow-uri', default='http://test:5000')
        parser.add_argument('--model-name', default='test_model')
        parser.add_argument('--model-stage', default='test')
        parser.add_argument('--fraud-threshold', type=float, default=0.5)
        parser.add_argument('--batch-timeout', default='30 seconds')
        parser.add_argument('--max-offsets', type=int, default=1000)
        parser.add_argument('--demo-duration', type=int, default=30)
        parser.add_argument('--checkpoint-location', default='test')
        parser.add_argument('--app-name', default='test')
        
        args = parser.parse_args()
        logger.info("✅ ПРОСТОЙ ТЕСТ: Аргументы получены")
        
        # Логирование всех параметров
        logger.info(f"🔗 Kafka Brokers: {args.kafka_brokers}")
        logger.info(f"📥 Input Topic: {args.input_topic}")
        logger.info(f"🤖 MLflow URI: {args.mlflow_uri}")
        logger.info(f"🏆 Model: {args.model_name}")
        
        # Проверка Python окружения
        logger.info(f"🐍 Python version: {sys.version}")
        logger.info(f"📁 Python path: {sys.path[0]}")
        
        # Попытка импорта PySpark
        logger.info("🔧 Попытка импорта PySpark...")
        try:
            from pyspark.sql import SparkSession
            logger.info("✅ PySpark импортирован успешно")
            
            # Создание SparkSession
            logger.info("🔧 Создание Spark Session...")
            spark = SparkSession.builder \
                .appName("SimpleKafkaTest") \
                .config("spark.sql.adaptive.enabled", "true") \
                .getOrCreate()
            
            logger.info(f"✅ Spark Session создана: {spark.version}")
            
            # Простой тест Spark
            test_data = [("test", 1), ("simple", 2)]
            df = spark.createDataFrame(test_data, ["name", "value"])
            count = df.count()
            logger.info(f"✅ Spark тест: {count} записей")
            
            # Симуляция работы
            logger.info("🎭 Симуляция работы streaming job...")
            for i in range(3):
                logger.info(f"  📦 Batch {i+1}: Симуляция обработки...")
                time.sleep(5)
            
            spark.stop()
            logger.info("✅ ПРОСТОЙ ТЕСТ УСПЕШЕН!")
            sys.exit(0)
            
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта PySpark: {e}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
