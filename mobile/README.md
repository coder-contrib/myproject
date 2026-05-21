# Ceramix ERP - Flutter Frontend

Flutter mobile/web application for the Ceramix AI ERP system.

## Setup

```bash
cd mobile
flutter pub get
flutter run
```

## Architecture

- **Clean Architecture** with feature-based organization
- **Riverpod** for state management
- **Dio + Retrofit** for API communication
- **Go Router** for navigation
- **Freezed** for immutable models

## Structure

```
lib/
├── core/           # Shared utilities, theme, constants
├── data/           # API clients, repositories, DTOs
├── domain/         # Entities, repository interfaces
├── presentation/   # UI screens, widgets, providers
└── main.dart       # App entry point
```

## Running

```bash
# Development
flutter run --dart-define=API_URL=http://localhost:8000

# Code generation
dart run build_runner build --delete-conflicting-outputs

# Tests
flutter test
```
