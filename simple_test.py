#!/usr/bin/env python3
"""
🚀 Простейший тест ML API
"""

from fastapi import FastAPI
from datetime import datetime
import uvicorn

app = FastAPI(title="🛡️ ML Fraud Detection Test API")

@app.get("/")
def root():
    return {
        "service": "🛡️ Fraud Detection API",
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "message": "API работает!"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/predict")
def predict(data: dict):
    return {
        "transaction_id": data.get("transaction_id", "test"),
        "is_fraud": False,
        "fraud_probability": 0.1,
        "confidence": "high",
        "model": "test-model",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Запуск простейшего ML API тестера...")
    print("📖 Docs: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
