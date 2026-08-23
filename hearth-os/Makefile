.PHONY: test run

test:
	PYTHONPATH=. python3 -m pytest -q

run:
	PYTHONPATH=. python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8080
