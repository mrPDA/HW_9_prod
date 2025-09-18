#!/usr/bin/env python3
"""
Самый простой тест для проверки PySpark environment
"""
import sys
import time

print("🚀 HELLO WORLD TEST: Запуск...")
print(f"🐍 Python version: {sys.version}")
print("📁 Python path entries:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

try:
    print("🔧 Попытка импорта PySpark...")
    from pyspark.sql import SparkSession
    print("✅ PySpark импортирован успешно!")
    
    print("🔧 Создание Spark Session...")
    spark = SparkSession.builder \
        .appName("HelloWorldTest") \
        .getOrCreate()
    
    print(f"✅ Spark Session создана: {spark.version}")
    
    # Простейший тест
    print("🧪 Простейший тест Spark...")
    data = [("hello", 1), ("world", 2)]
    df = spark.createDataFrame(data, ["text", "number"])
    count = df.count()
    print(f"✅ Spark DataFrame создан: {count} записей")
    
    # Показать содержимое
    print("📊 Содержимое DataFrame:")
    df.show()
    
    spark.stop()
    print("✅ HELLO WORLD TEST УСПЕШЕН!")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    print(f"📜 Traceback: {traceback.format_exc()}")
    sys.exit(1)

print("🎉 Тест завершен!")
sys.exit(0)
