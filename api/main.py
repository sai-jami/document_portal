import os
from typing import Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.document_ingestion.document_ingest import (DocHandler, DocumentComparator)
from src.document_analyser.document_analysis import DocumentAnalysis
from src.document_compare.document_comparator import DocumentComparatorLLM
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

@app.post("/compare")
async def compare(reference_file: UploadFile = File(...), actual_file: UploadFile = File(...)) -> Any:

    try:
        log.info(f"Received files for comparison: {reference_file.filename} and {actual_file.filename}")
        dc = DocumentComparator()
        reference_path, actual_path = dc.save_uploaded_files(
            
            FastAPIFileAdapter(reference_file),
             FastAPIFileAdapter(actual_file))
        _ = reference_path, actual_path

        combined_docs = dc.combine_documents()
        comp = DocumentComparatorLLM()
        df = comp.compare_documents(combined_docs)
        log.info("Document comparison completed.")
        return {"rows": df.to_dict(orient="records"), "session_id": dc.session_id}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Comparison failed")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")

    



