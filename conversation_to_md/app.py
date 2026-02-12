"""
AI Chat Vault Builder — Streamlit UI

Full-featured interface for processing AI chat exports:
  - Upload ZIP files from ChatGPT, Claude, Gemini, Grok
  - Configure output options (grouping, truncation, filenames, etc.)
  - Progress feedback at every step
  - Preview conversations
  - Download complete vault as ZIP (Markdown + CSV + Excel)
"""

from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import streamlit as st

from conversation_to_md.core.pipeline import convert_zip_bytes_to_vault
from conversation_to_md.core.renderer import RenderOptions


def main() -> None:
    st.set_page_config(
        page_title="AI Chat Vault Builder",
        page_icon="\U0001f4da",
        layout="wide",
    )

    st.title("\U0001f4da AI Chat Vault Builder")
    st.caption(
        "Convert AI chat exports (ChatGPT, Claude, Gemini, Grok) into a clean "
        "Markdown vault with Excel/CSV metadata — ready for Obsidian, Logseq, or any PKM system."
    )

    # ---- Sidebar: Settings ----
    with st.sidebar:
        st.header("Settings")

        st.subheader("Output structure")
        output_structure = st.radio(
            "File layout",
            ["structured", "flat"],
            index=0,
            help="Structured groups files into subfolders; flat puts everything in one directory.",
        )

        group_by = st.selectbox(
            "Group conversations by",
            ["platform", "model", "month", "year"],
            index=0,
            help="How to organize subfolders (only used in structured mode).",
        )

        st.subheader("Markdown formatting")
        include_timestamps = st.checkbox("Include timestamps", value=True)
        include_system = st.checkbox("Include system messages", value=False)
        emoji_headers = st.checkbox("Emoji role headers", value=True)

        st.subheader("Filename style")
        filename_style = st.selectbox(
            "Filename format",
            ["date_title", "date_first_words", "id_only"],
            format_func=lambda x: {
                "date_title": "Date + Title slug",
                "date_first_words": "Date + First words",
                "id_only": "Date + Conversation ID",
            }[x],
        )

        st.subheader("Content handling")
        truncate_enabled = st.checkbox("Truncate long messages", value=False)
        truncate_length = 0
        if truncate_enabled:
            truncate_length = st.number_input(
                "Max characters per message",
                min_value=500,
                max_value=50000,
                value=8000,
                step=500,
            )

        st.subheader("Export options")
        include_csv = st.checkbox("Generate CSV export", value=True)
        include_excel = st.checkbox("Generate Excel export", value=True)
        include_combined_md = st.checkbox("Generate combined Markdown file", value=False,
                                          help="One huge .md file with all conversations. Can be very large.")

    # ---- Main area: Upload ----
    st.subheader("Upload your chat export")
    uploaded_files = st.file_uploader(
        "Drop one or more ZIP files here",
        type=["zip"],
        accept_multiple_files=True,
        help="Supported: ChatGPT, Claude, Gemini, and Grok export ZIPs.",
    )

    if not uploaded_files:
        st.info(
            "Upload a .zip export from ChatGPT, Claude, Gemini, or Grok to get started.\n\n"
            "**How to get your data:**\n"
            "- **ChatGPT**: Settings > Data controls > Export data\n"
            "- **Claude**: Settings > Account > Export data\n"
            "- **Gemini**: Google Takeout > Gemini Apps\n"
            "- **Grok**: X/Twitter data export"
        )
        return

    # ---- Process button ----
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        convert_btn = st.button("Build Vault", type="primary", use_container_width=True)
    with col_btn2:
        dry_run_btn = st.button("Dry Run (preview only)", use_container_width=True)

    if not convert_btn and not dry_run_btn:
        st.info(f"{len(uploaded_files)} file(s) uploaded. Click **Build Vault** to process.")
        return

    is_dry_run = dry_run_btn and not convert_btn

    # ---- Build options ----
    options = RenderOptions(
        include_timestamps=include_timestamps,
        include_system_messages=include_system,
        emoji_headers=emoji_headers,
        output_structure=output_structure,
        truncate_length=truncate_length,
        filename_style=filename_style,
        group_by=group_by,
    )

    # ---- Processing ----
    status_container = st.container()
    progress_bar = st.progress(0, text="Starting...")
    status_log: list[str] = []
    log_area = st.empty()

    def on_progress(msg: str) -> None:
        status_log.append(msg)
        # Show last 15 log lines
        display = "\n".join(status_log[-15:])
        log_area.code(display, language=None)

    output_dir = Path(tempfile.mkdtemp(prefix="vault_output_"))

    try:
        all_results = []
        total_conversations = []

        for file_idx, uploaded_file in enumerate(uploaded_files):
            file_label = uploaded_file.name
            on_progress(f"\n{'='*50}")
            on_progress(f"Processing file {file_idx + 1}/{len(uploaded_files)}: {file_label}")
            on_progress(f"{'='*50}")

            progress_bar.progress(
                (file_idx) / len(uploaded_files),
                text=f"Processing {file_label}..."
            )

            data = uploaded_file.read()
            on_progress(f"Read {len(data) / 1024 / 1024:.1f} MB")

            if is_dry_run:
                # Dry run: parse only, don't write files
                from conversation_to_md.core.detect import detect_source
                from conversation_to_md.core.pipeline import ADAPTERS
                from conversation_to_md.adapters import generic
                from conversation_to_md.utils.unzip import extract_zip_from_bytes
                import shutil as _shutil

                on_progress("DRY RUN: Parsing without writing files...")
                extracted_dir = extract_zip_from_bytes(data)
                try:
                    source = detect_source(extracted_dir)
                    on_progress(f"Detected source: {source}")
                    adapter = ADAPTERS.get(source, generic.parse)
                    conversations = adapter(extracted_dir, progress_callback=on_progress)
                    on_progress(f"Found {len(conversations)} conversation(s)")
                    total_conversations.extend(conversations)
                finally:
                    _shutil.rmtree(extracted_dir, ignore_errors=True)
            else:
                file_output_dir = output_dir if len(uploaded_files) == 1 else output_dir / f"import_{file_idx}"

                result = convert_zip_bytes_to_vault(
                    data=data,
                    output_dir=file_output_dir,
                    options=options,
                    include_csv=include_csv,
                    include_excel=include_excel,
                    include_combined_md=include_combined_md,
                    truncate_length=truncate_length,
                    progress_callback=on_progress,
                )
                all_results.append(result)
                convos = result.get("conversations", [])
                total_conversations.extend(convos)

                if result.get("errors"):
                    for err in result["errors"]:
                        on_progress(f"WARNING: {err}")

        progress_bar.progress(1.0, text="Complete!")
        on_progress(f"\nTotal: {len(total_conversations)} conversations processed")

        # ---- Display results ----
        if is_dry_run:
            _show_dry_run_results(total_conversations)
        else:
            _show_full_results(all_results, total_conversations, output_dir)

    except Exception as exc:
        st.error(f"Processing failed: {exc}")
        on_progress(f"FATAL ERROR: {exc}")
        import traceback
        on_progress(traceback.format_exc())
    finally:
        if is_dry_run:
            shutil.rmtree(output_dir, ignore_errors=True)


