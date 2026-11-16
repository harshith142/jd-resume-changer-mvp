import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List


def extract_keywords(jd: str) -> List[str]:
    stop = {
        "the", "and", "with", "for", "from", "this", "that", "your", "you", "are",
        "our", "will", "have", "has", "into", "about", "role", "work", "years",
        "experience", "using", "knowledge", "strong", "good", "team", "including",
        "preferred", "requirements", "responsibilities", "should", "must", "looking",
        "candidate", "opportunity", "environment", "solutions", "culture", "across",
        "well", "help", "come", "make", "impact", "every", "part", "teams", "both",
        "hands", "candidate", "candidates", "building", "deliver", "support", "success",
        "understand", "understanding", "responsible", "verbal", "written", "skills",
        "ability", "working", "develop", "developing", "build", "conduct", "provide",
        "overview", "benefits", "equal", "statement", "privacy", "policy"
    }
    raw_tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9+#.\-/]{1,25}\b", jd)
    seen = []
    for t in raw_tokens:
        clean = t.strip(".,;:()")
        low = clean.lower()
        if len(clean) >= 2 and low not in stop and low not in [x.lower() for x in seen]:
            seen.append(clean)
    return seen[:80]


def calculate_ats_audit(pdf_text: str, jd: str, pages: Optional[int] = 1) -> Dict[str, Any]:
    lower_text = pdf_text.lower()
    jd_keywords = extract_keywords(jd)

    parse_pts = 35
    if len(pdf_text.strip()) < 200:
        parse_pts -= 20
    if pages and pages > 1:
        parse_pts -= 10

    structure_pts = 20
    required_sections = ["education", "experience", "projects", "skills"]
    for sec in required_sections:
        if sec not in lower_text:
            structure_pts -= 5

    matched_in_body = []
    matched_skills_only = []
    missing_kws = []

    skills_match = re.search(r"(?:skills|technical skills)([\s\S]{0,1000})(?:experience|projects|education|$)", lower_text)
    skills_text = skills_match.group(1) if skills_match else ""
    body_text = lower_text.replace(skills_text, "")

    for kw in jd_keywords:
        kw_low = kw.lower()
        pattern = r"\b" + re.escape(kw_low) + r"\b"
        in_body = bool(re.search(pattern, body_text))
        in_skills = bool(re.search(pattern, skills_text))
        if in_body:
            matched_in_body.append(kw)
        elif in_skills:
            matched_skills_only.append(kw)
        else:
            missing_kws.append(kw)

    total_kws = len(jd_keywords) or 1
    total_matched = len(matched_in_body) + len(matched_skills_only)
    match_ratio = total_matched / total_kws
    kw_pts = round(20 * (match_ratio * 0.85 + (len(matched_in_body) / total_kws) * 0.15))
    kw_pts = max(0, min(20, kw_pts))

    content_pts = 15
    bullets = [line.strip() for line in pdf_text.splitlines() if line.strip().startswith(("-", "•", "*")) or len(line.strip()) > 35]
    quantified = [b for b in bullets if re.search(r"\d+%|\b\d+\b|[\$₹€]", b)]
    quant_rate = (len(quantified) / len(bullets)) if bullets else 0
    if quant_rate < 0.35:
        content_pts -= 5
    elif quant_rate < 0.20:
        content_pts -= 10
    weak_openers = [b for b in bullets if re.match(r"^(responsible for|helped|assisted|worked on|involved in)", b, re.I)]
    if len(weak_openers) > 2:
        content_pts -= 3

    formatting_pts = 10
    if re.search(r"[^\x00-\x7F]{5,}", pdf_text):
        formatting_pts -= 4

    overall_score = max(0, min(100, parse_pts + structure_pts + kw_pts + content_pts + formatting_pts))

    return {
        "ats_score": overall_score,
        "matched": matched_in_body + matched_skills_only,
        "matched_in_body": matched_in_body,
        "matched_skills_only": matched_skills_only,
        "missing": missing_kws[:25],
        "quant_rate": round(quant_rate * 100),
        "breakdown": {
            "parseability": parse_pts,
            "structure": structure_pts,
            "keywords": kw_pts,
            "content": content_pts,
            "formatting": formatting_pts
        }
    }


def compile_tex(tex: str):
    work = Path(tempfile.mkdtemp(prefix="resume_"))
    tex_file = work / "resume.tex"
    tex_file.write_text(tex, encoding="utf-8")

    if not shutil.which("pdflatex"):
        raise RuntimeError("pdflatex is not installed or not on PATH.")

    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error"]
    import os
    if os.name == "nt":
        cmd.append("-enable-installer")
    cmd.append("resume.tex")

    try:
        proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        raise RuntimeError("LaTeX compilation timed out after 90 seconds.")

    log = (proc.stdout + "\n" + proc.stderr)[-12000:]
    pdf = work / "resume.pdf"
    if proc.returncode != 0 or not pdf.exists():
        raise RuntimeError(f"LaTeX compilation failed:\n{log}")

    pages = None
    if shutil.which("pdfinfo"):
        p = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", p.stdout)
        if m:
            pages = int(m.group(1))

    return pdf, pages, log