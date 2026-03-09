import base64
from typing import List
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    texts = []

    for page in doc:
        text = page.get_text("text")
        if text:
            texts.append(text)

    doc.close()
    return "\n".join(texts)


def render_pdf_pages_to_base64(pdf_path: str, max_pages: int = 3) -> List[str]:
    doc = fitz.open(pdf_path)
    images_b64 = []

    for i, page in enumerate(doc):
        if i >= max_pages:
            break

        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_b64.append(img_b64)

    doc.close()
    return images_b64