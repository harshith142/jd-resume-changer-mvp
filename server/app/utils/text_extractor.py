"""
Text Extractor - Extract text from various file formats.
Extracted from server/main.py for reuse across the application.
"""
import base64
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict


async def extract_text_from_file(filename: str, content_base64: str) -> Dict[str, str]:
    """
    Extract text content from uploaded file.

    Args:
        filename: Original filename
        content_base64: Base64 encoded file content

    Returns:
        Dictionary with 'text' key containing extracted text

    Raises:
        ValueError: For invalid base64 or unsupported file type
    """
    try:
        raw_bytes = base64.b64decode(content_base64)
    except Exception as e:
        raise ValueError(f'Invalid base64 content: {e}')

    ext = Path(filename).suffix.lower()

    if ext in ['.txt', '.text']:
        try:
            return {'text': raw_bytes.decode('utf-8')}
        except UnicodeDecodeError:
            return {'text': raw_bytes.decode('latin-1', errors='ignore')}

    elif ext in ['.docx', '.doc']:
        try:
            import io
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                xml_content = z.read('word/document.xml').decode('utf-8')
                text = re.sub(r'<[^>]+>', ' ', xml_content)
                text = re.sub(r'\s+', ' ', text).strip()
                return {'text': text}
        except Exception as e:
            raise ValueError(f'Failed to extract text from DOCX: {e}')

    elif ext == '.pdf':
        if not shutil.which('pdftotext'):
            raise ValueError('pdftotext is not installed on the server.')
        with tempfile.TemporaryDirectory() as td:
            pdf_path = Path(td) / 'input.pdf'
            txt_path = Path(td) / 'output.txt'
            pdf_path.write_bytes(raw_bytes)
            res = subprocess.run(
                ['pdftotext', str(pdf_path), str(txt_path)],
                capture_output=True, text=True, timeout=30
            )
            if res.returncode != 0 or not txt_path.exists():
                raise ValueError(f'pdftotext failed: {res.stderr}')
            return {'text': txt_path.read_text(encoding='utf-8', errors='ignore')}

    else:
        raise ValueError(f'Unsupported file type: {ext}')


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF file using pdftotext."""
    if not shutil.which('pdftotext'):
        return ''
    with tempfile.TemporaryDirectory() as td:
        txt_out = Path(td) / 'text.txt'
        subprocess.run(['pdftotext', str(pdf_path), str(txt_out)], capture_output=True, timeout=15)
        if txt_out.exists():
            return txt_out.read_text(encoding='utf-8', errors='ignore')
    return ''