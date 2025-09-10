.PHONY: help dev-start dev-stop dev-ready dev-demo dev-clear logs test smoke sync-import sync-push conflicts db-backup oauth prod front-dev front-build docker-up docker-down docker-logs docker-start docker-rebuild-backend docker-rebuild-frontend e2e e2e-headed

-include .env

HOST ?= 127.0.0.1
PORT ?= 8776
BASE ?= http://$(HOST):$(PORT)
API_KEY ?= dev-key
FAKE ?= 0
DB_PATH ?= backend/data/dev-pelubot-sync.db
GOOGLE_OAUTH_JSON ?= oauth_tokens.json
# Auto-detect Docker Compose (v2 plugin preferred, fallback to v1)
# You can still override: make DOCKER=docker-compose docker-up
DOCKER ?= $(shell if docker compose version >/dev/null 2>&1; then echo 'docker compose'; \
                   elif command -v docker-compose >/dev/null 2>&1; then echo 'docker-compose'; \
                   else echo 'docker compose'; fi)

help:
	@echo "Targets:"
	@echo "  make dev-start   # start uvicorn on $(BASE)"
	@echo "  make dev-stop    # stop uvicorn"
	@echo "  make dev-ready   # wait /ready"
	@echo "  make dev-clear   # clear calendars via admin API"
	@echo "  make dev-demo    # clear calendars and create demo reservation"
	@echo "  make test        # run backend tests"
	@echo "  make logs        # tail backend/server2.log"
	@echo "  make smoke       # end-to-end flow: create->reschedule->cancel->sync"
	@echo "  make sync-import # import GCAL -> DB (vars: START, END, DAYS)"
	@echo "  make sync-push   # push DB -> GCAL (vars: START, END, DAYS)"
	@echo "  make conflicts   # detect conflicts (vars: START, END, DAYS)"
	@echo "  make db-backup   # copy dev DB with timestamp"
	@echo "  make oauth       # run OAuth flow to capture token"
	@echo "  make prod        # run uvicorn with 2 workers on $(BASE)"
	@echo "  make front-dev   # run Vite dev server"
	@echo "  make front-build # build frontend"
	@echo "  make docker-up   # build & run backend+frontend with Docker"
	@echo "  make docker-down # stop and remove containers/volumes"
	@echo "  make docker-logs # tail docker compose logs"
	@echo "  make docker-start # up without --build"
	@echo "  make docker-rebuild-backend  # rebuild only backend"
	@echo "  make docker-rebuild-frontend # rebuild only frontend"
	@echo "  make e2e         # run Playwright tests (headless)"
	@echo "  make e2e-headed  # run Playwright headed (debug)"

dev-start:
	cd backend && \
	( [ -f uvicorn2.pid ] && kill $$(cat uvicorn2.pid) 2>/dev/null || true ) && \
	( command -v fuser >/dev/null && fuser -k $(PORT)/tcp >/dev/null 2>&1 || true ) && \
	API_KEY=$(API_KEY) AUTO_SYNC_FROM_GCAL=false PELUBOT_FAKE_GCAL=$(FAKE) GOOGLE_OAUTH_JSON=$(GOOGLE_OAUTH_JSON) DATABASE_URL=sqlite:///$$PWD/$(notdir $(DB_PATH)) \
		nohup uvicorn app.main:app --host $(HOST) --port $(PORT) --log-level warning > server2.log 2>&1 & echo $$! > uvicorn2.pid

dev-stop:
	cd backend && \
	( [ -f uvicorn2.pid ] && kill $$(cat uvicorn2.pid) 2>/dev/null || true ) && \
	( command -v fuser >/dev/null && fuser -k $(PORT)/tcp >/dev/null 2>&1 || true )

dev-ready:
	@for i in $$(seq 1 50); do \
		out=$$(curl -s $(BASE)/ready || true); \
		echo $$out | grep -E -q '"ok":\s*(true|false)' && { echo $$out; exit 0; }; \
		sleep 0.2; \
	done; \
	echo "timeout waiting for $(BASE)/ready"; tail -n 50 backend/server2.log; exit 1

dev-clear: dev-ready
	@echo "Clearing calendars via admin API..."
	BASE=$(BASE) API_KEY=$(API_KEY) python backend/scripts/dev_demo.py --clear-only

dev-demo: dev-start dev-ready
	@echo "Running demo: clear calendars + create reservation + check conflicts"
	sleep 0.3
	BASE=$(BASE) API_KEY=$(API_KEY) CLEAR_ALL=true python backend/scripts/dev_demo.py
	@echo "Done."

test:
	cd backend && PYTEST_ADDOPTS=-q PELUBOT_FAKE_GCAL=1 pytest

logs:
	tail -n 100 -f backend/server2.log

smoke: dev-start dev-ready
	@echo "Running smoke flow (create -> reschedule -> cancel -> sync)..."
	BASE=$(BASE) API_KEY=$(API_KEY) python backend/scripts/smoke_flow.py

