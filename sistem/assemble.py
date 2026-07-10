#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble manifest.json + sorular.html -> final.html based on SISTEM.md §2."""
import os
import sys
import json
import re
import argparse

def main():
    parser = argparse.ArgumentParser(description="Assemble manifest.json + sorular.html -> final.html")
    parser.add_argument("manifest", help="Path to manifest.json")
    parser.add_argument("sorular", help="Path to sorular.html")
    parser.add_argument("css", help="Path to flow.css (relative/absolute for HTML link)")
    parser.add_argument("out", help="Path to output HTML file")
    args = parser.parse_args()

    if not os.path.exists(args.manifest):
        print(f"Error: manifest file '{args.manifest}' not found.")
        sys.exit(1)
    if not os.path.exists(args.sorular):
        print(f"Error: sorular file '{args.sorular}' not found.")
        sys.exit(1)

    # Read manifest.json
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Parse blocks from sorular.html
    with open(args.sorular, "r", encoding="utf-8") as f:
        sorular_content = f.read()

    blocks = {}
    # F13 düzeltmesi (2026-07-10): açılış tag'inin TÜM öznitelikleri (style
    # dahil — .page-faithful konteynerleri mm boyutlarını inline style'da
    # taşır) olduğu gibi korunur; eskiden class/id/page yeniden kurulurken
    # diğer öznitelikler sessizce düşüyordu.
    pattern = re.compile(r'<(section|div)(\s+class="[^"]*"\s+id="([^"]+)"\s+data-kaynak-sayfa="[^"]*"[^>]*)>(.*?)</\1>', re.DOTALL)
    duplicates = []
    for tag, attrs, b_id, inner in pattern.findall(sorular_content):
        if b_id in blocks:
            duplicates.append(b_id)
        blocks[b_id] = f'<{tag}{attrs}>{inner}</{tag}>'
    if duplicates:
        # SISTEM.md 2: id kalici ve TEKIL olmali; cakisma sessizce blok kaybettirir.
        print(f"HATA: sorular.html icinde mukerrer id: {sorted(set(duplicates))}")
        sys.exit(2)

    title = f"{manifest.get('baslik', 'Test')} — Sürüm {manifest.get('surum', 1)}"
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="{args.css}">
</head>
<body>
  <div class="page-flow">
"""

    for page_entry in manifest.get("akis", []):
        p_num = page_entry.get("sayfa")
        html += f'    <div class="page-content" data-sayfa="{p_num}">\n'
        for b_id in page_entry.get("bloklar", []):
            if b_id in blocks:
                indented_block = "      " + blocks[b_id].replace("\n", "\n      ")
                html += indented_block + "\n"
            else:
                print(f"Warning: block '{b_id}' in manifest not found in sorular.html")
        html += '    </div>\n'

    html += """  </div>
</body>
</html>
"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Assembled successfully: {args.out}")

if __name__ == "__main__":
    main()
