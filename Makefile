# Shortcuts for working on Daily Drill. Every line is one `uv run drill ...` command, so it behaves the
# same from PowerShell, Windows Terminal, a Mac or Linux. No make? Type the command after the tab.

.PHONY: help check test page map preview server setup deploy

help:    ## list these shortcuts
	@uv run python -c "import re; [print(f'  make {t:<8} {h}') for t, h in re.findall(r'^([a-z]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

check:   ## build the page and run the fast tests: before every commit
	uv run drill dev check

test:    ## every test, the slow notebook ones too
	uv run drill dev check --all

page:    ## build the page only, into dist/
	uv run drill build-page

map:     ## write docs/tutor/CURRICULUM_MAP.md for the tutor project
	uv run drill tutor map

preview: export DRILL_PORT = 8788
preview: export DRILL_DATABASE_URL = sqlite:///.drill/preview.db
preview: ## the page at http://localhost:8788, with a throwaway database (restart after `make page`)
	uv run drill-server

server:  ## the page at http://localhost:8787, with your own progress
	uv run drill-server

setup:   ## put Daily Drill in the work workspace: asks, shows the plan, asks again before changing anything
	uv run drill cloud port --ask --target work

deploy:  ## upload and start the work app (costs money while it runs)
	uv run drill cloud deploy --target work
