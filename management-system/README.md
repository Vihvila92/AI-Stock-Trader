# AI Stock Trader - Management System Docker Setup

## Structure

The project consists of four main components:

- **Backend**: Python/FastAPI server (ai-stock-trader-backend)
- **Frontend**: Next.js application (ai-stock-trader-frontend)
- **Proxy**: Nginx reverse proxy (uses official nginx image)
- **Database**: PostgreSQL (uses official postgres image)

## Usage

### Development (uses docker-compose.override.yml)

```bash
# Start all services in development mode
docker-compose up -d

# Services:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - Proxy: http://localhost:80
# - Database: localhost:5432
```

### Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or set environment variables and use main file
export DOCKERHUB_USERNAME=kozzyvizzy
export TAG=latest
docker-compose up -d
```

## Environment Variables

Copy `.env.example` → `.env` and modify as needed:

```bash
cp .env.example .env
```

## Docker Images

GitHub Actions automatically builds and pushes:

- `kozzyvizzy/ai-stock-trader-backend:latest` (main branch)
- `kozzyvizzy/ai-stock-trader-backend:dev` (dev branch)
- `kozzyvizzy/ai-stock-trader-backend:test` (test branch)

Same logic applies to frontend.

## Development Tools

### Local Build

```bash
# Backend
docker build -t ai-stock-trader-backend ./backend

# Frontend
docker build -t ai-stock-trader-frontend --target production ./frontend
```

### Log Monitoring

```bash
# All services logs
docker-compose logs -f

# Individual service logs
docker-compose logs -f backend
```
