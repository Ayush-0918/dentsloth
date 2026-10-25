# The Lazy Payoff: Automated Dental Resale Benchmark

Measured via `scripts/measure_lazy_payoff.py` over 10 consecutive end-to-end listing runs (photo upload -> EXIF stripping -> Gemma vision classification -> TabPFN regression pricing -> bilingual listing generation).

## 1. Measured Benchmarks

| Metric | Real Measured Value |
|---|---|
| **Runs Sampled** | 10 |
| **Median Duration** | **4.83 seconds** |
| **p90 Duration** | **5.15 seconds** |
| **Fastest Run** | 4.81 seconds |
| **Slowest Run** | 7.21 seconds |
| **Execution Mode** | `DEMO_MODE=False` (Local Fast Inference) |

---

## 2. Lazy vs. Manual Comparison

* **Traditional Manual Listing Workflow:** ~8 minutes (480 seconds)
  * Manual identification of instrument catalog number: ~90s
  * Web search for past sales / retail price: ~150s
  * Formulating bilingual description and condition disclaimers: ~180s
  * Form upload and category selection: ~60s
* **DentSloth Lazy Workflow:** **4.83 seconds** (1 snap, sloth does the rest).
* **Net Time Saved per Instrument:** ~475 seconds (**99.3x faster**).
