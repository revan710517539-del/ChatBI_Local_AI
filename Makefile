# Variables
COMMAND := up -d
PROJECT := chatbi
PORT    := 8000
UV      := $(shell if command -v uv >/dev/null 2>&1; then echo uv; else echo $$HOME/.local/bin/uv; fi)
PNPM    := $(shell if command -v pnpm >/dev/null 2>&1; then echo pnpm; elif command -v corepack >/dev/null 2>&1; then echo "corepack pnpm"; else echo pnpm; fi)

ifeq ($(filter up,$(MAKECMDGOALS)),up)
COMMAND := up -d
endif
ifeq ($(filter down,$(MAKECMDGOALS)),down)
COMMAND := down
endif

.PHONY: docker up down dev-client default install pre-commit-install run dev cli example test lint format fmt

docker:
	@set -euxo pipefail; \
	cmd="$(COMMAND)"; \
	if [ "$$cmd" = "up" ]; then \
		cmd="up -d"; \
	fi; \
	pushd ./docker > /dev/null && \
	export COMPOSE_PROJECT_NAME=$(PROJECT) && docker compose $$cmd && \
	popd > /dev/null; \
	if [ "$$cmd" = "down" ]; then \
		rm -rf ./docker/database; \
	fi

up:
	@:

down:
	@:

dev-client:
	@echo "Running dev client"
	@$(PNPM) run -C web dev

dev-server:
	@echo "Running dev server"
	$(UV) run fastapi dev chatbi/main.py --port $(PORT)


# update the api spec for the client
gen-api:
	@echo "Updating API spec"
	$(PNPM) run -C web api:init

default:
	@echo "Available targets: docker, dev-client, install, pre-commit-install, run, dev, cli, example, test, lint, format (fmt)"

# To pass extra arguments, call with: make install ARGS="arg1 arg2 ..."
install:
	$(UV) sync $(ARGS)

pre-commit-install:
	$(UV) run pre-commit install

run:
	$(UV) run fastapi run chatbi/main.py --port $(PORT)


# To pass extra arguments, call with: make cli ARGS="your args"
cli:
	$(UV) run python -m chatbi.cli $(ARGS)

# To pass extra arguments, call with: make example ARGS="your args"
example:
	$(UV) run python -m chatbi.cli example $(ARGS)

test:
	$(UV) run pytest -s

lint:
	$(UV) run ruff format -q . --check
	$(UV) run ruff check .

format: fmt

fmt:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .
	taplo fmt
