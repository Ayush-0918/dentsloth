.PHONY: install seed backend frontend dev

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

seed: ## Generate synthetic data and seed demo listings
	python scripts/generate_seed_prices.py
	python scripts/seed_demo_listings.py

backend: ## Start FastAPI dev server
	uvicorn backend.main:app --reload --port 8000

frontend: ## Start Vite dev server
	cd frontend && npm run dev

dev: ## Start both (requires two terminals or use tmux)
	$(MAKE) backend &
	$(MAKE) frontend

test:
	pytest backend/tests/ -v
