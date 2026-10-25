"""Process all sample dental instrument images and print classification metrics and latency."""
import asyncio
import os
import sys
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.llm.provider import get_llm_provider
from backend.utils.image_ops import validate_and_strip_exif

SAMPLES_DIR = os.path.join(BASE_DIR, "data", "sample_images")


async def run_samples():
    print("=" * 95)
    print(" DentSloth Gemma Vision Pipeline — Sample Images Benchmark")
    print("=" * 95)

    if not os.path.exists(SAMPLES_DIR):
        print(f"Error: Directory {SAMPLES_DIR} does not exist.")
        return

    sample_files = sorted([f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])
    if not sample_files:
        print(f"No image files found in {SAMPLES_DIR}.")
        return

    provider = get_llm_provider()
    total_images = len(sample_files)
    total_latency = 0.0
    refusals = 0
    passed = 0

    print(f"Found {total_images} sample image(s) to process.\n")
    header = f"{'Sample File':<32} | {'Items':<6} | {'Identified Type':<20} | {'Grade':<5} | {'Conf':<5} | {'Can List?':<9} | {'Latency':<8}"
    print(header)
    print("-" * len(header))

    for fname in sample_files:
        fpath = os.path.join(SAMPLES_DIR, fname)
        with open(fpath, "rb") as f:
            raw_bytes = f.read()

        # Step 1: Strip EXIF and validate
        t0 = time.perf_counter()
        clean_bytes, mime = validate_and_strip_exif(raw_bytes)

        # Step 2: Run vision provider
        result = await provider.identify(clean_bytes, mime_type=mime, filename=fname)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_latency += elapsed_ms

        if result.can_list:
            passed += 1
            status_str = "✅ YES"
        else:
            refusals += 1
            status_str = "⛔ REFUSED"

        items_str = f"{len(result.items)}"
        types_summary = ", ".join(i.instrument_type for i in result.items)
        if len(types_summary) > 18:
            types_summary = types_summary[:17] + "…"
        grades_summary = "/".join(i.condition_grade.value for i in result.items)
        avg_conf = sum(i.confidence for i in result.items) / max(len(result.items), 1)

        print(f"{fname:<32} | {items_str:<6} | {types_summary:<20} | {grades_summary:<5} | {avg_conf:<5.2f} | {status_str:<9} | {elapsed_ms:>6.1f}ms")
        if not result.can_list and result.refusal_reason:
            print(f"   ↳ 🛡️ Guardrail Refusal: {result.refusal_reason}")

    print("-" * len(header))
    avg_latency = total_latency / total_images if total_images else 0.0
    print(f"\nSummary:")
    print(f" • Total images processed: {total_images}")
    print(f" • Approved for listing:   {passed}")
    print(f" • Guardrail refusals:     {refusals} (single-use or low confidence)")
    print(f" • Average latency:        {avg_latency:.1f} ms")
    print("=" * 95)


if __name__ == "__main__":
    asyncio.run(run_samples())
