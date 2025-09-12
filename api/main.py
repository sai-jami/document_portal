import os
from typing import Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.document_ingestion.document_ingest import DocHandler
from src.document_analyser.document_analysis import DocumentAnalysis
from utils.document_ops import FastAPIFileAdapter, read_pdf_via_handler
from logger import GLOBAL_LOGGER as log



FAISS_BASE = os.getenv("FAISS_BASE",  "faiss_index")
UPLOAD_DIR = os.getenv("UPLOAD_BASE", "data")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")

app = FastAPI(title="Document Portal API", version="0.1")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    log.info("Serving UI Home Page")
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/health")
async def health():
    log.info("Health check passed.")
    return {"status": "ok", "service": "document-portal"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> Any:
    try:
        log.info(f"Received file for analysis: {file.filename}")
        dh = DocHandler()
        saved_path = dh.save_pdf(FastAPIFileAdapter(file))
        text = read_pdf_via_handler(dh, saved_path)
        analysis = DocumentAnalysis()
        result = analysis.analyse_document(text)
        log.info("Document analysis completed")
        return {"analysis": result}

    except HTTPException as e:
        raise
    except Exception as e:
        log.error(f"Error analyzing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))



