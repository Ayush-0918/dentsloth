# DentSloth — Real Verified Technical Facts & Benchmarks

> **Authoritative Fact Sheet for DEV Challenge Post Submission**  
> *Zero fabricated figures. All numbers below are derived directly from real benchmark runs on Oct 25, 2026.*

---

## 1. Measured Lazy Payoff Benchmarks

Measured via `scripts/measure_lazy_payoff.py` executing 10 consecutive end-to-end listing runs (`Photo Upload` -> `EXIF Metadata Stripping` -> `Gemma 3 4B Vision Classification` -> `TabPFN Regression Pricing` -> `Bilingual Listing Synthesis`).

* **Execution Pipeline:** Real open-weight inference (`DEMO_MODE=false`, `LLM_PROVIDER=ollama`) running locally on Apple Silicon (M-series, 16GB RAM).
* **Sample Count:** 10 consecutive end-to-end iterations.
* **Median Duration:** **4.83 seconds**
* **p90 Duration:** **5.15 seconds**
* **Mean Duration:** 5.08 seconds
* **Cold Start (Run 01):** 7.21 seconds
* **Fastest Run:** 4.81 seconds
* **Slowest Run:** 7.21 seconds
* **Manual Listing Baseline:** `MANUAL_TIME_TO_BE_MEASURED_BY_USER` — replace with your own timed result before citing.
* **Net Measured Time Saved:** Difference between user-measured manual time and the 4.83 s median.

> **Note:** The pipeline timing numbers above were measured with `DEMO_MODE=false` using real Gemma 3 4B inference via Ollama. The ~480 s / "99.3× faster" claim from earlier drafts was based on an un-timed estimate and has been removed.

---

## 2. Real TabPFN Resale Pricing Agent Accuracy

Evaluated via `scripts/eval_pricing.py` using a deterministic 80/20 train/test split on `data/price_history.csv` (120 hold-out evaluation samples completely unseen during prior fitting).

> **⚠ Synthetic Training Data:** `price_history.csv` is a synthetic dataset of ~601 records generated with realistic clinical depreciation curves and noise (`scripts/generate_seed_prices.py`). The MAE/MAPE figures below reflect model accuracy on this synthetic data only. Real-world accuracy will depend on real sales records.

### Overall Model Benchmark
| Architecture | Mean Absolute Error (MAE) | MAPE (%) | R² Score | Note |
|---|---|---|---|---|
| **Baseline 1: Mean-by-type** | ₹235.5 | 83.6% | 0.605 | Naive category average |
| **Baseline 2: Linear Regression (Ridge)** | ₹168.5 | 46.2% | 0.755 | Standard feature weighting |
| **TabPFN Foundation Model (Ours)** | **₹58.3** | **14.7%** | **0.906** | **Zero-training tabular transformer** |

* **Relative Error Reduction:** TabPFN achieves a **75.2% reduction in MAE** compared to historical category-mean pricing.

### TabPFN Cohort Breakdowns (Holdout MAE)
* **By Condition Grade:**
  * **Grade A (Like-new):** ₹33.1 MAE
  * **Grade B (Good / Standard wear):** ₹74.2 MAE
  * **Grade C (Fair / Re-tipping required):** ₹50.3 MAE
* **By Brand Tier:**
  * **Premium (Hu-Friedy, NSK, Kohler, KaVo):** ₹39.5 MAE
  * **Midrange (GDC, Dentsply, API, Miltex):** ₹81.1 MAE
  * **Economy (Generic, Budget Plus, Unknown):** ₹29.7 MAE

### Clinical Sanity Rules Enforced
1. **85% Ceiling Cap:** The suggested resale price never exceeds `round(0.85 * original_new_price)`.
2. **Floor Protection:** Minimum price floor of `max(50, round(0.10 * original_new_price))`.
3. **50-Rupee Quantization:** Quantized to nearest ₹50 for seamless clinic marketplace transactions.
4. **Quantile Interval:** Provides low/high bounds ensuring `price_low <= suggested_price <= price_high`.

---

## 3. Architecture & Deployment Matrix

