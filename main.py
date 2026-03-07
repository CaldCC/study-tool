import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import processor
from inputs import url_handler, doi_handler, pdf_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Study Tool")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class URLRequest(BaseModel):
    url: str


class DOIRequest(BaseModel):
    doi: str


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/process/url")
async def process_url(req: URLRequest):
    try:
        extracted = await url_handler.extract(req.url)
    except Exception as exc:
        log.error("URL extraction failed: %s", exc)
        raise HTTPException(status_code=422, detail=f"Could not fetch URL: {exc}")
    try:
        result = await processor.process(extracted["text"], extracted["images"])
    except Exception as exc:
        log.error("Processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    return JSONResponse(result)


@app.post("/process/doi")
async def process_doi(req: DOIRequest):
    try:
        extracted = await doi_handler.extract(req.doi)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.error("DOI extraction failed: %s", exc)
        raise HTTPException(status_code=422, detail=f"Could not resolve DOI: {exc}")
    try:
        result = await processor.process(extracted["text"], extracted["images"])
    except Exception as exc:
        log.error("Processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    return JSONResponse(result)


@app.post("/process/pdf")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Uploaded file must be a PDF.")
    data = await file.read()
    extracted = pdf_handler.extract(data)
    try:
        result = await processor.process(extracted["text"], extracted["images"])
    except Exception as exc:
        log.error("Processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    return JSONResponse(result)
