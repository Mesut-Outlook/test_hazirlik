"""FAZ 4 — Yerel Web Arayüzü backend'i (FastAPI).

Çalıştırma: arayuz/calistir.sh (venv kurar/etkinleştirir + uvicorn başlatır + tarayıcıda açar)
veya doğrudan: arayuz/backend/venv/bin/uvicorn main:app --app-dir arayuz/backend --port 8756

API sözleşmesi COORDINATION.md → "FAZ 4" bölümünde SABİTTİR; bu dosya yalnızca
router'ları toplayıp statik ön yüzü (arayuz/web/, F2 dolduracak) servis eder.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config import WEB_DIR
import ayarlar
import fs_api
import jobs_api
import pdf_api
import temalar_api

app = FastAPI(title="Test Hazırlık — Arayüz Backend")

# DNS rebinding koruması: sunucu yalnızca 127.0.0.1'i dinliyor ama kötü niyetli
# bir site kendi alan adını 127.0.0.1'e çözdürüp tarayıcı üzerinden API'ye
# istek atabilir (Host başlığı o sitenin adı olur). Yerel adlar dışındaki
# Host'ları reddet.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])


@app.exception_handler(StarletteHTTPException)
async def hata_govdesi(request, exc: StarletteHTTPException):
    """Sözleşme: hata gövdesi her zaman {hata, detay} biçiminde."""
    detail = exc.detail
    if isinstance(detail, dict) and "hata" in detail:
        gövde = detail
    else:
        gövde = {"hata": str(detail), "detay": ""}
    return JSONResponse(status_code=exc.status_code, content=gövde)


app.include_router(ayarlar.router)
app.include_router(fs_api.router)
app.include_router(temalar_api.router)
app.include_router(jobs_api.router)
app.include_router(pdf_api.router)

# Statik ön yüz — F2 ajanı arayuz/web/ içine index.html/app.js/style.css dolduracak.
# check_dir=False: klasör boş/henüz oluşturulmamışsa uygulama yine ayağa kalksın.
app.mount("/", StaticFiles(directory=WEB_DIR, html=True, check_dir=False), name="web")
