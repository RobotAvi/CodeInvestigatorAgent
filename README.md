# 🏗️ Architecture Agent

Интеллектуальный агент для анализа архитектуры микросервисов с использованием LlamaIndex, LangChain и LangGraph.

## 🎯 Основные возможности

- **Анализ архитектуры**: Автоматический анализ структуры микросервисов
- **C4 диаграммы**: Генерация и навигация по C4 архитектурным диаграммам
- **GitLab интеграция**: Подключение к GitLab через MCP для анализа репозиториев
- **Локальная LLM**: Работа с локальными языковыми моделями (Ollama)
- **Мультиагентность**: Создание и управление несколькими агентами
- **Интерактивный чат**: Веб-интерфейс для общения с агентами
- **Анализ кода**: Автоматическое извлечение архитектурной информации из кода

## 🏛️ Архитектура системы

### Компоненты

1. **Agent Manager** - управление агентами и их жизненным циклом
2. **LLM Client** - клиент для работы с локальными языковыми моделями
3. **GitLab MCP Client** - интеграция с GitLab через MCP протокол
4. **C4 Diagram Generator** - генератор C4 архитектурных диаграмм
5. **Code Analyzer** - анализатор кода для извлечения архитектурной информации
6. **Web Interface** - веб-интерфейс с чатом и отображением диаграмм

### Технологический стек

- **Backend**: FastAPI, Python 3.8+
- **LLM**: Ollama (локальные модели)
- **Frontend**: HTML/CSS/JavaScript, Plotly.js
- **AI Framework**: LangChain, LangGraph, LlamaIndex
- **Communication**: WebSocket, MCP (Model Context Protocol)
- **Visualization**: Plotly, C4 Model

## 🚀 Установка и запуск

### Предварительные требования

1. **Python 3.8+**
2. **Ollama** - для локальных LLM моделей
3. **MCP Server** - для интеграции с GitLab

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка

1. Создайте файл `.env` с настройками:

```env
# LLM Configuration
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2

# GitLab Configuration
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_TOKEN=your-gitlab-token

# MCP Configuration
MCP_SERVER_URL=ws://localhost:3000

# Web Interface
HOST=0.0.0.0
PORT=8000
```

2. Запустите Ollama и загрузите модель:

```bash
ollama pull llama2
```

3. Настройте MCP сервер для GitLab интеграции

### Запуск приложения

```bash
python main.py
```

Приложение будет доступно по адресу: http://localhost:8000

## 📖 Использование

### Создание агента

1. Откройте веб-интерфейс
2. Введите имя агента в поле "Agent name"
3. Нажмите "Create Agent"
4. Выберите созданного агента из списка

### Основные команды

#### Анализ репозиториев
```
Покажи все репозитории в GitLab
```

#### Создание C4 диаграммы
```
Создай C4 диаграмму для системы "MyMicroserviceSystem"
```

#### Анализ кода
```
Проанализируй репозиторий "backend-service"
```

#### Поиск кода
```
Найди все упоминания "UserController" в коде
```

#### Навигация по диаграмме
```
Покажи детали компонента "API Gateway"
```

### Примеры использования

#### Сценарий 1: Анализ новой функции

```
Пользователь: "Хочу добавить экран авторизации в веб-приложение"

Агент:
1. Анализирует существующие репозитории
2. Находит связанные компоненты (auth-service, frontend)
3. Создает C4 диаграмму с выделением затронутых элементов
4. Предлагает план реализации
```

#### Сценарий 2: Архитектурный обзор

```
Пользователь: "Покажи архитектуру всей системы"

Агент:
1. Сканирует все репозитории
2. Создает контекстную C4 диаграмму
3. Позволяет навигацию по уровням (Context → Container → Component)
4. Отображает связи между сервисами
```

## 🔧 API Endpoints

### Агенты

- `GET /api/agents` - список всех агентов
- `POST /api/agents` - создание нового агента
- `DELETE /api/agents/{agent_id}` - удаление агента
- `GET /api/agents/{agent_id}/context` - контекст агента

