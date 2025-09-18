"""
🤖 Model Tests
==============

Тесты для ML модели и предсказаний.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

from app.models.fraud_detector import FraudDetectionModel


@pytest.fixture
def sample_transaction_data():
    """Пример данных транзакции для тестов"""
    return pd.DataFrame({
        "transaction_id": ["txn_001"],
        "amount": [150.75],
        "merchant_category": ["restaurant"],
        "hour_of_day": [14],
        "day_of_week": [2],
        "user_age": [35],
        "location_risk_score": [0.2]
    })


@pytest.fixture
def batch_transaction_data():
    """Пример batch данных для тестов"""
    return pd.DataFrame({
        "transaction_id": ["txn_001", "txn_002", "txn_003"],
        "amount": [50.0, 999.99, 25.0],
        "merchant_category": ["grocery", "electronics", "restaurant"],
        "hour_of_day": [10, 23, 12],
        "day_of_week": [1, 6, 3],
        "user_age": [25, 45, 30],
        "location_risk_score": [0.1, 0.8, 0.3]
    })


class TestFraudDetectionModel:
    """Тесты класса FraudDetectionModel"""
    
    def test_model_initialization(self):
        """Тест инициализации модели"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model",
            model_alias="test"
        )
        
        assert model.mlflow_uri == "http://test:5000"
        assert model.model_name == "test_model"
        assert model.model_alias == "test"
        assert not model.is_loaded
        assert model.model is None
    
    def test_preprocess_data(self, sample_transaction_data):
        """Тест предобработки данных"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model"
        )
        
        processed = model._preprocess_data(sample_transaction_data)
        
        # Проверяем что данные обработаны
        assert len(processed) == 1
        assert "amount" in processed.columns
        assert "merchant_category" in processed.columns
        
        # Проверяем что категории закодированы как числа
        assert processed["merchant_category"].dtype in [np.int64, np.float64]
        
        # Проверяем заполнение пропущенных значений
        assert not processed.isnull().any().any()
    
    def test_preprocess_missing_values(self):
        """Тест обработки пропущенных значений"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model"
        )
        
        # Данные с пропущенными значениями
        data_with_nans = pd.DataFrame({
            "transaction_id": ["txn_001"],
            "amount": [100.0],
            "merchant_category": ["restaurant"],
            "hour_of_day": [14],
            "day_of_week": [2],
            "user_age": [None],  # Пропущенное значение
            "location_risk_score": [None]  # Пропущенное значение
        })
        
        processed = model._preprocess_data(data_with_nans)
        
        # Проверяем что пропущенные значения заполнены
        assert not processed.isnull().any().any()
        assert processed["user_age"].iloc[0] == 35  # Дефолтное значение
        assert processed["location_risk_score"].iloc[0] == 0.5  # Дефолтное значение
    
    def test_merchant_category_encoding(self):
        """Тест кодирования категорий продавцов"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000", 
            model_name="test_model"
        )
        
        test_data = pd.DataFrame({
            "transaction_id": ["txn_001", "txn_002"],
            "amount": [100.0, 200.0],
            "merchant_category": ["grocery", "unknown_category"],
            "hour_of_day": [10, 15],
            "day_of_week": [1, 2]
        })
        
        processed = model._preprocess_data(test_data)
        
        # grocery должно быть закодировано как 0
        assert processed["merchant_category"].iloc[0] == 0
        # unknown_category должно быть закодировано как 7 (other)
        assert processed["merchant_category"].iloc[1] == 7
    
    @pytest.mark.asyncio
    async def test_load_model_mock(self):
        """Тест загрузки модели с мокированием MLflow"""
        with patch('mlflow.set_tracking_uri'), \
             patch('mlflow.tracking.MlflowClient') as mock_client_class, \
             patch('mlflow.pyfunc.load_model') as mock_load_model, \
             patch('asyncio.get_event_loop') as mock_loop:
            
            # Настраиваем моки
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_model_version = Mock()
            mock_model_version.version = "1"
            mock_model_version.current_stage = "Production"
            mock_model_version.run_id = "test_run_id"
            mock_model_version.creation_timestamp = 1234567890
            mock_model_version.last_updated_timestamp = 1234567890
            mock_model_version.description = "Test model"
            mock_model_version.tags = []
            
            mock_client.get_model_version_by_alias.return_value = mock_model_version
            
            # Мокируем загруженную модель
            mock_loaded_model = Mock()
            mock_load_model.return_value = mock_loaded_model
            
            # Мокируем event loop
            mock_executor = Mock()
            mock_executor.return_value = mock_loaded_model
            mock_loop.return_value.run_in_executor = mock_executor
            
            # Создаем и загружаем модель
            model = FraudDetectionModel(
                mlflow_uri="http://test:5000",
                model_name="test_model",
                model_alias="test"
            )
            
            await model.load_model()
            
            # Проверяем что модель загружена
            assert model.is_loaded
            assert model.model_version == "1"
            assert model.model is not None
    
    @pytest.mark.asyncio 
    async def test_predict_mock(self, sample_transaction_data):
        """Тест предсказания с мокированной моделью"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model"
        )
        
        # Мокируем загруженную модель
        mock_ml_model = Mock()
        mock_ml_model.predict.return_value = np.array([0])  # Не мошенничество
        mock_ml_model.predict_proba.return_value = np.array([[0.7, 0.3]])  # 30% вероятность мошенничества
        
        model.model = mock_ml_model
        model.is_loaded = True
        model.model_version = "test_v1"
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            
            # Настраиваем моки для predict и predict_proba
            async def mock_predict(*args):
                return mock_ml_model.predict(args[1])
            
            async def mock_predict_proba(*args):
                return mock_ml_model.predict_proba(args[1])
            
            mock_loop.return_value.run_in_executor.side_effect = [
                mock_predict(None, None),  # predict
                mock_predict_proba(None, None)  # predict_proba
            ]
            
            result = await model.predict(sample_transaction_data)
            
            # Проверяем результат
            assert "is_fraud" in result
            assert "fraud_probability" in result
            assert result["fraud_probability"] == 0.3
            assert not result["is_fraud"]  # Не мошенничество при вероятности 0.3
            assert result["model_version"] == "test_v1"
    
    def test_get_model_info(self):
        """Тест получения информации о модели"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model",
            model_alias="champion"
        )
        
        model.model_version = "1"
        model.is_loaded = True
        model.load_time = 1500.0
        model.feature_names = ["amount", "category"]
        
        info = model.get_model_info()
        
        assert info["model_name"] == "test_model"
        assert info["model_version"] == "1"
        assert info["model_alias"] == "champion"
        assert info["is_loaded"] is True
        assert info["load_time_ms"] == 1500.0
        assert len(info["feature_names"]) == 2
    
    def test_estimate_model_size(self):
        """Тест оценки размера модели"""
        model = FraudDetectionModel(
            mlflow_uri="http://test:5000",
            model_name="test_model"
        )
        
        # Мокируем простую модель
        model.model = {"test": "data"}
        
        size = model._estimate_model_size()
        assert isinstance(size, float)
        assert size >= 0.0


@pytest.mark.asyncio
async def test_predict_without_loaded_model():
    """Тест предсказания без загруженной модели"""
    model = FraudDetectionModel(
        mlflow_uri="http://test:5000",
        model_name="test_model"
    )
    
    # Модель не загружена
    assert not model.is_loaded
    
    sample_data = pd.DataFrame({
        "transaction_id": ["txn_001"],
        "amount": [100.0],
        "merchant_category": ["restaurant"],
        "hour_of_day": [14],
        "day_of_week": [2]
    })
    
    # Ожидаем RuntimeError
    with pytest.raises(RuntimeError, match="Model not loaded"):
        await model.predict(sample_data)
