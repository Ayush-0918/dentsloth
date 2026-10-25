"""DentSloth TabPFN Pricing Agent.

Leverages TabPFN (open-weight tabular foundation model) to estimate fair market resale
prices and quantile uncertainty intervals for used dental instruments.
Enforces strict clinical sanity rules (caps, floors, rounding to nearest Rs 50).
"""
import json
import logging
import os
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd

from ..config import get_settings

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_HISTORY_CSV = os.path.join(DATA_DIR, "price_history.csv")
CATALOG_JSON = os.path.join(DATA_DIR, "instrument_catalog.json")

# Brand classification mappings
PREMIUM_BRANDS = {"hu-friedy", "nsk", "kohler", "kavo", "lm dental", "medesy", "bien-air", "w&h"}
MIDRANGE_BRANDS = {"gdc", "dentsply", "api", "ss white", "miltex", "nordent", "coltene"}
ECONOMY_BRANDS = {"budget plus", "generic", "unknown"}

BRAND_TIER_MAP = {"economy": 0, "midrange": 1, "premium": 2}
CONDITION_GRADE_MAP = {"C": 1, "B": 2, "A": 3}


def round_to_50(val: float) -> int:
    """Round to nearest 50 INR."""
    return max(50, int(round(val / 50.0) * 50))


def classify_brand(brand: str) -> str:
    """Classify brand into brand tier."""
    b_lower = (brand or "").strip().lower()
    if b_lower in PREMIUM_BRANDS or any(p in b_lower for p in PREMIUM_BRANDS):
        return "premium"
    if b_lower in MIDRANGE_BRANDS or any(m in b_lower for m in MIDRANGE_BRANDS):
        return "midrange"
    return "economy"


