#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SISTEM.md §6 dogrulama: kaynak PDF (v2) ile uretilen cikti PDF arasinda
anahtar kelime sayimi + KUR etiketi/bolum basligi butunlugu kontrolu.

A4a (Claude-Sonnet #6) sirasinda, extract.py'de bulunan bir regresyonu
(kur-tag/tag-kurgusu metninin figur-suppression tarafindan silinmesi) tam
olarak bu tur bir sayim karsilastirmasi ortaya cikardi - bu yuzden bu script
her extract+print kosusundan sonra calistirilmasi tavsiye edilir.

Kullanim:
    python3 qa/dogrula.py [kaynak.pdf] [cikti.pdf]
    (parametresiz calistirilirsa depo kokundeki v2 ve cikti/1.tema_egemen_sarikci_v3.pdf kullanilir)
"""
import os
import subprocess
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_V2 = os.path.join(REPO_ROOT, "temalar", "01-tema", "kaynak", "1.tema_egemen_sarikci_v2.pdf")
DEFAULT_V3 = os.path.join(REPO_ROOT, "cikti", "1.tema_egemen_sarikci_v3.pdf")


def get_text(path):
    res = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True)
    return res.stdout.decode('utf-8', errors='ignore')


PHRASES = [
    "GÜNLÜK HAYAT UYGULAMALARI",
    "ÖSYM SORULARINA HAZIRLIK",
    "ÖSYM KURGULARSA",
    "PİST ALANI",
    "ISINMA HAREKETLERİ",
    "Klasikleşmiş Uygulamalar",
    "Kurgusu",
    "işleminin sonucu kaçtır",
]


def main():
    v2 = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_V2
    v3 = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_V3

    t2 = get_text(v2)
    t3 = get_text(v3)

    TARGET_V3 = {
        "GÜNLÜK HAYAT UYGULAMALARI": 5,
        "ÖSYM SORULARINA HAZIRLIK": 5,
        "ÖSYM KURGULARSA": 4,
        "PİST ALANI": 5,
        "ISINMA HAREKETLERİ": 10,
        "Klasikleşmiş Uygulamalar": 11,
        "Kurgusu": 20,
        "işleminin sonucu kaçtır": 120,
    }

    # Tema 1 tespiti
    v2_base = os.path.basename(v2).lower()
    is_theme_1 = "01-tema" in v2 or "1.tema" in v2_base or "1_tema" in v2_base

    if is_theme_1:
        print(f"Tema 1 doğrulaması yapılıyor...")
        print(f"{'ifade':40s} {'v2':>6s} {'v3':>6s}  {'target':>6s}  durum")
    else:
        print(f"Genel Tema doğrulaması yapılıyor...")
        print(f"{'ifade':40s} {'v2':>6s} {'v3':>6s}  durum")
        
    all_ok = True
    for p in PHRASES:
        c2 = len(re.findall(re.escape(p), t2, re.IGNORECASE))
        c3 = len(re.findall(re.escape(p), t3, re.IGNORECASE))
        if is_theme_1:
            target = TARGET_V3[p]
            ok = c3 == target
            print(f"{p:40s} {c2:6d} {c3:6d}  {target:6d}  {'OK' if ok else 'FARK'}")
        else:
            # Diğer temalarda:
            # Başlıkların/etiketlerin sayısı azalabilir (mükerrer üst/alt bilgi temizliği yüzünden): c3 <= c2
            # Soru kalıpları ("Kurgusu", "sonucu kaçtır") birebir aynı kalmalıdır: c3 == c2
            if p in ["Kurgusu", "işleminin sonucu kaçtır"]:
                ok = (c3 == c2)
            else:
                ok = (c3 <= c2)
            print(f"{p:40s} {c2:6d} {c3:6d}  {'OK' if ok else 'FARK'}")
        all_ok = all_ok and ok

    print()
    print("120=120 kontrolu (bkz. gorev talimati):")
    c2 = t2.count("120")
    c3 = t3.count("120")
    print(f"  '120' v2={c2} v3={c3}")

    print()
    print("Sayfa sayilari:")
    info2 = subprocess.run(["pdfinfo", v2], capture_output=True, encoding="utf-8", errors="ignore").stdout
    info3 = subprocess.run(["pdfinfo", v3], capture_output=True, encoding="utf-8", errors="ignore").stdout
    for line in info2.splitlines():
        if line.startswith("Pages"):
            print("  v2:", line)
    for line in info3.splitlines():
        if line.startswith("Pages"):
            print("  v3:", line)

    # Görsel-tekrar kontrolü:
    theme_dir = os.path.dirname(os.path.dirname(os.path.abspath(v2)))
    sorular_path = os.path.join(theme_dir, "sorular.html")
    if not os.path.exists(sorular_path):
        sorular_path = os.path.join(os.path.dirname(os.path.abspath(v2)), "sorular.html")
    if not os.path.exists(sorular_path):
        sorular_path = os.path.join(REPO_ROOT, "temalar", "01-tema", "sorular.html")
    if os.path.exists(sorular_path):
        print("\nGörsel Tekrar Kontrolü:")
        with open(sorular_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        sections = re.findall(r'<section[^>]*class="[^"]*question[^"]*"[^>]*>(.*?)</section>', html_content, re.DOTALL)
        dup_found = False
        for idx, sec in enumerate(sections):
            imgs = re.findall(r'<img[^>]+src="([^"]+)"', sec)
            seen = set()
            for img in imgs:
                if img in seen:
                    print(f"  [HATA] Soru (indeks {idx+1}) içinde mükerrer görsel: {img}")
                    dup_found = True
                seen.add(img)
            for i in range(len(imgs) - 1):
                if imgs[i] == imgs[i+1]:
                    print(f"  [HATA] Soru (indeks {idx+1}) içinde ardışık aynı görsel: {imgs[i]}")
                    dup_found = True
        
        if not dup_found:
            print("  Tüm görseller benzersiz, mükerrer görsel tespiti temiz. [OK]")
        else:
            all_ok = False

    sys.exit(0 if all_ok else 1)



if __name__ == "__main__":
    main()
