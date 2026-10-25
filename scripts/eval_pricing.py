"""Evaluate TabPFN vs Baselines (Mean-by-type, Linear Regression) on Holdout Synthetic Test Set."""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from typing import Tuple
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.config import get_settings
_s = get_settings()
if _s.tabpfn_api_key:
    os.environ["TABPFN_TOKEN"] = _s.tabpfn_api_key

from backend.pricing.tabpfn_model import (
    PRICE_HISTORY_CSV,
    BRAND_TIER_MAP,
    CONDITION_GRADE_MAP,
    round_to_50,
)

EVAL_MD_PATH = os.path.join(BASE_DIR, "data", "eval.md")


def encode_df(df: pd.DataFrame, type_list: list[str]) -> Tuple[np.ndarray, np.ndarray]:
    X_rows = []
    y_vals = []
    for _, row in df.iterrows():
        t_idx = type_list.index(row["instrument_type"]) if row["instrument_type"] in type_list else 0
        b_idx = BRAND_TIER_MAP.get(str(row["brand_tier"]).lower(), 0)
        c_idx = CONDITION_GRADE_MAP.get(str(row["condition_grade"]).upper(), 2)
        age = float(row["age_years"])
        cycles = float(row.get("sterilization_cycles_est", age * 50))
        orig_p = float(row["original_price_inr"])

        X_rows.append([t_idx, b_idx, c_idx, age, cycles, orig_p])
        y_vals.append(float(row["sale_price_inr"]))

    return np.array(X_rows, dtype=np.float32), np.array(y_vals, dtype=np.float32)


