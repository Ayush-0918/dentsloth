# 🦥 DentSloth

> **Snap one photo of a used dental instrument. DentSloth identifies it, grades it, prices it fairly, writes the listing (English + Hindi), and while you sleep it finds a buyer.**

Built for the **DEV Hacktoberfest Open-Source AI Challenge – Week 3: Slow and Steady** (theme: open-weight AI that rewards laziness — it does the work so you don't have to).

---

## The Problem

New dental instruments are expensive; young dentists and new clinics struggle to afford a full setup. Clinics upgrade or close, and good instruments sit unused because reselling is a chore: photograph, identify, research price, write a description, find a buyer. **DentSloth automates all of that from a single photo.**

## Two Lazy Loops

### 1 · Seller Loop (lazy listing)
Photo → Gemma 3 4B vision identifies instrument(s) → TabPFN predicts fair price → Gemma writes bilingual listing → saved to MongoDB with embeddings → published.

### 2 · Buyer Loop (Starter Kit Builder)
New dentist types plain words: *"opening a general practice, budget ₹60k, need basic exam + scaling + extraction set"* → vector search retrieves best listings → greedy budget kit assembled → gaps added to wishlist.

**Overnight Sloth Run**: background matcher script () matches listings with wishlists on demand or schedule, leaving each user a 2-line summary.

---

## Open-Source AI (the core)

| Model | Role | Where it runs |
|---|---|---|
| **Gemma 3 4B** (open-weight) | Vision ID, bilingual listing, wishlist parsing | Local via Ollama · or Google AI Studio for hosted demo |
| **TabPFN** (open-weight tabular FM) | Resale price prediction with uncertainty range | Local in-process · `TABPFN_MODE=api` fallback |
| **nomic-embed-text** (open-weight) | Semantic embeddings for matching | Local via Ollama · sentence-transformers fallback |

`LLM_PROVIDER=ollama` → clinic photos **never leave the clinic's machine**.  
`LLM_PROVIDER=hosted` → Google AI Studio for the public demo.

---

## Architecture

```
frontend/       React · Vite · TypeScript · CSS design tokens
  src/pages/    SnapAndList, Marketplace, KitBuilder, Dashboard, Landing
  src/api/      Typed API client with VITE_API_URL env var
backend/        Python · FastAPI · Pydantic v2
  api/          identify, price, listings, wishlist, kit, dashboard
  llm/          OllamaProvider / HostedGemmaProvider (switchable)
  pricing/      TabPFN 2.2.1 with sanity rules (85% cap, ₹50 floor)
  db.py         MongoDB Atlas with seamless SQLite fallback
scripts/        eval_pricing, measure_lazy_payoff, sloth_run, seed
data/           Synthetic catalog + price history CSV + sample images
docs/           POST_FACTS, lazy_payoff, architecture, screenshots
```

### Data Flow

```
Photo → EXIF strip → Gemma vision → TabPFN pricing → Bilingual text → DB → Published
                                                                        ↓
Wishlist ←→ Embedding match (cosine) ← Nightly Sloth Run → Morning Summary
```

---

## Partner Technologies

- **Gemma** – open-weight vision + language backbone
- **TabPFN** – tabular price prediction (Prior Labs)
- **MongoDB Atlas** + Atlas Vector Search – listings, wishlists, semantic matching
- **Render** – API + static frontend (Sloth Run executed on-demand via )
- **.tech domain** – `dentsloth.tech`

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- Node 20+
- [Ollama](https://ollama.ai) running locally
- MongoDB Atlas cluster (free tier works) — or local `mongod`

```bash
# 1. Clone and configure
git clone https://github.com/<your-handle>/dentsloth.git
cd dentsloth
cp .env.example .env
# Edit .env: set MONGODB_URI, OLLAMA_BASE_URL, etc.

# 2. Pull models
ollama pull gemma3:4b
ollama pull nomic-embed-text

# 3. Set up Python virtualenv
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# 4. Generate synthetic data
python scripts/generate_seed_prices.py

# 5. Start backend (terminal 1)
uvicorn backend.main:app --reload --port 8000

# 6. Start frontend (terminal 2)
cd frontend && npm install && npm run dev

# 7. Open http://localhost:5173
```

---

## Environment Variables

See [`.env.example`](.env.example) for all variables. Key ones:

| Variable | Default | Description |
|---|---|---|
| `DEMO_MODE` | `true` | Use pre-recorded model outputs (safe for demos) |
| `LLM_PROVIDER` | `ollama` | `ollama` (local) or `hosted` (AI Studio) |
| `MONGODB_URI` | localhost | Atlas connection string |
| `TABPFN_MODE` | `local` | `local` or `api` (use `api` on Render) |
| `TABPFN_API_KEY` | — | Prior Labs API key (only if `TABPFN_MODE=api`) |
| `GEMMA_API_KEY` | — | Google AI Studio key (only if `LLM_PROVIDER=hosted`) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `VITE_API_URL` | `/api` | Frontend env var for API base URL (production: full URL) |
| `VITE_DEMO_MODE` | — | Frontend env var to pre-set demo mode |

---

## Deployment (Render)

A [`render.yaml`](render.yaml) blueprint is included:

1. **dentsloth-api** — FastAPI web service (`LLM_PROVIDER=hosted`, `TABPFN_MODE=api`)
2. **dentsloth-web** — Static frontend (Vite build, `VITE_API_URL` set to API domain)
*(Note: Render free tier does not include cron jobs. Sloth Run is executed manually or via external schedule via )*

Set secrets (`GEMMA_API_KEY`, `MONGODB_URI`, `TABPFN_API_KEY`) in the Render dashboard — they are never committed.

> **TabPFN on Render:** The free tier has 512 MB RAM. TabPFN + PyTorch may exceed this. Use `TABPFN_MODE=api` for production and document the `TABPFN_API_KEY` env var in Render.

---

## Data (Synthetic)

> ⚠️ **All data in this repository is SYNTHETIC and ILLUSTRATIVE.**

- `data/instrument_catalog.json` — ~40 common dental instruments with **illustrative** price ranges.
- `data/price_history.csv` — ~600 synthetic sale records generated by `scripts/generate_seed_prices.py`. **Not real sales data.**
- Demo listings use **fictional clinic names** and **fictional prices**.
- The TabPFN MAE/MAPE figures in `docs/POST_FACTS.md` are benchmarked on this synthetic data.
- The manual workflow time is a placeholder (`MANUAL_TIME_TO_BE_MEASURED_BY_USER`).

Never display these numbers as real market statistics.

---


### MongoDB Atlas & Vector Search
- **Data Collections:** `listings`, `wishlists`, `kits`, `events`.
- **Health Verification:** `GET /health` returns `storage_backend: "atlas"` in production and `"sqlite"` in local/offline fallback.
- **Vector Search:** Automatic `$vectorSearch` with fallback to in-memory cosine similarity if index is building.
- **Index Definition:** `scripts/atlas_index.json` (64 dimensions, cosine similarity).
- **Index Automation:** Run `python scripts/create_vector_index.py` or use Atlas UI.
- **Demo Seed:** Run `python scripts/seed_demo_listings.py` to seed 10 synthetic listings with vector embeddings.

## Why Open?

- **Privacy**: Local Gemma means clinic photos never leave the clinic's machine.
- **Offline**: Works on a laptop without internet in `LLM_PROVIDER=ollama` mode.
- **Cost**: No per-call API cost; models run on local hardware.
- **Swappable**: Same prompts work on local Ollama and hosted AI Studio — just change one env var.
- **Refittable**: TabPFN can be retrained on a clinic's own sales history without sending data anywhere.

---

## Safety & Disclaimers

- **No patient data.** Instruments only. Upload photos of instruments on a plain background. EXIF/GPS stripped on upload.
- **Prohibited items**: Single-use disposables, implants, needles/sharps, and anything that cannot be reprocessed are refused.
- **Reprocessing note**: Buyers must clean and sterilize instruments per their local regulations. DentSloth is a classifieds tool and does not certify instruments.
- **No medical or regulatory claims.**

---

## Honest Limitations

- Gemma can misidentify instruments, especially unusual or obscure ones.
- Prices are suggestions based on synthetic training data; treat as a starting point for negotiation.
- Atlas Vector Search match quality depends on embedding coverage of the catalog.
- In `DEMO_MODE=true`, model outputs are pre-recorded — not live inference.
- TabPFN is trained on synthetic data; real accuracy depends on real sales records.
- TabPFN weights are distributed under a non-commercial research license from Prior Labs.

---

## Technical Benchmarks

See [`docs/POST_FACTS.md`](docs/POST_FACTS.md) for verified numbers:
- **Pipeline speed**: 4.83 s median per listing (real Gemma inference, `DEMO_MODE=false`)
- **TabPFN MAE**: ₹58.3 on synthetic holdout (75.2% reduction vs mean-by-type baseline)
- Full disclosure of synthetic data, demo elements, and limitations

---

*DentSloth is a hackathon project. Not a certified medical device marketplace. Use responsibly.*
