# 🚀 Agent LLM Deployment System - Autonomous AI Web Developer

A **Brahmacode-inspired** autonomous AI agent designed to build, deploy, and update complete web applications from natural language project briefs. Built with **FastAPI**, **SQLAlchemy 2.0**, and modern async patterns.

## ✨ Key Features

- **🔄 Autonomous End-to-End Development**: Receives project briefs and handles entire development lifecycle
- **🎯 Multi-Round Capability**: Round 1 (new projects) and Round 2+ (updates) with RAG-powered context
- **🤖 Think-Plan-Act-Review Methodology**: Structured AI agent behavior for high-quality results
- **🚀 Automated Deployment**: Creates GitHub repos and deploys to GitHub Pages automatically
- **🔧 Multi-LLM Provider Support**: OpenAI, Anthropic, Gemini, Copilot with automatic failover
- **📚 Interactive API Documentation**: Beautiful Swagger UI at `/docs`
- **🐳 Production Ready**: Docker containerization with health checks
- **📊 Comprehensive Monitoring**: Structured logging and observability

## 🏗️ Architecture

```
src/
├── main.py              # FastAPI application entry point
├── api/
│   └── routes.py        # API endpoints and request handling
├── agent/
│   ├── orchestrator.py  # Core AI agent with Think-Plan-Act-Review
│   └── tools.py         # Agent tools for file system, Git, validation
├── services/
│   ├── database.py      # Async SQLAlchemy operations
│   ├── github.py        # GitHub integration and deployment
│   └── llm.py           # Multi-provider LLM management
├── models/
│   ├── database.py      # SQLAlchemy models
│   └── schemas.py       # Pydantic API schemas
└── core/
    ├── config.py        # Pydantic settings management
    └── logging.py       # Structured logging configuration
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+
# Git
# Node.js and npm (for ESLint)
# Google Chrome/Chromium (for Playwright)
```

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-llm-deployment

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium --with-deps
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required:
# - GITHUB_TOKEN (with repo permissions)
# - OPENAI_API_KEY or other LLM provider keys
# - HF_TOKEN (Hugging Face for database sync)
```

### 4. Run the Application

```bash
# Start the FastAPI server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the run script
python run.py
```

The API will be available at `http://localhost:8000`

## 📖 API Usage

### Interactive Documentation

Visit `http://localhost:8000/docs` for complete API documentation with:
- ✅ **Try it out** buttons for each endpoint
- ✅ **Request/response examples**
- ✅ **Model validation schemas**
- ✅ **Authentication requirements**

### Core Endpoints

#### Request Autonomous Development
```http
POST /api/request
Content-Type: application/json

{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "nonce": "unique-request-id",
  "task": "markdown-converter-abc123",
  "round": 1,
  "brief": "Create a web app that converts Markdown to HTML in real-time",
  "checks": [
    "Must use a CDN Markdown parser",
    "Must have live preview",
    "Must be responsive"
  ],
  "evaluation_url": "https://your-callback-url.com"
}
```

**Response:**
```json
{
  "task": "markdown-converter-abc123",
  "status": "accepted",
  "message": "Task accepted and queued for autonomous processing",
  "nonce": "unique-request-id",
  "estimated_completion_time_minutes": 5
}
```

#### Check Task Status
```http
GET /api/status/{task_id}
```

#### Health Check
```http
GET /health
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key | ⚠️* |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | ⚠️* |
| `GEMINI_API_KEYS` | Google Gemini API Keys (comma-separated) | ⚠️* |
| `HF_TOKEN` | Hugging Face Token | ✅ |
| `DATABASE_ID` | Hugging Face Dataset ID | ✅ |

*At least one LLM provider required

### Advanced Configuration

```bash
# Multi-provider LLM setup
GEMINI_API_KEYS=key1,key2,key3
COPILOT_GITHUB_TOKEN=your-copilot-token

# Production settings
DEPLOYMENT_ENV=production
LOG_LEVEL=WARNING
MAX_CONCURRENT_TASKS=5
```

## 🤖 Autonomous AI Agent

The system uses a sophisticated AI agent that follows the **Think-Plan-Act-Review** methodology:

1. **Think**: Analyze requirements and understand the task
2. **Plan**: Create detailed development plan with steps
3. **Act**: Execute development with code generation and validation
4. **Review**: Quality assurance and final validation

### Agent Capabilities

- **Code Generation**: HTML, CSS, JavaScript generation
- **File Management**: Workspace creation and file operations
- **Git Integration**: Repository creation and deployment
- **Quality Assurance**: Linting, validation, and testing
- **Multi-round Updates**: Context-aware modifications

## 🐳 Docker Deployment

### Development
```bash
# Build image
docker build -t agent-llm-deployment .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  agent-llm-deployment
```

### Production Deployment

**Render** (Recommended):
1. Connect your GitHub repository
2. Select Docker as runtime
3. Add environment variables
4. Deploy!

**Hugging Face Spaces**:
1. Create new Space with Docker
2. Upload `Dockerfile` and `src/`
3. Add environment variables
4. Deploy automatically

## 🔒 Security Features

- **API Key Authentication**: Multiple LLM provider support
- **Rate Limiting**: Configurable request throttling
- **Input Validation**: Pydantic model validation
- **CORS Protection**: Configurable cross-origin policies
- **Secret Management**: Secure credential handling

## 📊 Monitoring & Observability

- **Structured Logging**: JSON-formatted logs with structlog
- **Health Checks**: Comprehensive system health monitoring
- **Error Tracking**: Ready for Sentry integration
- **Performance Metrics**: Prepared for Prometheus/Grafana

## 🧪 Development

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Test specific module
pytest tests/test_api.py -v
```

### Code Quality
```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Type check
mypy src/
```

## 🚧 Roadmap

- [ ] **Advanced RAG**: Vector-based code understanding for updates
- [ ] **WebSocket Support**: Real-time progress updates
- [ ] **Advanced Testing**: Browser automation and end-to-end tests
- [ ] **Plugin System**: Extensible tool architecture
- [ ] **Multi-tenancy**: Support for multiple organizations
- [ ] **Web UI**: React dashboard for task management

## 📝 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ using FastAPI, SQLAlchemy 2.0, and the Think-Plan-Act-Review methodology**

*Inspired by Brahmacode - Autonomous AI Web Developer*