def run_evaluation():
    print("=" * 75)
    print(" DentSloth TabPFN Pricing Evaluation Benchmark")
    print("=" * 75)

    df = pd.read_csv(PRICE_HISTORY_CSV, comment="#")
    print(f"Loaded {len(df)} synthetic sales records from {PRICE_HISTORY_CSV}.")

    # Deterministic 80/20 train/test split
    train_df, test_df = train_test_split(df, test_size=0.20, random_state=42)
    print(f"Split: {len(train_df)} training samples, {len(test_df)} hold-out evaluation samples.")

    types = sorted(list(df["instrument_type"].unique()))
    X_train, y_train = encode_df(train_df, types)
    X_test, y_test = encode_df(test_df, types)

    # 1. Baseline 1: Mean-by-Type
    type_means = train_df.groupby("instrument_type")["sale_price_inr"].mean().to_dict()
    global_mean = train_df["sale_price_inr"].mean()
    y_pred_mean = np.array([type_means.get(t, global_mean) for t in test_df["instrument_type"]])

    mae_mean = mean_absolute_error(y_test, y_pred_mean)
    mape_mean = mean_absolute_percentage_error(y_test, y_pred_mean) * 100.0
    r2_mean = r2_score(y_test, y_pred_mean)

    # 2. Baseline 2: Linear Regression (Ridge)
    lr = Ridge(alpha=1.0)
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    # Sanity clip
    y_pred_lr = np.clip(y_pred_lr, 50, test_df["original_price_inr"] * 0.85)

    mae_lr = mean_absolute_error(y_test, y_pred_lr)
    mape_lr = mean_absolute_percentage_error(y_test, y_pred_lr) * 100.0
    r2_lr = r2_score(y_test, y_pred_lr)

    # 3. Model Under Test: TabPFN
    print("\nFitting TabPFN on training split...")
    from tabpfn import TabPFNRegressor
    tabpfn = TabPFNRegressor(device="cpu", n_estimators=4)
    tabpfn.fit(X_train, y_train)
    y_pred_tabpfn_raw = tabpfn.predict(X_test)

    # Apply sanity caps and rounding
    y_pred_tabpfn = []
    for raw, orig_p in zip(y_pred_tabpfn_raw, test_df["original_price_inr"]):
        cap = float(round(orig_p * 0.85))
        floor = float(max(50.0, round(orig_p * 0.10)))
        pred_val = round_to_50(max(floor, min(cap, raw)))
        y_pred_tabpfn.append(pred_val)
    y_pred_tabpfn = np.array(y_pred_tabpfn)

    mae_tabpfn = mean_absolute_error(y_test, y_pred_tabpfn)
    mape_tabpfn = mean_absolute_percentage_error(y_test, y_pred_tabpfn) * 100.0
    r2_tabpfn = r2_score(y_test, y_pred_tabpfn)

    # Cohort breakdowns for TabPFN
    test_eval_df = test_df.copy()
    test_eval_df["y_true"] = y_test
    test_eval_df["y_pred"] = y_pred_tabpfn
    test_eval_df["abs_err"] = np.abs(y_test - y_pred_tabpfn)

    grade_breakdown = test_eval_df.groupby("condition_grade")["abs_err"].mean().to_dict()
    tier_breakdown = test_eval_df.groupby("brand_tier")["abs_err"].mean().to_dict()

    print("\n" + "=" * 75)
    print(f"{'Model / Architecture':<28} | {'MAE (INR)':<12} | {'MAPE (%)':<10} | {'R²':<8}")
    print("-" * 75)
    print(f"{'1. Baseline: Mean-by-type':<28} | ₹{mae_mean:<10.1f} | {mape_mean:<8.1f}% | {r2_mean:<8.3f}")
    print(f"{'2. Baseline: Linear Regression':<28} | ₹{mae_lr:<10.1f} | {mape_lr:<8.1f}% | {r2_lr:<8.3f}")
    print(f"{'3. TabPFN (Ours)':<28} | ₹{mae_tabpfn:<10.1f} | {mape_tabpfn:<8.1f}% | {r2_tabpfn:<8.3f}")
    print("-" * 75)

    mae_improvement = ((mae_mean - mae_tabpfn) / mae_mean) * 100.0
    print(f"\nTabPFN Error Reduction vs Mean-by-type: {mae_improvement:.1f}%")

    # Write Markdown Document
    md_content = f"""# TabPFN Resale Pricing Agent — Real Evaluation Report

Generated by `scripts/eval_pricing.py` using real hold-out splits (80% train / 20% test) on `{PRICE_HISTORY_CSV}`.

> **Dataset:** 601 synthetic clinical sales records (labeled illustrative data).  
> **Evaluation Protocol:** 20% holdout test set ({len(test_df)} samples) unseen during prior fitting.  
> **Hardware:** Apple Silicon CPU inference (`device="cpu"`).

---

## 1. Overall Performance Comparison

| Model | MAE (INR) | MAPE (%) | R² Score | Note |
|---|---|---|---|---|
| **Baseline 1: Mean-by-type** | ₹{mae_mean:.1f} | {mape_mean:.1f}% | {r2_mean:.3f} | Naive category average |
| **Baseline 2: Linear Regression (Ridge)** | ₹{mae_lr:.1f} | {mape_lr:.1f}% | {r2_lr:.3f} | Standard linear feature weighting |
| **TabPFN Foundation Model (Ours)** | **₹{mae_tabpfn:.1f}** | **{mape_tabpfn:.1f}%** | **{r2_tabpfn:.3f}** | **Zero-training tabular prior-data transformer** |

**Relative Error Reduction:** TabPFN achieves a **{mae_improvement:.1f}% reduction in MAE** compared to simple historical mean pricing.

---

## 2. Cohort Breakdowns (TabPFN MAE)

### By Condition Grade
| Condition Grade | Description | Holdout MAE (INR) |
|---|---|---|
| **Grade A** | Excellent / like-new | ₹{grade_breakdown.get('A', 0.0):.1f} |
| **Grade B** | Good / standard wear | ₹{grade_breakdown.get('B', 0.0):.1f} |
| **Grade C** | Fair / re-tipping needed | ₹{grade_breakdown.get('C', 0.0):.1f} |

### By Brand Tier
| Brand Tier | Example Brands | Holdout MAE (INR) |
|---|---|---|
| **Premium** | Hu-Friedy, NSK, Kohler, KaVo | ₹{tier_breakdown.get('premium', 0.0):.1f} |
| **Midrange** | GDC, Dentsply, API, Miltex | ₹{tier_breakdown.get('midrange', 0.0):.1f} |
| **Economy** | Generic, Budget Plus, Unknown | ₹{tier_breakdown.get('economy', 0.0):.1f} |

---

## 3. Sanity Rules Enforced
1. **85% Ceiling:** Suggested price is strictly capped at `round(original_new_price * 0.85)`.
2. **Floor Protection:** Minimum price floor of `max(50, 0.10 * original_new_price)`.
3. **Rounding:** Quantized to nearest ₹50 for seamless clinic marketplace transactions.
4. **Quantile Interval:** Provides low/high uncertainty range ensuring `price_low <= suggested_price <= price_high`.
"""

    with open(EVAL_MD_PATH, "w") as f:
        f.write(md_content)
    print(f"\nSuccessfully wrote real benchmark metrics to {EVAL_MD_PATH}")


if __name__ == "__main__":
    from typing import Tuple
    run_evaluation()
