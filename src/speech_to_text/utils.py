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


def validate_audio(content_type: str | None, size_bytes: int) -> str:
    """
    Validate MIME type and file size.
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

    if size_bytes > MAX_FILE_SIZE_BYTES:
        mb = size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({mb:.1f} MB). Maximum allowed size is 25 MB.",
        )

    return ALLOWED_MIME_TYPES[normalised]
