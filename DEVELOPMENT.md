# AI Stock Trader - Development Tools

This document describes the development tools and configurations used in the project.

## 🛠️ Development Environment Setup

### 1. Basic Installation

```bash
# Clone repository
git clone <repository-url>
cd AI-Stock-Trader

# Install frontend dependencies
cd management-system/frontend
npm install

# Install backend dependencies (in virtual environment)
cd ../backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
cd ../..
pre-commit install
```

### 2. VS Code Setup

Open `AI-Stock-Trader.code-workspace` in VS Code for optimal development experience.

Recommended extensions will install automatically:

- Python
- ESLint
- Prettier
- Tailwind CSS
- Docker
- GitHub Copilot

## 🧪 Testing

### Frontend Tests (Jest + Testing Library)

```bash
cd management-system/frontend

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

### Backend Tests (pytest)

```bash
cd management-system/backend

# Run tests
pytest

# Run tests with coverage report
pytest --cov=. --cov-report=html

# Run specific file tests
pytest tests/test_api.py

# Run tests by markers
pytest -m unit
pytest -m integration
```

## 🔍 Code Quality Assurance

### Frontend

```bash
cd management-system/frontend

# ESLint check
npm run lint

# ESLint fix
npm run lint:fix

# Prettier formatting
npm run format

# Prettier check
npm run format:check

# TypeScript type check
npm run type-check
```

### Backend

```bash
cd management-system/backend

# Black formatting
black .

# Flake8 check
flake8 .

# isort import order
isort .

# mypy type check
mypy .

# Bandit security check
bandit -r .
```

## 🔧 Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- **Frontend**: ESLint, Prettier, TypeScript check
- **Backend**: Black, Flake8, isort, Bandit, mypy
- **Docker**: Hadolint
- **General**: detect-secrets, trailing whitespace, file size

Manual execution:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## 📊 Coverage Reports

### Frontend

Coverage report is generated in `coverage/` folder when you run `npm run test:coverage`.

### Backend (Coverage)

Coverage report is generated in `htmlcov/` folder when you run pytest with coverage options.

## 🎯 Coverage Targets

- **Frontend**: 80% branch, function, line, statement coverage
- **Backend**: 80% overall coverage
- **New files**: 90% coverage requirement

## 🚀 Development Workflow

1. **Create new branch**: `git checkout -b feature/new-feature`
2. **Develop**: Write code and tests
3. **Test**: `npm test` and `pytest`
4. **Check quality**: Pre-commit hooks run automatically
5. **Commit**: `git commit -m "feat: add new feature"`
6. **Push**: `git push origin feature/new-feature`
7. **Pull Request**: Create PR on GitHub

## 🐳 Docker Development

```bash
# Start development environment
docker-compose up -d

# Follow logs
docker-compose logs -f

# Stop environment
docker-compose down
```

## 🔧 Tool Configurations

### Frontend Configurations

- `eslint.config.js` - ESLint rules
- `prettier.config.js` - Prettier formatting
- `jest.config.js` - Jest testing
- `jest.setup.js` - Jest setup
- `.lintstagedrc.json` - Lint-staged

### Backend Configurations

- `pytest.ini` - Pytest testing
- `mypy.ini` - mypy type checking
- `pyproject.toml` - Black, isort (if used)

### Project Configurations

- `.pre-commit-config.yaml` - Pre-commit hooks
- `AI-Stock-Trader.code-workspace` - VS Code workspace

## 🔍 Debugging

### VS Code Debugging

- **Frontend**: "Debug Next.js Frontend" configuration
- **Backend**: "Debug Python Backend" configuration

### Browser Debugging

- Frontend dev server: [http://localhost:3000](http://localhost:3000)
- Devtools available

## 📝 Additional Information

- See project documentation in `Documentation/` folder
- GitHub Actions CI/CD pipeline in `.github/workflows/` folder
- Docker configurations in `docker-compose*.yml` files

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Follow code quality standards
4. Write tests
5. Ensure all tests pass
6. Create Pull Request

---

Development tools are configured to ensure high code quality and consistent development experience for all project developers.
