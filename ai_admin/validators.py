"""Input, path, format, and content validators for AI Admin."""

import os
import re
from typing import Optional, Tuple

_UUID_OR_HEX_RE = re.compile(r"^[a-zA-Z0-9_\-]{8,64}$")
_CANDIDATE_ID_RE = re.compile(r"^cand_[a-f0-9]{16,32}$")
_LANG_CODE_RE = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?$")

_VALID_IMAGE_TYPES = {
    "primary", "backdrop", "logo", "thumb", "banner", "art", "disc", "clearlogo"
}

# Image Magic Bytes
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_WEBP_RIFF = b"RIFF"
_WEBP_MAGIC = b"WEBP"

# Subtitle timestamp regex
_SRT_TIMESTAMP_RE = re.compile(
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}"
)


def validate_item_id(item_id: str) -> bool:
    """Validate Jellyfin item ID format."""
    if not item_id or not isinstance(item_id, str):
        return False
    return bool(_UUID_OR_HEX_RE.match(item_id.strip()))


def validate_candidate_id(cand_id: str) -> bool:
    """Validate server-issued opaque candidate ID format."""
    if not cand_id or not isinstance(cand_id, str):
        return False
    return bool(_CANDIDATE_ID_RE.match(cand_id.strip()))


def validate_language_code(lang: str) -> bool:
    """Validate ISO-639 language code format."""
    if not lang or not isinstance(lang, str):
        return False
    return bool(_LANG_CODE_RE.match(lang.strip().lower()))


def validate_image_type(img_type: str) -> bool:
    """Validate requested Jellyfin artwork type."""
    if not img_type or not isinstance(img_type, str):
        return False
    return img_type.strip().lower() in _VALID_IMAGE_TYPES


def validate_image_bytes(data: bytes, max_bytes: int = 15 * 1024 * 1024) -> Tuple[bool, str]:
    """Validate raw image payload for size and magic bytes header."""
    if not data or not isinstance(data, (bytes, bytearray)):
        return False, "Empty or invalid image data."

    if len(data) > max_bytes:
        return False, f"Image size exceeds maximum limit ({len(data)} > {max_bytes} bytes)."

    if len(data) < 16:
        return False, "Image data too small to be valid."

    # Check magic bytes
    if data.startswith(_JPEG_MAGIC):
        return True, "image/jpeg"
    if data.startswith(_PNG_MAGIC):
        return True, "image/png"
    if data.startswith(_WEBP_RIFF) and len(data) >= 12 and data[8:12] == _WEBP_MAGIC:
        return True, "image/webp"

    return False, "Unsupported image format; only JPEG, PNG, and WebP are allowed."


def validate_subtitle_bytes(data: bytes, max_bytes: int = 3 * 1024 * 1024) -> Tuple[bool, str]:
    """Validate raw subtitle bytes: size, not HTML, not binary, valid timestamp format."""
    if not data or not isinstance(data, (bytes, bytearray)):
        return False, "Empty subtitle content."

    if len(data) > max_bytes:
        return False, f"Subtitle size exceeds limit ({len(data)} > {max_bytes} bytes)."

    # Reject null bytes (binary files)
    if b"\x00" in data[:1024]:
        return False, "Binary file detected; expected text subtitle."

    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return False, "Failed to decode subtitle text."

    # Reject HTML error pages
    first_chunk = text[:300].lower()
    if "<html" in first_chunk or "<!doctype html" in first_chunk or "<body" in first_chunk:
        return False, "HTML error page detected instead of subtitle file."

    # Verify timestamp format
    if not _SRT_TIMESTAMP_RE.search(text):
        return False, "Invalid subtitle: standard timestamp sequence not found."

    return True, "valid_subtitle"


def safe_join_path(root_dir: str, *segments: str) -> Tuple[bool, str]:
    """Safely join filesystem path segments within an approved root directory.

    Rejects directory traversal (../), absolute escapes, and symlink targets outside root.
    """
    try:
        abs_root = os.path.abspath(root_dir)
        target = os.path.abspath(os.path.join(abs_root, *segments))
        if target == abs_root or target.startswith(abs_root + os.sep):
            return True, target
        return False, "Path traversal attempt detected."
    except Exception as e:
        return False, f"Invalid path resolution: {e}"
