#!/usr/bin/env python3
"""
Простейший Streaming Test без Kafka - только для проверки PySpark
"""
import argparse
import sys
import time
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Simple Streaming Test')
    # Добавляем все аргументы, которые может передавать DAG, но игнорируем их
    parser.add_argument('--kafka-brokers', help='Kafka brokers (ignored)')
    parser.add_argument('--input-topic', help='Kafka input topic (ignored)')
    parser.add_argument('--output-topic', help='Kafka output topic (ignored)')
    parser.add_argument('--metrics-topic', help='Kafka metrics topic (ignored)')
    parser.add_argument('--mlflow-uri', help='MLflow tracking URI (ignored)')
    parser.add_argument('--model-name', help='MLflow model name (ignored)')
    parser.add_argument('--model-stage', help='MLflow model stage (ignored)')
    parser.add_argument('--fraud-threshold', type=float, help='Fraud prediction threshold (ignored)')
    parser.add_argument('--batch-timeout', help='Batch processing timeout (ignored)')
    parser.add_argument('--max-offsets', type=int, help='Max offsets per trigger (ignored)')
    parser.add_argument('--demo-duration', type=int, help='Duration in seconds to run (ignored)')
    parser.add_argument('--checkpoint-location', help='Checkpoint location (ignored)')
    parser.add_argument('--app-name', help='Application name (ignored)')
    args = parser.parse_args()
    
    try:
        logger.info("🚀 Запуск простейшего Streaming Test (БЕЗ Kafka)")
        
        # Создаем SparkSession
        spark = SparkSession.builder \
            .appName("SimpleStreamingTest") \
            .getOrCreate()
        
        logger.info(f"✅ Spark Session создана: {spark.version}")
        logger.info("📊 Создаем тестовый DataFrame для симуляции streaming...")
        
        # Создаем простой DataFrame без streaming
        data = [("tx_001", 100.50, "user_123"), ("tx_002", 250.75, "user_456")]
        df = spark.createDataFrame(data, ["transaction_id", "amount", "user_id"])
        
        count = df.count()
        logger.info(f"✅ Тестовый DataFrame создан: {count} записей")
        
        # Показываем содержимое
        logger.info("📋 Содержимое тестового DataFrame:")
        df.show()
        
        # Симулируем обработку
        logger.info("⚡ Симулируем обработку данных...")
        processed_df = df.withColumn("processed", df.amount * 1.1)
        processed_df.show()
        
        logger.info("✅ Простейший Streaming Test завершился успешно!")
        
        spark.stop()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в простейшем Streaming Test: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            if 'spark' in locals():
                spark.stop()
        except:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()
