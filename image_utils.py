"""Photo processing and private owner-clue helpers."""

from __future__ import annotations

import hashlib
import hmac
import io
import secrets
from pathlib import Path
from typing import Any

PBKDF2_ROUNDS = 310_000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


def make_secret_hash(secret: str) -> dict[str, str]:
    """Store a salted slow hash; never store the original private clue."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.strip().encode("utf-8"), salt, PBKDF2_ROUNDS)
    return {"verification_salt": salt.hex(), "verification_hash": digest.hex()}


def check_secret(secret: str, salt_hex: str, expected_hash: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", secret.strip().encode("utf-8"), salt, PBKDF2_ROUNDS
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected_hash)


def describe_image(image: Any) -> dict[str, Any]:
    # Pillow is imported only for upload handling; text evaluation can run without it.
    from PIL import Image, ImageOps

    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((512, 512), Image.Resampling.LANCZOS)
    pixels = list(image.convert("L").resize((8, 8), Image.Resampling.LANCZOS).getdata())
    average = sum(pixels) / len(pixels)
    bit_string = "".join("1" if value >= average else "0" for value in pixels)
    image_hash = f"{int(bit_string, 2):016x}"

    # Eight bins for each RGB channel retain a simple color profile.
    rgb_histograms = image.histogram()
    histogram: list[float] = []
    for channel in range(3):
        values = rgb_histograms[channel * 256 : (channel + 1) * 256]
        bins = [sum(values[index : index + 32]) for index in range(0, 256, 32)]
        total = sum(bins) or 1
        histogram.extend(value / total for value in bins)
    return {"image_hash": image_hash, "color_histogram": histogram}


def save_uploaded_image(uploaded_file: Any, destination: Path, relative_path: str) -> dict[str, Any]:
    """Validate, rotate, resize and re-encode a photo to remove EXIF metadata."""
    from PIL import Image, ImageOps

    content = uploaded_file.getvalue()
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("Photo must be 5 MB or smaller.")
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("Photo dimensions are too large.")
            cleaned = ImageOps.exif_transpose(source).convert("RGB")
            cleaned.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            destination.parent.mkdir(parents=True, exist_ok=True)
            cleaned.save(destination, format="JPEG", quality=88, optimize=True)
            descriptor = describe_image(cleaned)
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError("Please upload a valid JPG or PNG item photo.") from error
    descriptor["image_path"] = relative_path.replace("\\", "/")
    return descriptor


def image_similarity(first: dict[str, Any], second: dict[str, Any]) -> float | None:
    """Compare compact visual descriptors; requires photos on both reports."""
    first_hash = first.get("image_hash")
    second_hash = second.get("image_hash")
    first_hist = first.get("color_histogram")
    second_hist = second.get("color_histogram")
    if not first_hash or not second_hash or not first_hist or not second_hist:
        return None
    try:
        hash_a, hash_b = int(first_hash, 16), int(second_hash, 16)
        hash_score = 1.0 - ((hash_a ^ hash_b).bit_count() / 64.0)
        dot = sum(float(a) * float(b) for a, b in zip(first_hist, second_hist))
        norm_a = sum(float(a) ** 2 for a in first_hist) ** 0.5
        norm_b = sum(float(b) ** 2 for b in second_hist) ** 0.5
        color_score = dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
        return max(0.0, min(1.0, 0.5 * hash_score + 0.5 * color_score))
    except (TypeError, ValueError, ZeroDivisionError):
        return None
