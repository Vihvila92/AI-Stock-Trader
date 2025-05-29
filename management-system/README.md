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

## TODO: Node-Agent Integration

The following features need to be implemented to support the node-agent system:

### Agent Registration & Management

- [ ] **Registration Token API**: Generate secure, time-limited (30 minutes) registration tokens for new agents
- [ ] **Agent Registration Endpoint**: Accept agent registration requests with tokens and create permanent device credentials
- [ ] **Device UUID Management**: Generate and store immutable device identifiers (UUIDs) for each registered agent
- [ ] **Agent Status Tracking**: Monitor agent connection status (online/offline, last seen)
- [ ] **Agent Deregistration**: Remove agents from the system and revoke credentials

### Communication & Control

- [ ] **Secure Communication Protocol**: Implement TLS-encrypted communication channel (WebSocket/REST/MQTT)
- [ ] **Command Queue System**: Queue and dispatch commands to specific agents
- [ ] **Resource Monitoring Dashboard**: Display real-time resource data (CPU, memory, disk, network) from all agents
- [ ] **Agent Health Monitoring**: Track agent health and performance metrics

### Module Management

- [ ] **Module Repository**: Store and manage modules that can be deployed to agents
- [ ] **Module Deployment API**: Send module installation/execution commands to agents
- [ ] **Module Version Control**: Track module versions and updates
- [ ] **Execution Status Tracking**: Monitor module execution status and results from agents

### Security & Authentication

- [ ] **Token Encryption/Encoding**: Implement secure token generation that cannot be read by humans
- [ ] **Device Certificate Management**: Generate and manage device-specific certificates
- [ ] **Permission System**: Define what each agent is allowed to execute
- [ ] **Audit Logging**: Log all agent actions and communications for security auditing

### UI Components

- [ ] **Agent Dashboard**: Overview of all registered agents with status indicators
- [ ] **Agent Details View**: Detailed view of individual agent resources and logs
- [ ] **Command Interface**: UI for sending commands to agents
- [ ] **Module Management UI**: Interface for uploading and managing modules
- [ ] **Registration Token Generator**: UI for generating and managing registration tokens

### Database Schema

- [ ] **Agents Table**: Store agent information (UUID, name, status, credentials)
- [ ] **Registration Tokens Table**: Manage active registration tokens
- [ ] **Commands Table**: Store command history and status
- [ ] **Resource Metrics Table**: Store historical resource data from agents
- [ ] **Modules Table**: Store module metadata and deployment information
