# Syntra AI Orchestrator

**Syntra** is an intelligent AI-powered orchestration service for the Goalixa productivity platform. It provides automated DevOps operations, task planning, and code review capabilities through a multi-agent system powered by CrewAI and FastAPI.

## Overview

Syntra acts as an intelligent automation layer that can:
- Plan complex tasks using AI
- Execute DevOps operations on Kubernetes clusters
- Review and validate changes
- Interact with Git repositories
- Analyze logs and incidents
- Provide both REST API and CLI interfaces

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Syntra Service                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │              FastAPI REST API                       │ │
│  │           /api/ask (POST)                           │ │
│  └────────────┬───────────────────────────────────────┘ │
│               │                                          │
│  ┌────────────▼───────────────────────────────────────┐ │
│  │           Orchestration Layer                       │ │
│  │          (crew_runner.py)                           │ │
│  └────────────┬───────────────────────────────────────┘ │
│               │                                          │
│  ┌────────────▼───────────────────────────────────────┐ │
│  │              Agent System                           │ │
│  │  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ PlannerAgent │  │ DevOpsAgent  │                │ │
│  │  └──────────────┘  └──────────────┘                │ │
│  │  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ReviewerAgent │  │   BaseAgent  │                │ │
│  │  └──────────────┘  └──────────────┘                │ │
│  └────────────────────────────────────────────────────┘ │
│               │                                          │
│  ┌────────────▼───────────────────────────────────────┐ │
│  │               Tools Layer                           │ │
│  │  Git Tools │ K8s Tools │ Log Tools │ Auth          │ │
│  └────────────────────────────────────────────────────┘ │
│               │                                          │
│  ┌────────────▼───────────────────────────────────────┐ │
│  │              Memory Layer                           │ │
│  │        Incident Memory (ChromaDB)                   │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Features

### Multi-Agent System
- **PlannerAgent**: Analyzes requests and creates execution plans
- **DevOpsAgent**: Executes DevOps operations (Kubernetes, Git, etc.)
- **ReviewerAgent**: Reviews and validates execution results
- **BaseAgent**: Abstract base class for all agents

### Tools & Integrations
- **Kubernetes Tools**: Pod management, cluster operations
- **Git Tools**: Repository operations
- **Log Tools**: Log analysis and monitoring
- **Permission Client**: Integration with Goalixa Auth Service

### Memory System
- **Incident Memory**: ChromaDB-based vector storage for incident history
- Persistent context for AI agents

### Interfaces
- **REST API**: FastAPI-based HTTP endpoints
- **CLI**: Interactive command-line interface

## Tech Stack

- **Backend Framework**: FastAPI
- **AI Orchestration**: CrewAI
- **CLI Framework**: Typer + Rich
- **Language Models**: LangChain (Claude integration)
- **HTTP Client**: httpx (async)
- **Vector Database**: ChromaDB
- **Cache**: Redis
- **Kubernetes**: Python client
- **Authentication**: Custom auth client

## Project Structure

```
syntra/
├── agents/              # Agent implementations
│   ├── base_agent/     # Abstract base agent
│   ├── planner_agent/  # Task planning agent
│   ├── devops_agent/   # DevOps execution agent
│   └── reviewer_agent/ # Review and validation agent
├── api/                # FastAPI routes and schemas
│   ├── routes.py       # API endpoints
│   ├── schemas.py      # Pydantic models
│   ├── dependencies.py # Dependency injection
│   └── main.py         # API configuration
├── orchestration/      # Agent orchestration logic
│   └── crew_runner.py  # CrewAI task runner
├── tools/              # Utility tools
│   ├── git_tools/      # Git operations
│   ├── kubernetes_tools/ # K8s operations
│   └── log_tools/      # Log analysis
├── auth/               # Authentication
│   └── permission_client/ # Auth service client
├── memory/             # Memory and context
│   └── incident_memory/ # Incident tracking
├── cli/                # Beautiful CLI (Typer + Rich)
│   ├── main.py         # CLI entry point
│   ├── console.py      # Rich console configuration
│   ├── api.py          # Async API client
│   ├── utils.py        # CLI utilities
│   └── config.py       # CLI configuration
├── CLI/                # Old CLI (deprecated)
│   └── cli.py          # Legacy interactive CLI
├── syntra              # CLI executable script
├── deployment/         # Kubernetes manifests
│   └── argo.yaml       # ArgoCD deployment
├── config.py           # Configuration settings
├── main.py             # FastAPI application entry
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
└── docker-compose.yml  # Local development
```

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- kubectl (for Kubernetes tools)
- Access to Goalixa Auth Service

### Installation

1. **Clone the repository**:
   ```bash
   cd /Users/snapp/Desktop/projects/Goalixa/Services/syntra
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running Locally

#### Option 1: Direct Python
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 2: Docker Compose
```bash
docker-compose up --build
```

### Verify Installation

```bash
curl http://localhost:8000/
# Response: {"service": "Syntra AI Orchestrator", "status": "running"}
```

## Usage

### REST API

**Ask AI to perform a task**:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Check pod status in production namespace"}'
```

