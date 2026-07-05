import re
import os
from html.parser import HTMLParser

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages = {}
        self.current_page = None
        self.current_section = None
        self.in_rt = False
        self.rt_content = ""
        self.in_opts = False
        self.opts_content = ""
        self.current_theory_boxes = []
        self.current_images = []
        self.current_questions = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "div" and attrs_dict.get("class") == "page-content":
            self.current_page = int(attrs_dict.get("data-sayfa", 0))
            self.pages[self.current_page] = {
                "text": [],
                "questions": [],
                "images": [],
                "theory_boxes": [],
                "root_spans": [],
                "opts_blocks": []
            }
            self.current_theory_boxes = []
            self.current_images = []
            self.current_questions = []
            
        if self.current_page:
            if tag == "section":
                self.current_section = attrs_dict
                classes = attrs_dict.get("class", "")
                if "question" in classes:
                    self.pages[self.current_page]["questions"].append(attrs_dict)
                if "theory-box" in classes:
                    self.pages[self.current_page]["theory_boxes"].append(attrs_dict)
            
            elif tag == "img":
                self.pages[self.current_page]["images"].append(attrs_dict)
                
            elif tag == "span" and attrs_dict.get("class") == "rt":
                self.in_rt = True
                self.rt_content = ""
                
            elif tag == "div" and attrs_dict.get("class") == "opts":
                self.in_opts = True
                self.opts_content = ""
                
    def handle_endtag(self, tag):
        if self.current_page:
            if tag == "section":
                self.current_section = None
            elif tag == "span" and self.in_rt:
                self.in_rt = False
                self.pages[self.current_page]["root_spans"].append({
                    "content": self.rt_content,
                    "section_id": self.current_section.get("id") if self.current_section else None
                })
            elif tag == "div" and self.in_opts:
                self.in_opts = False
                self.pages[self.current_page]["opts_blocks"].append({
                    "content": self.opts_content,
                    "section_id": self.current_section.get("id") if self.current_section else None
                })
                
    def handle_data(self, data):
        if self.current_page:
            self.pages[self.current_page]["text"].append(data)
            if self.in_rt:
                self.rt_content += data
            if self.in_opts:
                self.opts_content += data

def parse_html():
    html_path = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/1tema.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    parser = PageParser()
    parser.feed(html_content)
    return parser.pages

def parse_text_diff():
    diff_path = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/qa/r2/text_diff.txt"
    if not os.path.exists(diff_path):
        return {}
        
    with open(diff_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split by PAGE headings
    pages_diff = {}
    parts = re.split(r'=== PAGE (\d+) ===', content)
    for i in range(1, len(parts), 2):
        pnum = int(parts[i])
        diff_text = parts[i+1]
        pages_diff[pnum] = diff_text
    return pages_diff

def analyze():
    html_pages = parse_html()
    diff_pages = parse_text_diff()
    
    report_lines = []
    
    # We want to perform QA comparison for v2 pages 46 to 90.
    # Note: v2 page N maps to some taslak2 pages.
    # Let's write down the rules and checks for each page.
    
    for page_num in range(46, 91):
        page = html_pages.get(page_num, None)
        diff = diff_pages.get(page_num, "")
        
        issues = []
        
        if not page:
            issues.append("Sayfa HTML'de bulunamadı (kayıp)")
            report_lines.append(f"[sayfa {page_num:03d}] sorun — sayfa HTML'de bulunamadı.")
            continue
            
        full_text = " ".join(page["text"])
        
        # 1. Check root clashing
        for rt in page["root_spans"]:
            content = rt["content"]
            # Look for too long root contents or leaks
            if len(content) > 100:
                issues.append(f"kök çizgisi taşmış (unclosed root: '{content[:30]}...' id: {rt['section_id']})")
            elif re.search(r'(işleminin|olduğuna|ise|veya|A\)|B\)|C\)|D\)|E\))', content):
                issues.append(f"kök çizgisi metin/şık üzerine taşmış: '{content[:40]}' id: {rt['section_id']}")
                
        # 2. Check option squeezing
        for opts in page["opts_blocks"]:
            content = opts["content"]
            # Look for lack of spaces between options like A)...B)...
            # e.g., options like A)1B)2C)3
            squeezed = re.findall(r'[A-E]\)[^\s]{1,6}[A-E]\)', content)
            if squeezed:
                issues.append(f"seçenekler bitişik/sıkışık: {squeezed}")
                
        # 3. Check theory box segmentation
        theory_boxes = page["theory_boxes"]
        if len(theory_boxes) > 4:
            # check if sequential IDs
            box_ids = [tb.get("id", "") for tb in theory_boxes]
            issues.append(f"bilgi kutusu bölünmüş (consecutive theory-boxes: {', '.join(box_ids)})")
            
        # 4. Check for page numbers leaking into superscripts or text (common minor)
        # Look for sayfa numarasının bir önceki/sonraki metne karışıp üs olarak sızması
        num_leak = re.search(r'[A-E]\)\s*\d+(' + str(page_num) + r'|' + str(page_num-1) + r'|' + str(page_num+1) + r')', full_text)
        if num_leak:
            issues.append(f"sayfa numarası üsse sızmış: '{num_leak.group(0)}'")
            
        # 5. Check diff for obvious errors or missing parts
        # If there are differences containing questions or options in diff
        
        if issues:
            # Format report line
            report_lines.append(f"[sayfa {page_num:03d}] " + ", ".join(issues))
        else:
            report_lines.append(f"[sayfa {page_num:03d}] temiz")
            
    # Write to target file
    out_path = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/qa/report_r2_46_90.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for line in report_lines:
            f.write(line + "\n")
            
    print(f"Report generated at {out_path}")
    
    # Print the report here for our own inspection
    for line in report_lines:
        print(line)

if __name__ == "__main__":
    analyze()
