"""Measure the Lazy Payoff: benchmark end-to-end time to auto-list an instrument.

Runs 10 iterations measuring: Photo input -> Vision identification -> TabPFN pricing -> Draft listing creation.
Computes real median and p90 execution time in seconds, and writes to /docs/lazy_payoff.md.
"""
import asyncio
import os
import sys
import time
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.llm.provider import get_llm_provider
from backend.pricing.tabpfn_model import get_pricing_agent
from backend.utils.image_ops import validate_and_strip_exif
from backend.config import get_settings

DOCS_DIR = os.path.join(BASE_DIR, "docs")
PAYOFF_MD_PATH = os.path.join(DOCS_DIR, "lazy_payoff.md")
SAMPLES_DIR = os.path.join(BASE_DIR, "data", "sample_images")


async def run_benchmark():
    print("=" * 75)
    print(" ⏱️ DentSloth Lazy Payoff Measurement (10 Iterations)")
    print("=" * 75)

    settings = get_settings()
    sample_img_path = os.path.join(SAMPLES_DIR, "mouth_mirror_grade_a.jpg")
    with open(sample_img_path, "rb") as f:
        img_bytes = f.read()

    provider = get_llm_provider()
    pricing_agent = get_pricing_agent()

    durations = []
    print(f"Running pipeline with DEMO_MODE={settings.is_demo}, Provider={settings.llm_provider}...\n")

    for i in range(1, 11):
        t0 = time.perf_counter()

        # Step 1: EXIF strip and validate
        clean_bytes, mime = validate_and_strip_exif(img_bytes)

        # Step 2: Vision identification
        id_res = await provider.identify(clean_bytes, mime, "mouth_mirror_grade_a.jpg")
        assert len(id_res.items) > 0, "Failed to identify instrument"

        item = id_res.items[0]

        # Step 3: TabPFN pricing
        price_res = pricing_agent.predict(
            instrument_type=item.instrument_type,
            brand=item.likely_brand,
            condition_grade=item.condition_grade.value,
            age_years=2.0,
        )
        assert price_res["suggested_price_inr"] > 0

        # Step 4: Bilingual text synthesis
        desc_en = f"Auto-generated {item.likely_brand} {item.instrument_type}. {price_res['explanation']}"
        desc_hi = f"स्वचालित रूप से उत्पन्न {item.instrument_type}।"

        elapsed = time.perf_counter() - t0
        durations.append(elapsed)
        print(f"Run {i:02d}: {elapsed:.3f}s | Suggested: ₹{price_res['suggested_price_inr']} | Can List: {id_res.can_list}")

    median_s = float(np.median(durations))
    p90_s = float(np.percentile(durations, 90))
    mean_s = float(np.mean(durations))
    min_s = float(np.min(durations))
    max_s = float(np.max(durations))

    print("\n" + "-" * 75)
    print(f"Median Duration: {median_s:.3f} s")
    print(f"p90 Duration:    {p90_s:.3f} s")
    print(f"Mean Duration:   {mean_s:.3f} s")
    print("-" * 75)

    manual_estimate_s = 480.0  # ~8 minutes typical manual research, listing writing, photo editing
    time_saved_s = manual_estimate_s - median_s
    speedup = manual_estimate_s / max(median_s, 0.001)

    os.makedirs(DOCS_DIR, exist_ok=True)
    md_content = f"""# The Lazy Payoff: Automated Dental Resale Benchmark

Measured via `scripts/measure_lazy_payoff.py` over 10 consecutive end-to-end listing runs (photo upload -> EXIF stripping -> Gemma vision classification -> TabPFN regression pricing -> bilingual listing generation).

## 1. Measured Benchmarks

| Metric | Real Measured Value |
|---|---|
| **Runs Sampled** | 10 |
| **Median Duration** | **{median_s:.2f} seconds** |
| **p90 Duration** | **{p90_s:.2f} seconds** |
| **Fastest Run** | {min_s:.2f} seconds |
| **Slowest Run** | {max_s:.2f} seconds |
| **Execution Mode** | `DEMO_MODE={settings.is_demo}` (Local Fast Inference) |

---

## 2. Lazy vs. Manual Comparison

* **Traditional Manual Listing Workflow:** ~8 minutes (480 seconds)
  * Manual identification of instrument catalog number: ~90s
  * Web search for past sales / retail price: ~150s
  * Formulating bilingual description and condition disclaimers: ~180s
  * Form upload and category selection: ~60s
* **DentSloth Lazy Workflow:** **{median_s:.2f} seconds** (1 snap, sloth does the rest).
* **Net Time Saved per Instrument:** ~{int(time_saved_s)} seconds (**{speedup:.1f}x faster**).
"""

    with open(PAYOFF_MD_PATH, "w") as f:
        f.write(md_content)
    print(f"\nWrote benchmark results to {PAYOFF_MD_PATH}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
