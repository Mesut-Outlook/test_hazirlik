import re
import os
from html.parser import HTMLParser

class MathPDFParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages = {}
        self.current_page = None
        self.current_section = None
        self.section_stack = []
        self.current_data = []
        self.in_rt = False
        self.rt_content = ""
        self.rt_start_pos = None
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "div" and attrs_dict.get("class") == "page-content":
            self.current_page = int(attrs_dict.get("data-sayfa", 0))
            self.pages[self.current_page] = {
                "raw_html": "",
                "text": [],
                "blocks": [],
                "images": [],
                "options": [],
                "theory_boxes": [],
                "root_spans": []
            }
            
        if self.current_page:
            self.pages[self.current_page]["raw_html"] += f"<{tag} " + " ".join([f'{k}="{v}"' for k, v in attrs]) + ">"
            
            if tag == "section":
                self.current_section = attrs_dict
                self.pages[self.current_page]["blocks"].append(attrs_dict)
                if "theory-box" in attrs_dict.get("class", ""):
                    self.pages[self.current_page]["theory_boxes"].append(attrs_dict)
            
            elif tag == "img":
                self.pages[self.current_page]["images"].append(attrs_dict)
                
            elif tag == "span" and attrs_dict.get("class") == "rt":
                self.in_rt = True
                self.rt_content = ""
                self.rt_start_pos = len(self.pages[self.current_page]["text"])
                
            elif attrs_dict.get("class") == "opts":
                self.section_stack.append("opts")
                
    def handle_endtag(self, tag):
        if self.current_page:
            self.pages[self.current_page]["raw_html"] += f"</{tag}>"
            
            if tag == "section":
                self.current_section = None
            elif tag == "span" and self.in_rt:
                self.in_rt = False
                self.pages[self.current_page]["root_spans"].append({
                    "content": self.rt_content,
                    "section_id": self.current_section.get("id") if self.current_section else None
                })
            elif tag == "div" and self.section_stack and self.section_stack[-1] == "opts":
                self.section_stack.pop()
                
    def handle_data(self, data):
        if self.current_page:
            self.pages[self.current_page]["raw_html"] += data
            self.pages[self.current_page]["text"].append(data)
            
            if self.in_rt:
                self.rt_content += data
                
            if self.section_stack and self.section_stack[-1] == "opts":
                self.pages[self.current_page]["options"].append(data)

def analyze():
    html_path = "/home/mesuto/Documents/PROJELER/test_hazirlik/build_linux/1tema.html"
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        return
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    parser = MathPDFParser()
    parser.feed(html_content)
    
    print(f"Total parsed pages: {len(parser.pages)}")
    
    for page_num in sorted(parser.pages.keys()):
        if page_num > 45:
            continue
            
        page = parser.pages[page_num]
        issues = []
        
        # 1. Check Option Squeezing & format
        # Check if option text has options like A) B) C) D) E) joined without spaces
        opts_text = "".join(page["options"])
        squeezed_match = re.search(r'[A-E]\)[^\s]{1,10}[A-E]\)', opts_text)
        if squeezed_match:
            issues.append(f"Option squeezing detected: '{squeezed_match.group(0)}'")
            
        # Check if options are in the main text block instead of the .opts div (can happen during parsing errors)
        full_text = " ".join(page["text"])
        
        # Check for unclosed/long root spans (Root clashing)
        # If a root span has too many characters or contains word characters/options, it's clashing.
        for rt in page["root_spans"]:
            content = rt["content"]
            # If root contains words like "işleminin", "veya", "ise", "olduğuna" or choice tags
            if len(content) > 60:
                issues.append(f"Root span too long ({len(content)} chars): '{content[:30]}...' in block {rt['section_id']}")
            elif re.search(r'(işleminin|olduğuna|ise|veya|sırasıyla|seçenek|şeklinde|A\)|B\)|C\)|D\)|E\))', content):
                issues.append(f"Root clashing/leak: contains text/choices '{content[:40]}' in block {rt['section_id']}")
                
        # Check for theory box segmentation (multiple theory boxes on the same page with similar content or sequential ids)
        t_boxes = page["theory_boxes"]
        if len(t_boxes) > 1:
            # check if they have consecutive IDs or if there are too many
            t_ids = [t.get("id", "") for t in t_boxes]
            issues.append(f"Multiple theory boxes ({len(t_boxes)}): {', '.join(t_ids)}")
            
        # Check for table/graphics text extraction duplication
        # Look for patterns of numbers/chars that look like table header or table extraction
        if "Tablo" in full_text or "grafik" in full_text:
            # if we have image but also lots of weird layout text
            image_blocks = [b for b in page["blocks"] if "img" in page["raw_html"]]
            
        # Check for missing questions or images
        # Let's print summary for each page
        if issues:
            print(f"[Page {page_num:03d}] {'; '.join(issues)}")
        else:
            print(f"[Page {page_num:03d}] Clean or no automatic issues found.")

if __name__ == "__main__":
    analyze()
