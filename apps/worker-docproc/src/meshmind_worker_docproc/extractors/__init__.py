"""Document extractors by format."""

from .base import ExtractionResult, Extractor
from .csv_json import extract_csv, extract_json
from .doc import extract_doc
from .docx import extract_docx
from .html import extract_html
from .pdf import extract_pdf
from .rtf import extract_rtf
from .spreadsheet import extract_xlsx, extract_xls
from .text import extract_txt, extract_md

EXTRACTORS: dict[str, Extractor] = {
    "pdf": extract_pdf,
    "docx": extract_docx,
    "doc": extract_doc,
    "xlsx": extract_xlsx,
    "xls": extract_xls,
    "txt": extract_txt,
    "md": extract_md,
    "rtf": extract_rtf,
    "html": extract_html,
    "csv": extract_csv,
    "json": extract_json,
}
