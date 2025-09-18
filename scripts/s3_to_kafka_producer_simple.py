#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой S3 to Kafka Producer для DataProc
========================================

Минимальная версия для тестирования без сложных зависимостей.
"""

import json
import time
import logging
import argparse
import sys
import random
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_kafka_producer(args):
    """
    Симулируем Kafka producer - пока что просто логируем данные
    В реальной версии здесь будет отправка в Kafka
    """
    logger.info("🚀 Запуск S3 to Kafka Producer (простая версия)")
    logger.info(f"📦 S3 Bucket: {args.s3_bucket}")
    logger.info(f"📁 Список файлов: {args.file_list}")
    logger.info(f"🔗 Kafka Brokers: {args.kafka_brokers}")
    logger.info(f"📨 Topic: {args.topic}")
    logger.info(f"⚡ TPS: {args.tps}")
    logger.info(f"⏱️ Duration: {args.duration} секунд")
    
    # Симулируем обработку данных
    total_messages = int(args.tps) * int(args.duration)
    logger.info(f"📊 Планируется отправить: {total_messages} сообщений")
    
    start_time = datetime.now()
    messages_sent = 0
    
    try:
        for i in range(total_messages):
            # Симулируем создание сообщения
            message = {
                "transaction_id": f"tx_{i:06d}",
                "amount": round(random.uniform(10.0, 1000.0), 2),
                "merchant_id": f"m_{random.randint(100, 999)}",
                "user_id": f"u_{random.randint(1000, 9999)}",
                "timestamp": datetime.now().isoformat(),
                "is_fraud": random.choice([0, 1]) if random.random() < 0.1 else 0
            }
            
            # В реальной версии здесь будет: producer.send(topic, message)
            if i % 100 == 0:  # Логируем каждые 100 сообщений
                logger.info(f"📤 Отправлено сообщений: {i+1}/{total_messages}")
            
            messages_sent += 1
            
            # Контроль скорости (TPS)
            if messages_sent % int(args.tps) == 0:
                time.sleep(1.0)  # Пауза 1 секунда каждые TPS сообщений
                
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ ЗАВЕРШЕНО: Отправлено {messages_sent} сообщений за {duration:.2f} секунд")
        logger.info(f"📊 Средняя скорость: {messages_sent/duration:.2f} TPS")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке данных: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Simple S3 to Kafka Producer')
    
    # S3 параметры
    parser.add_argument('--s3-bucket', required=True, help='S3 bucket name')
    parser.add_argument('--file-list', required=True, help='Comma-separated list of files')
    parser.add_argument('--s3-endpoint-url', help='S3 endpoint URL')
    parser.add_argument('--s3-access-key', help='S3 access key')
    parser.add_argument('--s3-secret-key', help='S3 secret key')
    
    # Kafka параметры
    parser.add_argument('--kafka-brokers', required=True, help='Kafka brokers')
    parser.add_argument('--kafka-user', help='Kafka username')
    parser.add_argument('--kafka-password', help='Kafka password')
    parser.add_argument('--topic', required=True, help='Kafka topic')
    
    # Streaming параметры
    parser.add_argument('--tps', type=int, default=10, help='Transactions per second')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')
    parser.add_argument('--shuffle-files', action='store_true', help='Shuffle files')
    
    args = parser.parse_args()
    
    logger.info("🎯 Простой S3 to Kafka Producer - тестовая версия")
    logger.info("⚠️ ВНИМАНИЕ: Это симуляция! Реальная отправка в Kafka будет добавлена позже.")
    
    try:
        success = simulate_kafka_producer(args)
        if success:
            logger.info("🎉 Producer завершился успешно!")
            sys.exit(0)
        else:
            logger.error("❌ Producer завершился с ошибкой!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
