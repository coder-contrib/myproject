# Ceramix AI ERP

Enterprise Resource Planning system built with FastAPI + Flutter.

## Backend

- FastAPI with async SQLAlchemy 2.0
- PostgreSQL with pgvector
- Redis for caching and pub/sub
- Celery for background tasks
- Multi-tenant architecture

## Frontend (Flutter)

- Material 3 design
- Riverpod state management
- Dio + Retrofit for API communication
- Go Router for navigation
- Real-time WebSocket notifications

## Getting Started

```bash
# Backend
docker compose up -d

# Frontend
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://localhost:8000
```

## Project Structure

```
.
├── app/              # FastAPI backend
├── mobile/           # Flutter frontend
├── tests/            # Backend test suite
├── devops/           # Monitoring (Prometheus/Grafana)
├── workflows/        # CI/CD pipeline definitions
└── docker-compose.yml
```
