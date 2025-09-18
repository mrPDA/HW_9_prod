#!/usr/bin/env python3
"""
Kafka ML Streaming Job - Debug версия для диагностики ошибок
"""
import argparse
import sys
import time
import logging
from datetime import datetime
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Запуск DEBUG версии Kafka ML Streaming Job...")
    
    try:
        # 1. Парсинг аргументов с детальным логированием
        parser = argparse.ArgumentParser(description='Kafka ML Streaming Job - Debug')
        parser.add_argument('--kafka-brokers', required=True)
        parser.add_argument('--input-topic', required=True)
        parser.add_argument('--output-topic', required=True)
        parser.add_argument('--metrics-topic', required=True)
        parser.add_argument('--mlflow-uri', required=True)
        parser.add_argument('--model-name', required=True)
        parser.add_argument('--model-stage', default='champion')
        parser.add_argument('--fraud-threshold', type=float, default=0.5)
        parser.add_argument('--batch-timeout', default='30 seconds')
        parser.add_argument('--max-offsets', type=int, default=1000)
        parser.add_argument('--demo-duration', type=int, default=60, help='Demo duration in seconds')
        parser.add_argument('--checkpoint-location', help='Checkpoint location (ignored in demo)')
        parser.add_argument('--app-name', help='Application name (ignored in demo)')
        
        args = parser.parse_args()
        logger.info("✅ Аргументы успешно распознаны")
        
        # 2. Логирование всех параметров
        logger.info("📋 ПОЛУЧЕННЫЕ ПАРАМЕТРЫ:")
        logger.info(f"  🔗 Kafka Brokers: '{args.kafka_brokers}'")
        logger.info(f"  📥 Input Topic: '{args.input_topic}'")
        logger.info(f"  📤 Output Topic: '{args.output_topic}'")
        logger.info(f"  📊 Metrics Topic: '{args.metrics_topic}'")
        logger.info(f"  🤖 MLflow URI: '{args.mlflow_uri}'")
        logger.info(f"  🏆 Model Name: '{args.model_name}'")
        logger.info(f"  🎯 Model Stage: '{args.model_stage}'")
        logger.info(f"  ⚡ Fraud Threshold: {args.fraud_threshold}")
        logger.info(f"  ⏱️ Demo Duration: {args.demo_duration} секунд")
        
        # 3. Проверка на пустые значения
        required_params = {
            'kafka_brokers': args.kafka_brokers,
            'input_topic': args.input_topic,
            'output_topic': args.output_topic,
            'metrics_topic': args.metrics_topic,
            'mlflow_uri': args.mlflow_uri,
            'model_name': args.model_name
        }
        
        empty_params = [k for k, v in required_params.items() if not v or v == 'None']
        if empty_params:
            logger.error(f"❌ ОШИБКА: Пустые обязательные параметры: {empty_params}")
            sys.exit(1)
        
        logger.info("✅ Все обязательные параметры заполнены")
        
        # 4. Создание SparkSession с детальным логированием
        logger.info("🔧 Создание Spark Session...")
        spark = SparkSession.builder \
            .appName("KafkaMLStreamingDebug") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        logger.info(f"✅ Spark Session создана: {spark.version}")
        logger.info(f"📊 Spark Config: {spark.conf.getAll()}")
        
        # 5. Тест простой операции Spark
        logger.info("🧪 Тестирование базовых операций Spark...")
        test_data = [("test", 1), ("debug", 2)]
        test_df = spark.createDataFrame(test_data, ["name", "value"])
        count = test_df.count()
        logger.info(f"✅ Spark работает корректно: {count} записей в тестовом DataFrame")
        
        # 6. Симуляция работы без реального Kafka (для отладки)
        logger.info("🎭 Симуляция Kafka ML Streaming (без реального подключения)...")
        
        start_time = time.time()
        processed_batches = 0
        
        while time.time() - start_time < args.demo_duration:
            processed_batches += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Симуляция обработки batch'а
            logger.info(f"[{current_time}] 📦 Batch #{processed_batches}: Симуляция обработки данных...")
            
            # Имитация ML inference
            fake_predictions = processed_batches * 10
            logger.info(f"  🤖 Симуляция ML предсказаний: {fake_predictions} транзакций обработано")
            
            # Проверяем каждые 3 batch'а
            if processed_batches % 3 == 0:
                elapsed = int(time.time() - start_time)
                logger.info(f"  📊 Статистика: {processed_batches} batches за {elapsed}с")
            
            time.sleep(5)  # Пауза между batch'ами
        
        # 7. Финальная статистика
        total_elapsed = int(time.time() - start_time)
        logger.info("🎯 DEBUG тест завершен успешно!")
        logger.info(f"  ⏱️ Время работы: {total_elapsed} секунд")
        logger.info(f"  📦 Обработано batches: {processed_batches}")
        logger.info(f"  🔗 Kafka (симуляция): {args.kafka_brokers}")
        logger.info(f"  🏆 Модель (симуляция): {args.model_name} ({args.model_stage})")
        
        spark.stop()
        logger.info("✅ Kafka ML Streaming DEBUG завершился успешно!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в DEBUG версии: {e}")
        import traceback
        logger.error(f"📜 Полный traceback:\n{traceback.format_exc()}")
        
        try:
            if 'spark' in locals():
                spark.stop()
                logger.info("🛑 Spark Session остановлена")
        except Exception as stop_error:
            logger.error(f"❌ Ошибка при остановке Spark: {stop_error}")
            
        sys.exit(1)

if __name__ == "__main__":
    main()