**API Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Beautiful CLI Interface

Syntra includes a beautiful, high-performance CLI built with **Typer** and **Rich**.

#### Installation

Install CLI dependencies:
```bash
pip install typer rich httpx aiohttp
```

#### Usage

**Quick Start**:
```bash
# Run the CLI
python -m cli --help

# Or use the executable script
./syntra --help
```

**Available Commands**:

```bash
# Ask Syntra AI to perform a task
python syntra_cli.py ask "list all pods in production namespace"

# Interactive mode (standard)
python syntra_cli.py interactive

# Enhanced REPL mode (recommended) - with history!
python syntra_repl.py

# Check health
python syntra_cli.py health

# Show info
python syntra_cli.py info

# List agents
python syntra_cli.py agents

# List tools
python syntra_cli.py tools

# Show version
python syntra_cli.py --version
```

### Interactive Modes

#### Standard Mode
```bash
python syntra_cli.py interactive
```
Basic interactive session with prompt.

#### Enhanced REPL Mode (Recommended)
```bash
python syntra_repl.py
```
Full-featured REPL with:
- 📜 Command history (100 commands)
- 📊 Session statistics
- 🎯 Better formatting
- 💡 Enhanced commands

**REPL Commands:**
- `help` - Show all commands
- `history` - Show command history
- `stats` - Session statistics
- `clear` - Clear screen
- `server` - Server info
- `exit` - Exit REPL

# Interactive mode (like ChatGPT CLI)
syntra interactive

# Check API health
syntra health

# Show CLI information
syntra info

# List available agents
syntra agents

# List available tools
syntra tools

# Show version
syntra --version
```

**Examples**:

```bash
# Single command
syntra ask "Check pod status in production"

# With custom server
syntra ask "deploy latest version" --server http://api.example.com

# JSON output
syntra ask "list pods" --json

# Interactive mode
syntra interactive
> list pods in default namespace
> check logs for auth service
> exit
```

**CLI Features**:
- 🎨 Beautiful colored output with Rich
- ⚡ Fast async HTTP client
- 🔄 Spinners for long operations
- 📊 Tables for structured data
- 💡 Interactive mode
- 📝 JSON output option
- 🏥 Health checks
- ❯ Auto-completion (coming soon)

## Configuration

Environment variables (`.env`):

```bash
# Service
PROJECT_NAME=Syntra AI Orchestrator
API_VERSION=v1

# Auth Service
AUTH_SERVICE_URL=http://auth-service:8000

# Kubernetes
KUBECTL_PATH=/usr/local/bin/kubectl

# AI Model
MODEL_NAME=claude

# Database (optional)
REDIS_URL=redis://localhost:6379
CHROMADB_PATH=./data/chromadb
```

## Deployment

### Docker
```bash
docker build -t syntra-ai:latest .
docker run -p 8000:8000 -e AUTH_SERVICE_URL=http://auth-service syntra-ai:latest
```

### Kubernetes with ArgoCD
The `deployment/argo.yaml` contains ArgoCD deployment configuration.

Apply to cluster:
```bash
kubectl apply -f deployment/argo.yaml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service health check |
| POST | `/api/ask` | Submit AI task |

## Development

### Adding a New Agent

1. Create new agent class inheriting from `BaseAgent`:
   ```python
   # agents/my_agent/my_agent.py
   from agents.base_agent import BaseAgent

   class MyAgent(BaseAgent):
       def __init__(self):
           super().__init__("my_agent")

       def execute(self, task: str):
           # Implementation here
           return result
   ```

2. Add agent to crew in `orchestration/crew_runner.py`

3. Update documentation

### Adding New Tools

Create new tool in `tools/` directory:
```python
# tools/my_tool/my_tool.py

def my_operation(param: str):
    """Tool description"""
    # Implementation
    return result
```

## Current Status

**Phase**: Early Development / MVP

**Implemented**:
- Base agent framework
- FastAPI REST API
- Basic orchestration
- Kubernetes tools (pod listing)
- CLI interface
- Docker configuration

**In Progress**:
- Full CrewAI integration
- AI-powered planning
- Complete tool implementations
- Auth service integration
- Incident memory with ChromaDB

**Planned**:
- Advanced Git operations
- Log analysis with AI
- Review agent with validation rules
- Multi-step task execution
- Webhook support
- Metrics and monitoring

## Integration with Goalixa

Syntra integrates with the Goalixa platform:
- **Auth Service**: Permission validation
- **Core API**: Task and project management
- **Kubernetes**: Cluster operations for all Goalixa services

## Contributing

1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit PR for review

## License

Internal Goalixa Service - Proprietary

---

**Last Updated**: 2026-03-22
**Version**: 0.1.0-alpha

