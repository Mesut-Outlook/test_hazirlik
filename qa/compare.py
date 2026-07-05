#!/usr/bin/env python3
import os
import sys
import argparse
import difflib
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

def normalize_text(text):
    """Normalize text by stripping lines and ignoring empty lines."""
    lines = []
    for line in text.splitlines():
        line_stripped = " ".join(line.split())  # normalize internal spaces
        if line_stripped:
            lines.append(line_stripped)
    return lines

def create_comparison(v2_path, v3_path, output_dir, start_page, end_page, dpi=150):
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Opening PDF files:\n  V2: {v2_path}\n  V3: {v3_path}")
    doc_v2 = fitz.open(v2_path)
    doc_v3 = fitz.open(v3_path)
    
    num_pages_v2 = len(doc_v2)
    num_pages_v3 = len(doc_v3)
    print(f"Page counts: V2 has {num_pages_v2} pages, V3 has {num_pages_v3} pages.")
    
    # Bound the page range (1-indexed input)
    max_pages = max(num_pages_v2, num_pages_v3)
    start_idx = max(0, start_page - 1)
    end_idx = min(max_pages, end_page if end_page is not None else max_pages)
    
    print(f"Processing pages {start_idx + 1} to {end_idx}...")
    
    diff_report_path = os.path.join(output_dir, "text_diff.txt")
    diff_report_lines = []
    
    for i in range(start_idx, end_idx):
        page_num = i + 1
        print(f"Comparing page {page_num} / {end_idx}...", end="\r", flush=True)
        
        # 1. Text extraction and normalization
        text_v2 = ""
        text_v3 = ""
        
        has_v2 = i < num_pages_v2
        has_v3 = i < num_pages_v3
        
        if has_v2:
            text_v2 = doc_v2[i].get_text("text")
        if has_v3:
            text_v3 = doc_v3[i].get_text("text")
            
        lines_v2 = normalize_text(text_v2)
        lines_v3 = normalize_text(text_v3)
        
        page_diff = list(difflib.unified_diff(
            lines_v2, lines_v3,
            fromfile=f"V2_Page_{page_num}",
            tofile=f"V3_Page_{page_num}",
            lineterm=""
        ))
        
        if page_diff:
            diff_report_lines.append(f"=== PAGE {page_num} ===\n")
            diff_report_lines.extend([line + "\n" for line in page_diff])
            diff_report_lines.append("\n" + "="*40 + "\n\n")
            
        # 2. Visual rendering and merging
        img_v2 = None
        img_v3 = None
        
        if has_v2:
            pix_v2 = doc_v2[i].get_pixmap(dpi=dpi)
            img_v2 = Image.frombytes("RGB", [pix_v2.width, pix_v2.height], pix_v2.samples)
        if has_v3:
            pix_v3 = doc_v3[i].get_pixmap(dpi=dpi)
            img_v3 = Image.frombytes("RGB", [pix_v3.width, pix_v3.height], pix_v3.samples)
            
        # Determine canvas sizes
        w_v2, h_v2 = img_v2.size if img_v2 else (0, 0)
        w_v3, h_v3 = img_v3.size if img_v3 else (0, 0)
        
        width = w_v2 + w_v3 + 10  # 10px divider
        height = max(h_v2, h_v3) + 40  # 40px top bar for labels
        
        # Create combined image
        combined = Image.new("RGB", (width, height), (240, 240, 240))
        draw = ImageDraw.Draw(combined)
        
        # Draw labels
        label_color = (0, 0, 0)
        draw.text((10, 10), f"V2 Reference - Page {page_num}", fill=label_color)
        draw.text((w_v2 + 20, 10), f"V3 Taslak - Page {page_num}", fill=label_color)
        
        # Paste pages
        if img_v2:
            combined.paste(img_v2, (0, 40))
        if img_v3:
            combined.paste(img_v3, (w_v2 + 10, 40))
            
        # Draw divider line
        draw.line([(w_v2 + 5, 0), (w_v2 + 5, height)], fill=(180, 180, 180), width=2)
        
        # Save page image
        out_img_name = f"cmp_{page_num:03d}.png"
        combined.save(os.path.join(output_dir, out_img_name))
        
    print(f"\nFinished page rendering and comparisons.")
    
    # Save the diff report
    with open(diff_report_path, "w", encoding="utf-8") as f:
        f.writelines(diff_report_lines)
    print(f"Text diff report saved to: {diff_report_path}")
    
    # Summarize discrepancies
    if diff_report_lines:
        print(f"ALERT: Discrepancies found in text content. Check {diff_report_path} for details.")
    else:
        print("Success: No text differences found (excluding layout/font structure).")

def main():
    parser = argparse.ArgumentParser(description="Compare PDF pages visually and textually for QA.")
    parser.add_argument("--v2", default="/home/mesuto/Documents/PROJELER/test_hazirlik/1.tema_egemen_sarikci_v2.pdf", help="Path to v2 reference PDF")
    parser.add_argument("--v3", default="/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/v3_taslak.pdf", help="Path to v3 test PDF")
    parser.add_argument("--out", default="/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/qa", help="Output directory for QA reports")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-indexed)")
    parser.add_argument("--end", type=int, default=None, help="End page (1-indexed, inclusive)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for page rendering")
    
    args = parser.parse_args()
    
    create_comparison(args.v2, args.v3, args.out, args.start, args.end, args.dpi)

if __name__ == "__main__":
    main()
