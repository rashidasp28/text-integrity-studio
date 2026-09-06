"""Strict, in-memory document ingestion adapters for Phase 5."""

from __future__ import annotations

import base64
import io
import zipfile
from html.parser import HTMLParser
from pathlib import PurePath
from typing import Any

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException


MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 2_000
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 200
MAX_EXTRACTED_CHARACTERS = 5_000_000


class _SafeHTMLText(HTMLParser):
    BLOCKS = {"address", "article", "aside", "blockquote", "br", "div", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "p", "section", "table", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.suppressed = 0
        self.block_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "noscript"}:
            self.suppressed += 1
        elif not self.suppressed and tag in self.BLOCKS:
            self.parts.append("\n")
            self.block_count += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "noscript"} and self.suppressed:
            self.suppressed -= 1
        elif not self.suppressed and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line).strip()


def _decode_payload(encoded: str) -> bytes:
    if not isinstance(encoded, str):
        raise ValueError("Document content must be base64 text.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("Document content is not valid base64.") from error
    if not data:
        raise ValueError("The selected document is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Document exceeds the 4 MB import limit.")
    return data


def _decode_plain(data: bytes) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if b"\x00" in data:
        raise ValueError("The selected text file appears to be binary.")
    try:
        return data.decode("utf-8-sig"), warnings
    except UnicodeDecodeError as error:
        raise ValueError("Text files must use UTF-8 encoding.") from error


def _extract_html(data: bytes) -> tuple[str, dict[str, Any], list[str]]:
    text, warnings = _decode_plain(data)
    parser = _SafeHTMLText()
    parser.feed(text)
    return parser.text(), {"blocks": parser.block_count}, warnings


def _extract_docx(data: bytes) -> tuple[str, dict[str, Any], list[str]]:
    warnings = ["DOCX text was extracted for analysis; edited DOCX round-trip export is not enabled."]
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as error:
        raise ValueError("The selected DOCX is not a valid ZIP-based document.") from error
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("DOCX contains too many archive entries.")
        total = sum(info.file_size for info in infos)
        if total > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("DOCX uncompressed content exceeds the 20 MB safety limit.")
        for info in infos:
            path = PurePath(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("DOCX contains an unsafe archive path.")
            if info.filename.casefold().endswith("vbaproject.bin"):
                raise ValueError("Macro-enabled document content is not accepted.")
            if info.compress_size and info.file_size / info.compress_size > 100:
                raise ValueError("DOCX contains an archive entry with an unsafe compression ratio.")
        try:
            xml = archive.read("word/document.xml")
        except KeyError as error:
            raise ValueError("DOCX does not contain word/document.xml.") from error
    if len(xml) > MAX_UNCOMPRESSED_BYTES:
        raise ValueError("DOCX document XML exceeds the safety limit.")
    try:
        root = ElementTree.fromstring(xml)
    except (ElementTree.ParseError, DefusedXmlException) as error:
        raise ValueError("DOCX document XML is malformed or contains prohibited XML constructs.") from error
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == namespace + "t" and node.text:
                parts.append(node.text)
            elif node.tag == namespace + "tab":
                parts.append("\t")
            elif node.tag in {namespace + "br", namespace + "cr"}:
                parts.append("\n")
        paragraphs.append("".join(parts))
    text = "\n".join(paragraphs)
    tables = sum(1 for _ in root.iter(namespace + "tbl"))
    return text, {"paragraphs": len(paragraphs), "tables": tables}, warnings


def _extract_pdf(data: bytes) -> tuple[str, dict[str, Any], list[str]]:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ValueError("PDF extraction support is not installed.") from error
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
    except Exception as error:
        raise ValueError("The selected PDF could not be parsed safely.") from error
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError("PDF exceeds the 200-page extraction limit.")
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as error:
            raise ValueError("PDF text extraction failed on one or more pages.") from error
        if sum(map(len, pages)) > MAX_EXTRACTED_CHARACTERS:
            raise ValueError("Extracted PDF text exceeds the 5,000,000-character limit.")
    warnings = ["PDF text extraction does not preserve layout and cannot produce an edited PDF."]
    if not any(page.strip() for page in pages):
        warnings.append("No selectable text was found; scanned PDFs require OCR, which is not included.")
    return "\n\n".join(pages), {"pages": len(reader.pages)}, warnings


def import_document(name: str, encoded_content: str) -> dict[str, Any]:
    """Extract text from a supported document without writing it to disk."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("A document name is required.")
    suffix = PurePath(name).suffix.casefold()
    data = _decode_payload(encoded_content)
    if suffix in {".txt", ".md"}:
        text, warnings = _decode_plain(data)
        structure: dict[str, Any] = {"lines": len(text.splitlines())}
    elif suffix in {".html", ".htm"}:
        text, structure, warnings = _extract_html(data)
    elif suffix == ".docx":
        text, structure, warnings = _extract_docx(data)
    elif suffix == ".pdf":
        text, structure, warnings = _extract_pdf(data)
    else:
        raise ValueError("Supported document types are TXT, Markdown, HTML, DOCX and PDF.")
    return {
        "name": PurePath(name).name,
        "format": suffix.lstrip("."),
        "text": text,
        "character_count": len(text),
        "structure": structure,
        "warnings": warnings,
        "processing": "local-in-memory",
    }
