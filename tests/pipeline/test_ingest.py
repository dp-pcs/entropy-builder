import io
import zipfile
from pipeline.ingest import ingest
from pipeline.models import VaultFile


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_ingest_zip_extracts_markdown():
    zb = _make_zip({"Books/Atomic Habits.md": "# Atomic Habits\nGreat book."})
    sources = [{"type": "zip", "content": zb, "filename": "vault.zip"}]
    files = ingest(sources)
    assert any(f.path == "Books/Atomic Habits.md" for f in files)
    assert any("Atomic Habits" in f.content for f in files)


def test_ingest_zip_skips_non_text():
    zb = _make_zip({"image.png": b"\x89PNG", "note.md": "# Note"})
    sources = [{"type": "zip", "content": zb, "filename": "vault.zip"}]
    files = ingest(sources)
    paths = [f.path for f in files]
    assert "note.md" in paths
    assert "image.png" not in paths


def test_ingest_opml_converts_to_markdown():
    opml = b"""<?xml version="1.0"?>
<opml version="2.0">
  <body>
    <outline text="My big idea" _note="Details about the idea"/>
    <outline text="Another thought"/>
  </body>
</opml>"""
    sources = [{"type": "opml", "content": opml, "filename": "export.opml"}]
    files = ingest(sources)
    assert len(files) == 2
    assert any("My big idea" in f.content for f in files)
    assert any("Details about the idea" in f.content for f in files)


def test_ingest_raw_markdown():
    md = b"# My Notes\n\nSome content here."
    sources = [{"type": "file", "content": md, "filename": "notes.md"}]
    files = ingest(sources)
    assert len(files) == 1
    assert files[0].path == "notes.md"
    assert "Some content here" in files[0].content


def test_ingest_multiple_sources_merged():
    zb = _make_zip({"note1.md": "# Note 1"})
    md = b"# Note 2"
    sources = [
        {"type": "zip", "content": zb, "filename": "vault.zip"},
        {"type": "file", "content": md, "filename": "note2.md"},
    ]
    files = ingest(sources)
    paths = [f.path for f in files]
    assert "note1.md" in paths
    assert "note2.md" in paths


def test_ingest_empty_sources():
    assert ingest([]) == []
