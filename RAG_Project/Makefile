.PHONY: help install test run clean

VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip
PYTEST = $(VENV_NAME)/bin/pytest

help:
	@echo "RAG Project Makefile"
	@echo "--------------------"
	@echo "make install  - Create venv and install dependencies"
	@echo "make test     - Run unit tests"
	@echo "make run      - Run the retrieval CLI (generates samples in results/sample/)"
	@echo "make clean    - Remove venv and cache files"

install:
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	PYTHONPATH=. $(PYTEST) tests/ --cov=pubmed_interface --cov-report=term-missing

run:
	PYTHONPATH=. $(PYTHON) cli.py --prompt-file prompts.jsonl --output results/sample/ --max 30 --since 2024/01/01

clean:
	rm -rf $(VENV_NAME)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf logs/
