"""Generate synthetic realistic sample dental images and demo_cache.json."""
import json
import os
from PIL import Image, ImageDraw, ImageFilter
import piexif

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_images")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# 1. Sample Images & Pre-recorded clinical evaluations
CACHE_DATA = {
    "mouth_mirror_grade_a.jpg": {
        "items": [
            {
                "instrument_type": "mouth_mirror",
                "likely_brand": "Hu-Friedy",
                "material": "stainless_steel",
                "condition_grade": "A",
                "visible_defects": [],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.94,
            }
        ],
        "notes": "Hu-Friedy #5 front surface dental mirror. Pristine mirror glass, intact reflective coating, flawless ergonomic handle.",
    },
    "gracey_curette_grade_b.jpg": {
        "items": [
            {
                "instrument_type": "gracey_curette",
                "likely_brand": "Hu-Friedy",
                "material": "stainless_steel",
                "condition_grade": "B",
                "visible_defects": ["Minor surface abrasion on shank", "Standard handle wear"],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.91,
            }
        ],
        "notes": "Hu-Friedy Gracey 13/14 area-specific periodontal curette. Intact cutting edge, standard autoclave markings.",
    },
    "sickle_scaler_grade_c.jpg": {
        "items": [
            {
                "instrument_type": "sickle_scaler",
                "likely_brand": "unknown",
                "material": "stainless_steel",
                "condition_grade": "C",
                "visible_defects": ["Blunted cutting blade", "Micro-pitting on working tip", "Discoloration near neck"],
                "needs_sharpening": True,
                "is_single_use": False,
                "confidence": 0.86,
            }
        ],
        "notes": "Posterior sickle scaler 204S. Working tip exhibits significant wear and requires professional re-sharpening before clinical use.",
    },
    "tray_instruments_multi.jpg": {
        "items": [
            {
                "instrument_type": "mouth_mirror",
                "likely_brand": "Hu-Friedy",
                "material": "stainless_steel",
                "condition_grade": "A",
                "visible_defects": [],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.93,
            },
            {
                "instrument_type": "dental_probe",
                "likely_brand": "Hu-Friedy",
                "material": "stainless_steel",
                "condition_grade": "A",
                "visible_defects": [],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.92,
            },
            {
                "instrument_type": "college_tweezers",
                "likely_brand": "unknown",
                "material": "stainless_steel",
                "condition_grade": "B",
                "visible_defects": ["Light handle friction marks"],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.89,
            }
        ],
        "notes": "Sterilization cassette tray containing 3-piece diagnostic kit: Mouth Mirror, #23 Explorer Probe, and Cotton Pliers.",
    },
    "disposable_needle_syringe.jpg": {
        "items": [
            {
                "instrument_type": "disposable_dental_needle",
                "likely_brand": "Septodont",
                "material": "plastic_and_stainless_steel",
                "condition_grade": "A",
                "visible_defects": [],
                "needs_sharpening": False,
                "is_single_use": True,
                "confidence": 0.96,
            }
        ],
        "notes": "Single-use disposable 27G long infiltration needle with plastic sheath. Non-reusable biohazard item.",
    },
    "blurry_unknown_object.jpg": {
        "items": [
            {
                "instrument_type": "unidentified_object",
                "likely_brand": "unknown",
                "material": "unknown",
                "condition_grade": "C",
                "visible_defects": ["Severe motion blur", "Insufficient contrast", "Unidentifiable silhouette"],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.28,
            }
        ],
        "notes": "Low confidence evaluation: image resolution is degraded with high motion blur. Unable to determine diagnostic instrument boundaries.",
    },
    "straight_elevator_grade_b.jpg": {
        "items": [
            {
                "instrument_type": "straight_elevator",
                "likely_brand": "GDC",
                "material": "stainless_steel",
                "condition_grade": "B",
                "visible_defects": ["Light handle scratches", "Clean blade"],
                "needs_sharpening": False,
                "is_single_use": False,
                "confidence": 0.90,
            }
        ],
        "notes": "GDC straight Coupland elevator #1. Sturdy pear-shaped handle, sharp working gouge blade, minor cosmetic scuffs.",
    },
}

# Write demo cache
cache_path = os.path.join(SAMPLES_DIR, "demo_cache.json")
with open(cache_path, "w") as f:
    json.dump(CACHE_DATA, f, indent=2)
print(f"Wrote demo cache with {len(CACHE_DATA)} entries to {cache_path}")


