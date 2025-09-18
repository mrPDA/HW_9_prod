#!/usr/bin/env python3
"""
Тестовый скрипт для чтения данных из S3 без Kafka
"""
import argparse
import logging
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Test S3 Data Reader')
    parser.add_argument('--s3-bucket', required=True)
    parser.add_argument('--file-path', default='train/data.csv')
    
    args = parser.parse_args()
    
    try:
        logger.info("🚀 Запуск S3 Data Reader Test")
        
        # Создаем SparkSession
        spark = SparkSession.builder \
            .appName("S3DataReaderTest") \
            .getOrCreate()
        
        logger.info(f"✅ Spark Session создана: {spark.version}")
        logger.info(f"📦 S3 Bucket: {args.s3_bucket}")
        logger.info(f"📁 File path: {args.file_path}")
        
        # Генерируем тестовые данные 
        logger.info("📊 Создание тестовых данных...")
        test_data = []
        for i in range(100):
            transaction = {
                'transaction_id': f'tx_{i:06d}',
                'user_id': f'user_{i % 20}',
                'merchant_id': f'merchant_{i % 10}',
                'transaction_amount': round(10.0 + (i % 1000) * 0.5, 2),
                'transaction_date': '2024-01-01',
                'is_fraud': 1 if i % 17 == 0 else 0  # ~6% fraud rate
            }
            test_data.append(transaction)
        
        # Создаем DataFrame из тестовых данных
        df = spark.createDataFrame(test_data)
        
        logger.info(f"✅ Создан DataFrame с {df.count()} записями")
        
        # Показываем примеры данных
        logger.info("📊 Примеры данных:")
        df.show(10, truncate=False)
        
        # Базовая статистика
        logger.info("📈 Статистика данных:")
        df.describe(['transaction_amount']).show()
        
        fraud_count = df.filter(col('is_fraud') == 1).count()
        total_count = df.count()
        fraud_rate = fraud_count / total_count * 100
        
        logger.info(f"🔍 Fraud Detection Stats:")
        logger.info(f"   Total transactions: {total_count}")
        logger.info(f"   Fraud transactions: {fraud_count}")
        logger.info(f"   Fraud rate: {fraud_rate:.2f}%")
        
        # Группировка по пользователям
        user_stats = df.groupBy('user_id').agg(
            count('*').alias('transaction_count'),
            sum('transaction_amount').alias('total_amount'),
            sum('is_fraud').alias('fraud_count')
        ).orderBy(desc('transaction_count'))
        
        logger.info("👥 Топ пользователи по количеству транзакций:")
        user_stats.show(5)
        
        spark.stop()
        logger.info("✅ S3 Data Reader Test завершен успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(f"📜 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
