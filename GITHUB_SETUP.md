# 🔧 Настройка GitHub Actions CI/CD Pipeline

## 📋 Пошаговая инструкция

### 1. 🔗 Создание GitHub репозитория

1. Идите на [GitHub](https://github.com) и создайте новый репозиторий
2. Название: `ml-fraud-detection-api`
3. Описание: `🛡️ Production ML API for fraud detection with full DevOps stack`
4. Public/Private: на ваш выбор
5. **НЕ** инициализируйте с README (у нас уже есть файлы)

### 2. 🔑 Настройка секретов GitHub

Идите в Settings → Secrets and variables → Actions вашего репозитория и добавьте:

#### **YC_KEY** (обязательно)
```bash
# Содержимое файла github-actions-key.json
cat github-actions-key.json | pbcopy  # macOS
cat github-actions-key.json | xclip   # Linux
```

#### **YC_REGISTRY_ID** (обязательно)
```
crptv4gc9kktat18e7ts
```

#### **KUBECONFIG_PRODUCTION** (обязательно)
```bash
# Base64 encoded kubeconfig
base64 kubeconfig-github-actions.yaml | pbcopy  # macOS
base64 kubeconfig-github-actions.yaml | xclip   # Linux
```

#### **KUBECONFIG_STAGING** (опционально)
```bash
# Тот же kubeconfig для staging (в реальности - отдельный кластер)
base64 kubeconfig-github-actions.yaml | pbcopy
```

#### **SLACK_WEBHOOK_URL** (опционально)
```
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. 📤 Загрузка кода в GitHub

```bash
# Добавить remote origin
git remote add origin https://github.com/YOUR_USERNAME/ml-fraud-detection-api.git

# Загрузить код
git push -u origin main

# Создать ветку develop для staging
git checkout -b develop
git push -u origin develop
```

### 4. 🚀 Проверка CI/CD

#### Автоматический запуск тестов:
1. Создайте Pull Request из `develop` в `main`
2. Посмотрите на вкладку **Actions** - должны запуститься тесты

#### Деплой в staging:
1. Push в ветку `develop` автоматически деплоит в staging
2. Проверьте логи в Actions

#### Production деплой:
1. Создайте release tag:
```bash
git tag -a v1.0.0 -m "🚀 First production release"
git push origin v1.0.0
```
2. Посмотрите Actions - должен запуститься full pipeline

## 📊 Мониторинг pipeline

### Actions Dashboard
- **URL**: `https://github.com/YOUR_USERNAME/ml-fraud-detection-api/actions`
- **Статусы**: ✅ Success, ❌ Failed, 🟡 In Progress
- **Логи**: Кликните на любой workflow для детальных логов

### Что происходит в pipeline:

1. **🧪 Test Stage** (всегда):
   - Code linting (flake8)
   - Unit tests (pytest)
   - Security scan (bandit)
   - Coverage report

2. **🐳 Build Stage** (после тестов):
   - Docker build
   - Push to Yandex Container Registry
   - Multi-platform support

3. **🔒 Security Stage** (main/develop):
   - Container vulnerability scan (Trivy)
   - SARIF upload to GitHub Security

4. **🚀 Deploy Staging** (ветка develop):
   - Automatic deploy to staging cluster
   - Smoke tests

5. **🚀 Deploy Production** (теги v*):
   - Production deployment
   - Extended smoke tests
   - GitHub Release creation
   - Slack notification

## 🛠️ Локальное тестирование pipeline

### Запуск тестов локально:
```bash
make test              # Unit тесты
make lint              # Code quality
make security          # Security scan
```

### Эмуляция build:
```bash
make build             # Docker build
make run-docker        # Запуск в контейнере
```

### Проверка K8s манифестов:
```bash
kubectl apply --dry-run=client -f k8s/
```

## 📋 Troubleshooting

### Ошибка авторизации в YC Registry:
- Проверьте корректность `YC_KEY`
- Убедитесь что сервисный аккаунт имеет права `container-registry.images.pusher`

### Ошибка деплоя в K8s:
- Проверьте `KUBECONFIG_PRODUCTION` (должен быть base64)
- Убедитесь что сервисный аккаунт имеет права `k8s.cluster-api.cluster-admin`

### Тесты не проходят:
- Проверьте совместимость версий в `app/requirements.txt`
- Убедитесь что все файлы добавлены в git

## 🎯 Результат настройки

После правильной настройки у вас будет:

✅ **Полностью автоматизированный CI/CD**  
✅ **Автоматические тесты на каждый PR**  
✅ **Staging деплой на каждый commit в develop**  
✅ **Production деплой на каждый release tag**  
✅ **Security scanning образов**  
✅ **Мониторинг и алерты**  

---

## 📞 Поддержка

- **GitHub Issues**: Для багов и feature requests
- **Actions Logs**: Для диагностики pipeline
- **Kubernetes Dashboard**: Для мониторинга деплоя

**Удачи с настройкой! 🚀**
