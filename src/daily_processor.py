from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .llm_client import LLMClient
from .pdf_utils import read_pdf_payload
from .utils import parse_pdf_date_from_filename, save_json


class DailyProcessor:
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.llm = LLMClient(config)

    def process_pdf(self, pdf_path: str | Path) -> Path:
        pdf_path = Path(pdf_path)
        pdf_date = parse_pdf_date_from_filename(pdf_path.name)
        self.logger.info("Processing PDF: %s", pdf_path.name)

        payload = read_pdf_payload(
            pdf_path,
            include_page_images=self.config["app"].get("include_page_images", True),
            max_image_pages=self.config["app"].get("max_image_pages_per_pdf", 8),
        )
        summary = self.llm.summarize_daily_pdf(payload, pdf_date.isoformat())

        out_path = Path(self.config["paths"]["daily_json"]) / f"{pdf_path.stem}.json"
        save_json(summary.model_dump(), out_path)
        self.logger.info("Saved daily JSON: %s", out_path)
        return out_path

    def process_all(self, force: bool = False) -> List[Path]:
        input_dir = Path(self.config["paths"]["input_pdfs"])
        output_dir = Path(self.config["paths"]["daily_json"])
        results: List[Path] = []

        for pdf_path in sorted(input_dir.glob("*.pdf")):
            out_path = output_dir / f"{pdf_path.stem}.json"
            if out_path.exists() and not force:
                self.logger.info("Skipping already processed PDF: %s", pdf_path.name)
                continue
            results.append(self.process_pdf(pdf_path))

        return results
