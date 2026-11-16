import io
import zipfile
import re
import tempfile
import subprocess
import shutil
import asyncio
from pathlib import Path
from typing import Optional


async def extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract text from various file formats."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext in ["txt", "text"]:
        return content.decode("utf-8", errors="ignore")

    elif ext in ["docx", "doc"]:
        return await extract_from_docx(content)

    elif ext == "pdf":
        return await extract_from_pdf(content)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def extract_from_docx(content: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            xml_content = z.read("word/document.xml").decode("utf-8")
            # Simple XML tag removal
            text = re.sub(r"<[^>]+>", " ", xml_content)
            text = re.sub(r"\s+", " ", text).strip()
            return text
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {e}")


async def extract_from_pdf(content: bytes) -> str:
    """Extract text from PDF using pdftotext."""
    if not shutil.which("pdftotext"):
        raise ValueError("pdftotext is not installed on the server")

    with tempfile.TemporaryDirectory() as td:
        pdf_path = Path(td) / "input.pdf"
        txt_path = Path(td) / "output.txt"
        pdf_path.write_bytes(content)

        proc = await asyncio.create_subprocess_exec(
            "pdftotext", str(pdf_path), str(txt_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0 or not txt_path.exists():
            raise ValueError(f"pdftotext failed: {stderr.decode()}")

        return txt_path.read_text(encoding="utf-8", errors="ignore")