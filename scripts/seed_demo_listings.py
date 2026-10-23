#!/usr/bin/env python3
"""
Seed 15 demo listings into MongoDB.
ALL DATA IS SYNTHETIC – fictional clinic names, fictional prices.
Run: python scripts/seed_demo_listings.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.db import get_collection
from backend.models import ConditionGrade, ListingStatus, Lifecycle
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
        "instrument_type": "handpiece_highspeed",
        "brand": "NSK", "condition_grade": "B",
        "age_years": 4.0, "original_price_inr": 18000,
        "suggested_price_inr": 7000, "price_low": 6000, "price_high": 8500,
        "description_en": "NSK high-speed air turbine. Serviced 6 months ago. Spins smooth, no wobble.",
        "description_hi": "NSK हाई-स्पीड एयर टर्बाइन। 6 महीने पहले सर्विस की गई। सुचारू चलती है।",
        "clinic_name": "Metro Implant Centre (Demo)", "city": "Delhi",
        "lifecycle": {"sterilization_cycles_est": 800, "last_sharpened": None},
        "price_explanation": "Condition B, 4 yrs, premium brand – handpieces depreciate steadily; 39% of new.",
    },
    {
        "instrument_type": "ultrasonic_scaler_unit",
        "brand": "Dentsply", "condition_grade": "B",
        "age_years": 3.5, "original_price_inr": 22000,
        "suggested_price_inr": 8500, "price_low": 7500, "price_high": 10000,
        "description_en": "Dentsply Cavitron Select unit with 3 tips. Powers on, all modes work.",
        "description_hi": "Dentsply Cavitron Select यूनिट 3 टिप्स के साथ। चालू होती है, सभी मोड काम करते हैं।",
        "clinic_name": "Bright Smiles Clinic (Demo)", "city": "Bangalore",
        "lifecycle": {"sterilization_cycles_est": 420, "last_sharpened": None},
        "price_explanation": "Condition B, 3.5 yrs, mid-tier brand – range derived from synthetic sales dataset.",
    },
    {
        "instrument_type": "periodontal_probe",
        "brand": "Hu-Friedy", "condition_grade": "A",
        "age_years": 0.5, "original_price_inr": 800,
        "suggested_price_inr": 550, "price_low": 500, "price_high": 620,
        "description_en": "Williams probe. As-new condition. Selling because upgrading to cassette system.",
        "description_hi": "Williams प्रोब। नई जैसी हालत। कैसेट सिस्टम अपग्रेड के कारण बेच रहे हैं।",
        "clinic_name": "Ridgeview Orthodontics (Demo)", "city": "Chennai",
        "lifecycle": {"sterilization_cycles_est": 20, "last_sharpened": None},
        "price_explanation": "Condition A, 0.5 yrs – near-new. Price ~69% of retail.",
    },
    {
        "instrument_type": "composite_instrument_set",
        "brand": "Hu-Friedy", "condition_grade": "A",
        "age_years": 1.5, "original_price_inr": 3200,
        "suggested_price_inr": 1800, "price_low": 1600, "price_high": 2100,
        "description_en": "5-piece composite set (TPFD). Light use only. No tip damage.",
        "description_hi": "5-piece कंपोज़िट सेट (TPFD)। केवल हल्का उपयोग। टिप में कोई नुकसान नहीं।",
        "clinic_name": "Lakeview Polyclinic (Demo)", "city": "Mumbai",
        "lifecycle": {"sterilization_cycles_est": 60, "last_sharpened": None},
        "price_explanation": "Condition A, 1.5 yrs, premium brand – priced at 56% of new.",
    },
    {
        "instrument_type": "extraction_forceps_lower_molar",
        "brand": "GDC", "condition_grade": "C",
        "age_years": 8.0, "original_price_inr": 1800,
        "suggested_price_inr": 400, "price_low": 300, "price_high": 500,
        "description_en": "Lower molar forceps. Functional but shows age. Surface pitting on handle. Priced accordingly.",
        "description_hi": "निचली दाढ़ संदंश। काम करती है पर पुरानी दिखती है। हैंडल पर गड्ढे हैं। कीमत उसी हिसाब से।",
        "clinic_name": "Hillcrest Family Dentistry (Demo)", "city": "Hyderabad",
        "lifecycle": {"sterilization_cycles_est": 600, "last_sharpened": None},
        "price_explanation": "Condition C, 8 yrs, mid-tier – floor price applied.",
    },
    {
        "instrument_type": "shade_guide",
        "brand": "Vita", "condition_grade": "B",
        "age_years": 4.0, "original_price_inr": 5500,
        "suggested_price_inr": 2200, "price_low": 1900, "price_high": 2600,
        "description_en": "Vita Classic 16-shade guide. All tabs present. Minor staining on A3, A3.5.",
        "description_hi": "Vita Classic 16-शेड गाइड। सभी टैब मौजूद। A3, A3.5 पर हल्का दाग।",
        "clinic_name": "Metro Implant Centre (Demo)", "city": "Delhi",
        "lifecycle": {"sterilization_cycles_est": None, "last_sharpened": None},
        "price_explanation": "Condition B, 4 yrs – shade guides age by staining, not mechanical wear.",
    },
    {
        "instrument_type": "weingart_plier",
        "brand": "Ormco", "condition_grade": "B",
        "age_years": 3.0, "original_price_inr": 2200,
        "suggested_price_inr": 900, "price_low": 800, "price_high": 1100,
        "description_en": "Ormco Weingart utility plier. Good tip alignment. No corrosion.",
        "description_hi": "Ormco Weingart यूटिलिटी प्लायर। अच्छा टिप अलाइनमेंट। कोई जंग नहीं।",
        "clinic_name": "Ridgeview Orthodontics (Demo)", "city": "Chennai",
        "lifecycle": {"sterilization_cycles_est": 200, "last_sharpened": None},
        "price_explanation": "Condition B, 3 yrs, mid-tier brand – ortho pliers hold value well.",
    },
    {
        "instrument_type": "handpiece_lowspeed",
        "brand": "W&H", "condition_grade": "A",
        "age_years": 2.0, "original_price_inr": 12000,
        "suggested_price_inr": 7000, "price_low": 6200, "price_high": 8000,
        "description_en": "W&H straight micromotor. Very low usage. All attachments included.",
        "description_hi": "W&H सीधा माइक्रोमोटर। बहुत कम उपयोग। सभी अटैचमेंट शामिल।",
        "clinic_name": "Bright Smiles Clinic (Demo)", "city": "Bangalore",
        "lifecycle": {"sterilization_cycles_est": 120, "last_sharpened": None},
        "price_explanation": "Condition A, 2 yrs, premium brand – near-new premium handpiece.",
    },
    {
        "instrument_type": "rubber_dam_forceps",
        "brand": "Hu-Friedy", "condition_grade": "B",
        "age_years": 6.0, "original_price_inr": 2000,
        "suggested_price_inr": 700, "price_low": 600, "price_high": 850,
        "description_en": "Ivory-style rubber dam forceps. Spring works fine. Some surface wear.",
        "description_hi": "Ivory-style रबर डैम फोरसेप्स। स्प्रिंग ठीक है। कुछ सतही घिसाव।",
        "clinic_name": "Hillcrest Family Dentistry (Demo)", "city": "Hyderabad",
        "lifecycle": {"sterilization_cycles_est": 350, "last_sharpened": None},
        "price_explanation": "Condition B, 6 yrs, premium brand – rubber dam instruments last long.",
    },
    {
        "instrument_type": "needle_holder",
        "brand": "Miltex", "condition_grade": "A",
        "age_years": 1.0, "original_price_inr": 1800,
        "suggested_price_inr": 1100, "price_low": 980, "price_high": 1250,
        "description_en": "Mayo-Hegar needle holder. Excellent grip. Ratchet locks firmly.",
        "description_hi": "Mayo-Hegar नीडल होल्डर। उत्कृष्ट पकड़। रैचेट मजबूती से लॉक होती है।",
        "clinic_name": "Sunrise Dental Care (Demo)", "city": "Pune",
        "lifecycle": {"sterilization_cycles_est": 30, "last_sharpened": None},
        "price_explanation": "Condition A, 1 yr, mid-tier brand – priced at ~61% of new.",
    },
    {
        "instrument_type": "bone_file",
        "brand": "GDC", "condition_grade": "B",
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

col = get_collection("listings")
col.delete_many({"clinic_name": {"$regex": r"\(Demo\)"}})  # idempotent

now = datetime.utcnow()
inserted = 0
for raw in LISTINGS:
    doc = {
        **raw,
        "image_url": None,
        "status": "published",
        "embedding": [],
        "created_at": now,
        "lifecycle": raw.get("lifecycle", {}),
        "_synthetic": True,
    }
    col.insert_one(doc)
    inserted += 1

print(f"Seeded {inserted} demo listings (SYNTHETIC)")
