# entropy_builder/pipeline/ingest.py
import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from .models import VaultFile

_TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml"}


def ingest(sources: list[dict]) -> list[VaultFile]:
    """
    sources: list of {"type": "zip"|"opml"|"file", "content": bytes, "filename": str}
    Returns: list of VaultFile with normalized content
    """
    files = []
    for source in sources:
        t = source["type"]
        if t == "zip":
            files.extend(_extract_zip(source["content"]))
        elif t == "opml":
            files.extend(_parse_opml(source["content"]))
        elif t == "file":
            files.extend(_process_file(source["content"], source["filename"]))
    return files


def _extract_zip(content: bytes) -> list[VaultFile]:
    files = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            if Path(name).suffix.lower() in _TEXT_EXTENSIONS:
                try:
                    with zf.open(name) as f:
                        text = f.read().decode("utf-8", errors="replace")
                    files.append(VaultFile(path=name, content=text))
                except Exception:
                    pass
    return files


def _parse_opml(content: bytes) -> list[VaultFile]:
    files = []
    try:
        root = ElementTree.fromstring(content.decode("utf-8"))
        for outline in root.findall(".//outline"):
            text = outline.get("text", "").strip()
            note = outline.get("_note", "").strip()
            if len(text) > 2:
                body = f"# {text}\n\n{note}" if note else f"# {text}"
                safe_name = "".join(c for c in text if c.isalnum() or c in " -_")[:50]
                files.append(VaultFile(path=f"workflowy/{safe_name}.md", content=body))
    except ElementTree.ParseError:
        pass
    return files


def _process_file(content: bytes, filename: str) -> list[VaultFile]:
    ext = Path(filename).suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return [VaultFile(path=filename, content=content.decode("utf-8", errors="replace"))]
    if ext == ".pdf":
        return [VaultFile(path=filename[:-4] + ".md", content=_extract_pdf(content))]
    if ext == ".docx":
        return [VaultFile(path=filename[:-5] + ".md", content=_extract_docx(content))]
    return []


def _extract_pdf(content: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def _extract_docx(content: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"
