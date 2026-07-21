.PHONY: install dev test lint demo docker

install:
	python -m pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check app tests scripts

demo:
	python scripts/create_demo_book.py

docker:
	docker compose up --build
