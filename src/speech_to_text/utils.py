from fastapi import HTTPException

# Supported MIME types and their canonical form for the Content-Type header
ALLOWED_MIME_TYPES: dict[str, str] = {
    "audio/wav":        "audio/wav",
    "audio/x-wav":      "audio/wav",
    "audio/wave":       "audio/wav",
    "audio/mpeg":       "audio/mpeg",
    "audio/mp3":        "audio/mpeg",
    "audio/mp4":        "audio/mp4",
    "audio/x-m4a":      "audio/mp4",
    "audio/m4a":        "audio/mp4",
    "audio/webm":       "audio/webm",
    "audio/ogg":        "audio/ogg",
    "audio/flac":       "audio/flac",
    "audio/x-flac":     "audio/flac",
}

# 25 MB — enough for ~13 min of 16kHz/16-bit mono WAV
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


def _sniff_audio_format(data: bytes) -> str | None:
    """Return canonical MIME type from file magic bytes, or None if unrecognized."""
    if len(data) < 4:
        return None

    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WAVE":
        return "audio/wav"

    if data[:4] == b"fLaC":
        return "audio/flac"

    if data[:4] == b"OggS":
        return "audio/ogg"

    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "audio/webm"

    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "audio/mp4"

    if data[:3] == b"ID3":
        return "audio/mpeg"

    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "audio/mpeg"

    return None


def validate_audio(content_type: str | None, data: bytes) -> str:
    """
    Validate MIME type, file size, and magic-byte content.
    Returns the canonical MIME type string to use as Content-Type.
    Raises HTTPException (415 / 413) on failure.
    """
    normalised = (content_type or "").lower().split(";")[0].strip()

    if normalised not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported audio format '{content_type}'. "
                f"Accepted: {', '.join(sorted(set(ALLOWED_MIME_TYPES.values())))}"
            ),
        )

    size_bytes = len(data)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        mb = size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({mb:.1f} MB). Maximum allowed size is 25 MB.",
        )

    detected = _sniff_audio_format(data)
    if detected is None:
        raise HTTPException(
            status_code=415,
            detail="File content is not a recognized audio format.",
        )

    canonical = ALLOWED_MIME_TYPES[normalised]
    if detected != canonical:
        raise HTTPException(
            status_code=415,
            detail=(
                f"File content ({detected}) does not match "
                f"declared type ({canonical})."
            ),
        )

    return canonical