| Component | Local Privacy-Preserving Mode | Hosted / Demo Mode |
|---|---|---|
| **Vision & Language** | **Gemma 3 4B** local via Ollama (`http://localhost:11434`) | Google AI Studio (`HostedGemmaProvider` via `gemini-2.0-flash` or hosted Gemma) |
| **Tabular FM Pricing** | **TabPFN 2.2.1** running in-process on CPU (`device="cpu"`) | Prior Labs API (`TABPFN_MODE=api`) |
| **Database Storage** | MongoDB Atlas cluster via `.env` with seamless local SQLite fallback | Local SQLite / Atlas cluster |
| **Vector Matching** | 64-dim normalized semantic embeddings with in-memory cosine matching | MongoDB Atlas Vector Search |
| **Mock Fallback** | Disabled when `DEMO_MODE=false` | Enabled with visible `DEMO MODE` badge |

---



### MongoDB Atlas & Vector Search Verified Details
* **Collections on Atlas:** `listings`, `wishlists`, `kits`, `events`.
* **Health Verification:** `GET /api/health` exposes `storage_backend` (`"atlas"` or `"sqlite"`) and `matching_mode` (`"atlas"` or `"in_memory_cosine"`).
* **Atlas Vector Index:** Defined in `scripts/atlas_index.json` (64 dimensions, cosine metric) on collection `listings`, path `embedding`. Initialized via `scripts/create_vector_index.py`.
* **Zero-Downtime Fallback:** If the Atlas cluster is unreachable or vector index is not ready, queries transparently fall back to thread-safe local SQLite and in-memory cosine similarity.
* **Seeded Demo Listings:** `scripts/seed_demo_listings.py` seeds 10 illustrative synthetic clinic listings pre-computed with 64-dim vectors.

## 4. Honest Disclosures: Synthetic & Demo Elements

1. **`data/price_history.csv`:** Synthetic clinical sales dataset containing 601 records generated using real clinical depreciation curves and realistic noise. **Labeled as illustrative synthetic data.** The MAE/MAPE figures in §2 are measured on this synthetic data.
2. **`data/instrument_catalog.json`:** Curated catalog of ~40 common dental instruments with representative retail price bounds.
3. **Clinic & Seller Names:** Fictional illustrative clinic names (e.g. *Sunrise Dental Clinic, Lakeview Polyclinic*).
4. **Notifications:** Sloth Run notifications are logged to the `events` collection and displayed on the morning dashboard. Physical SMS/WhatsApp gateways are mocked for hackathon testing.
5. **EXIF Privacy:** Uploaded photos have all EXIF and GPS geolocation metadata stripped before being processed by any model.
6. **Manual Baseline:** The manual listing time has **not** been independently measured. The placeholder `MANUAL_TIME_TO_BE_MEASURED_BY_USER` should be replaced with a real timed benchmark before any comparative claims are made.

---

## 5. Known Limitations & Edge Cases

* **Single-Use Safety Refusal:** Single-use disposables (disposable needles, plastic suctions, sutures) are refused by clinical safety guardrails.
* **Low-Confidence Guardrail:** Photos with <0.40 model confidence trigger a clear refusal screen requesting a retake on a plain background.
* **Clean Background Requirement:** Gemma vision performs best when instruments are photographed on a neutral dental tray or plain cloth.
* **TabPFN Non-Commercial License:** TabPFN weights are distributed under non-commercial research terms; commercial production deployment requires licensing from Prior Labs.
* **Synthetic Data Only:** All pricing accuracy metrics are benchmarked on synthetic data. Real-world accuracy will vary with actual sales data.

---

## 6. Captured Mobile Screenshots (390px Viewport)

* `docs/screenshots/mobile_snap.png` — Mobile photo dropzone with EXIF privacy disclaimer.
* `docs/screenshots/mobile_marketplace.png` — Mobile marketplace with condition chips and INR listings.
* `docs/screenshots/mobile_kit.png` — Starter Kit Builder with budget progress and auto-gap detection.
* `docs/screenshots/mobile_dashboard.png` — Morning Sloth Run summary, Lazy Payoff time-saved calculator, and live inventory feed.
