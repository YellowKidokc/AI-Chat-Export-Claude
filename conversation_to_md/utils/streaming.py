"""
Streaming JSON parser for large files.

Uses ijson to iterate over JSON arrays without loading the entire file
into memory. Falls back to standard json.load for small files or when
ijson encounters issues.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Iterator, Optional

import ijson

# Files above this threshold (bytes) use streaming parsing.
STREAMING_THRESHOLD = 50 * 1024 * 1024  # 50 MB


def iter_json_array(
    filepath: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Iterator[dict]:
    """
    Yield individual objects from a top-level JSON array.

    For files larger than STREAMING_THRESHOLD, uses ijson streaming parser
    to avoid loading everything into memory. Smaller files use standard
    json.load for speed.

    Args:
        filepath: Path to the JSON file.
        progress_callback: Optional function for status messages.

    Yields:
        Individual dict objects from the JSON array.
    """
    file_size = os.path.getsize(filepath)
    log = progress_callback or (lambda _: None)

    if file_size > STREAMING_THRESHOLD:
        log(f"Large file detected ({file_size / 1024 / 1024:.0f} MB), using streaming parser...")
        yield from _stream_parse(filepath, log)
    else:
        log("Loading JSON file...")
        yield from _standard_parse(filepath, log)


def _stream_parse(
    filepath: Path,
    log: Callable[[str], None],
) -> Iterator[dict]:
    """Use ijson to stream-parse a JSON array of objects."""
    try:
        with open(filepath, "rb") as fh:
            # ijson.items yields each top-level array element
            parser = ijson.items(fh, "item")
            for obj in parser:
                if isinstance(obj, dict):
                    yield obj
    except (ijson.JSONError, Exception) as exc:
        log(f"Streaming parse error: {exc}. Falling back to standard parser.")
        yield from _standard_parse(filepath, log)


def _standard_parse(
    filepath: Path,
    log: Callable[[str], None],
) -> Iterator[dict]:
    """Standard json.load — works for all valid JSON, but loads into memory."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        log(f"JSON parse error: {exc}")
        return

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        yield data
