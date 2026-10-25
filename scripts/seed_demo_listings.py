#!/usr/bin/env python3
"""
Seed 15 demo listings into MongoDB Atlas (or local SQLite fallback).
ALL DATA IS SYNTHETIC – fictional clinic names, fictional prices.
Run: python scripts/seed_demo_listings.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.db import get_collection, get_storage_backend, ping_db
from backend.api.listings import compute_text_embedding
from datetime import datetime

LISTINGS = [
    {
        "instrument_type": "sickle_scaler",
        "brand": "Hu-Friedy", "condition_grade": "B",
        "age_years": 3.0, "original_price_inr": 900,
        "suggested_price_inr": 400, "price_low": 350, "price_high": 480,
        "description_en": "Hu-Friedy H6/H7 sickle scaler. Good condition, tip intact. Cleaned and bagged.",
        "description_hi": "Hu-Friedy H6/H7 सिकल स्केलर। अच्छी स्थिति में, नोक सही है। साफ और पैक किया हुआ।",
        "clinic_name": "Sunrise Dental Care (Demo)", "city": "Pune",
        "lifecycle": {"sterilization_cycles_est": 180, "last_sharpened": "2024-08"},
        "price_explanation": "Condition B, 3 yrs, premium brand – based on 28 synthetic comparable sales.",
    },
    {
        "instrument_type": "gracey_curette",
        "brand": "Hu-Friedy", "condition_grade": "A",
        "age_years": 1.0, "original_price_inr": 1400,
        "suggested_price_inr": 850, "price_low": 780, "price_high": 950,
        "description_en": "Gracey 13/14 curette. Barely used, excellent edge. Purchased new 1 year ago.",
        "description_hi": "Gracey 13/14 क्यूरेट। बहुत कम इस्तेमाल, शानदार धार। 1 साल पहले नया खरीदा था।",
        "clinic_name": "Lakeview Polyclinic (Demo)", "city": "Mumbai",
        "lifecycle": {"sterilization_cycles_est": 40, "last_sharpened": "2025-01"},
        "price_explanation": "Condition A, 1 yr, premium brand – priced at ~61% of new.",
    },
    {
        "instrument_type": "extraction_forceps_upper_anterior",
        "brand": "GDC", "condition_grade": "B",
        "age_years": 5.0, "original_price_inr": 1200,
        "suggested_price_inr": 400, "price_low": 350, "price_high": 480,
        "description_en": "GDC upper anterior forceps. Working hinges, no cracks. Suitable for general use.",
        "description_hi": "GDC ऊपरी पूर्व दाँत संदंश। काम करती काज, कोई दरार नहीं। सामान्य उपयोग के लिए उपयुक्त।",
        "clinic_name": "Sunrise Dental Care (Demo)", "city": "Pune",
        "lifecycle": {"sterilization_cycles_est": 300, "last_sharpened": None},
        "price_explanation": "Condition B, 5 yrs, mid-tier brand – based on 19 synthetic sales.",
    },
    {
        "instrument_type": "straight_elevator",
        "brand": "API", "condition_grade": "A",
        "age_years": 1.5, "original_price_inr": 700,
        "suggested_price_inr": 400, "price_low": 350, "price_high": 450,
        "description_en": "API straight elevator #34. Blade in prime condition, handle scratch-free.",
        "description_hi": "API सीधा एलिवेटर #34। ब्लेड बेहतरीन स्थिति में, हैंडल पर खरोंच नहीं।",
        "clinic_name": "Metro Implant Centre (Demo)", "city": "Delhi",
        "lifecycle": {"sterilization_cycles_est": 60, "last_sharpened": None},
        "price_explanation": "Condition A, 1.5 yrs, economy-plus brand – good starter tool.",
    },
    {
        "instrument_type": "mouth_mirror_handle",
        "brand": "GDC", "condition_grade": "B",
        "age_years": 2.0, "original_price_inr": 350,
        "suggested_price_inr": 150, "price_low": 100, "price_high": 180,
        "description_en": "Standard mirror handle. Thread clean, minor surface scuffs from autoclave.",
        "description_hi": "मानक माउथ मिरर हैंडल। चूड़ी साफ, ऑटोक्लेव से सतह पर मामूली निशान।",
        "clinic_name": "Apex Ortho Associates (Demo)", "city": "Bengaluru",
        "lifecycle": {"sterilization_cycles_est": 120, "last_sharpened": None},
        "price_explanation": "Condition B, 2 yrs, workhorse item – priced for fast sale.",
    },
    {
        "instrument_type": "college_tweezers",
        "brand": "Hu-Friedy", "condition_grade": "A",
        "age_years": 0.8, "original_price_inr": 650,
        "suggested_price_inr": 400, "price_low": 350, "price_high": 450,
        "description_en": "College cotton pliers / tweezers with serrated tips. Perfect alignment.",
        "description_hi": "कॉलेज कॉटन प्लायर्स / चिमटी। दांतेदार सिरे, बिल्कुल सही अलाइनमेंट।",
        "clinic_name": "Lakeview Polyclinic (Demo)", "city": "Mumbai",
        "lifecycle": {"sterilization_cycles_est": 35, "last_sharpened": None},
        "price_explanation": "Condition A, 0.8 yrs, premium brand – high demand.",
    },
    {
        "instrument_type": "periodontal_probe",
        "brand": "Hu-Friedy", "condition_grade": "B",
        "age_years": 3.0, "original_price_inr": 800,
        "suggested_price_inr": 350, "price_low": 300, "price_high": 420,
        "description_en": "UNC-15 periodontal probe with black mm markings. Markings clear and legible.",
        "description_hi": "UNC-15 पीरियोडॉन्टल प्रोब। काले मिलीमीटर निशान स्पष्ट और पढ़ने योग्य हैं।",
        "clinic_name": "Sunrise Dental Care (Demo)", "city": "Pune",
        "lifecycle": {"sterilization_cycles_est": 200, "last_sharpened": None},
        "price_explanation": "Condition B, 3 yrs, premium brand – markings intact.",
    },
    {
        "instrument_type": "needle_holder_mathieu",
        "brand": "Kohler", "condition_grade": "A",
        "age_years": 1.2, "original_price_inr": 2800,
        "suggested_price_inr": 1700, "price_low": 1500, "price_high": 1900,
        "description_en": "Mathieu needle holder, TC inserts. Ratchet locks firmly. German stainless steel.",
        "description_hi": "मैथ्यू नीडल होल्डर, टीसी इंसर्ट। रैचेट मजबूती से लॉक होता है।",
        "clinic_name": "Metro Implant Centre (Demo)", "city": "Delhi",
        "lifecycle": {"sterilization_cycles_est": 55, "last_sharpened": None},
        "price_explanation": "Condition A, 1.2 yrs, premium German brand – TC inserts intact.",
    },
    {
        "instrument_type": "bone_file_sugarman",
        "brand": "API", "condition_grade": "B",
        "age_years": 4.0, "original_price_inr": 800,
        "suggested_price_inr": 280, "price_low": 230, "price_high": 350,
        "description_en": "Sugarman bone file. Teeth intact. Mild staining but fully functional.",
        "description_hi": "Sugarman बोन फाइल। दाँत सही हैं। हल्का दाग पर पूरी तरह काम करती है।",
        "clinic_name": "Metro Implant Centre (Demo)", "city": "Delhi",
        "lifecycle": {"sterilization_cycles_est": 240, "last_sharpened": None},
        "price_explanation": "Condition B, 4 yrs, economy brand – bone files are very affordable.",
    },
    {
        "instrument_type": "universal_curette",
        "brand": "Nordent", "condition_grade": "B",
        "age_years": 2.5, "original_price_inr": 1100,
        "suggested_price_inr": 480, "price_low": 420, "price_high": 560,
        "description_en": "Columbia 13/14 universal curette. Tip intact, slight handle wear.",
        "description_hi": "Columbia 13/14 यूनिवर्सल क्यूरेट। टिप सही, हैंडल पर हल्की घिसाव।",
        "clinic_name": "Lakeview Polyclinic (Demo)", "city": "Mumbai",
        "lifecycle": {"sterilization_cycles_est": 150, "last_sharpened": "2024-06"},
        "price_explanation": "Condition B, 2.5 yrs, mid-tier brand – based on synthetic sales data.",
    },
]

def seed():
    backend = get_storage_backend()
    print(f"Seeding demo listings into storage backend: {backend}")
    col = get_collection("listings")
    
    # Idempotent cleanup of past demo listings
    try:
        col.delete_many({"_synthetic": True})
    except Exception as e:
        print(f"Warning during cleanup: {e}")

    now = datetime.utcnow().isoformat()
    inserted = 0
    for raw in LISTINGS:
        embed_text = f"{raw['instrument_type']} {raw['brand']} {raw['city']} {raw['description_en']}"
        embed = compute_text_embedding(embed_text)
        doc = {
            **raw,
            "image_url": None,
            "status": "published",
            "embedding": embed,
            "created_at": now,
            "lifecycle": raw.get("lifecycle", {}),
            "_synthetic": True,
        }
        col.insert_one(doc)
        inserted += 1

    print(f"✅ Successfully seeded {inserted} demo listings with 64-dim vector embeddings ({backend})")

if __name__ == "__main__":
    seed()