def _show_dry_run_results(conversations: list) -> None:
    """Display dry run results (parsing preview without file output)."""
    st.subheader("Dry Run Results")

    if not conversations:
        st.warning("No conversations found.")
        return

    from conversation_to_md.core.exporter import get_stats
    stats = get_stats(conversations)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Conversations", stats["total_conversations"])
    col2.metric("Messages", f"{stats['total_messages']:,}")
    col3.metric("Total Characters", f"{stats['total_characters']:,}")
    platforms = ", ".join(f"{k}: {v}" for k, v in stats["platforms"].items())
    col4.metric("Platforms", platforms)

    if stats.get("models"):
        st.subheader("Models found")
        for model, count in sorted(stats["models"].items(), key=lambda x: -x[1]):
            st.text(f"  {model}: {count} conversations")

    # Preview first few conversations
    st.subheader("Preview (first 5 conversations)")
    from conversation_to_md.core.renderer import RenderOptions, render_conversation
    preview_options = RenderOptions()
    for conv in conversations[:5]:
        with st.expander(f"{conv.title or 'Untitled'} ({conv.message_count} messages)"):
            md = render_conversation(conv, preview_options)
            st.markdown(f"```markdown\n{md[:3000]}\n```")


def _show_full_results(all_results: list, conversations: list, output_dir: Path) -> None:
    """Display full processing results with download buttons."""
    st.subheader("Results")

    if not conversations:
        st.warning("No conversations found in the uploaded file(s).")
        return

    from conversation_to_md.core.exporter import get_stats
    stats = get_stats(conversations)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Conversations", stats["total_conversations"])
    col2.metric("Messages", f"{stats['total_messages']:,}")
    col3.metric("Total Characters", f"{stats['total_characters']:,}")

    date_range = ""
    if stats.get("date_range_start") and stats.get("date_range_end"):
        date_range = f"{stats['date_range_start'].strftime('%Y-%m-%d')} to {stats['date_range_end'].strftime('%Y-%m-%d')}"
    col4.metric("Date Range", date_range or "N/A")

    # Platform & model breakdown
    if stats.get("platforms"):
        st.subheader("Platforms")
        for plat, count in stats["platforms"].items():
            st.text(f"  {plat}: {count} conversations")

    if stats.get("models"):
        st.subheader("Models")
        for model, count in sorted(stats["models"].items(), key=lambda x: -x[1]):
            st.text(f"  {model}: {count} conversations")

    # Errors
    all_errors = []
    for r in all_results:
        all_errors.extend(r.get("errors", []))
    if all_errors:
        with st.expander(f"Warnings / Errors ({len(all_errors)})"):
            for err in all_errors:
                st.warning(err)

    # Download buttons
    st.subheader("Downloads")

    # Full vault as ZIP
    zip_buffer = _zip_directory(output_dir)
    today = date.today().strftime("%Y-%m-%d")
    st.download_button(
        label=f"Download Complete Vault (ZIP)",
        data=zip_buffer,
        file_name=f"AI_Chat_Vault_{today}.zip",
        mime="application/zip",
        type="primary",
    )

    # Individual downloads for CSV/Excel if they exist
    col_dl1, col_dl2 = st.columns(2)
    for r in all_results:
        if r.get("csv_path") and r["csv_path"].exists():
            with col_dl1:
                csv_data = r["csv_path"].read_bytes()
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="All_Conversations.csv",
                    mime="text/csv",
                )
        if r.get("excel_path") and r["excel_path"].exists():
            with col_dl2:
                excel_data = r["excel_path"].read_bytes()
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name="metadata_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    # Preview conversations
    st.subheader("Preview")
    from conversation_to_md.core.renderer import RenderOptions, render_conversation

    preview_options = RenderOptions()
    num_preview = min(10, len(conversations))

    # Search / filter
    search_query = st.text_input("Filter conversations by title", "")
    filtered = conversations
    if search_query:
        filtered = [c for c in conversations if search_query.lower() in (c.title or "").lower()]
        st.text(f"Showing {len(filtered)} matching conversation(s)")

    for conv in filtered[:num_preview]:
        label = conv.title or "Untitled"
        date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "no date"
        model = conv.model or conv.metadata.get("model", "")
        with st.expander(f"{date_str} | {label} | {conv.message_count} msgs | {model}"):
            md = render_conversation(conv, preview_options)
            st.markdown(f"```markdown\n{md[:4000]}\n```")

    # Cleanup
    shutil.rmtree(output_dir, ignore_errors=True)


def _zip_directory(directory: Path) -> bytes:
    """Create an in-memory ZIP of a directory's contents."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(directory)
                zf.write(file_path, arcname)
    buffer.seek(0)
    return buffer.getvalue()


if __name__ == "__main__":
    main()