sync-import:
		@echo "Sync import $(or $(START),today) .. $(or $(END),+$(or $(DAYS),7)d)"
		BASE=$(BASE) API_KEY=$(API_KEY) python - << 'PY'
	import os,json
	from urllib import request
	BASE=os.environ['BASE']; API_KEY=os.environ['API_KEY']
	START=os.environ.get('START'); END=os.environ.get('END'); DAYS=os.environ.get('DAYS')
	body={'mode':'import'}
	if START: body['start']=START
	if END: body['end']=END
	if DAYS: body['days']=int(DAYS)
	req=request.Request(BASE+'/admin/sync', data=json.dumps(body).encode(), method='POST')
	req.add_header('Content-Type','application/json'); req.add_header('X-API-Key',API_KEY)
	with request.urlopen(req) as r:
	    print(r.read().decode())
	PY

sync-push:
		@echo "Sync push $(or $(START),today) .. $(or $(END),+$(or $(DAYS),7)d)"
		BASE=$(BASE) API_KEY=$(API_KEY) python - << 'PY'
	import os,json
	from urllib import request
	BASE=os.environ['BASE']; API_KEY=os.environ['API_KEY']
	START=os.environ.get('START'); END=os.environ.get('END'); DAYS=os.environ.get('DAYS')
	body={'mode':'push'}
	if START: body['start']=START
	if END: body['end']=END
	if DAYS: body['days']=int(DAYS)
	req=request.Request(BASE+'/admin/sync', data=json.dumps(body).encode(), method='POST')
	req.add_header('Content-Type','application/json'); req.add_header('X-API-Key',API_KEY)
	with request.urlopen(req) as r:
	    print(r.read().decode())
	PY

conflicts:
		@echo "Conflicts for range"
		BASE=$(BASE) API_KEY=$(API_KEY) python - << 'PY'
	import os,json
	from urllib import request
	BASE=os.environ['BASE']; API_KEY=os.environ['API_KEY']
	START=os.environ.get('START'); END=os.environ.get('END'); DAYS=os.environ.get('DAYS')
	body={}
	if START: body['start']=START
	if END: body['end']=END
	if DAYS: body['days']=int(DAYS)
	req=request.Request(BASE+'/admin/conflicts', data=json.dumps(body).encode(), method='POST')
	req.add_header('Content-Type','application/json'); req.add_header('X-API-Key',API_KEY)
	with request.urlopen(req) as r:
	    print(r.read().decode())
	PY

db-backup:
	@ts=$$(date +%Y%m%d-%H%M%S); cp backend/data/dev-pelubot-sync.db backend/data/dev-pelubot-sync.$${ts}.db; echo "Backup created: backend/data/dev-pelubot-sync.$${ts}.db"

oauth:
	cd backend && python scripts/oauth.py

prod: dev-stop
	cd backend && \
	API_KEY=$(API_KEY) AUTO_SYNC_FROM_GCAL=false PELUBOT_FAKE_GCAL=$(FAKE) GOOGLE_OAUTH_JSON=$(GOOGLE_OAUTH_JSON) DATABASE_URL=sqlite:///$$PWD/$(notdir $(DB_PATH)) \
		nohup uvicorn app.main:app --host $(HOST) --port $(PORT) --workers 2 --log-level info > server2.log 2>&1 & echo $$! > uvicorn2.pid
	@$(MAKE) dev-ready PORT=$(PORT)

front-dev:
	cd Frontend/shadcn-ui && pnpm i && pnpm dev

front-build:
	cd Frontend/shadcn-ui && pnpm i && pnpm build

docker-up:
	$(DOCKER) up --build -d
	@echo "Backend: http://localhost:$${BACKEND_PORT:-8776} | Frontend: http://localhost:$${FRONTEND_PORT:-8080}"

docker-down:
	$(DOCKER) down -v

docker-logs:
	$(DOCKER) logs -f --tail=200

docker-start:
	$(DOCKER) up -d
	@echo "Backend: http://localhost:$${BACKEND_PORT:-8776} | Frontend: http://localhost:$${FRONTEND_PORT:-8080}"

docker-rebuild-backend:
	$(DOCKER) up -d --no-deps --build backend

docker-rebuild-frontend:
	$(DOCKER) up -d --no-deps --build frontend

e2e:
	# Ensure app is up before running E2E (prefer start to avoid recreate on compose v1)
	-$(DOCKER) start backend frontend >/dev/null 2>&1 || $(DOCKER) up -d backend frontend
	$(DOCKER) run --rm e2e

e2e-headed:
 	# Run headed (opens browser in container with xvfb) and keeps artifacts
	-$(DOCKER) start backend frontend >/dev/null 2>&1 || $(DOCKER) up -d backend frontend
	$(DOCKER) run --rm -e PWDEBUG=console e2e npx playwright test --headed
