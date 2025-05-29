# AI Stock Trader

A secure, distributed system for automated stock trading using artificial intelligence and machine learning.

## Overview

AI Stock Trader is a modular, security-focused platform that combines advanced trading strategies with machine learning. The system utilizes a distributed architecture with a central management system and individual processing nodes.

### Key Features

- Secure, distributed architecture
- Zero-trust security model
- Modular processing system
- Real-time market data analysis
- Automated trading capabilities
- Scalable infrastructure
- Containerized microservices with automated CI/CD

## System Architecture

```ascii
┌─────────────────────┐
│  Management System  │
│  ┌───────────────┐ │
│  │    Frontend   │ │
│  │   (Next.js)   │ │
│  └───────────────┘ │
│  ┌───────────────┐ │
│  │    Backend    │ │
│  │   (FastAPI)   │ │
│  └───────────────┘ │
└─────────────────────┘
         ▲
         │
    Secure API
         │
         ▼
┌─────────────────────┐
│    Node Agents      │
└─────────────────────┘
         ▲
         │
         ▼
┌─────────────────────┐
│ Processing Modules  │
└─────────────────────┘
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

### Quick Start

1. Clone the repository:

```bash
git clone https://github.com/Vihvila92/AI-Stock-Trader.git
cd AI-Stock-Trader
```

1. Start the management system:

```bash
cd management-system
docker-compose up -d
```

1. Access the services:

- **Web Interface**: <http://localhost:80> (via nginx proxy)
- **Frontend**: <http://localhost:3000> (Next.js)
- **Backend API**: <http://localhost:8000> (FastAPI)
- **Database**: localhost:5432 (PostgreSQL)

### Docker Architecture

The system uses a microservices architecture with automated Docker image builds:

#### Management System Components

- **Backend**: `kozzyvizzy/ai-stock-trader-backend`
- **Frontend**: `kozzyvizzy/ai-stock-trader-frontend`
- **Proxy**: `nginx:1.25-alpine` (official image + custom config)
- **Database**: `postgres:16` (official image)

#### Environment-specific Deployments

```bash
# Development (uses docker-compose.override.yml)
docker-compose up -d

# Testing environment
export TAG=test
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Images & CI/CD

GitHub Actions automatically builds and pushes Docker images to Docker Hub:

**Branches → Tags:**

- `main` → `latest`
- `dev` → `dev`
- `test` → `test`

**Available Images:**

- `kozzyvizzy/ai-stock-trader-backend:latest|dev|test`
- `kozzyvizzy/ai-stock-trader-frontend:latest|dev|test`

### Development

The project uses a containerized development workflow with automated Docker builds:

#### Branch Strategy

- `main`: Production releases
- `test`: Testing and validation
- `dev`: Active development

#### Local Development

```bash
# Start development environment (uses override config)
cd management-system
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Production Deployment

```bash
# Deploy with production images from Docker Hub
cd management-system
docker-compose -f docker-compose.prod.yml up -d
```

## Documentation

Comprehensive documentation is available in the `/Documentation` directory:

- [Project Overview and Goals](Documentation/01_project_and_goals.md)
- [Technical Structure](Documentation/02_technical_structure.md)
- [Usage and UI Guide](Documentation/03_usage_and_ui.md)
- [Testing and Development](Documentation/04_testing_and_development_practices.md)
- [Future Plans](Documentation/05_future_plans_and_questions.md)

## Security

The system implements multiple security layers:

- Individual agent encryption keys
- Daily key rotation
- Zero-trust architecture
- Dynamic permission system
- Anomaly detection

## Current Status

Project is in active development (v1.0.0). Core components under construction:

- Management System ✅
- Agent System (planned)
- Basic Processing Modules (planned)

## Contributing

Currently a single-developer project. Contribution guidelines will be added as the project matures.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Trading Disclaimer

This software is an experimental project intended for educational and research purposes only.
It is not meant for actual trading or financial decision-making. See the [LICENSE](LICENSE)
file for full disclaimer and terms.

## Contact

- GitHub: [@Vihvila92](https://github.com/Vihvila92)
- Security Issues: Please create a new issue on [GitHub Issues](https://github.com/Vihvila92/AI-Stock-Trader/issues) with the `security` label

## Acknowledgments

- List any references or inspirations
- Credit any third-party libraries or tools used