class TabPFNPricingAgent:
    """TabPFN pricing agent with training, inference, and sanity rules."""

    def __init__(self, mode: Optional[str] = None):
        settings = get_settings()
        self.mode = mode or settings.tabpfn_mode
        self.api_key = settings.tabpfn_api_key
        if self.api_key:
            os.environ["TABPFN_TOKEN"] = self.api_key
        self.model = None
        self.catalog = self._load_catalog()
        self.df_train: Optional[pd.DataFrame] = None
        self.instrument_types: list[str] = []
        self._fitted = False

    def _load_catalog(self) -> Dict[str, Any]:
        if os.path.exists(CATALOG_JSON):
            try:
                with open(CATALOG_JSON, "r") as f:
                    data = json.load(f)
                    return {item["id"]: item for item in data.get("instruments", [])}
            except Exception as e:
                logger.warning(f"Could not load catalog: {e}")
        return {}

    def get_default_original_price(self, instrument_type: str) -> float:
        """Lookup illustrative catalog price midpoint if original price is missing."""
        clean_type = instrument_type.lower().replace(" ", "_").replace("-", "_")
        item = self.catalog.get(clean_type)
        if item and "new_price_range_inr" in item:
            low, high = item["new_price_range_inr"]
            return float((low + high) / 2.0)
        return 1200.0  # Safe general midpoint for basic dental hand instruments

    def encode_row(
        self,
        instrument_type: str,
        brand_tier: str,
        condition_grade: str,
        age_years: float,
        sterilization_cycles_est: float,
        original_price_inr: float,
    ) -> np.ndarray:
        """Vectorize tabular features for TabPFN."""
        # Categorical features
        type_idx = (
            self.instrument_types.index(instrument_type)
            if instrument_type in self.instrument_types
            else 0
        )
        b_tier_num = BRAND_TIER_MAP.get(brand_tier.lower(), 0)
        c_grade_num = CONDITION_GRADE_MAP.get(condition_grade.upper(), 2)

        return np.array(
            [
                float(type_idx),
                float(b_tier_num),
                float(c_grade_num),
                float(age_years),
                float(sterilization_cycles_est),
                float(original_price_inr),
            ],
            dtype=np.float32,
        )

    def fit(self, csv_path: str = PRICE_HISTORY_CSV):
        """Fit TabPFN on synthetic historical sales data."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Price history data not found at: {csv_path}")

        df = pd.read_csv(csv_path, comment="#")
        self.df_train = df
        self.instrument_types = sorted(list(df["instrument_type"].unique()))

        X_rows = []
        y_vals = []
        for _, row in df.iterrows():
            feat = self.encode_row(
                instrument_type=str(row["instrument_type"]),
                brand_tier=str(row["brand_tier"]),
                condition_grade=str(row["condition_grade"]),
                age_years=float(row["age_years"]),
                sterilization_cycles_est=float(row.get("sterilization_cycles_est", row["age_years"] * 50)),
                original_price_inr=float(row["original_price_inr"]),
            )
            X_rows.append(feat)
            y_vals.append(float(row["sale_price_inr"]))

        X = np.vstack(X_rows)
        y = np.array(y_vals, dtype=np.float32)

        # Initialize TabPFN Regressor
        if self.mode == "api":
            try:
                from tabpfn_client import TabPFNRegressor as APIRegressor
                self.model = APIRegressor()
                self.model.fit(X, y)
                self._fitted = True
                logger.info("Fitted TabPFN via API mode successfully")
                return
            except Exception as e:
                logger.warning(f"TabPFN API mode initialization failed: {e}. Falling back to local.")

        # Local mode (or lightweight production fallback if TabPFN/torch not installed)
        try:
            from tabpfn import TabPFNRegressor
            self.model = TabPFNRegressor(device="cpu", n_estimators=4)
            self.model.fit(X, y)
            self._fitted = True
            logger.info("Fitted TabPFN locally on CPU successfully")
        except Exception as err:
            logger.warning(f"TabPFN local model not available ({err}). Falling back to lightweight Ridge baseline for production resilience.")
            from sklearn.linear_model import Ridge
            self.model = Ridge()
            self.model.fit(X, y)
            self._fitted = True
            logger.info("Fitted Ridge fallback pricing model successfully")

    def predict(
        self,
        instrument_type: str,
        brand: str,
        condition_grade: str,
        age_years: float,
        original_price_inr: Optional[float] = None,
        sterilization_cycles_est: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Estimate price with quantile bounds, applying strict clinical sanity rules."""
        if not self._fitted:
            self.fit()

        brand_tier = classify_brand(brand)
        if original_price_inr is None or original_price_inr <= 0:
            original_price_inr = self.get_default_original_price(instrument_type)

        if sterilization_cycles_est is None or sterilization_cycles_est < 0:
            sterilization_cycles_est = float(round(age_years * 50.0))

        feat = self.encode_row(
            instrument_type=instrument_type,
            brand_tier=brand_tier,
            condition_grade=condition_grade,
            age_years=age_years,
            sterilization_cycles_est=sterilization_cycles_est,
            original_price_inr=original_price_inr,
        )
        X_test = feat.reshape(1, -1)

        # TabPFN prediction
        raw_pred = float(self.model.predict(X_test)[0])

        # ── SANITY RULES ───────────────────────────────────────────────────────
        # Rule 1: Cap at 85% of original new price
        cap_price = float(round(original_price_inr * 0.85))

        # Rule 2: Minimum floor (at least 10% of new price or Rs 50)
        floor_price = float(max(50.0, round(original_price_inr * 0.10)))

        # Constrain suggested price
        suggested_raw = max(floor_price, min(cap_price, raw_pred))
        suggested_price = round_to_50(suggested_raw)

        # Quantile uncertainty range (±15% spread around prediction, bounded by floor and cap)
        low_raw = max(floor_price, min(suggested_raw, suggested_raw * 0.85))
        high_raw = max(suggested_raw, min(cap_price, suggested_raw * 1.15))

        price_low = round_to_50(low_raw)
        price_high = round_to_50(high_raw)

        # Ensure low <= suggested <= high
        if price_low > suggested_price:
            price_low = suggested_price
        if price_high < suggested_price:
            price_high = suggested_price

        # Human-readable explanation
        sample_count = len(self.df_train[self.df_train["instrument_type"] == instrument_type]) if self.df_train is not None else 25
        explanation = (
            f"Based on {sample_count} comparable synthetic sales: Grade {condition_grade.upper()}, "
            f"{age_years:.1f} yrs old, {brand_tier} brand ({brand or 'unbranded'}). "
            f"Sanity checks applied: capped at 85% of new price (₹{int(cap_price):,}) with floor of ₹{int(floor_price):,}."
        )

        return {
            "suggested_price_inr": suggested_price,
            "price_low": price_low,
            "price_high": price_high,
            "explanation": explanation,
            "original_price_inr": original_price_inr,
            "brand_tier": brand_tier,
        }


_global_pricing_agent: Optional[TabPFNPricingAgent] = None


def get_pricing_agent() -> TabPFNPricingAgent:
    """Singleton getter for TabPFN pricing agent."""
    global _global_pricing_agent
    if _global_pricing_agent is None:
        _global_pricing_agent = TabPFNPricingAgent()
    return _global_pricing_agent
