"""
CLI entry point for conversation-to-markdown conversion.

Usage:
    python -m conversation_to_md.cli input.zip [--output ./output] [--flat] [--no-timestamps] [--no-emoji] [--system]
    python -m conversation_to_md.cli input.zip --vault [--csv] [--excel] [--group-by model]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from conversation_to_md.core.pipeline import convert_zip, convert_zip_to_vault
from conversation_to_md.core.renderer import RenderOptions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert AI chat export ZIPs to Markdown files, CSV, and Excel."
    )
    parser.add_argument("input", type=Path, help="Path to the ZIP file to convert")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("./output"),
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--flat", action="store_true",
        help="Flat output (no subfolders)"
    )
    parser.add_argument(
        "--no-timestamps", action="store_true",
        help="Omit timestamps from output"
    )
    parser.add_argument(
        "--no-emoji", action="store_true",
        help="Omit emoji from role headers"
    )
    parser.add_argument(
        "--system", action="store_true",
        help="Include system messages in output"
    )
    parser.add_argument(
        "--vault", action="store_true",
        help="Build a complete vault with CSV/Excel exports"
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="Generate CSV export (requires --vault)"
    )
    parser.add_argument(
        "--excel", action="store_true",
        help="Generate Excel export (requires --vault)"
    )
    parser.add_argument(
        "--combined-md", action="store_true",
        help="Generate a single combined Markdown file (requires --vault)"
    )
    parser.add_argument(
        "--group-by", choices=["platform", "model", "month", "year"],
        default="platform",
        help="How to group conversations into subfolders (default: platform)"
    )
    parser.add_argument(
        "--filename-style", choices=["date_title", "date_first_words", "id_only"],
        default="date_title",
        help="Filename format (default: date_title)"
    )
    parser.add_argument(
        "--truncate", type=int, default=0,
        help="Truncate messages longer than N characters (0 = no truncation)"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    options = RenderOptions(
        include_timestamps=not args.no_timestamps,
        include_system_messages=args.system,
        emoji_headers=not args.no_emoji,
        output_structure="flat" if args.flat else "structured",
        truncate_length=args.truncate,
        filename_style=args.filename_style,
        group_by=args.group_by,
    )

    def on_progress(msg: str) -> None:
        print(msg)

    if args.vault:
        # Full vault build
        include_csv = args.csv
        include_excel = args.excel
        # If --vault but neither --csv nor --excel, enable both by default
        if not include_csv and not include_excel:
            include_csv = True
            include_excel = True

        result = convert_zip_to_vault(
            zip_path=args.input,
            output_dir=args.output,
            options=options,
            include_csv=include_csv,
            include_excel=include_excel,
            include_combined_md=args.combined_md,
            truncate_length=args.truncate,
            progress_callback=on_progress,
        )

        md_files = result.get("md_files", [])
        stats = result.get("stats", {})
        errors = result.get("errors", [])

        if not md_files:
            print("No conversations found.", file=sys.stderr)
            sys.exit(1)

        print(f"\nVault built successfully!")
        print(f"  Conversations: {stats.get('total_conversations', 0)}")
        print(f"  Messages: {stats.get('total_messages', 0):,}")
        print(f"  Markdown files: {len(md_files)}")
        if result.get("csv_path"):
            print(f"  CSV: {result['csv_path']}")
        if result.get("excel_path"):
            print(f"  Excel: {result['excel_path']}")
        if errors:
            print(f"\n  Warnings: {len(errors)}")
            for err in errors:
                print(f"    - {err}")
        print(f"\nOutput: {args.output}/")
    else:
        # Simple markdown-only conversion
        written, source = convert_zip(args.input, args.output, options, on_progress)

        if not written:
            print("No conversations found.", file=sys.stderr)
            sys.exit(1)

        print(f"\nDone. {len(written)} file(s) written to {args.output}/")


if __name__ == "__main__":
    main()
