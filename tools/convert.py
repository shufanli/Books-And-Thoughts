#!/usr/bin/env python3
"""
Book format converter — converts PDF/EPUB/MOBI/AZW3 to Markdown for Claude.

Usage:
  python3 convert.py book.pdf
  python3 convert.py book.epub -o ./output
  python3 convert.py ./my-books/          # batch convert a folder
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SUPPORTED = {".pdf", ".epub", ".mobi", ".azw3", ".azw"}


# ─── PDF ──────────────────────────────────────────────────────────────────────

def convert_pdf(src: Path, dest: Path) -> bool:
    try:
        import fitz  # pymupdf
    except ImportError:
        print("  [error] pymupdf not installed. Run: pip3 install pymupdf")
        return False

    doc = fitz.open(src)
    parts = []

    # Collect all font sizes to determine heading thresholds dynamically
    all_sizes = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["text"].strip():
                        all_sizes.append(span["size"])

    if not all_sizes:
        doc.close()
        dest.write_text("", encoding="utf-8")
        return True

    body_size = sorted(all_sizes)[len(all_sizes) // 2]  # median ≈ body text
    h2_threshold = body_size * 1.3
    h3_threshold = body_size * 1.15

    prev_text = ""
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            block_lines = []
            for line in block["lines"]:
                line_text = " ".join(
                    span["text"] for span in line["spans"]
                ).strip()
                if not line_text:
                    continue

                # Use size of first span for the whole line
                size = line["spans"][0]["size"] if line["spans"] else body_size

                if size >= h2_threshold and len(line_text) < 120:
                    block_lines.append(f"\n## {line_text}\n")
                elif size >= h3_threshold and len(line_text) < 120:
                    block_lines.append(f"\n### {line_text}\n")
                else:
                    block_lines.append(line_text)

            if block_lines:
                joined = "\n".join(block_lines)
                # Avoid duplicate consecutive blocks (common in scanned PDFs)
                if joined.strip() != prev_text.strip():
                    parts.append(joined)
                    prev_text = joined

        parts.append("")  # page break separator

    doc.close()
    dest.write_text("\n".join(parts), encoding="utf-8")
    return True


# ─── EPUB ─────────────────────────────────────────────────────────────────────

def convert_epub(src: Path, dest: Path) -> bool:
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup, Tag
    except ImportError:
        print("  [error] ebooklib/beautifulsoup4 not installed.")
        print("          Run: pip3 install ebooklib beautifulsoup4")
        return False

    book = epub.read_epub(str(src), options={"ignore_ncx": True})
    chapters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        md = _html_to_md(soup)
        if md.strip():
            chapters.append(md)

    dest.write_text("\n\n---\n\n".join(chapters), encoding="utf-8")
    return True


def _html_to_md(soup) -> str:
    from bs4 import NavigableString, Tag

    lines = []

    def walk(node):
        if isinstance(node, NavigableString):
            text = str(node).strip()
            if text:
                lines.append(text)
            return

        tag = node.name
        if tag in ("script", "style", "head"):
            return

        if tag == "h1":
            lines.append(f"\n# {node.get_text(strip=True)}\n")
        elif tag == "h2":
            lines.append(f"\n## {node.get_text(strip=True)}\n")
        elif tag == "h3":
            lines.append(f"\n### {node.get_text(strip=True)}\n")
        elif tag == "h4":
            lines.append(f"\n#### {node.get_text(strip=True)}\n")
        elif tag == "p":
            text = node.get_text(" ", strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif tag in ("ul", "ol"):
            for li in node.find_all("li", recursive=False):
                lines.append(f"- {li.get_text(' ', strip=True)}")
            lines.append("")
        elif tag == "blockquote":
            for line in node.get_text("\n", strip=True).splitlines():
                lines.append(f"> {line}")
            lines.append("")
        elif tag == "br":
            lines.append("")
        elif tag in ("div", "section", "article", "body", "html", "span"):
            for child in node.children:
                walk(child)
        # Images, tables etc. are skipped intentionally

    for child in soup.children:
        walk(child)

    # Collapse 3+ consecutive blank lines into 2
    text = "\n".join(lines)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


# ─── MOBI / AZW3 ──────────────────────────────────────────────────────────────

def convert_mobi_azw(src: Path, dest: Path) -> bool:
    if not shutil.which("ebook-convert"):
        print("  [error] Calibre not found.")
        print("          Install: brew install --cask calibre")
        print("          After install, reopen terminal and retry.")
        return False

    tmp_epub = src.with_suffix(".epub")
    try:
        result = subprocess.run(
            ["ebook-convert", str(src), str(tmp_epub)],
            capture_output=True,
            check=True,
        )
        ok = convert_epub(tmp_epub, dest)
    except subprocess.CalledProcessError as e:
        print(f"  [error] Calibre failed: {e.stderr.decode()[:200]}")
        ok = False
    finally:
        if tmp_epub.exists():
            tmp_epub.unlink()

    return ok


# ─── Entry point ──────────────────────────────────────────────────────────────

def convert_one(src: Path, out_dir: Path) -> bool:
    suffix = src.suffix.lower()
    if suffix not in SUPPORTED:
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / (src.stem + ".md")

    print(f"Converting  {src.name}")

    if suffix == ".pdf":
        ok = convert_pdf(src, dest)
    elif suffix == ".epub":
        ok = convert_epub(src, dest)
    else:
        ok = convert_mobi_azw(src, dest)

    if ok:
        kb = dest.stat().st_size // 1024
        print(f"  → {dest}  ({kb} KB)")
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Convert books (PDF/EPUB/MOBI/AZW3) to Markdown for Claude."
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Book files or a directory containing books.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: same folder as each input file).",
    )
    args = parser.parse_args()

    # Collect files
    files: list[Path] = []
    for raw in args.input:
        p = Path(raw).expanduser()
        if p.is_dir():
            for ext in SUPPORTED:
                files.extend(sorted(p.glob(f"**/*{ext}")))
        elif p.exists():
            files.append(p)
        else:
            print(f"[warn] Not found: {raw}")

    if not files:
        print("No supported files found.")
        sys.exit(1)

    print(f"Found {len(files)} file(s).\n")
    ok = sum(
        convert_one(f, args.output if args.output else f.parent) for f in files
    )
    print(f"\nDone: {ok}/{len(files)} converted successfully.")
    if ok < len(files):
        sys.exit(1)


if __name__ == "__main__":
    main()
