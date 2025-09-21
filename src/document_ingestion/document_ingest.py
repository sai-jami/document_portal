import os
import json
import hashlib
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any

import fitz  # PyMuPDF
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from utils.model_loader import ModelLoader
from exceptions.custom_exception import DocumentPortalException
from utils.file_io import generate_session_id
from logger import GLOBAL_LOGGER as log


SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt"]

class FaissManager:

    def __init__(self, index_dir:Path, model_loader:Optional[ModelLoader] = None):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.meta_path = self.index_dir / "ingested_meta.json"
        self._meta : Dict[str, Any] = {"rows":{}}

        if self.meta_path.exists():
            try:
                meta_text = self.meta_path.read_text(encoding="utf-8")
                self._meta = json.loads(meta_text) if meta_text else {"rows":{}}
            except Exception as e:
                self._meta = {"rows":{}}

        self.model_loader = model_loader or ModelLoader()
        self.embedding = self.model_loader.load_embedding_model()
        self.vectorstore : Optional[FAISS] = None

    def _exists(self)-> bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()

    @staticmethod
    def _fingerprint(text: str, md: Dict[str, Any])-> str:
        src = md.get("source", "") or md.get("file_path", "")
        rid = md.get("row_id", "") 
        if src is not None:
            return f"{src}::{'' if rid is None else rid}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def _save_meta(self):
        self.meta_path.write_text(json.dumps(self._meta, ensure_ascii=False,  indent=2), encoding="utf-8")

    def add_documents(self, docs: List[Document]):

        if self.vectorstore is None:
            raise RuntimeError("Call load_or_create() before add_documents_idempotent().")
        
        new_docs : List[Document] = []

        for d in docs:
            key = self._fingerprint(d.page_content, d.metadata or {})

            if key in self._meta["rows"]:
                continue

            self._meta["rows"][key] = True
            new_docs.append(d)

        if new_docs:
            self.vectorstore.add_documents(new_docs)
            self.vectorstore.save_local(self.index_dir)
            self._save_meta()

        return len(new_docs)

    def load_or_create(self, texts:Optional[List[str]] = None, metadata:Optional[List[dict]] = None):
        if self._exists():
            self.vectorstore = FAISS.load_local(str(self.index_dir), embeddings = self.embedding, allow_dangerous_deserialization=True)

            return self.vectorstore

        if not texts:
            raise DocumentPortalException("No existing FAISS index and no data to create one", sys)

        self.vectorstore = FAISS.from_texts(texts, self.embedding, metadatas=metadata or [])
        self.vectorstore.save_local(str(self.index_dir))

        return self.vectorstore
    
class DocHandler:

    def __init__(self, data_dir:Optional[str] = None, session_id:Optional[str] = None):

        self.data_dir = data_dir or os.getenv("DATA_STORAGE_PATH",os.path.join(os.getcwd(), "data", "document_analysis"))
        self.session_id = session_id or generate_session_id("session")
        self.session_path = os.path.join(self.data_dir, self.session_id)

        os.makedirs(self.session_path, exist_ok=True)
        log.info("DocHandler initialized", session_id=self.session_id, session_path=self.session_path)

    def save_pdf(self, uploaded_file) -> str:

        try:
            filename = os.path.basename(uploaded_file.name)
            if not filename.endswith(".pdf"):
                raise ValueError("Only PDF files are supported")
            save_path = os.path.join(self.session_path, filename)
            with open(save_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())
            log.info("PDF saved successfully", file=filename, save_path=save_path, session_id=self.session_id)
            return save_path
        except Exception as e:
            log.error("Failed to save PDF", error=str(e), session_id=self.session_id)
            raise DocumentPortalException(f"Failed to save PDF: {str(e)}", sys) from e
        
    def read_pdf(self, pdf_path:str) -> str:

        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_chunks.append((f"\n--- Page {page_num + 1} ---\n{page.get_text()}"))

            text = "\n".join(text_chunks)
            log.info("PDF read successfully", pdf_path=pdf_path, session_id=self.session_id, pages=len(text_chunks))
            return text
        except Exception as e:
            log.error("Failed to read PDF", error=str(e), session_id=self.session_id, pdf_path=pdf_path)
            raise DocumentPortalException(f"Could not process PDF: {pdf_path}", e) from e

class DocumentComparator:

    def __init__(self, base_dir:str = "data/document_compare", session_id:Optional[str] = None):
        self.base_dir = base_dir
        self.session_id = session_id or generate_session_id("session")
        self.session_path = os.path.join(self.base_dir, self.session_id)
        os.makedirs(self.session_path, exist_ok=True)
        log.info("DocumentComparator initialized", session_id=self.session_id, session_path=self.session_path)
        
    def save_uploaded_files(self, reference_file:UploadFile, actual_file:UploadFile):
        try:
            reference_path = os.path.join(self.session_path, reference_file.filename)
            actual_path = os.path.join(self.session_path, actual_file.filename)
            for fobj, out in ((reference_file, reference_path), (actual_file, actual_path)):
                if not fobj.name.lower().endswith(".pdf"):
                    raise ValueError("Only PDF files are allowed.")
                with open(out, "wb") as f:
                    if hasattr(fobj, "read"):
                        f.write(fobj.read())
                    else:
                        f.write(fobj.getbuffer())

            log.info("Files saved", reference=str(reference_path), actual=str(actual_path), session=self.session_id)
            return reference_path, actual_path

        except Exception as e:
            log.error("Failed to save files", error=str(e), session=self.session_id)
            raise DocumentPortalException(f"Failed to save files: {str(e)}", sys) from e

    def read_pdf(self, pdf_path:str) -> str:

        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError("Encrypted PDFs are not supported.")
                parts = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text() #type: ignore
                    if text.strip():
                        parts.append(f"\n --- Page {page_num + 1} --- \n{text}")
            log.info("PDF read successfully", file=str(pdf_path), pages=len(parts))
            return "\n".join(parts)
        except Exception as e:
            log.error("Failed to read PDF", error=str(e), session=self.session_id, pdf_path=pdf_path)
            raise DocumentPortalException(f"Failed to read PDF: {str(e)}", sys) from e

    def combine_documents(self) -> str:
        try:
            docs = []
            for file in sorted(self.session_path.iterdir()):
                if file.is_file() and file.suffix.lower() == ".pdf":
                    content = self.read_pdf(str(file))
                    docs.append(f"Document: {file.name}\n{content}")

            combined_text = = "\n\n".join(docs)
            log.info("Documents combined", count=len(doc_parts), session=self.session_id)
            return combined_text
        except Exception as e:
            log.error("Failed to combine documents", error=str(e), session=self.session_id)
            raise DocumentPortalException(f"Failed to combine documents: {str(e)}", sys) from e

    def cleanup(self):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in sessions[keep_latest:]:
                shutil.rmtree(folder, ignore_errors=True)
                log.info("Old session folder deleted", path=str(folder))
        except Exception as e:
            log.error("Error cleaning old sessions", error=str(e))
            raise DocumentPortalException("Error cleaning old sessions", e) from e

        
        

