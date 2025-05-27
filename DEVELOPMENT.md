# AI Stock Trader - Kehitystyökalut

Tämä dokumentti kuvaa projektissa käytettävät kehitystyökalut ja niiden asetukset.

## 🛠️ Kehitysympäristön setup

### 1. Perusasennus

```bash
# Kloonaa repositorio
git clone <repository-url>
cd AI-Stock-Trader

# Asenna frontend riippuvuudet
cd management-system/frontend
npm install

# Asenna backend riippuvuudet (virtuaaliympäristössä)
cd ../backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# tai .venv\Scripts\activate  # Windows
pip install -r requirements.txt -r requirements-dev.txt

# Asenna pre-commit hooks
cd ../..
pre-commit install
```

### 2. VS Code setup

Avaa `AI-Stock-Trader.code-workspace` VS Codessa optimaalista kehityskokemusta varten.

Suositellut extensiot asentuvat automaattisesti:

- Python
- ESLint
- Prettier
- Tailwind CSS
- Docker
- GitHub Copilot

## 🧪 Testaus

### Frontend testit (Jest + Testing Library)

```bash
cd management-system/frontend

# Aja testit
npm test

# Aja testit watch-moodissa
npm run test:watch

# Aja testit coverage-reportilla
npm run test:coverage
```

### Backend testit (pytest)

```bash
cd management-system/backend

# Aja testit
pytest

# Aja testit coverage-reportilla
pytest --cov=. --cov-report=html

# Aja vain tietyn tiedoston testit
pytest tests/test_api.py

# Aja testit markereiden mukaan
pytest -m unit
pytest -m integration
```

## 🔍 Koodin laadunvarmistus

### Frontend

```bash
cd management-system/frontend

# ESLint tarkistus
npm run lint

# ESLint korjaus
npm run lint:fix

# Prettier formatointi
npm run format

# Prettier tarkistus
npm run format:check

# TypeScript tyyppitarkistus
npm run type-check
```

### Backend

```bash
cd management-system/backend

# Black formatointi
black .

# Flake8 tarkistus
flake8 .

# isort import järjestys
isort .

# mypy tyyppitarkistus
mypy .

# Bandit security tarkistus
bandit -r .
```

## 🔧 Pre-commit hooks

Pre-commit hooks ajetaan automaattisesti ennen jokaista committia:

- **Frontend**: ESLint, Prettier, TypeScript tarkistus
- **Backend**: Black, Flake8, isort, Bandit, mypy
- **Docker**: Hadolint
- **Yleinen**: detect-secrets, trailing whitespace, file size

Manuaalinen ajo:

```bash
# Aja kaikki hooks
pre-commit run --all-files

# Aja tietty hook
pre-commit run black --all-files
```

## 📊 Coverage raportit

### Frontend

Coverage raportti generoituu `coverage/` kansioon kun ajat `npm run test:coverage`.

### Backend

Coverage raportti generoituu `htmlcov/` kansioon kun ajat pytest coverage-optioilla.

## 🎯 Coverage tavoitteet

- **Frontend**: 80% branch, function, line, statement coverage
- **Backend**: 80% overall coverage
- **Uudet tiedostot**: 90% coverage vaatimus

## 🚀 Development workflow

1. **Luo uusi branch**: `git checkout -b feature/uusi-ominaisuus`
2. **Kehitä**: Kirjoita koodi ja testit
3. **Testaa**: `npm test` ja `pytest`
4. **Tarkista laatu**: Pre-commit hooks ajetaan automaattisesti
5. **Commit**: `git commit -m "feat: lisää uusi ominaisuus"`
6. **Push**: `git push origin feature/uusi-ominaisuus`
7. **Pull Request**: Luo PR GitHubissa

## 🐳 Docker kehitys

```bash
# Käynnistä kehitysympäristö
docker-compose up -d

# Seuraa lokeja
docker-compose logs -f

# Pysäytä ympäristö
docker-compose down
```

## 🔧 Työkalujen konfiguraatiot

### Frontend konfiguraatiot

- `eslint.config.js` - ESLint säännöt
- `prettier.config.js` - Prettier formatointi
- `jest.config.js` - Jest testaus
- `jest.setup.js` - Jest setup
- `.lintstagedrc.json` - Lint-staged

### Backend konfiguraatiot

- `pytest.ini` - Pytest testaus
- `mypy.ini` - mypy tyyppitarkistus
- `pyproject.toml` - Black, isort (jos käytössä)

### Projekti konfiguraatiot

- `.pre-commit-config.yaml` - Pre-commit hooks
- `AI-Stock-Trader.code-workspace` - VS Code workspace

## 🔍 Debuggaus

### VS Code debugging

- **Frontend**: "Debug Next.js Frontend" konfiguraatio
- **Backend**: "Debug Python Backend" konfiguraatio

### Browser debugging

- Frontend dev server: http://localhost:3000
- Devtools käytettävissä

## 📝 Lisätietoja

- Katso projektin dokumentaatio `Documentation/` kansiosta
- GitHub Actions CI/CD pipeline `.github/workflows/` kansiossa
- Docker konfiguraatiot `docker-compose*.yml` tiedostoissa

## 🤝 Kontribuointi

1. Fork repositorio
2. Luo feature branch
3. Noudata koodin laatustandardeja
4. Kirjoita testit
5. Varmista että kaikki testit menevät läpi
6. Luo Pull Request

---

Kehitystyökalut on konfiguroitu takaamaan korkea koodin laatu ja yhtenäinen kehityskokemus kaikille projektin kehittäjille.
