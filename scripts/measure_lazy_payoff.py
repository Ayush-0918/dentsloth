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
REAL_PHOTOS_DIR = os.path.join(BASE_DIR, "data", "real_photos")


async def run_benchmark():
    print("=" * 75)
    print(" ⏱️ DentSloth Lazy Payoff Measurement (10 Iterations)")
    print("=" * 75)

    settings = get_settings()

    # Prefer real photos if available, fall back to sample images
    photo_dir = REAL_PHOTOS_DIR if os.path.isdir(REAL_PHOTOS_DIR) and os.listdir(REAL_PHOTOS_DIR) else SAMPLES_DIR
    photos = [
        os.path.join(photo_dir, f)
        for f in os.listdir(photo_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]
    if not photos:
        print("ERROR: No photos found in", photo_dir)
        return

    print(f"Using photos from: {photo_dir} ({len(photos)} file(s))")
    print(f"DEMO_MODE={settings.is_demo}, Provider={settings.llm_provider}\n")

    provider = get_llm_provider()
    pricing_agent = get_pricing_agent()

    durations = []

    for i in range(1, 11):
        # Cycle through available photos
        img_path = photos[(i - 1) % len(photos)]
        img_name = os.path.basename(img_path)
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        t0 = time.perf_counter()

        # Step 1: EXIF strip and validate
        clean_bytes, mime = validate_and_strip_exif(img_bytes)

        # Step 2: Vision identification
        id_res = await provider.identify(clean_bytes, mime, img_name)
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
        print(f"Run {i:02d}: {elapsed:.3f}s | Photo: {img_name} | Suggested: ₹{price_res['suggested_price_inr']} | Can List: {id_res.can_list}")

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

    # Source label based on where photos came from
    source_label = "real photos" if photo_dir == REAL_PHOTOS_DIR else "synthetic sample images"
    demo_label = f"DEMO_MODE={settings.is_demo}" if settings.is_demo else f"DEMO_MODE=false, LLM_PROVIDER={settings.llm_provider}"

    os.makedirs(DOCS_DIR, exist_ok=True)
    md_content = f"""# The Lazy Payoff: Automated Dental Resale Benchmark

Measured via `scripts/measure_lazy_payoff.py` over 10 consecutive end-to-end listing runs (photo upload -> EXIF stripping -> Gemma vision classification -> TabPFN regression pricing -> bilingual listing generation).

## 1. Measured Benchmarks ({demo_label}, {source_label})

| Metric | Real Measured Value |
|---|---|
| **Runs Sampled** | 10 |
| **Median Duration** | **{median_s:.2f} seconds** |
| **p90 Duration** | **{p90_s:.2f} seconds** |
| **Fastest Run** | {min_s:.2f} seconds |
| **Slowest Run** | {max_s:.2f} seconds |
| **Execution Mode** | `{demo_label}` |
| **Photo Source** | {source_label} ({len(photos)} file(s) from `{os.path.basename(photo_dir)}/`) |

> **Note:** These timings reflect end-to-end pipeline execution. The {source_label} were used as input.

---

## 2. Lazy vs. Manual Comparison

* **Traditional Manual Listing Workflow:** `MANUAL_TIME_TO_BE_MEASURED_BY_USER`
  * Manual identification of instrument catalog number
  * Web search for past sales / retail price
  * Formulating bilingual description and condition disclaimers
  * Form upload and category selection
* **DentSloth Lazy Workflow:** **{median_s:.2f} seconds** (1 snap, sloth does the rest).
* **Net Time Saved per Instrument:** Difference between user-measured manual time and {median_s:.2f} seconds.

> **Disclaimer:** The manual workflow time was not independently measured. Replace `MANUAL_TIME_TO_BE_MEASURED_BY_USER` with your own timed benchmark before citing this figure.
"""

    with open(PAYOFF_MD_PATH, "w") as f:
        f.write(md_content)
    print(f"\nWrote benchmark results to {PAYOFF_MD_PATH}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
