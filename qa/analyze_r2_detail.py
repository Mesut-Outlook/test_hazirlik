#!/usr/bin/env python3
import re
import os
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

V2_PATH = "/home/mesuto/Documents/PROJELER/test_hazirlik/1.tema_egemen_sarikci_v2.pdf"
V3_PATH = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/v3_taslak2.pdf"
HTML_PATH = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/1tema.html"
REPORT_PATH = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/qa/report_r2_1_45.txt"

def get_html_issues():
    if not os.path.exists(HTML_PATH):
        return {}
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    page_issues = {p: [] for p in range(1, 46)}
    
    # 1. Parse pages
    pages = soup.find_all("div", class_="page-content")
    for page in pages:
        try:
            pnum = int(page.get("data-sayfa", 0))
        except (ValueError, TypeError):
            continue
        if pnum < 1 or pnum > 45:
            continue
            
        # A. Check for Root clashing / unclosed root spans in this page
        rt_spans = page.find_all("span", class_="rt")
        for rt in rt_spans:
            text = rt.get_text().strip()
            # If the span text is extremely long, it means the tag was not closed properly
            if len(text) > 80:
                page_issues[pnum].append(f"rt kök çizgisi taşmış (unclosed root: '{text[:25]}...')" )
            elif re.search(r'(olduğuna göre|işleminin sonucu|ise|A\)|B\)|C\)|D\)|E\))', text):
                page_issues[pnum].append(f"rt kök çizgisi metin/şık üzerine taşmış: '{text[:30]}...'")
                
        # B. Check for Theory Box Segmentation in this page
        children = page.find_all(recursive=False)
        theory_seq = []
        for child in children:
            if child.name == "section" and any("theory-box" in c or "t01-t" in child.get("id", "") for c in child.get("class", [])):
                theory_seq.append(child.get("id", "unknown"))
            else:
                if len(theory_seq) > 1:
                    page_issues[pnum].append(f"bilgi kutusu bölünmüş (consecutive theory-boxes: {', '.join(theory_seq)})")
                theory_seq = []
        if len(theory_seq) > 1:
            page_issues[pnum].append(f"bilgi kutusu bölünmüş (consecutive theory-boxes: {', '.join(theory_seq)})")
            
        # C. Check for Option Squeezing in the text of this page
        opts_divs = page.find_all("div", class_="opts")
        for opt_div in opts_divs:
            text = opt_div.get_text().strip()
            if re.search(r'[A-E]\)[^\s]{1,6}[A-E]\)', text):
                page_issues[pnum].append(f"seçenek bitişik: '{text[:20]}'")
                
        all_text = page.get_text()
        squeezed_matches = re.findall(r'[A-E]\)[A-Za-z0-9_]{1,5}[A-E]\)', all_text)
        if squeezed_matches:
            for match in squeezed_matches:
                page_issues[pnum].append(f"seçenek bitişik: '{match}'")
                
    return page_issues

def get_pdf_issues():
    doc_v3 = fitz.open(V3_PATH)
    pdf_issues = {p: [] for p in range(1, 46)}
    
    for pidx in range(min(45, len(doc_v3))):
        pnum = pidx + 1
        page = doc_v3[pidx]
        
        # Check overlaps
        words = page.get_text("words")
        # word: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        lines = {}
        for w in words:
            key = (w[5], w[6])  # (block, line)
            if key not in lines:
                lines[key] = []
            lines[key].append(w)
            
        line_keys = list(lines.keys())
        for i in range(len(line_keys)):
            for j in range(i + 1, len(line_keys)):
                k1 = line_keys[i]
                k2 = line_keys[j]
                
                words1 = lines[k1]
                words2 = lines[k2]
                
                x0_1 = min(w[0] for w in words1)
                x1_1 = max(w[2] for w in words1)
                y0_1 = min(w[1] for w in words1)
                y1_1 = max(w[3] for w in words1)
                
                x0_2 = min(w[0] for w in words2)
                x1_2 = max(w[2] for w in words2)
                y0_2 = min(w[1] for w in words2)
                y1_2 = max(w[3] for w in words2)
                
                v_overlap = min(y1_1, y1_2) - max(y0_1, y0_2)
                h_overlap = min(x1_1, x1_2) - max(x0_1, x0_2)
                
                h1 = y1_1 - y0_1
                h2 = y1_2 - y0_2
                min_h = min(h1, h2)
                
                if v_overlap > 0.7 * min_h and h_overlap > 15:
                    t1 = " ".join(w[4] for w in words1).strip()
                    t2 = " ".join(w[4] for w in words2).strip()
                    # Ignore if they contain identical text or numbers that are headers or page margins
                    if t1 != t2 and abs(y0_1 - y0_2) > 3:
                        # Make sure they are not just inline formulas or superscript/subscript
                        if not (t1.isdigit() and len(t1) <= 2) and not (t2.isdigit() and len(t2) <= 2):
                            pdf_issues[pnum].append(f"metin üst üste binmiş (overlap): '{t1[:15]}' ve '{t2[:15]}'")
                            
        # Check text layer option squeezing
        text = page.get_text()
        squeezed = re.findall(r'[A-E]\)[A-Za-z0-9_]{1,5}[A-E]\)', text)
        if squeezed:
            for sq in squeezed:
                pdf_issues[pnum].append(f"seçenek bitişik: '{sq}'")
                
        # Check for page numbers leaked into the text
        page_num_leaks = re.findall(r'[A-E]\)\s+\d+\s+\d+', text)
        if page_num_leaks:
            for leak in page_num_leaks:
                pdf_issues[pnum].append(f"sayfa numarası üsse sızmış: '{leak}'")
                
    return pdf_issues

def main():
    html_issues = get_html_issues()
    pdf_issues = get_pdf_issues()
    
    report = []
    
    # We want to perform page-by-page QA comparison for pages 1 to 45.
    # We must state the verdict for EACH page individually.
    for pnum in range(1, 46):
        issues = []
        if pnum in html_issues:
            issues.extend(html_issues[pnum])
        if pnum in pdf_issues:
            for issue in pdf_issues[pnum]:
                if issue not in issues:
                    issues.append(issue)
                    
        # Check specific known structural issues or clean pages
        # Let's clean up some minor false positives for overlaps:
        # e.g., if there's only minor superscript/subscript detection
        filtered_issues = []
        for iss in issues:
            # Filter out known false positives
            if "metin üst üste binmiş" in iss:
                # Let's keep it but make it clean if it's very minor
                filtered_issues.append(iss)
            else:
                filtered_issues.append(iss)
                
        if not filtered_issues:
            verdict = f"[sayfa {pnum:03d}] temiz"
        else:
            # Limit description size and format nicely
            # If there are issues, state them
            desc = " - ".join(list(dict.fromkeys(filtered_issues))) # unique issues
            verdict = f"[sayfa {pnum:03d}] sorun — {desc}"
            
        report.append(verdict)
        print(verdict)
        
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print(f"Wrote report to {REPORT_PATH}")

if __name__ == "__main__":
    main()
