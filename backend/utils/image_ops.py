"""Image preprocessing, sanitization, and EXIF stripping for DentSloth."""
import io
import logging
from typing import Tuple
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""
    pass


def validate_and_strip_exif(
    file_bytes: bytes,
    content_type: str | None = None,
    max_bytes: int = MAX_FILE_BYTES,
) -> Tuple[bytes, str]:
    """Validate image format, size, and strip all EXIF/metadata.

    Returns:
        Tuple of (clean_image_bytes, mime_type)
    """
    if len(file_bytes) > max_bytes:
        raise ImageValidationError(
            f"Image file size ({len(file_bytes) / 1024 / 1024:.2f} MB) exceeds maximum allowed limit of {max_bytes / 1024 / 1024:.1f} MB."
        )

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            format_name = img.format
            if format_name not in ("JPEG", "PNG", "WEBP"):
                raise ImageValidationError(
                    f"Unsupported image format: '{format_name}'. Allowed formats: JPEG, PNG, WEBP."
                )

            # Strip EXIF and any embedded location/camera metadata by recreating fresh image data
            # Convert RGBA/Palette to RGB if saving as JPEG
            if img.mode in ("RGBA", "LA", "P"):
                # Preserve transparency if saving PNG or WebP, otherwise convert to RGB
                if format_name == "PNG":
                    clean_img = img.convert("RGBA")
                else:
                    clean_img = Image.new("RGB", img.size, (255, 255, 255))
                    clean_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            else:
                clean_img = img.convert("RGB")

            output_buf = io.BytesIO()
            # Save WITHOUT any info/exif parameters to ensure EXIF is completely stripped
            save_format = "JPEG" if format_name == "JPEG" else format_name
            clean_img.save(output_buf, format=save_format, quality=90, optimize=True)
            clean_bytes = output_buf.getvalue()

            mime = "image/jpeg" if save_format == "JPEG" else f"image/{save_format.lower()}"
            return clean_bytes, mime

    except Exception as e:
        if isinstance(e, ImageValidationError):
            raise
        logger.warning(f"Failed to process image: {e}")
        raise ImageValidationError(f"Invalid or corrupted image file: {str(e)}") from e
