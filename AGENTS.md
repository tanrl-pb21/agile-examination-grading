# Repository Guidelines

## Project Structure & Module Organization
- Backend lives in `backend/`; FastAPI app entrypoint is `backend/src/main.py` with routers in `backend/src/routers/` and shared logic under `backend/src/services/`.
- HTML templates and static assets sit in `backend/templates/` and `backend/static/` for Jinja2 rendering and static file mounting.
- Database helpers are in `backend/src/db.py` (loads `SUPABASE_DB_URL` from `.env`), so set that before running the app.
- Tests are grouped by scope in `backend/tests/` (`unit/`, `acceptance/`, `feature/` for pytest-bdd Gherkin scenarios).

## Build, Test, and Development Commands
- Create env and install (from `backend/`): `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`.
- Run the API locally with reload: `uvicorn src.main:app --reload --port 8000`. Ensure `SUPABASE_DB_URL` is exported.
- Format and lint: `ruff check src tests` and `black src tests`.
- Type check: `mypy src`.
- Test suites: `pytest` for all, `pytest tests/unit -q` for fast unit runs, `pytest --cov=src` if you need coverage locally.

## Coding Style & Naming Conventions
- Python 3.12 target; 4-space indents; keep line length at 88 (Black/Ruff config).
- Prefer double quotes; module, package, and file names use `snake_case`; routers/services follow verb_noun naming (`exams.py`, `grading.py`).
- Let Black handle formatting and Ruff enforce import sorting/errors; avoid manual stylistic deviations.

## Testing Guidelines
- Use pytest fixtures in `backend/tests/conftest.py`; keep new tests near the feature layer they cover (unit vs acceptance).
- Name tests `test_<unit_under_test>.py` and functions `test_<behavior>()`.
- For behavior specs, add/extend `.feature` files in `backend/tests/feature/` and pair them with step definitions/tests as needed.

## Commit & Pull Request Guidelines
- Follow existing Git history prefixes (`fix:`, `test:`, `style:`, `merge:`). Use imperative, concise subject lines (~50 chars ideal).
- Keep PRs focused; include a short summary, test evidence (commands run), and reference related issues/tickets.
- Add screenshots or response samples when changing templates/endpoints; call out any config/env changes explicitly.
