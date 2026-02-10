"""
Vault builder: creates the complete output folder structure.

Produces the desired vault layout:
    My_AI_Chat_Vault/
    +-- Conversations_by_Model/   (or by Platform/Month/Year)
    |   +-- ChatGPT/
    |   |   +-- 2025-01-15_conversation-title_0001.md
    |   +-- Claude/
    |   +-- Grok/
    +-- All_Chats_Combined/
    |   +-- All_Conversations.csv
    +-- metadata_export.xlsx
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from conversation_to_md.core.exporter import export_csv, export_excel, get_stats
from conversation_to_md.core.models import Conversation
from conversation_to_md.core.renderer import RenderOptions, render_conversation, write_conversations


def build_vault(
    conversations: List[Conversation],
    output_dir: Path,
    options: RenderOptions,
    include_csv: bool = True,
    include_excel: bool = True,
    include_combined_md: bool = False,
    truncate_length: int = 0,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Build the complete vault folder structure.

    Args:
        conversations: Parsed conversation objects.
        output_dir: Root output directory for the vault.
        options: Rendering options for Markdown files.
        include_csv: Whether to generate CSV export.
        include_excel: Whether to generate Excel export.
        include_combined_md: Whether to generate a single combined Markdown file.
        truncate_length: Truncation length for Excel/CSV content (0 = no truncation).
        progress_callback: Optional function for status messages.

    Returns:
        Dict with keys: md_files, csv_path, excel_path, combined_md_path, stats
    """
    log = progress_callback or (lambda _: None)
    result = {
        "md_files": [],
        "csv_path": None,
        "excel_path": None,
        "combined_md_path": None,
        "stats": {},
        "errors": [],
    }

    if not conversations:
        log("No conversations to process.")
        return result

    # --- Statistics ---
    log("Computing statistics...")
    result["stats"] = get_stats(conversations)

    # --- Markdown files (one per conversation) ---
    conversations_dir = output_dir / "Conversations"
    log(f"Writing {len(conversations)} Markdown files...")

    written = []
    for idx, conv in enumerate(conversations):
        try:
            md_text = render_conversation(conv, options)
            filename = _vault_filename(conv, idx, options)

            if options.output_structure == "flat":
                folder = conversations_dir
            else:
                folder_name = _get_vault_group(conv, options)
                folder = conversations_dir / folder_name

            folder.mkdir(parents=True, exist_ok=True)
            path = folder / filename
            path.write_text(md_text, encoding="utf-8")
            written.append(path)
        except Exception as exc:
            error_msg = f"Error writing conversation '{conv.title}' (id={conv.id}): {exc}"
            log(error_msg)
            result["errors"].append(error_msg)

        if (idx + 1) % 25 == 0:
            log(f"  Written {idx + 1}/{len(conversations)} Markdown files...")

    result["md_files"] = written
    log(f"Wrote {len(written)} Markdown file(s)")

    # --- CSV export ---
    if include_csv:
        log("Creating CSV export...")
        combined_dir = output_dir / "All_Chats_Combined"
        combined_dir.mkdir(parents=True, exist_ok=True)
        csv_path = combined_dir / "All_Conversations.csv"
        try:
            export_csv(conversations, csv_path, truncate_length)
            result["csv_path"] = csv_path
            log(f"CSV export saved: {csv_path.name}")
        except Exception as exc:
            error_msg = f"CSV export error: {exc}"
            log(error_msg)
            result["errors"].append(error_msg)

    # --- Excel export ---
    if include_excel:
        log("Creating Excel export...")
        excel_path = output_dir / "metadata_export.xlsx"
        try:
            export_excel(conversations, excel_path, truncate_length)
            result["excel_path"] = excel_path
            log(f"Excel export saved: {excel_path.name}")
        except Exception as exc:
            error_msg = f"Excel export error: {exc}"
            log(error_msg)
            result["errors"].append(error_msg)

    # --- Combined Markdown (optional) ---
    if include_combined_md:
        log("Creating combined Markdown file...")
        combined_dir = output_dir / "All_Chats_Combined"
        combined_dir.mkdir(parents=True, exist_ok=True)
        combined_path = combined_dir / "All_Conversations.md"
        try:
            with open(combined_path, "w", encoding="utf-8") as fh:
                for conv in conversations:
                    md_text = render_conversation(conv, options)
                    fh.write(md_text)
                    fh.write("\n\n---\n\n")
            result["combined_md_path"] = combined_path
            log(f"Combined Markdown saved: {combined_path.name}")
        except Exception as exc:
            error_msg = f"Combined Markdown error: {exc}"
            log(error_msg)
            result["errors"].append(error_msg)

    log("Vault build complete!")
    return result


def _get_vault_group(conv: Conversation, options: RenderOptions) -> str:
    """Determine vault subfolder for a conversation."""
    from slugify import slugify

    if options.group_by == "model":
        model = conv.model or conv.metadata.get("model", "unknown")
        return slugify(model, lowercase=False) if model else "unknown_model"
    elif options.group_by == "month":
        if conv.created_at:
            return conv.created_at.strftime("%Y-%m")
        return "no_date"
    elif options.group_by == "year":
        if conv.created_at:
            return conv.created_at.strftime("%Y")
        return "no_date"
    else:
        return conv.platform_display


def _vault_filename(conv: Conversation, index: int, options: RenderOptions) -> str:
    """Generate vault-friendly filename."""
    from slugify import slugify

    date_prefix = ""
    if conv.created_at:
        date_prefix = conv.created_at.strftime("%Y-%m-%d") + "_"

    if options.filename_style == "id_only":
        return f"{date_prefix}{conv.id[:40]}_{index:04d}.md"
    elif options.filename_style == "date_first_words":
        first_words = ""
        first_msg = conv.first_user_message
        if first_msg:
            words = first_msg.split()[:6]
            first_words = slugify(" ".join(words), max_length=50)
        if not first_words:
            first_words = slugify(conv.title or "untitled", max_length=50)
        return f"{date_prefix}{first_words}_{index:04d}.md"
    else:
        title_slug = slugify(conv.title or "untitled", max_length=80)
        if not title_slug:
            title_slug = "untitled"
        return f"{date_prefix}{title_slug}_{index:04d}.md"
