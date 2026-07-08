"""GET /api/pdf?path= — PDF stream (önizleme). Sadece proje kökü (cikti/, temalar/)
veya kullanıcının ev dizini altındaki dosyalara izin verir (utils.guvenli_proje_yolu)."""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from utils import ApiHata, guvenli_proje_yolu

router = APIRouter()


@router.get("/api/pdf")
def get_pdf(path: str = Query(...)):
    gercek = guvenli_proje_yolu(path)
    # Bu uç nokta yalnızca PDF önizleme içindir; ev dizinindeki rastgele
    # dosyaların (ör. anahtar/yapılandırma) indirilebilmesini engelle.
    if not gercek.lower().endswith(".pdf"):
        raise ApiHata(400, "geçersiz dosya türü", "yalnızca .pdf dosyaları önizlenebilir")
    return FileResponse(gercek, media_type="application/pdf", filename=None)