### WebSocket

- `WS /ws/{agent_id}` - WebSocket для чата с агентом

### Диаграммы

- `GET /api/diagrams/{diagram_id}` - получение диаграммы
- `POST /api/diagrams/{diagram_id}/highlight` - выделение элементов

## 🏗️ Архитектура агента

### LangGraph Workflow

```
User Message → Analyze Request → Execute Tools → Generate Response
```

1. **Analyze Request Node**: Анализирует запрос пользователя и определяет необходимые инструменты
2. **Execute Tools Node**: Выполняет выбранные инструменты
3. **Generate Response Node**: Генерирует финальный ответ

### Инструменты агента

#### GitLab Tools
- `gitlab_list_repositories` - список репозиториев
- `gitlab_analyze_repository` - анализ структуры репозитория
- `gitlab_search_code` - поиск кода

#### C4 Diagram Tools
- `c4_create_diagram` - создание C4 диаграммы
- `c4_drill_down` - навигация по уровням
- `c4_highlight_elements` - выделение элементов

#### Code Analysis Tools
- `code_analysis` - анализ структуры кода
- `find_code_references` - поиск ссылок в коде

### Модель данных

#### C4 Elements
- **Context Level**: Система и внешние акторы
- **Container Level**: Контейнеры (приложения, БД, очереди)
- **Component Level**: Компоненты внутри контейнеров
- **Code Level**: Детали реализации

#### Agent Context
- Репозитории
- Результаты анализа
- Текущая диаграмма
- История поиска

## 🔍 Анализ кода

### Поддерживаемые языки

- **Python**: Flask, FastAPI, Django
- **JavaScript/TypeScript**: Node.js, Express
- **React**: Компоненты, хуки, роутинг
- **Java**: Spring Boot, JPA
- **Go**: HTTP серверы, структуры

### Извлекаемая информация

- Классы и методы
- API endpoints
- Компоненты и сервисы
- Зависимости
- Модели данных
- Конфигурация

## 🎨 C4 Диаграммы

### Уровни детализации

1. **Context**: Общий контекст системы
2. **Container**: Контейнеры и их технологии
3. **Component**: Компоненты внутри контейнеров
4. **Code**: Детали реализации

### Интерактивность

- Навигация между уровнями
- Выделение элементов
- Интерактивные диаграммы (Plotly)
- Экспорт в различные форматы

## 🔧 Конфигурация

### Настройки LLM

```python
# config.py
LOCAL_LLM_URL = "http://localhost:11434"
LOCAL_LLM_MODEL = "llama2"
```

### Настройки GitLab

```python
GITLAB_URL = "https://your-gitlab-instance.com"
GITLAB_TOKEN = "your-gitlab-token"
```

### Настройки MCP

```python
MCP_SERVER_URL = "ws://localhost:3000"
```

## 🚀 Развертывание

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  architecture-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOCAL_LLM_URL=http://ollama:11434
    depends_on:
      - ollama
      - mcp-server
  
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
  
  mcp-server:
    image: your-mcp-server
    ports:
      - "3000:3000"
```

## 🧪 Тестирование

### Запуск тестов

```bash
python -m pytest tests/
```

### Тестовые сценарии

1. Создание и управление агентами
2. Анализ репозиториев
3. Генерация C4 диаграмм
4. Интеграция с GitLab
5. WebSocket коммуникация

## 🔮 Планы развития

### Краткосрочные цели

- [ ] Улучшение анализа кода
- [ ] Поддержка дополнительных языков
- [ ] Расширенные C4 диаграммы
- [ ] Интеграция с другими системами контроля версий

### Долгосрочные цели

- [ ] Машинное обучение для улучшения анализа
- [ ] Автоматическое предложение архитектурных решений
- [ ] Интеграция с CI/CD пайплайнами
- [ ] Поддержка облачных платформ

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

- Issues: GitHub Issues
- Документация: README.md
- Примеры: examples/ директория

---

**Architecture Agent** - Интеллектуальный помощник для анализа и планирования архитектуры микросервисов.