# The Lazy Payoff: Automated Dental Resale Benchmark

Measured via `scripts/measure_lazy_payoff.py` over 10 consecutive end-to-end listing runs (photo upload -> EXIF stripping -> Gemma vision classification -> TabPFN regression pricing -> bilingual listing generation).

## 1. Measured Benchmarks (DEMO_MODE=false, local Ollama inference)

| Metric | Real Measured Value |
|---|---|
| **Runs Sampled** | 10 |
| **Median Duration** | **4.83 seconds** |
| **p90 Duration** | **5.15 seconds** |
| **Fastest Run** | 4.81 seconds |
| **Slowest Run** | 7.21 seconds |
| **Execution Mode** | `DEMO_MODE=false`, `LLM_PROVIDER=ollama` (Gemma 3 4B local) |

> **Note:** The above numbers were measured with `DEMO_MODE=false` using real open-weight inference (Gemma 3 4B via Ollama) on Apple Silicon. They do NOT represent `DEMO_MODE=true` demo-fallback timing.

---

## 2. Lazy vs. Manual Comparison

* **Traditional Manual Listing Workflow:** `MANUAL_TIME_TO_BE_MEASURED_BY_USER`
  * Manual identification of instrument catalog number
  * Web search for past sales / retail price
  * Formulating bilingual description and condition disclaimers
  * Form upload and category selection
* **DentSloth Lazy Workflow:** **4.83 seconds** (1 snap, sloth does the rest).
* **Net Time Saved per Instrument:** Difference between user-measured manual time and 4.83 seconds.

> **Disclaimer:** The manual workflow time was not independently measured. Replace `MANUAL_TIME_TO_BE_MEASURED_BY_USER` with your own timed benchmark before citing this figure.
