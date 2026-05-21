<p align="center">
  <h1 align="center">Ceramix AI ERP</h1>
  <p align="center">
    A full-stack, AI-powered Enterprise Resource Planning system built for the ceramics industry.
    <br />
    <strong>FastAPI + PostgreSQL + Flutter + AI</strong>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white" alt="Flutter" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

---

## Overview

**Ceramix AI ERP** is a comprehensive enterprise resource planning platform purpose-built for ceramics manufacturing businesses. It combines modern backend architecture with an AI-powered intelligence layer and a cross-platform Flutter mobile/desktop frontend.

The system is designed around **multi-tenant isolation**, ensuring data separation across organizations while sharing infrastructure efficiently.

---

## Key Features

### Business Modules

| Module | Description |
|--------|-------------|
| **Sales & Invoicing** | Invoice lifecycle management (draft, confirmed, paid, void), line-item calculations, tax handling, POS support |
| **Inventory Management** | Multi-warehouse stock tracking, stock movements (in/out/transfer), low-stock alerts, real-time quantity updates |
| **Accounting & Treasury** | Double-entry journal system with balanced debit/credit validation, profit & loss reports, chart of accounts |
| **Purchases & Procurement** | Purchase order management, supplier tracking, goods receipt |
| **Manufacturing** | Production planning, bill of materials, work orders, batch tracking |
| **CRM (Customer Relations)** | Customer profiles, contact management, lifetime value analytics, purchase history |
| **HR & Payroll** | Employee management, attendance, payroll processing |
| **Notifications** | Event-driven notifications via WebSocket, email, and push |

### AI-Powered Intelligence

- **Natural Language Query Assistant** - Ask business questions in plain English ("What are total sales this month?")
- **Semantic Search** - Find products, customers, and invoices using meaning-based search powered by pgvector embeddings
- **Trend Analysis** - AI-driven revenue forecasting and anomaly detection
- **Executive Report Generation** - Auto-generated summaries of business performance
- **Prompt Template System** - Customizable AI prompt registry for different use cases
- **Feedback Loop** - Rating system for continuous AI response quality improvement

### Real-Time Features

- **WebSocket Notifications** - Live updates pushed to connected clients
- **Tenant-Scoped Broadcasting** - Messages isolated per organization
- **User-Targeted Messaging** - Direct notifications to specific users
- **Auto-Reconnection** - Client automatically recovers from connection drops

### Webhook System

- **Event-Driven Webhooks** - Subscribe to events (invoice.created, payment.received, stock.low, etc.)
- **HMAC-SHA256 Signature Verification** - Cryptographic payload integrity validation
- **Replay Attack Protection** - Timestamp-based tolerance window
- **Exponential Backoff Retry** - Automatic retry with jitter on delivery failure (up to 5 attempts)
- **Delivery Monitoring** - Full delivery history and success/failure statistics

### Reporting & Analytics

- **Dashboard Overview** - KPIs: revenue, orders, customers, growth metrics
- **Sales Trends** - Configurable time-period trend visualization
- **Top Products & Customers** - Ranked performance lists
- **Revenue Breakdown** - Category and segment analysis
- **Financial Statements** - Profit & loss with date-range filtering
- **Materialized Views** - Pre-computed aggregations for fast dashboard loading
- **Export Formats** - CSV, Excel (XLSX), and PDF report generation

### Security & Authentication

- **JWT Access/Refresh Tokens** - Secure authentication with automatic token rotation
- **bcrypt Password Hashing** - Industry-standard password storage
- **Multi-Tenant Data Isolation** - Row-level security ensuring tenants cannot access each other's data
- **Role-Based Access Control** - Admin, manager, user, cashier roles
- **File Upload Validation** - Extension whitelist, size limits, MIME type magic-byte verification, path traversal prevention

### Monitoring & Observability

- **Prometheus Metrics** - Counter, gauge, histogram metric types with label support
- **Grafana Dashboards** - Pre-configured visualization for API performance
- **Health Check Endpoints** - Readiness and liveness probes for orchestrators
- **Performance Tracking** - Per-endpoint latency and throughput monitoring
- **Audit Logging** - Traceable record of all system actions
- **Error Tracking** - Aggregated error reporting

---

## Architecture

```
                    ┌──────────────────────────────────────────────────────┐
                    │                 Flutter Frontend                      │
                    │   (iOS / Android / Web / Desktop)                     │
                    │   Riverpod + Dio + GoRouter + fl_chart               │
                    └──────────────────────┬───────────────────────────────┘
                                           │ REST API + WebSocket
                    ┌──────────────────────▼───────────────────────────────┐
                    │                FastAPI Backend                        │
                    │                                                       │
                    │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
                    │  │  Auth   │ │  Sales   │ │Inventory │ │   AI    │ │
                    │  └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
                    │       │           │            │             │       │
                    │  ┌────▼───────────▼────────────▼─────────────▼────┐ │
                    │  │         Shared Core Layer                       │ │
                    │  │  (Security, Pagination, Webhooks, Files)        │ │
                    │  └────────────────────┬───────────────────────────┘ │
                    └───────────────────────┼─────────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────────┐
                    │              Data Layer                              │
                    │                                                      │
                    │  ┌────────────────┐  ┌───────┐  ┌────────────────┐ │
                    │  │  PostgreSQL 16 │  │ Redis │  │    Celery      │ │
                    │  │  + pgvector    │  │  7.x  │  │  (Background)  │ │
                    │  └────────────────┘  └───────┘  └────────────────┘ │
                    └─────────────────────────────────────────────────────┘
```

