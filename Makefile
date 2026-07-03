REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV := $(REPO_ROOT)/.venv
DEV_STAMP := $(VENV)/.baseline-tools-installed
PREVIEW_DIR := $(REPO_ROOT)/.graphfakos-preview
PYTHON := $(VENV)/bin/python3.11
PIP := $(PYTHON) -m pip
PRE_COMMIT := $(PYTHON) -m pre_commit
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff

.PHONY: help venv dev-install hooks-install hooks-run preview preview-demo preview-dense preview-timeline preview-warnings preview-path preview-provenance preview-workbench preview-budget preview-islands preview-html clean-preview fix format format-check lint test browser-test check release-check

help:
	@printf '%s\n' \
		'Targets:' \
		'  make dev-install   Create/update .venv and install graphfakos with dev extras' \
		'  make hooks-install Install pre-commit and commit-msg hooks into .git/hooks' \
		'  make hooks-run     Run pre-commit across the graphfakos repo' \
		'  make preview       Serve the dynamic viewer locally and open a browser' \
		'  make preview-demo  Serve generated agent-memory demo data' \
		'  make preview-dense Serve generated dense graph demo data' \
		'  make preview-timeline Serve generated timeline demo data' \
		'  make preview-warnings Serve generated warning-state demo data' \
		'  make preview-path  Serve generated pathfinding demo data' \
		'  make preview-provenance Serve generated evidence/provenance demo data' \
		'  make preview-workbench Serve mixed code/knowledge workbench demo data' \
		'  make preview-budget Serve generated render-budget stress data' \
		'  make preview-islands Serve generated disconnected-islands data' \
		'  make preview-html  Write/open a repo-local static export under .graphfakos-preview/' \
		'  make clean-preview Remove repo-local generated preview files' \
		'  make fix           Apply Ruff formatting and autofixes' \
		'  make format        Run Ruff formatter' \
		'  make format-check  Check formatting without changing files' \
		'  make lint          Run Ruff lint' \
		'  make test          Run package pytest suite' \
		'  make browser-test  Run browser runtime pytest coverage' \
		'  make check         Run format-check, lint, and test' \
		'  make release-check Run package release smoke'

venv:
	@test -x "$(PYTHON)" || python3.11 -m venv "$(VENV)"

$(DEV_STAMP): pyproject.toml | venv
	$(PIP) install --upgrade pip setuptools wheel
	cd "$(REPO_ROOT)" && $(PIP) install -e ".[dev]"
	@touch "$(DEV_STAMP)"

dev-install: $(DEV_STAMP)

hooks-install: $(DEV_STAMP)
	$(PRE_COMMIT) install --install-hooks --hook-type pre-commit --hook-type commit-msg

hooks-run: $(DEV_STAMP)
	$(PRE_COMMIT) run --all-files

preview: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --screen explore --serve --open

preview-demo: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario agent-memory --screen explore --serve --open

preview-dense: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario dense --screen explore --layout grouped --render-limit 240 --serve --open

preview-timeline: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario timeline --screen timeline --layout timeline --render-limit 240 --serve --open

preview-warnings: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario warnings --screen provider_status --serve --open

preview-path: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario pathfinding --screen path --source-node-id provider:entry --target-node-id artifact:result --serve --open

preview-provenance: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario provenance --screen provenance --serve --open

preview-workbench: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario workbench-mixed --screen explore --focus-node-id agent:reviewer --style-color-by source --style-size-by degree --style-edge-width-by confidence --serve --open

preview-budget: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario budget --screen explore --render-limit 24 --serve --open

preview-islands: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui --demo-scenario islands --screen provider_status --serve --open

preview-html: $(DEV_STAMP)
	mkdir -p "$(PREVIEW_DIR)"
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTHON) -m graphfakos ui \
		--screen explore \
		--html-out "$(PREVIEW_DIR)/graphfakos-viewer.html" \
		--embed-out "$(PREVIEW_DIR)/graphfakos-viewer-embed.html" \
		--json \
		--open

clean-preview:
	rm -rf "$(PREVIEW_DIR)"

fix: $(DEV_STAMP)
	$(RUFF) format "$(REPO_ROOT)"
	$(RUFF) check --fix "$(REPO_ROOT)"

format: $(DEV_STAMP)
	$(RUFF) format "$(REPO_ROOT)"

format-check: $(DEV_STAMP)
	$(RUFF) format --check "$(REPO_ROOT)"

lint: $(DEV_STAMP)
	$(RUFF) check "$(REPO_ROOT)"

test: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTEST) -q "$(REPO_ROOT)/tests"

browser-test: $(DEV_STAMP)
	PYTHONPATH="$(REPO_ROOT)/src" $(PYTEST) -q "$(REPO_ROOT)/tests/test_browser_runtime.py"

check: format-check lint test

release-check: $(DEV_STAMP)
	cd "$(REPO_ROOT)" && $(PYTHON) scripts/release_check.py
