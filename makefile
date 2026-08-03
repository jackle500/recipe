PY = .venv/bin/python
UVICORN = .venv/bin/uvicorn

run:
	$(UVICORN) app:app --reload

test:
	$(PY) -m pytest tests/ -v

seed:
	$(PY) scripts/load_seed.py

staples:
	$(PY) scripts/mark_staples.py
