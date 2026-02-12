"""
Main conversion pipeline.

Orchestrates: ZIP extract -> detect source -> adapter parse -> render / export.
This is the single entry point for the entire conversion process.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from conversation_to_md.adapters import chatgpt, claude, gemini, generic, grok
from conversation_to_md.core.detect import detect_source
from conversation_to_md.core.models import Conversation
from conversation_to_md.core.renderer import RenderOptions, write_conversations
from conversation_to_md.core.vault import build_vault
from conversation_to_md.utils.unzip import extract_zip, extract_zip_from_bytes

# Adapter registry: source key -> parse function
ADAPTERS = {
    "chatgpt": chatgpt.parse,
    "claude": claude.parse,
    "gemini": gemini.parse,
    "grok": grok.parse,
    "unknown": generic.parse,
}


def convert_zip(
    zip_path: Path,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Path], str]:
    """
    Full pipeline: ZIP file -> Markdown files.

    Args:
        zip_path: Path to the ZIP file to convert
        output_dir: Directory where .md files will be written
        options: Rendering options (defaults to sensible defaults)
        progress_callback: Optional function called with status messages

    Returns:
        Tuple of (list of written file paths, detected source name)
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip(zip_path)

    try:
        return _process_extracted(extracted_dir, output_dir, options, _log)
    finally:
        shutil.rmtree(extracted_dir, ignore_errors=True)


def convert_zip_bytes(
    data: bytes,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Path], str]:
    """
    Full pipeline from raw bytes (e.g. Streamlit upload).

    Same as convert_zip but accepts bytes instead of a file path.
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip_from_bytes(data)

    try:
        return _process_extracted(extracted_dir, output_dir, options, _log)
    finally:
        shutil.rmtree(extracted_dir, ignore_errors=True)


def convert_zip_bytes_to_vault(
    data: bytes,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    include_csv: bool = True,
    include_excel: bool = True,
    include_combined_md: bool = False,
    truncate_length: int = 0,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Full vault pipeline from raw bytes.

    Extracts ZIP -> detects source -> parses -> builds complete vault structure
    with Markdown files, CSV, Excel, and optional combined Markdown.

    Returns a dict with: md_files, csv_path, excel_path, combined_md_path, stats, errors, source
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip_from_bytes(data)

    try:
        _log("Detecting source provider...")
        source = detect_source(extracted_dir)
        _log(f"Detected source: {source}")

        adapter = ADAPTERS.get(source, generic.parse)
        _log(f"Parsing conversations with {source} adapter...")
        conversations: List[Conversation] = adapter(extracted_dir, progress_callback=progress_callback)
        _log(f"Found {len(conversations)} conversation(s)")

        if not conversations:
            return {
                "md_files": [],
                "csv_path": None,
                "excel_path": None,
                "combined_md_path": None,
                "stats": {},
                "errors": [],
                "source": source,
            }

        result = build_vault(
            conversations=conversations,
            output_dir=output_dir,
            options=options,
            include_csv=include_csv,
            include_excel=include_excel,
            include_combined_md=include_combined_md,
            truncate_length=truncate_length,
            progress_callback=progress_callback,
        )
        result["source"] = source
        result["conversations"] = conversations
        return result
    finally:
        shutil.rmtree(extracted_dir, ignore_errors=True)


def convert_zip_to_vault(
    zip_path: Path,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    include_csv: bool = True,
    include_excel: bool = True,
    include_combined_md: bool = False,
    truncate_length: int = 0,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Full vault pipeline from a ZIP file path.
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip(zip_path)

    try:
        _log("Detecting source provider...")
        source = detect_source(extracted_dir)
        _log(f"Detected source: {source}")

        adapter = ADAPTERS.get(source, generic.parse)
        _log(f"Parsing conversations with {source} adapter...")
        conversations: List[Conversation] = adapter(extracted_dir, progress_callback=progress_callback)
        _log(f"Found {len(conversations)} conversation(s)")

        if not conversations:
            return {
                "md_files": [],
                "csv_path": None,
                "excel_path": None,
                "combined_md_path": None,
                "stats": {},
                "errors": [],
                "source": source,
            }

        result = build_vault(
            conversations=conversations,
            output_dir=output_dir,
            options=options,
            include_csv=include_csv,
            include_excel=include_excel,
            include_combined_md=include_combined_md,
            truncate_length=truncate_length,
            progress_callback=progress_callback,
        )
        result["source"] = source
        result["conversations"] = conversations
        return result
    finally:
        shutil.rmtree(extracted_dir, ignore_errors=True)


def _process_extracted(
    extracted_dir: Path,
    output_dir: Path,
    options: RenderOptions,
    log: Callable[[str], None],
) -> Tuple[List[Path], str]:
    """Process an already-extracted directory through detection, parsing, rendering."""
    log("Detecting source provider...")
    source = detect_source(extracted_dir)
    log(f"Detected source: {source}")

    adapter = ADAPTERS.get(source, generic.parse)
    log(f"Parsing conversations with {source} adapter...")
    conversations: List[Conversation] = adapter(extracted_dir, progress_callback=log)
    log(f"Found {len(conversations)} conversation(s)")

    if not conversations:
        return [], source

    log("Rendering Markdown files...")
    written = write_conversations(conversations, output_dir, options)
    log(f"Wrote {len(written)} Markdown file(s)")

    return written, source
