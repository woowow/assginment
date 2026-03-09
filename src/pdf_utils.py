from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz

from .utils import normalize_whitespace


@dataclass
class PdfPagePayload:
    page_number: int
    text: str
    image_b64: str | None = None


@dataclass
class PdfDocumentPayload:
    file_name: str
    file_path: str
    full_text: str
    pages: List[PdfPagePayload]


def read_pdf_payload(
    pdf_path: str | Path,
    include_page_images: bool = True,
    max_image_pages: int = 8,
    zoom: float = 1.5,
) -> PdfDocumentPayload:
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    pages: List[PdfPagePayload] = []
    full_text_parts: List[str] = []

    for idx, page in enumerate(doc):
        text = normalize_whitespace(page.get_text("text"))
        full_text_parts.append(f"\n\n[PAGE {idx + 1}]\n{text}")

        image_b64 = None
        if include_page_images and idx < max_image_pages:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")

        pages.append(
            PdfPagePayload(
                page_number=idx + 1,
                text=text,
                image_b64=image_b64,
            )
        )

    return PdfDocumentPayload(
        file_name=pdf_path.name,
        file_path=str(pdf_path),
        full_text="\n".join(full_text_parts).strip(),
        pages=pages,
    )
