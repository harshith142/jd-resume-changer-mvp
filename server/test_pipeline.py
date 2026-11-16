"""
End-to-end pipeline test: verifies ATS score, page count, and PDF generation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

tex = open(os.path.join(os.path.dirname(__file__), "master_resume.tex"), encoding="utf-8").read()

jd = """
Software Engineer - Generative AI & Full-Stack
We are looking for a Software Engineer with experience in:
- Python, FastAPI, React.js
- Google Gemini API / LLM integration / Prompt Engineering
- RESTful APIs, MongoDB, SQL
- Git, Agile, CI/CD
Responsibilities: Build AI-powered web applications, integrate LLMs, design backend APIs.
Preferred: Experience with Hugging Face Transformers, NLP, conversational AI.
"""

print("Running full pipeline test...")
r = client.post("/generate", json={"jd": jd, "master_tex": tex, "target_role": "Software Engineer - GenAI"})
d = r.json()

print(f"HTTP Status : {r.status_code}")
print(f"Pages       : {d.get('page_count')}")
ats = d.get("ats_score")
print(f"ATS Score   : {ats}")
print(f"Keywords    : {len(d.get('keyword_match', []))} matched")
print(f"PDF present : {bool(d.get('pdf_base64'))}")
print(f"Changes     :")
for c in (d.get("changes") or [])[:5]:
    print(f"  - {c}")

# Assertions
assert r.status_code == 200, f"Expected 200, got {r.status_code}: {d}"
assert d.get("pdf_base64"), "No PDF returned"
assert d.get("page_count") == 1, f"Expected 1 page, got {d.get('page_count')}"
assert ats is not None, "ats_score missing from response"
assert ats >= 85, f"ATS score {ats} is below 85"

print("\nAll assertions PASSED.")
