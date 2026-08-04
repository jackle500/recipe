PY = .venv/bin/python
UVICORN = .venv/bin/uvicorn

run:
	$(UVICORN) app:app --reload

test:
	$(PY) -m pytest tests/ -v

seeds:
	$(PY) scripts/load_seed.py

staples:
	$(PY) scripts/mark_staples.py

format:
	.venv/bin/ruff format .
	npx prettier --write .

lint:
	.venv/bin/ruff check . --fix
	npx prettier --check .