### Backend Stack

| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async REST API framework with automatic OpenAPI docs |
| **SQLAlchemy 2.0** | Async ORM with declarative models |
| **PostgreSQL 16** | Primary database with pgvector for AI embeddings |
| **Redis 7** | Caching, session store, pub/sub for real-time events |
| **Celery** | Distributed background task processing |
| **Alembic** | Database migration management |
| **Pydantic v2** | Request/response validation and serialization |

### Frontend Stack (Flutter)

| Technology | Purpose |
|-----------|---------|
| **Flutter 3.x** | Cross-platform UI (iOS, Android, Web, Desktop) |
| **Riverpod** | Reactive state management with dependency injection |
| **Dio + Interceptors** | HTTP client with auto JWT refresh on 401 |
| **Go Router** | Declarative routing with auth guards |
| **fl_chart** | Data visualization (line charts, bar charts) |
| **WebSocket Channel** | Real-time notification stream with auto-reconnect |
| **Material 3** | Modern design system with light/dark theme support |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| **Docker Compose** | Full-stack orchestration (app, db, redis, monitoring) |
| **Prometheus** | Metrics collection and alerting |
| **Grafana** | Monitoring dashboards |
| **GitHub Actions** | CI/CD pipeline (lint, test, build, deploy) |

---

## Project Structure

```
ceramix-ai-erp/
├── app/                          # FastAPI Backend Application
│   ├── main.py                   # Application entrypoint & middleware setup
│   ├── ai/                       # AI client, embeddings, prompt templates
│   ├── api/v1/                   # Versioned REST API routes
│   ├── background_jobs/          # Async task definitions
│   ├── core/                     # Security, config, pagination, database
│   ├── files/                    # File upload validation & storage
│   ├── jobs/                     # Celery task workers
│   ├── modules/                  # Business domain modules
│   │   ├── accounting/           #   Double-entry ledger & journal entries
│   │   ├── ai/                   #   AI query, search, analytics
│   │   ├── auth/                 #   Authentication & authorization
│   │   ├── crm/                  #   Customer relationship management
│   │   ├── hr/                   #   Human resources & payroll
│   │   ├── inventory/            #   Stock management & warehousing
│   │   ├── manufacturing/        #   Production & BOM management
│   │   ├── notifications/        #   Event-driven notification system
│   │   ├── purchases/            #   Procurement & supplier management
│   │   ├── reports/              #   Analytics & report generation
│   │   ├── sales/                #   Invoicing & order management
│   │   ├── tenants/              #   Multi-tenant configuration
│   │   ├── treasury/             #   Cash flow & financial management
│   │   └── users/                #   User profiles & role management
│   ├── monitoring/               # Prometheus metrics & health checks
│   ├── realtime/                 # WebSocket connection manager
│   ├── reports/                  # Export engine (CSV, Excel, PDF)
│   ├── shared/                   # Common utilities & base classes
│   ├── webhooks/                 # Webhook dispatch, signing, retry
│   └── websocket/                # WebSocket protocol handlers
│
├── mobile/                       # Flutter Frontend Application
│   ├── lib/
│   │   ├── main.dart             # App entry point
│   │   ├── core/                 # Theme, routing, network, error handling
│   │   ├── data/                 # Models, providers, API services
│   │   └── presentation/        # Screens & widgets
│   │       ├── auth/             #   Login & registration
│   │       ├── dashboard/        #   KPI cards, charts, top products
│   │       ├── products/         #   Product catalog & detail
│   │       ├── sales/            #   Invoice list, detail, creation
│   │       ├── inventory/        #   Stock levels & movements
│   │       ├── customers/        #   Customer management
│   │       ├── reports/          #   Report generation & AI insights
│   │       └── settings/         #   User preferences & profile
│   └── test/                     # Widget & unit tests
│
├── tests/                        # Backend Test Suite
│   ├── conftest.py               # Shared fixtures (db, client, mocks)
│   ├── factories.py              # Test data generators
│   ├── unit/                     # Unit tests (security, pagination, AI, etc.)
│   ├── integration/              # Integration tests (database, Redis, WebSocket)
│   ├── api/                      # API endpoint tests (auth, CRUD, reports)
│   └── load/                     # Load & performance tests (Locust + pytest)
│
├── database/                     # Database Schema & Migrations
│   ├── schema.sql                # Complete DDL (79KB+ comprehensive schema)
│   └── schema_part[1-3].sql      # Partitioned schema files
│
├── alembic/                      # Alembic Migration Scripts
├── devops/                       # Infrastructure Configuration
│   ├── prometheus.yml            # Prometheus scrape config
│   └── grafana/                  # Grafana dashboard definitions
│
├── scripts/                      # Utility Scripts
│   └── seed_db.py                # Database seeding for development
│
├── workflows/                    # CI/CD Pipeline Definitions
│   ├── ci.yml                    # Lint + Test + Security + Build
│   ├── deploy.yml                # Staging/Production deployment
│   ├── migrate.yml               # Database migration runner
│   └── release.yml               # Automated release & changelog
│
├── docker-compose.yml            # Production stack
├── docker-compose.dev.yml        # Development stack with hot-reload
├── Dockerfile                    # Production container image
├── Dockerfile.dev                # Development container with debugger
├── requirements.txt              # Python production dependencies
├── requirements-test.txt         # Test-only dependencies
├── pytest.ini                    # Test runner configuration
├── alembic.ini                   # Migration tool config
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (recommended for full-stack)
- **Python 3.11+** (for backend development)
- **Flutter 3.x** (for mobile/frontend development)
- **PostgreSQL 16** with pgvector extension
- **Redis 7**

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/coder-contrib/myproject.git
cd myproject

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
docker compose exec app alembic upgrade head

# Seed development data
docker compose exec app python scripts/seed_db.py
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Development Setup

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://localhost:8000
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# By category
pytest tests/ -m unit           # Unit tests only
pytest tests/ -m integration    # Integration tests (requires DB + Redis)
pytest tests/ -m api            # API endpoint tests
pytest tests/ -m load           # Load/performance tests

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Load testing with Locust
locust -f tests/load/locustfile.py --host http://localhost:8000
```

