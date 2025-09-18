#!/usr/bin/env python3
"""
Абсолютно минимальный Spark тест - без аргументов
"""
import sys
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Запуск минимального Spark теста...")
        
        # Создаем SparkSession
        spark = SparkSession.builder \
            .appName("MinimalSparkTest") \
            .getOrCreate()
        
        logger.info(f"✅ Spark Session создана: {spark.version}")
        
        # Минимальный тест
        data = [("hello", 1), ("world", 2), ("test", 3)]
        df = spark.createDataFrame(data, ["text", "number"])
        count = df.count()
        
        logger.info(f"✅ Минимальный тест успешен: {count} записей")
        df.show()
        
        spark.stop()
        logger.info("🎉 Минимальный Spark тест завершен успешно!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
