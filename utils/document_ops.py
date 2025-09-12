from fastapi import UploadFile


class FastAPIFileAdapter:
    def __init__(self, file: UploadFile):
        self._uf = file
        self.name = file.filename
    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()
def read_pdf_via_handler(handler, path: str) -> str:
    if hasattr(handler, "read_pdf"):
        return handler.read_pdf(path) # type: ignore
    if hasattr(handler, "read_"):
        return handler.read_(path) # type: ignore
    raise RuntimeError("DocHandler has neither read_pdf nor read_ method.")
    