---

## API Documentation

Once running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Core API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (liveness probe) |
| `/api/v1/auth/login` | POST | Authenticate and obtain JWT tokens |
| `/api/v1/auth/register` | POST | Register new user account |
| `/api/v1/auth/refresh` | POST | Refresh expired access token |
| `/api/v1/products/` | GET/POST | List or create products |
| `/api/v1/products/{id}` | GET/PUT/DELETE | Product CRUD operations |
| `/api/v1/sales/invoices/` | GET/POST | List or create invoices |
| `/api/v1/sales/invoices/{id}/status` | PATCH | Update invoice status |
| `/api/v1/inventory/stock/` | GET | View current stock levels |
| `/api/v1/inventory/movements/` | POST | Record stock movement |
| `/api/v1/inventory/transfers/` | POST | Inter-warehouse transfer |
| `/api/v1/inventory/alerts/low-stock` | GET | Low stock warnings |
| `/api/v1/reports/dashboard/overview` | GET | Dashboard KPIs |
| `/api/v1/reports/dashboard/sales-trend` | GET | Sales trend data |
| `/api/v1/reports/financial/profit-loss` | GET | P&L statement |
| `/api/v1/reports/export/sales` | GET | Export to CSV/Excel |
| `/api/v1/ai/query` | POST | Natural language query |
| `/api/v1/ai/search` | POST | Semantic vector search |
| `/api/v1/ai/analytics/trends` | POST | AI trend analysis |
| `/api/v1/ai/reports/generate` | POST | AI report generation |
| `/api/v1/webhooks/` | GET/POST | Manage webhook subscriptions |
| `/api/v1/monitoring/metrics` | GET | Prometheus metrics |
| `/api/v1/files/upload` | POST | Secure file upload |
| `/ws/notifications` | WS | Real-time notification stream |

---

## CI/CD Pipeline

The project includes a complete GitHub Actions pipeline:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | Push/PR to main, develop | Lint (ruff, mypy) + Tests + Security scan (bandit, safety) + Docker build |
| **Deploy** | Manual dispatch | Deploy to staging or production via SSH with health checks and rollback |
| **Migrate** | Manual dispatch | Run Alembic migrations (upgrade/downgrade) on target environment |
| **Release** | Tag push (v*.*.*) | Auto-generate changelog and create GitHub Release |

---

## Environment Variables

See `.env.example` for the complete list. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (async: `postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis connection URL |
| `SECRET_KEY` | JWT signing secret |
| `AI_API_KEY` | API key for AI/LLM provider |
| `ENVIRONMENT` | Runtime environment (development/staging/production) |

---

## Testing Strategy

| Layer | Framework | Description |
|-------|-----------|-------------|
| **Unit** | pytest | Isolated logic testing (security, pagination, AI, webhooks, files, metrics, retry, export) |
| **Integration** | pytest + real DB/Redis | Database operations, Redis caching, WebSocket manager |
| **API** | pytest + httpx | Full endpoint testing with auth flow |
| **Load** | Locust + pytest | Performance benchmarks (latency, throughput, concurrency) |

Load testing simulates three user profiles:
- **ERP User** - General operations across all modules
- **POS User** - High-frequency point-of-sale transactions
- **Reporting User** - Heavy analytical queries and exports

---

## License

This project is proprietary software. All rights reserved.

---

## Contributing

1. Create a feature branch from `main`
2. Implement your changes with tests
3. Ensure all CI checks pass
4. Submit a pull request with a clear description

---

<p align="center">
  <sub>Built with FastAPI, Flutter, PostgreSQL, Redis, and AI</sub>
</p>
