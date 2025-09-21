# 🛡️ ML Fraud Detection API - Makefile
# ===================================

.PHONY: help build test deploy clean install lint format

# 🎯 Default target
help: ## Show this help message
	@echo "🛡️ ML Fraud Detection API Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 📦 Installation
install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install -r app/requirements.txt
	pip install pytest pytest-asyncio pytest-cov httpx black isort flake8

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r app/requirements.txt
	pip install -r tests/requirements.txt
	pip install black isort flake8 bandit

# 🧪 Testing
test: ## Run unit tests
	@echo "🧪 Running unit tests..."
	PYTHONPATH=${PWD} pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	PYTHONPATH=${PWD} pytest tests/ -v --cov=app --cov-report=html --cov-report=xml

test-api: ## Test only API endpoints
	@echo "🧪 Testing API endpoints..."
	PYTHONPATH=${PWD} pytest tests/test_api.py -v

test-model: ## Test only ML model
	@echo "🧪 Testing ML model..."
	PYTHONPATH=${PWD} pytest tests/test_model.py -v

# 🚀 API Testing (новые команды)
test-api-public: ## Комплексное тестирование публичного API
	@echo "🧪 Running comprehensive API tests..."
	cd tests && python run_api_tests.py --url http://localhost:8000

test-api-local: ## Тестирование локального API с запуском
	@echo "🚀 Starting API and running tests..."
	cd app && python -m uvicorn main:app --host 0.0.0.0 --port 8000 & \
	sleep 10 && \
	cd tests && python run_api_tests.py --url http://localhost:8000 --quick

test-api-performance: ## Тестирование производительности API
	@echo "📈 Running performance tests..."
	cd tests && python load_test.py --url http://localhost:8000 --users 10 --duration 30

test-api-security: ## Тестирование безопасности API  
	@echo "🔒 Running security tests..."
	cd tests && python run_api_tests.py --url http://localhost:8000 --no-performance

test-api-reports: ## Генерация отчетов о тестировании
	@echo "📊 Generating API test reports..."
	cd tests && python run_api_tests.py --url http://localhost:8000 --output-dir ../test_results

# 🔍 Code Quality
lint: ## Run code linting
	@echo "🔍 Running code linting..."
	flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black app/ tests/
	isort app/ tests/

security: ## Run security scan
	@echo "🔒 Running security scan..."
	bandit -r app/ -f json -o security-report.json

# 🐳 Docker
build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t fraud-detection-api:latest .

build-prod: ## Build production Docker image
	@echo "🐳 Building production Docker image..."
	docker build -t fraud-detection-api:prod --target production .

run-docker: build ## Run application in Docker
	@echo "🚀 Running application in Docker..."
	docker run -d --name fraud-api -p 8000:8000 -p 9090:9090 fraud-detection-api:latest

# 🚀 Local Development
run: ## Run application locally
	@echo "🚀 Starting local development server..."
	cd app && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run application in production mode
	@echo "🚀 Starting production server..."
	cd app && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

# 🐳 Docker Compose
dev-up: ## Start development environment with Docker Compose
	@echo "🚀 Starting development environment..."
	docker-compose up -d

dev-down: ## Stop development environment
	@echo "⏹️ Stopping development environment..."
	docker-compose down

dev-logs: ## Show development environment logs
	@echo "📋 Showing logs..."
	docker-compose logs -f fraud-detection-api

dev-test: ## Run tests in Docker environment
	@echo "🧪 Running tests in Docker..."
	docker-compose --profile testing up test-runner --build

load-test: ## Run load tests
	@echo "⚡ Starting load tests..."
	docker-compose --profile load-testing up -d load-tester
	@echo "📊 Load testing UI available at: http://localhost:8089"

# ☸️ Kubernetes
k8s-build-push: ## Build and push image to registry
	@echo "🐳 Building and pushing to Kubernetes registry..."
	$(MAKE) build
	docker tag fraud-detection-api:latest cr.yandex/$(REGISTRY_ID)/fraud-detection-api:latest
	docker push cr.yandex/$(REGISTRY_ID)/fraud-detection-api:latest

k8s-deploy: ## Deploy to Kubernetes
	@echo "☸️ Deploying to Kubernetes..."
	kubectl apply -f k8s/

k8s-status: ## Check Kubernetes deployment status
	@echo "📊 Checking Kubernetes status..."
	kubectl get pods,svc,ingress -n fraud-detection

k8s-logs: ## Show Kubernetes pod logs
	@echo "📋 Showing Kubernetes logs..."
	kubectl logs -f deployment/fraud-detection-api -n fraud-detection

k8s-delete: ## Delete Kubernetes deployment
	@echo "🗑️ Deleting Kubernetes deployment..."
	kubectl delete -f k8s/

# 🌩️ Terraform
tf-init: ## Initialize Terraform
	@echo "🏗️ Initializing Terraform..."
	cd terraform && terraform init

tf-plan: ## Plan Terraform changes
	@echo "📋 Planning Terraform changes..."
	cd terraform && terraform plan

tf-apply: ## Apply Terraform changes
	@echo "🚀 Applying Terraform changes..."
	cd terraform && terraform apply

tf-destroy: ## Destroy Terraform infrastructure
	@echo "💥 Destroying Terraform infrastructure..."
	cd terraform && terraform destroy

# 🧹 Cleanup
clean: ## Clean up temporary files and containers
	@echo "🧹 Cleaning up..."
	docker container prune -f
	docker image prune -f
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

clean-all: ## Clean everything including volumes
	@echo "🧹 Deep cleaning..."
	docker-compose down -v
	docker system prune -af
	$(MAKE) clean

# 📊 Monitoring
health: ## Check API health
	@echo "🏥 Checking API health..."
	curl -f http://localhost:8000/health/ || echo "❌ API not healthy"

metrics: ## Show API metrics
	@echo "📊 Fetching API metrics..."
	curl http://localhost:8000/metrics/

test-predict: ## Test prediction endpoint
	@echo "🧪 Testing prediction endpoint..."
	curl -X POST http://localhost:8000/predict \
		-H "Content-Type: application/json" \
		-d '{"transaction_id":"test_001","amount":150.75,"merchant_category":"restaurant","hour_of_day":14,"day_of_week":2,"user_age":35,"location_risk_score":0.2}'

# 🚀 CI/CD Helpers
ci-test: install-dev lint security test-cov ## Run all CI tests
	@echo "✅ All CI tests completed"

release: ## Create a new release
	@echo "🚀 Creating release..."
	@read -p "Enter version (e.g., v1.0.0): " version; \
	git tag -a $$version -m "Release $$version"; \
	git push origin $$version

# 📖 Documentation
docs-serve: ## Serve documentation locally
	@echo "📖 Starting documentation server..."
	@echo "📚 API docs available at: http://localhost:8000/docs"
	@echo "📊 Monitoring at: http://localhost:3000 (admin/admin123)"

# Environment variables check
check-env: ## Check required environment variables
	@echo "🔍 Checking environment variables..."
	@echo "MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
	@echo "MODEL_NAME: ${MODEL_NAME}"
	@echo "REGISTRY_ID: ${REGISTRY_ID}"
