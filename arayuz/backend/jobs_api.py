"""GET /api/jobs/{id} + GET /api/jobs/{id}/events (SSE) — iş durumu/ilerleme/log."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from jobs import job_manager
from utils import ApiHata

router = APIRouter()


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = job_manager.al(job_id)
    if job is None:
        raise ApiHata(404, "iş bulunamadı", job_id)
    return job.gorunum()


@router.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    job = job_manager.al(job_id)
    if job is None:
        raise ApiHata(404, "iş bulunamadı", job_id)

    async def akis():
        gonderilen = 0
        while True:
            gorunum = job.gorunum()
            loglar = gorunum["loglar"]
            while gonderilen < len(loglar):
                yield f"event: log\ndata: {json.dumps(loglar[gonderilen], ensure_ascii=False)}\n\n"
                gonderilen += 1
            if gorunum["durum"] in ("tamam", "hata"):
                yield f"event: durum\ndata: {json.dumps(gorunum, ensure_ascii=False)}\n\n"
                break
            yield ": ping\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(akis(), media_type="text/event-stream")