def create_sample_image(filename: str, title: str, kind: str):
    width, height = 640, 480
    bg_color = (225, 230, 235)  # Clinical sterile stainless steel / ice silver tray
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw sterile surgical tray border
    draw.rectangle([20, 20, width - 20, height - 20], outline=(180, 190, 200), width=4)
    draw.rectangle([28, 28, width - 28, height - 28], outline=(200, 210, 220), width=2)

    if kind == "mirror":
        # Handle
        draw.line([(120, 360), (420, 160)], fill=(120, 130, 140), width=14)
        draw.line([(120, 360), (420, 160)], fill=(200, 210, 220), width=8)
        # Mirror head
        draw.ellipse([400, 80, 520, 200], fill=(170, 180, 190), outline=(90, 100, 110), width=4)
        draw.ellipse([415, 95, 505, 185], fill=(235, 245, 255), outline=(130, 140, 150), width=2)
    elif kind == "curette":
        # Handle with knurling
        draw.line([(100, 380), (450, 130)], fill=(130, 135, 140), width=16)
        draw.line([(100, 380), (450, 130)], fill=(190, 195, 200), width=10)
        # Curved terminal shank & blade
        draw.arc([430, 80, 520, 170], start=180, end=350, fill=(90, 95, 100), width=6)
    elif kind == "scaler":
        # Handle
        draw.line([(100, 380), (450, 130)], fill=(110, 115, 120), width=14)
        # Triangular pointed tip with wear marks
        draw.polygon([(450, 130), (510, 90), (480, 140)], fill=(80, 85, 90))
        draw.point([(490, 110), (492, 112)], fill=(160, 60, 40))  # micro wear mark
    elif kind == "multi":
        # 3 instruments in tray
        # Mirror
        draw.line([(80, 160), (420, 160)], fill=(180, 185, 190), width=10)
        draw.ellipse([420, 120, 480, 200], fill=(230, 240, 250), outline=(100, 105, 110), width=3)
        # Probe
        draw.line([(80, 240), (440, 240)], fill=(175, 180, 185), width=8)
        draw.line([(440, 240), (470, 210)], fill=(100, 105, 110), width=4)
        # Tweezers
        draw.line([(80, 320), (400, 300)], fill=(170, 175, 180), width=8)
        draw.line([(80, 320), (400, 340)], fill=(170, 175, 180), width=8)
    elif kind == "single_use":
        # Plastic syringe body with red/orange cap (single use indicator)
        draw.rectangle([140, 210, 360, 270], fill=(240, 245, 250), outline=(150, 160, 170), width=3)
        draw.rectangle([360, 230, 420, 250], fill=(240, 120, 50))  # Orange hub
        draw.line([(420, 240), (520, 240)], fill=(190, 195, 200), width=2)  # Needle
        draw.line([(80, 240), (140, 240)], fill=(120, 130, 140), width=10)  # Plunger
    elif kind == "blurry":
        # Blurry indistinct smear
        draw.ellipse([180, 160, 460, 320], fill=(160, 170, 180))
        img = img.filter(ImageFilter.GaussianBlur(radius=22))
        draw = ImageDraw.Draw(img)
    elif kind == "elevator":
        # Pear shaped handle
        draw.ellipse([80, 200, 200, 280], fill=(160, 165, 170), outline=(100, 105, 110), width=4)
        # Thick shank & straight gouge
        draw.line([(190, 240), (440, 240)], fill=(180, 185, 190), width=16)
        draw.polygon([(440, 230), (510, 240), (440, 250)], fill=(140, 145, 150))

    # Add label text on sterile drape
    draw.text((40, 40), f"DentSloth Clinical Sample: {title}", fill=(58, 15, 52))

    # Add EXIF metadata to test EXIF stripping
    zeroth_ifd = {
        piexif.ImageIFD.Make: b"DentSloth Clinical Cam",
        piexif.ImageIFD.Model: b"SlothCam-X1",
        piexif.ImageIFD.Software: b"DentSloth v2.0",
    }
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b"N",
        piexif.GPSIFD.GPSLatitude: ((18, 1), (31, 1), (25, 1)),  # Pune coordinates
    }
    exif_dict = {"0th": zeroth_ifd, "GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)

    out_path = os.path.join(SAMPLES_DIR, filename)
    img.save(out_path, "JPEG", quality=92, exif=exif_bytes)
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")


# Generate each sample
samples = [
    ("mouth_mirror_grade_a.jpg", "Mouth Mirror #5 (Grade A)", "mirror"),
    ("gracey_curette_grade_b.jpg", "Gracey Curette 13/14 (Grade B)", "curette"),
    ("sickle_scaler_grade_c.jpg", "Sickle Scaler 204S (Grade C)", "scaler"),
    ("tray_instruments_multi.jpg", "Examination Tray Set (3 Instruments)", "multi"),
    ("disposable_needle_syringe.jpg", "Disposable Infiltration Syringe 27G", "single_use"),
    ("blurry_unknown_object.jpg", "Degraded / Out-of-Focus Object", "blurry"),
    ("straight_elevator_grade_b.jpg", "Straight Coupland Elevator #1", "elevator"),
]

for filename, title, kind in samples:
    create_sample_image(filename, title, kind)

print("All 7 sample images generated successfully.")
