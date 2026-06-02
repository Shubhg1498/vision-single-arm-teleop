#!/usr/bin/env python3
"""Convert docs/version_1.md to docs/version 1.pdf using Chrome headless."""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "version_1.md"
PDF_PATH = ROOT / "docs" / "version 1.pdf"
HTML_PATH = ROOT / "docs" / "version_1.html"
CHROME = "/usr/bin/google-chrome"


def md_to_html(md_text: str) -> str:
    """Minimal markdown-to-HTML converter for this guide."""
    lines = md_text.splitlines()
    out: list[str] = []
    in_code = False
    in_table = False
    code_lang = ""
    table_rows: list[str] = []

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            return
        out.append('<table>')
        for i, row in enumerate(table_rows):
            cells = [c.strip() for c in row.strip().strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            out.append('<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells) + '</tr>')
            if i == 0 and len(table_rows) > 1 and all(set(r.strip().strip('|').replace('-', '').replace('|', '').strip()) <= {''} for r in table_rows[1:2]):
                pass
        out.append('</table>')
        table_rows = []
        in_table = False

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith('```'):
            if not in_code:
                flush_table()
                in_code = True
                code_lang = line[3:].strip()
                out.append(f'<pre><code class="{html.escape(code_lang)}">')
            else:
                in_code = False
                out.append('</code></pre>')
            i += 1
            continue

        if in_code:
            out.append(html.escape(line))
            i += 1
            continue

        if line.strip().startswith('|'):
            in_table = True
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i + 1].strip()):
                table_rows.append(line)
                i += 2
                continue
            table_rows.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        if line.startswith('# '):
            out.append(f'<h1>{inline(line[2:])}</h1>')
        elif line.startswith('## '):
            out.append(f'<h2>{inline(line[3:])}</h2>')
        elif line.startswith('### '):
            out.append(f'<h3>{inline(line[4:])}</h3>')
        elif line.strip() == '---':
            out.append('<hr>')
        elif line.strip() == '':
            out.append('')
        elif line.startswith('- '):
            out.append(f'<li>{inline(line[2:])}</li>')
        else:
            out.append(f'<p>{inline(line)}</p>')
        i += 1

    if in_table:
        flush_table()
    if in_code:
        out.append('</code></pre>')

    body = '\n'.join(out)
    body = re.sub(r'(<li>.*?</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', body, flags=re.DOTALL)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Vision Dual-Arm Teleoperation — Version 1</title>
<style>
  @page {{ margin: 2cm; }}
  body {{
    font-family: "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #1a1a1a;
    max-width: 100%;
    margin: 0;
    padding: 0;
  }}
  h1 {{ font-size: 22pt; border-bottom: 2px solid #333; padding-bottom: 8px; margin-top: 0; }}
  h2 {{ font-size: 16pt; margin-top: 24px; color: #222; page-break-after: avoid; }}
  h3 {{ font-size: 13pt; margin-top: 18px; page-break-after: avoid; }}
  pre {{
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px 12px;
    font-size: 9pt;
    line-height: 1.35;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    page-break-inside: avoid;
  }}
  code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9.5pt;
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
  }}
  pre code {{ background: none; padding: 0; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 10pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
  }}
  th {{ background: #e8e8e8; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin: 20px 0; }}
  ul {{ margin: 8px 0; padding-left: 24px; }}
  li {{ margin: 4px 0; }}
  p {{ margin: 8px 0; }}
  strong {{ color: #111; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> int:
    if not MD_PATH.exists():
        print(f"Missing source file: {MD_PATH}", file=sys.stderr)
        return 1

    md_text = MD_PATH.read_text(encoding="utf-8")
    html_text = md_to_html(md_text)
    HTML_PATH.write_text(html_text, encoding="utf-8")

    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={PDF_PATH}",
        HTML_PATH.as_uri(),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode

    if not PDF_PATH.exists():
        print("PDF was not created.", file=sys.stderr)
        return 1

    size_kb = PDF_PATH.stat().st_size / 1024
    print(f"Created: {PDF_PATH} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
