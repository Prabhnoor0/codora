#  AI Open Source Mentor

> **GitHub + Coursera + Duolingo + Copilot + StackOverflow + Mentor** — in one AI-powered platform.

An intelligent mentorship platform that understands repositories, understands developers, teaches codebases, recommends issues, predicts contribution success, guides implementation, and reviews pull requests.

---

##  Features

| Feature | Description |
|---|---|
|  **Repository Explainer** | AI analyzes README, code, architecture, and generates a complete overview |
|  **Architecture Visualization** | Interactive React Flow diagrams of services, modules, data flows |
|  **Subsystem Discovery** | Groups files into logical systems (Auth, Payments, API, etc.) |
|  **Knowledge Graph** | Neo4j graph: File→Function→Class→Module→Dependency |
|  **AI Codebase Teacher** | Personalized day-by-day learning paths |
|  **AI Mentor Chat** | Repository-aware streaming chat (never generic responses) |
|  **Contribution Readiness Score** | 0-100 score per issue with missing skills |
|  **Issue Tutor** | Converts issues into structured learning experiences |
|  **Affected File Prediction** | Predicts which files an issue will touch |
|  **PR Reviewer** | AI detects bugs, security issues, architectural violations |
|  **Developer Knowledge Graph** | Long-term memory of your skills and learning progress |

---

##  Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                      │
│  Auth → Dashboard → Repo Explorer → Mentor Chat → PR Review  │
└────────────────────┬─────────────────────────────────────────┘
                     │ REST + SSE Streaming
┌────────────────────▼─────────────────────────────────────────┐
│                  API GATEWAY (FastAPI)                        │
└──┬──────────┬──────────┬──────────┬──────────┬───────────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼──┐  ┌────▼───┐  ┌──▼──┐  ┌───▼────┐
│ PG  │  │Neo4j │  │ Qdrant │  │Redis│  │ Celery │
│ SQL │  │Graph │  │Vector  │  │Cache│  │Workers │
└─────┘  └──────┘  └────────┘  └─────┘  └───┬────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │      ML / AI Pipeline        │
                               │  CodeBERT │ XGBoost │ RAG   │
                               │  6 LLM Agents (LangGraph)   │
                               └─────────────────────────────┘
```

---

##  Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd ai-open-source-mentor
cp .env.example .env
```

### 2. Fill in `.env`

```env
# Required
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# At least one LLM key
GOOGLE_API_KEY=your_gemini_api_key    # Recommended (free tier)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

LLM_PROVIDER=google
LLM_MODEL=gemini-1.5-pro

# Optional: higher GitHub rate limits
GITHUB_PAT=ghp_your_personal_access_token
```

### 3. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Set **Callback URL**: `http://localhost:3000/auth/callback`
4. Copy **Client ID** and **Client Secret** to `.env`

### 4. Start everything

```bash
make dev
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: `neo4j`, password: `mentor_password`)
- **Flower** (Celery monitor): http://localhost:5555

### 5. Run database migrations

```bash
make migrate
```

---

##  Tech Stack

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + custom design system
- **React Flow** — interactive architecture diagrams
- **Framer Motion** — animations
- **Zustand** — state management
- **Axios** — API client

### Backend
- **FastAPI** + **Python 3.11**
- **Celery** + **Redis** — background task queue
- **SQLAlchemy** (async) + **Alembic** — ORM + migrations

### Databases
- **PostgreSQL 16** — primary data store
- **Neo4j 5** — knowledge graphs (repository + developer)
- **Qdrant** — vector embeddings (RAG)
- **Redis 7** — caching + task broker

### AI / ML
- **Sentence Transformers** (`all-MiniLM-L6-v2`) — lightweight embeddings (dev)
- **CodeBERT / GraphCodeBERT** — code embeddings (production)
- **XGBoost / LightGBM** — issue difficulty + readiness prediction
- **LangGraph** — multi-agent orchestration
- **6 Specialized Agents**: RepositoryAnalyst, CodeExplainer, MentorAgent, IssueTutor, PRReviewer, RecommendationAgent
- **LLM Providers**: Gemini / OpenAI GPT-4o / Claude Sonnet

---

##  Project Structure

```
ai-open-source-mentor/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic settings
│   ├── models/                 # SQLAlchemy ORM
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic
│   │   ├── github_service.py   # GitHub API client
│   │   ├── llm_service.py      # Multi-provider LLM
│   │   ├── rag_service.py      # RAG pipeline
│   │   ├── graph_service.py    # Neo4j operations
│   │   ├── embedding_service.py
│   │   └── agent_service.py    # 6 LLM agents
│   ├── tasks/                  # Celery background tasks
│   │   ├── analyze_repo.py     # 9-stage analysis pipeline
│   │   └── update_user_graph.py
│   └── ml/                     # ML models
│       ├── skill_extractor.py
│       ├── difficulty_predictor.py
│       └── readiness_predictor.py
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── dashboard/          # User dashboard
│   │   ├── auth/callback/      # OAuth handler
│   │   ├── repo/[owner]/[name]/
│   │   │   ├── page.tsx        # Repo overview
│   │   │   ├── architecture/   # React Flow diagram
│   │   │   ├── issues/         # Issue recommendations
│   │   │   ├── learn/          # Learning roadmap
│   │   │   └── mentor/         # AI chat
│   │   └── pr-review/          # PR reviewer
│   ├── lib/
│   │   ├── api.ts              # Axios client
│   │   └── store.ts            # Zustand stores
│   └── globals.css             # Design system
│
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

##  Development Commands

```bash
make dev              # Start all services
make down             # Stop all services
make migrate          # Run DB migrations
make test-backend     # Run pytest
make test-frontend    # Run Jest
make logs             # Follow all logs
make shell-db         # psql shell
make shell-neo4j      # Cypher shell
```

---

##  AI Agent Architecture

```
User Question
    │
    ▼
MentorAgent (RAG retrieval + Neo4j context)
    │
    ├─→ RepositoryAnalyst (architecture, subsystems)
    ├─→ CodeExplainer (file-level explanations)
    ├─→ IssueTutor (learning paths for issues)
    ├─→ PRReviewer (diff analysis)
    └─→ RecommendationAgent (issue matching)
```

Each agent:
1. Receives relevant code chunks from Qdrant (RAG)
2. Queries Neo4j for graph relationships
3. Calls LLM with structured prompts
4. Returns typed JSON responses

---

##  Data Flow

```
GitHub URL
    │
    ▼ GitHub API
Repository Metadata + File Tree + README + Issues
    │
    ├── LLM Analysis ──────────────────► Architecture Diagram
    │                                   └── Subsystems
    │
    ├── CodeBERT Embeddings ────────────► Qdrant (RAG)
    │
    ├── Neo4j Graph ────────────────────► File→Function→Class graph
    │
    └── Issue Analysis ─────────────────► Difficulty + Required Skills
```

---

##  Environment Variables

See [`.env.example`](.env.example) for all variables.

**Required**:
- `GITHUB_CLIENT_ID` + `GITHUB_CLIENT_SECRET`
- At least one of: `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

**Recommended**:
- `GITHUB_PAT` — Personal access token for higher API rate limits

---

