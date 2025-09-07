# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI backend
  - `main.py` (API, static mount), `models.py` (SQLAlchemy), `config.py` (env), `services/` (clock, parser, background), `telegram_api/` (Telethon client), `utils/` (DB, logging).
- `web/`: Static frontend (`index.html`, `script.js`, `styles.css`).
- `tests/`: Pytest suite (`tests/unit/...`, fixtures in `tests/conftest.py`).
- `run.py`: Entrypoint. `Makefile`: common tasks. `docker-compose.yml`/`Dockerfile`: container setup. `data/`, `logs/`: runtime artifacts.

## Build, Test, and Development Commands
- `make init-dev`: Create venv with uv and install `[dev]` deps.
- `make run`: Start API locally (serves static at `/static`).
- `make tests`: Run pytest with coverage (HTML in `htmlcov/`).
- `make test tests/unit/services/test_clock_service.py::test_fetch_and_store_updates_success`: Run a specific test.
- `make format` / `make lint` / `make mypy` / `make check`: Format, lint, type-check; use before PRs.
- Docker workflow: `make docker-up` / `docker-logs` / `docker-restart` / `docker-down` / `docker-reup`.

## Coding Style & Naming Conventions
- Python 3.11, 4-space indent, line length 120, double quotes (ruff config). Import ordering via ruff/isort (`app` is first-party).
- Names: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE` for constants.
- Frontend uses ESLint/Prettier: `npm run check`, `npm run lint:fix` on `web/`.

## Testing Guidelines
- Framework: pytest (+ asyncio, xdist). Tests live under `tests/`, named `test_*.py` with classes `Test*` and functions `test_*`.
- Coverage: fail under 85% (configured in `pyproject.toml`). Generate reports with `make tests`.
- Use fixtures (`tests/conftest.py`) for in-memory SQLite and FastAPI `TestClient`. Markers available: `unit`, `integration`, `slow`, `smoke`.

## Commit & Pull Request Guidelines
- Commit style: Conventional Commits (e.g., `feat: ...`, `fix: ...`). Keep commits scoped and descriptive.
- PRs: clear description, link issues, include screenshots for UI changes, note API changes, and list test coverage. Run `make check` and ensure new/changed code is tested.

## Security & Configuration Tips
- Create `.env` from `.env.example`; do not commit secrets. Required: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`.
- Default DB is SQLite at `./clock_data.db`. Logs in `./logs/`. CORS is open for dev; review before production.
- Background fetching isn’t auto-started; use `POST /api/clock/fetch` for manual updates.


## Working Agreement
- Change one axis at a time: either code or tests — never both in the same step.
- Tests mirror modules: one module → one test file (or a module-named folder) to keep navigation simple.
- Prefer function-style tests; avoid classes unless strictly needed for class-scope fixtures/marks.
- Use `pytest-mock` for mocking; avoid `unittest.mock` directly in tests.
- Follow AAA (Arrange–Act–Assert) with descriptive test names.
- Parametrize to remove duplication and improve clarity.
- Use English for identifiers, docstrings, and comments; keep Russian only where domain data requires it (e.g., parser inputs).
- Run `make check` (format, lint, mypy, JS checks) before PRs; keep changes minimal and focused.
- Do not alter unrelated code to satisfy tests; document behavioral changes and update tests in a dedicated, subsequent step.
- Discuss and plan any refactor that intentionally breaks tests before implementation.
