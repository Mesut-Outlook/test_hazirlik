"""temalar/NN-ad/tema_meta.json — arayüzün kendi ürettiği tema-başına küçük meta
dosyası (manifest.json'a KARIŞMAZ; sistem/assemble.py'nin beklediği şema sabit
kalır). Burada saklanan: orijinal kaynak dosya adı, kullanıcının seçtiği çıktı
klasörü, oluşturma zamanı, son job id'leri."""
from __future__ import annotations

import json
import os
import threading

# İş kuyruğu (job) işçi thread'i ile istek işleyen thread aynı tema_meta.json'a
# neredeyse eş zamanlı yazabilir (ör. POST /api/temalar dönerken son_extract_job
# yazarken, arka plandaki job da kaynak_pdf yazıyor olabilir). Kilitsiz oku+yaz
# oku()'nun yarı yazılmış/boş dosyayı görmesine (JSONDecodeError) yol açar —
# bu yüzden tema başına değil, tek global bir kilitle read-modify-write atomik
# hale getirilir (tema sayısı azken tek kilit yeterli, basitlik tercih edildi).
_KILIT = threading.Lock()


def yol(tema_dir: str) -> str:
    return os.path.join(tema_dir, "tema_meta.json")


def _oku_kilitsiz(tema_dir: str) -> dict:
    p = yol(tema_dir)
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        icerik = f.read()
    if not icerik.strip():
        return {}
    return json.loads(icerik)


def oku(tema_dir: str) -> dict:
    with _KILIT:
        return _oku_kilitsiz(tema_dir)


def yaz(tema_dir: str, veri: dict) -> None:
    with _KILIT:
        mevcut = _oku_kilitsiz(tema_dir)
        mevcut.update(veri)
        gecici = yol(tema_dir) + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(mevcut, f, ensure_ascii=False, indent=2)
        os.replace(gecici, yol(tema_dir))
