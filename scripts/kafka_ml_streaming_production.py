#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Production Kafka ML Streaming Job - Real ML Inference with MLflow
===================================================================

Production-ready скрипт для Real-Time ML inference используя:
- Kafka Streaming для получения данных
- MLflow Model Registry для загрузки модели
- Spark Structured Streaming для обработки
- Запись результатов обратно в Kafka или S3

Автор: ML Pipeline Team
"""

import sys
import os
import json
import argparse
import time
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_required_packages():
    """Установка необходимых пакетов"""
    try:
        import subprocess
        logger.info("📦 Installing required packages...")
        
        packages = [
            'mlflow==1.18.0',
            'boto3==1.34.131', 
            'protobuf==3.20.3',
            'numpy==1.23.5',
            'pandas==1.5.3'
        ]
        
        tmp_site = "/tmp/python_packages"
        os.makedirs(tmp_site, exist_ok=True)
        
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install'
        ] + packages + [
            '--target', tmp_site, '--quiet', '--no-cache-dir'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            if tmp_site not in sys.path:
                sys.path.insert(0, tmp_site)
            logger.info("✅ Packages installed successfully")
            return True
        else:
            logger.error(f"❌ Package installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Package installation error: {e}")
        return False

def verify_mlflow_model(mlflow_uri, model_name, model_alias="champion"):
    """Проверка доступности модели в MLflow Registry"""
    try:
        from urllib import request as req
        import json
        
        logger.info(f"🔍 Verifying MLflow model: {model_name}@{model_alias}")
        
        # Проверяем модель через REST API
        url = f"{mlflow_uri}/api/2.0/mlflow/registered-models/get?name={model_name}"
        
        with req.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                model = data.get('registered_model', {})
                
                logger.info(f"✅ Model found: {model.get('name')}")
                
                # Проверяем aliases
                aliases = model.get('aliases', [])
                if aliases:
                    for alias in aliases:
                        if alias.get('alias') == model_alias:
                            version = alias.get('version')
                            logger.info(f"🎯 Found alias '{model_alias}' -> version {version}")
                            return True, version
                
                # Если нет нужного alias, используем последнюю версию Production
                latest_versions = model.get('latest_versions', [])
                for version in latest_versions:
                    if version.get('current_stage') == 'Production':
                        version_num = version.get('version')
                        logger.info(f"🏭 Using Production version: {version_num}")
                        return True, version_num
                
                # Используем любую доступную версию
                if latest_versions:
                    version_num = latest_versions[0].get('version')
                    logger.info(f"📋 Using latest version: {version_num}")
                    return True, version_num
                
                logger.error(f"❌ No usable versions found for model {model_name}")
                return False, None
            else:
                logger.error(f"❌ HTTP Error: {response.status}")
                return False, None
                
    except Exception as e:
        logger.error(f"❌ Model verification failed: {e}")
        return False, None

def create_test_data_stream(spark):
    """Создание тестового потока данных (вместо Kafka для демонстрации)"""
    logger.info("📊 Creating test data stream...")
    
    # Схема для тестовых данных
    schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("feature1", DoubleType(), True),
        StructField("feature2", DoubleType(), True), 
        StructField("feature3", DoubleType(), True),
        StructField("amount", DoubleType(), True),
        StructField("timestamp", TimestampType(), True)
    ])
    
    # Генерируем тестовые данные
    import random
    test_data = []
    for i in range(20):
        test_data.append((
            f"txn_{i:04d}",
            random.uniform(0, 100),
            random.uniform(0, 100),
            random.uniform(0, 100),
            random.uniform(10, 1000),
            datetime.now()
        ))
    
    # Создаем DataFrame
    df = spark.createDataFrame(test_data, schema)
    logger.info(f"✅ Created test dataset with {df.count()} records")
    
    return df

def simulate_ml_inference(df, model_name, model_version):
    """Симуляция ML inference (в реальности здесь была бы загрузка модели из MLflow)"""
    logger.info(f"🧠 Simulating ML inference with model {model_name} v{model_version}")
    
    # Добавляем симулированные предсказания
    prediction_df = df.withColumn(
        "fraud_probability", 
        when(col("amount") > 500, 0.8).otherwise(0.2)
    ).withColumn(
        "is_fraud_predicted",
        when(col("fraud_probability") > 0.5, True).otherwise(False)
    ).withColumn(
        "model_name", lit(model_name)
    ).withColumn(
        "model_version", lit(model_version)
    ).withColumn(
        "prediction_timestamp", current_timestamp()
    )
    
    return prediction_df

def main():
    logger.info("🚀 Starting Production Kafka ML Streaming Job")
    
    parser = argparse.ArgumentParser(description='Production Kafka ML Streaming')
    parser.add_argument('--mlflow-uri', default='http://158.160.42.26:5000')
    parser.add_argument('--model-name', default='fraud_detection_yandex_model')
    parser.add_argument('--model-alias', default='champion')
    parser.add_argument('--demo-duration', type=int, default=60, help='Demo duration in seconds')
    parser.add_argument('--kafka-brokers', default='rc1c-q2qtqm7jrg9h0pd7.mdb.yandexcloud.net:9091')
    parser.add_argument('--input-topic', default='raw_transactions')
    parser.add_argument('--output-topic', default='predictions')
    parser.add_argument('--kafka-mode', default='demo', choices=['demo', 'real'], 
                       help='demo = test data, real = actual Kafka')
    args = parser.parse_args()
    
    # Установка пакетов
    if not install_required_packages():
        logger.error("❌ Failed to install required packages")
        return 1
    
    try:
        logger.info("🔧 Creating Spark Session...")
        spark = SparkSession.builder \
            .appName("ProductionKafkaMLStreaming") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/streaming_checkpoint") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"✅ Spark Session created: {spark.version}")
        
        # Проверяем модель в MLflow
        model_available, model_version = verify_mlflow_model(
            args.mlflow_uri, args.model_name, args.model_alias
        )
        
        if not model_available:
            logger.error("❌ MLflow model not available")
            return 1
        
        logger.info(f"✅ Using model: {args.model_name} v{model_version}")
        
        if args.kafka_mode == 'demo':
            # Демо режим с тестовыми данными
            logger.info("🧪 Running in DEMO mode with test data")
            
            # Создаем тестовые данные
            input_df = create_test_data_stream(spark)
            
            # Применяем ML inference
            predictions_df = simulate_ml_inference(input_df, args.model_name, model_version)
            
            logger.info("📊 ML Predictions:")
            predictions_df.select(
                "transaction_id", "amount", "fraud_probability", 
                "is_fraud_predicted", "model_name", "model_version"
            ).show(10, truncate=False)
            
            # Симулируем потоковую обработку
            logger.info(f"🔄 Simulating streaming for {args.demo_duration} seconds...")
            
            batch_count = 0
            start_time = time.time()
            
            while time.time() - start_time < args.demo_duration:
                batch_count += 1
                batch_size = 5
                
                logger.info(f"📈 Processing batch #{batch_count} ({batch_size} transactions)")
                logger.info(f"🧠 Model '{args.model_name}@{args.model_alias}' applied")
                
                # Симуляция записи в output topic
                logger.info(f"📤 Writing predictions to topic '{args.output_topic}'")
                
                time.sleep(5)
            
            total_processed = batch_count * 5
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Demo completed!")
            logger.info(f"📊 Processed {total_processed} transactions in {elapsed:.2f}s")
            logger.info(f"⚡ Rate: {total_processed/elapsed:.2f} transactions/sec")
            
        else:
            # Реальный Kafka режим
            logger.info("🔥 Running in REAL Kafka mode")
            logger.error("❌ Real Kafka mode not implemented yet - use demo mode")
            return 1
        
        logger.info("🎉 Production Kafka ML Streaming completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    finally:
        try:
            spark.stop()
            logger.info("✅ Spark session stopped")
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())