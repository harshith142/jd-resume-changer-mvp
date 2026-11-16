import os
import re
import json
import base64
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
from typing import List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="JD Resume Changer Local Compiler")

# Restrict CORS to localhost origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8765",
        "http://127.0.0.1:8765",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]

# Secondary Multi-Provider Configurations
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

class GenerateRequest(BaseModel):
    jd: str = Field(min_length=30)
    master_tex: str = Field(min_length=100)
    target_role: str = ""
    candidate_name: str = ""

class GenerateResponse(BaseModel):
    latex: str
    keyword_match: List[str]
    missing_keywords: List[str]
    changes: List[str]
    ats_notes: List[str]
    ats_score: float | None = None
    page_count: int | None = None
    compile_log: str = ""
    pdf_base64: str | None = None

SCHEMA = {
    "type": "object",
    "properties": {
        "latex": {"type": "string"},
        "keyword_match": {"type": "array", "items": {"type": "string"}},
        "missing_keywords": {"type": "array", "items": {"type": "string"}},
        "changes": {"type": "array", "items": {"type": "string"}},
        "ats_notes": {"type": "array", "items": {"type": "string"}},
        "ats_score": {
            "type": "number",
            "description": "ATS compatibility score 0-100. Must be >= 85 for a well-tailored resume."
        },
    },
    "required": ["latex", "keyword_match", "missing_keywords", "changes", "ats_notes", "ats_score"]
}

# ============================================================
# ROBUST LATEX SANITIZER + VALIDATOR
# ============================================================

class LatexValidationError(ValueError):
    """Raised when Gemini returns malformed or unsafe LaTeX."""
    pass


def _strip_code_fences(tex: str) -> str:
    """Remove Markdown code fences accidentally returned by Gemini."""
    tex = tex.strip()

    # ```latex ... ```
    tex = re.sub(
        r"^\s*```(?:latex|tex)?\s*",
        "",
        tex,
        flags=re.IGNORECASE
    )

    tex = re.sub(
        r"\s*```\s*$",
        "",
        tex
    )

    return tex.strip()


def _convert_markdown_links(tex: str) -> str:
    """
    Convert Markdown links:

        [LinkedIn](https://example.com)

    into:

        \\href{https://example.com}{LinkedIn}
    """

    pattern = re.compile(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)"
    )

    def replace(match):
        label = match.group(1).strip()
        url = match.group(2).strip()

        # Escape LaTeX-sensitive characters in the visible label.
        label = escape_latex_text(label)

        return rf"\href{{{url}}}{{{label}}}"

    return pattern.sub(replace, tex)


def _remove_markdown_formatting(tex: str) -> str:
    """
    Remove Markdown formatting that Gemini sometimes mixes into LaTeX.

    Examples:

        **Java**        -> Java
        __Java__        -> Java
        *Java*          -> Java
        _Java_          -> Java

    Existing LaTeX commands are preserved.
    """

    # Markdown bold.
    tex = re.sub(r"\*\*(.*?)\*\*", r"\1", tex, flags=re.DOTALL)

    # Markdown bold using __...__.
    tex = re.sub(r"(?<!\\)__([^_\n]+)__", r"\1", tex)

    # Markdown italic using *...*.
    # Avoid touching LaTeX commands or multiplication-like content.
    tex = re.sub(r"(?<!\\)\*([^*\n]+)\*", r"\1", tex)

    # Markdown italic using _..._.
    # Only process obvious paired underscores.
    tex = re.sub(r"(?<!\\)_([^_\n]+)_", r"\1", tex)

    # Markdown headings:
    #
    # ### Experience
    #
    # becomes:
    #
    # Experience
    tex = re.sub(
        r"(?m)^\s{0,3}#{1,6}\s+",
        "",
        tex
    )

    return tex


def _remove_markdown_bullets(tex: str) -> str:
    """
    Convert accidental Markdown bullets into LaTeX-friendly text.

        - Java
        * Spring Boot

    become ordinary lines.

    We deliberately do NOT convert them to \\item because the
    surrounding LaTeX environment may not be itemize.
    """

    tex = re.sub(
        r"(?m)^\s*[-*+]\s+",
        "",
        tex
    )

    return tex


def escape_latex_text(value: str) -> str:
    """
    Escape LaTeX special characters in plain text.

    This is used ONLY for text extracted from Markdown links.
    It must NOT be applied to the complete LaTeX document.
    """

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    return "".join(replacements.get(ch, ch) for ch in value)


def _check_malformed_embedded_links(tex: str) -> None:
    """
    Reject malformed mixed syntax such as:

        \\href{[https://github.com/example](https://github.com/example)}
        {GitHub}

    where Markdown links are placed inside LaTeX command arguments.
    """
    if re.search(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\s*\{[^}]*\[[^\]\n]+\]\(", tex):
        raise LatexValidationError(
            "Markdown link syntax remains inside LaTeX."
        )
    if re.search(r"\\href\s*\{\s*\[", tex):
        raise LatexValidationError(
            "Markdown link syntax remains inside LaTeX."
        )


def _check_nested_href(tex: str) -> None:
    """Reject nested \\href commands which are invalid in LaTeX."""
    if re.search(r"\\href\s*\{[^}]*\\href", tex):
        raise LatexValidationError(
            "Nested \\href commands are invalid in LaTeX."
        )


def _remove_accidental_markdown_links_leftovers(tex: str) -> str:
    r"""
    Detect Markdown-link remnants anywhere in the LaTeX document.

    Catches both:

        [GitHub](https://github.com/example)

    and malformed mixed syntax such as:

        \href{[https://github.com/example](https://github.com/example)}
        {GitHub}
    """

    # Standard Markdown link:
    # [text](https://...)
    if re.search(
        r"\[[^\]\n]+\]\(\s*https?://[^)\n]+\)",
        tex,
        flags=re.IGNORECASE
    ):
        raise LatexValidationError(
            "Markdown link syntax remains after sanitization."
        )

    # Markdown link embedded inside a LaTeX command/argument.
    if re.search(
        r"\[[^\]\n]+\]\(",
        tex
    ):
        raise LatexValidationError(
            "Markdown link syntax remains inside LaTeX."
        )

    return tex


def _check_balanced_braces(tex: str) -> None:
    """
    Validate { } balance while respecting escaped braces.

    Example of malformed LaTeX:

        \\textbf{Java

    will be rejected before pdflatex.
    """

    depth = 0
    escaped = False

    for index, char in enumerate(tex):

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth < 0:
                raise LatexValidationError(
                    f"Unexpected closing brace at character {index}."
                )

    if depth != 0:
        raise LatexValidationError(
            f"Unbalanced LaTeX braces: depth={depth}."
        )


def _check_document_structure(tex: str) -> None:
    """
    Ensure Gemini returned a complete LaTeX document.
    """

    if not re.search(
        r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}",
        tex
    ):
        raise LatexValidationError(
            "Missing \\documentclass."
        )

    if not re.search(
        r"\\begin\{document\}",
        tex
    ):
        raise LatexValidationError(
            "Missing \\begin{document}."
        )

    if not re.search(
        r"\\end\{document\}",
        tex
    ):
        raise LatexValidationError(
            "Missing \\end{document}."
        )

    begin_document = tex.find(r"\begin{document}")
    end_document = tex.rfind(r"\end{document}")

    if begin_document >= end_document:
        raise LatexValidationError(
            "Invalid document environment ordering."
        )


def _check_no_markdown(tex: str) -> None:
    """
    Reject Markdown that could not be safely converted.
    """

    forbidden_patterns = [
        (
            r"```",
            "Markdown code fence"
        ),
        (
            r"\[[^\]]+\]\([^)]+\)",
            "Markdown link"
        ),
        (
            r"(?m)^\s*#{1,6}\s+",
            "Markdown heading"
        ),
    ]

    for pattern, description in forbidden_patterns:
        if re.search(pattern, tex):
            raise LatexValidationError(
                f"Malformed output contains {description}."
            )

    # Markdown bold/italic markers are particularly dangerous because
    # they are easy for the model to accidentally emit.
    if re.search(r"\*\*[^*\n]+\*\*", tex):
        raise LatexValidationError(
            "Markdown bold syntax remains in LaTeX."
        )


def _check_control_characters(tex: str) -> None:
    """
    Reject invisible control characters that can corrupt the .tex file.
    """

    for index, char in enumerate(tex):

        code = ord(char)

        # Allow:
        # newline, carriage return, tab
        if char in "\n\r\t":
            continue

        # Reject ASCII control characters.
        if code < 32:
            raise LatexValidationError(
                f"Invalid control character U+{code:04X} "
                f"at position {index}."
            )


def _check_environment_balance(tex: str) -> None:
    """
    Basic \\begin{...}/\\end{...} validation.

    This catches common Gemini errors while allowing nested environments.
    """

    tokens = re.findall(
        r"\\(begin|end)\{([^}]+)\}",
        tex
    )

    stack = []

    for kind, name in tokens:

        if kind == "begin":
            stack.append(name)

        else:
            if not stack:
                raise LatexValidationError(
                    f"Unexpected \\end{{{name}}}."
                )

            expected = stack.pop()

            if expected != name:
                raise LatexValidationError(
                    f"Environment mismatch: "
                    f"expected \\end{{{expected}}}, "
                    f"found \\end{{{name}}}."
                )

    if stack:
        raise LatexValidationError(
            "Unclosed LaTeX environment(s): "
            + ", ".join(stack[-10:])
        )


def sanitize_latex(tex: str, master_tex: str | None = None) -> str:
    """
    Main LaTeX sanitization pipeline.

    Order matters:

        Gemini output
            ↓
        code-fence removal
            ↓
        preamble restoration / repairs
            ↓
        Markdown link conversion
            ↓
        Markdown formatting cleanup
            ↓
        Markdown bullet cleanup
            ↓
        structural validation
            ↓
        malformed-output rejection
            ↓
        clean LaTeX
    """

    if not isinstance(tex, str):
        raise LatexValidationError(
            "Generated LaTeX is not a string."
        )

    if not tex.strip():
        raise LatexValidationError(
            "Generated LaTeX is empty."
        )

    # Limit protects the local compiler from accidentally enormous
    # model output.
    if len(tex) > 50000:
        raise LatexValidationError(
            "Generated LaTeX is unexpectedly large."
        )

    tex = _strip_code_fences(tex)

    # Repair accidental unescaped newline dimensions from LLM JSON strings (e.g. \[-1pt] -> \\[-1pt])
    tex = re.sub(
        r"(?<!\\)\\\[(-?\d+(?:\.\d+)?(?:pt|em|ex|cm|mm|in|bp))\s*\]",
        r"\\\\[\1]",
        tex
    )

    # Repair accidental corrupted \parindent and \parskip from LLM outputs
    tex = re.sub(r"\\(?:parindent|rindent|[\r\n]\s*indent)\b", r"\\parindent", tex)
    tex = re.sub(r"\\(?:parskip|rskip|[\r\n]\s*skip)\b", r"\\parskip", tex)

    # If master_tex is provided, preserve the verified master preamble verbatim
    if master_tex and r"\begin{document}" in master_tex and r"\begin{document}" in tex:
        master_preamble = master_tex[:master_tex.find(r"\begin{document}")].strip()
        tex_body = tex[tex.find(r"\begin{document}"):].strip()
        tex = master_preamble + "\n" + tex_body

    # Check for malformed embedded markdown links inside commands before converting standalone links.
    _check_malformed_embedded_links(tex)

    # Replace invalid LaTeX quotation macros generated by LLMs like \dq
    tex = re.sub(r"\\dq\b", '"', tex)

    # Convert links BEFORE removing Markdown syntax.
    tex = _convert_markdown_links(tex)

    _check_nested_href(tex)

    tex = _remove_markdown_formatting(tex)

    tex = _remove_markdown_bullets(tex)

    tex = tex.replace("\r\n", "\n").replace("\r", "\n")

    # Remove accidental zero-width characters.
    tex = tex.replace("\ufeff", "")
    tex = tex.replace("\u200b", "")
    tex = tex.replace("\u200c", "")
    tex = tex.replace("\u200d", "")

    # Strip trailing whitespace from every line.
    tex = "\n".join(
        line.rstrip()
        for line in tex.splitlines()
    ).strip()

    _remove_accidental_markdown_links_leftovers(tex)

    _check_no_markdown(tex)

    _check_control_characters(tex)

    _check_document_structure(tex)

    _check_balanced_braces(tex)

    _check_environment_balance(tex)

    return tex


def clean_model_tex(value: str) -> str:
    """Wrapper for backward compatibility."""
    return sanitize_latex(value)

def extract_keywords(jd: str) -> list[str]:
    """
    Extract technical and professional keywords from the JD,
    filtering common English stop words and recruiter boilerplate.
    """
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

    # Find programming terms, acronyms, and multi-part technical terms (e.g., PySpark, CI/CD, React.js, C++)
    raw_tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9+#.\-/]{1,25}\b", jd)
    seen = []
    for t in raw_tokens:
        clean = t.strip(".,;:()")
        low = clean.lower()
        if len(clean) >= 2 and low not in stop and low not in [x.lower() for x in seen]:
            seen.append(clean)
    return seen[:80]


def calculate_ats_audit(pdf_text: str, jd: str, pages: int | None = 1) -> dict:
    """
    Client-grade ATS parsing audit modeled after industry standards (ToolAdda / Workday / Taleo).
    Evaluates:
      1. Parseability (35%): selectable text, single-column flow, page budget
      2. Structure (20%): standard ATS sections (Education, Skills, Experience, Projects)
      3. Keyword Match (20%): body demonstration vs. skills-only listing
      4. Content & Quantification (15%): metric/percentage density in bullets, strong verbs
      5. Formatting (10%): clean ATS headers, no unparseable blocks
    """
    lower_text = pdf_text.lower()
    jd_keywords = extract_keywords(jd)

    # 1. Parseability (35 pts max)
    parse_pts = 35
    if len(pdf_text.strip()) < 200:
        parse_pts -= 20
    if pages and pages > 1:
        parse_pts -= 10  # 1-page target

    # 2. Structure (20 pts max)
    structure_pts = 20
    required_sections = ["education", "experience", "projects", "skills"]
    for sec in required_sections:
        if sec not in lower_text:
            structure_pts -= 5

    # 3. Keyword Match (20 pts max)
    # Check if keyword is in the body (experience/projects) vs skills-only
    matched_in_body = []
    matched_skills_only = []
    missing_kws = []

    # isolate skills section if present
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

    # Reward keywords demonstrated in experience over skills-only listings
    kw_pts = round(20 * (match_ratio * 0.85 + (len(matched_in_body) / total_kws) * 0.15))
    kw_pts = max(0, min(20, kw_pts))

    # 4. Content & Metrics (15 pts max)
    content_pts = 15
    # Check bullet quantification rate (numbers, %, $, x scale)
    bullets = [line.strip() for line in pdf_text.splitlines() if line.strip().startswith(("-", "•", "*")) or len(line.strip()) > 35]
    quantified = [b for b in bullets if re.search(r"\d+%|\b\d+\b|[\$₹€]", b)]
    quant_rate = (len(quantified) / len(bullets)) if bullets else 0

    if quant_rate < 0.35:
        content_pts -= 5
    elif quant_rate < 0.20:
        content_pts -= 10

    # Weak openers check
    weak_openers = [b for b in bullets if re.match(r"^(responsible for|helped|assisted|worked on|involved in)", b, re.I)]
    if len(weak_openers) > 2:
        content_pts -= 3

    # 5. Formatting (10 pts max)
    formatting_pts = 10
    if re.search(r"[^\x00-\x7F]{5,}", pdf_text):  # encoding issues / garbage glyphs
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

def prompt_for(jd: str, master_tex: str, target_role: str) -> str:
    role_hint = target_role.strip() if target_role.strip() else "infer from the job description"
    return f"""
═══════════════════════════════════════════════════════════════
SYSTEM: PROFESSIONAL RESUME TAILORING ENGINE — LaTeX OUTPUT
═══════════════════════════════════════════════════════════════

You are a senior career consultant and LaTeX typesetter at a top-tier
recruiting firm. Your job is to produce a perfectly tailored, ATS-optimized
one-page resume in compilable LaTeX — using ONLY the facts in the master
resume below. The result will be sent directly to a real employer.

TARGET ROLE: {role_hint}

───────────────────────────────────────────────────────────────
SECTION 1 — ABSOLUTE RULES (never break these)
───────────────────────────────────────────────────────────────
TRUTHFULNESS:
• Every fact — employer, job title, date, technology, project,
  metric, certification, degree, link — must come verbatim from
  the MASTER RESUME. If it is not there, do not add it.
• Do NOT rephrase a responsibility into an achievement the resume
  does not support (e.g. "saved 30%" when no metric exists).
• Do NOT infer that a skill listed in Skills was used in a specific
  job unless the resume body explicitly says so.

CONTENT CHANGES ALLOWED:
• Reorder sections, bullets, and projects by JD relevance.
• Rewrite existing bullets for clarity and keyword alignment —
  but only using evidence already present in the master resume.
• Remove bullets and entire sections that are irrelevant to the JD.
• Combine redundant bullets into one stronger statement.
• Emphasize JD-aligned skills that are already in the master resume.
• The master resume contains a verified 9-project catalog with 4-5 bullet points each.
  SELECT the top 3-4 projects whose tech stack and domain best match the target JD.
  For the selected projects, retain at least 3-4 strong, high-impact bullet points with quantifiable metrics
  (STAR format: action verbs, technologies, and outcomes).
  Adjust vertical whitespace and concise phrasing to ensure the entire resume fits cleanly on ONE PAGE.

LATEX OUTPUT RULES:
• Return a COMPLETE, compilable .tex document — from
  \\documentclass to \\end{{document}}.
• Preserve ALL existing LaTeX commands, custom macros, packages,
  and document structure from the master resume template.
• Use ONLY LaTeX syntax. Never use Markdown inside LaTeX.
  ✗ Wrong:  **Java**       ✓ Correct: \\textbf{{Java}}
  ✗ Wrong:  *Software Eng* ✓ Correct: \\textit{{Software Engineer}}
  ✗ Wrong:  [Link](url)   ✓ Correct: \\href{{url}}{{Link}}
  ✗ Wrong:  ```latex ...  ✓ Correct: \\documentclass{{...}}
• Escape special characters: \\% \\& \\# \\$ \\_ \\{{ \\}}
• Do NOT add images, icons, tables, multi-column layouts, QR codes,
  profile photos, or any decorative element not in the original.
• Keep the resume to exactly ONE PAGE.

ATS OPTIMIZATION & SCORING:
• Naturally weave verified JD keywords into the resume body where
  the master resume evidence supports them.
• Use standard section headings: EDUCATION, SKILLS, EXPERIENCE, PROJECTS, CERTIFICATES.
• Do NOT keyword-stuff or repeat the same term unnaturally.
• In the SKILLS section, highlight and reorder the exact technologies from the master resume
  that the JD seeks (e.g. PySpark, Databricks, Azure, GCP, SQL, ETL, Testing, Agentic AI, Spring Boot, etc.).
• REALISTIC ATS SCORING:
  Evaluate the ATS match score objectively between 0 and 100 based on:
  1. Core Required Keyword Match (40%): How many must-have technical skills from the JD are present in the resume?
  2. Experience & Title Alignment (25%): Does the candidate's work history align with the target role?
  3. Action Verbs & Quantifiable Impact (20%): Are bullets framed with strong verbs and metrics?
  4. ATS Formatting & Structure (15%): Clean standard headers, no multi-column parsing traps, single-page fit.
  Provide an honest, realistic score. If high-priority JD requirements are genuinely missing from the master resume,
  reflect that gap in the score and explain it clearly in ats_notes.

───────────────────────────────────────────────────────────────
SECTION 2 — JOB DESCRIPTION
───────────────────────────────────────────────────────────────
{jd}

───────────────────────────────────────────────────────────────
SECTION 3 — MASTER RESUME (single source of truth)
───────────────────────────────────────────────────────────────
{master_tex}

───────────────────────────────────────────────────────────────
SECTION 4 — OUTPUT FORMAT
───────────────────────────────────────────────────────────────
Return a JSON object with these fields:
• latex           — the complete tailored .tex document (pure LaTeX, no Markdown)
• keyword_match   — list of JD keywords present in the tailored resume
• missing_keywords— list of JD keywords NOT in the master resume (cannot add)
• changes         — short, plain-English list of what was changed and why
• ats_notes       — list of ATS optimization tips applied
• ats_score       — realistic, objective ATS compatibility score (0-100) calculated from:
                    keyword overlap, role/title relevance, action verb strength, and ATS formatting.
                    Do NOT inflate the score if essential technical skills are missing.
""".strip()

async def call_llm(prompt: str) -> dict:
    """
    Multi-provider LLM caller with cascading fallback:
    1. Gemini API (gemini-3.5-flash-lite, etc.)
    2. OpenRouter API (if OPENROUTER_API_KEY is configured)
    3. NVIDIA NIM API (if NVIDIA_API_KEY is configured)
    4. Local Ollama (llama3.2:latest, etc.)
    """
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    gemini_errors = []

    # 1. Try Gemini Models
    if api_key:
        models_to_try = [os.getenv("GEMINI_MODEL", GEMINI_MODEL)] + [
            m for m in FALLBACK_MODELS if m != os.getenv("GEMINI_MODEL", GEMINI_MODEL)
        ]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": SCHEMA,
                "temperature": 0.2
            }
        }
        async with httpx.AsyncClient(timeout=120) as client:
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    r = await client.post(url, json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(text)
                    gemini_errors.append(f"{model}: HTTP {r.status_code}")
                except Exception as exc:
                    gemini_errors.append(f"{model}: {str(exc)[:80]}")
                    continue

    # 2. Try OpenRouter Fallback
    openrouter_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_API_KEY)
    if openrouter_key:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_key}"},
                    json={
                        "model": "meta-llama/llama-3.3-70b-instruct",
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "user", "content": prompt + "\nRespond strictly in valid JSON matching the schema."}]
                    }
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as exc:
            gemini_errors.append(f"OpenRouter: {str(exc)[:80]}")

    # 3. Try NVIDIA NIM Fallback
    nvidia_key = os.getenv("NVIDIA_API_KEY", NVIDIA_API_KEY)
    if nvidia_key:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}"},
                    json={
                        "model": "nvidia/nemotron-3-ultra-550b-a55b",
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "user", "content": prompt + "\nRespond strictly in valid JSON."}]
                    }
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as exc:
            gemini_errors.append(f"NVIDIA: {str(exc)[:80]}")

    # 4. Try Local Ollama Fallback
    ollama_host = os.getenv("OLLAMA_HOST", OLLAMA_HOST).rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt + "\nOutput strictly valid JSON with keys: latex, keyword_match, missing_keywords, changes, ats_notes, ats_score.",
                    "format": "json",
                    "stream": False
                }
            )
            if r.status_code == 200:
                raw_json = r.json().get("response", "{}")
                return json.loads(raw_json)
    except Exception as exc:
        gemini_errors.append(f"Ollama: {str(exc)[:80]}")

    raise HTTPException(502, f"All LLM providers failed or unavailable. Errors: {'; '.join(gemini_errors)}")

async def call_gemini(prompt: str):
    """Backward compatibility wrapper."""
    return await call_llm(prompt)

def compile_tex(tex: str):
    work = Path(tempfile.mkdtemp(prefix="resume_"))
    tex_file = work / "resume.tex"
    tex_file.write_text(tex, encoding="utf-8")

    if not shutil.which("pdflatex"):
        raise HTTPException(500, "pdflatex is not installed or not on PATH.")

    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error"]
    if os.name == "nt":
        cmd.append("-enable-installer")
    cmd.append("resume.tex")

    try:
        proc = subprocess.run(
            cmd, cwd=work, capture_output=True, text=True, timeout=90
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(422, "LaTeX compilation timed out after 90 seconds.")

    log = (proc.stdout + "\n" + proc.stderr)[-12000:]
    pdf = work / "resume.pdf"
    if proc.returncode != 0 or not pdf.exists():
        raise HTTPException(422, f"LaTeX compilation failed:\n{log}")

    pages = None
    if shutil.which("pdfinfo"):
        p = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", p.stdout)
        if m:
            pages = int(m.group(1))

    return pdf, pages, log

class JDRequest(BaseModel):
    jd: str = Field(min_length=30)


JD_SCHEMA = {
    "type": "object",
    "properties": {
        "job_title": {
            "type": "string"
        },
        "experience_level": {
            "type": "string"
        },
        "must_have_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "nice_to_have_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "responsibilities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "job_title",
        "experience_level",
        "must_have_skills",
        "nice_to_have_skills",
        "responsibilities",
        "keywords"
    ]
}


@app.post("/analyze-jd")
async def analyze_jd(req: JDRequest):

    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: JOB DESCRIPTION INTELLIGENCE ANALYZER
═══════════════════════════════════════════════════════════════

You are a senior technical recruiter with 15 years of experience
across software engineering, data science, product management,
finance, marketing, operations, and all other industries.

Your task is to extract a structured intelligence profile from the
job description below. This profile will be used to tailor a
candidate's resume for maximum ATS and human-reviewer alignment.

───────────────────────────────────────────────────────────────
EXTRACTION RULES
───────────────────────────────────────────────────────────────
1. Extract ONLY what is explicitly stated or strongly implied by
   the JD text. Never invent requirements.
2. Distinguish "must-have" (required) from "nice-to-have"
   (preferred/bonus) skills precisely — many JDs mark these clearly.
3. For keywords: include technical terms, domain words, tools,
   certifications, soft skills, and industry buzzwords that an ATS
   system would scan for. Think like an ATS engine.
4. Experience level: derive from years mentioned, seniority words
   (junior/mid/senior/lead/principal), or role responsibilities.
5. Responsibilities: use active verb phrases as written in the JD
   (e.g. "Design and implement scalable REST APIs").
6. This works for ALL job types — software, data, product, design,
   finance, marketing, HR, operations, consulting, research, etc.

───────────────────────────────────────────────────────────────
JOB DESCRIPTION
───────────────────────────────────────────────────────────────
{req.jd}
""".strip()

    if not GEMINI_API_KEY:
        raise HTTPException(
            500,
            "GEMINI_API_KEY is not configured."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": JD_SCHEMA,
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:

        response = await client.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload
        )

    if response.status_code >= 400:
        raise HTTPException(
            502,
            f"Gemini API error: {response.text}"
        )

    data = response.json()

    try:

        result = data[
            "candidates"
        ][0][
            "content"
        ][
            "parts"
        ][0][
            "text"
        ]

        return json.loads(result)

    except Exception as e:

        raise HTTPException(
            502,
            f"Could not parse Gemini response: {e}"
        )

class ResumeRequest(BaseModel):
    master_tex: str = Field(min_length=100)


RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_name": {
            "type": "string"
        },
        "headline": {
            "type": "string"
        },
        "technical_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "languages": {
            "type": "array",
            "items": {"type": "string"}
        },
        "frameworks": {
            "type": "array",
            "items": {"type": "string"}
        },
        "databases": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tools": {
            "type": "array",
            "items": {"type": "string"}
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "dates": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "company",
                    "role",
                    "dates",
                    "evidence"
                ]
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "dates": {"type": "string"},
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "name",
                    "dates",
                    "technologies",
                    "evidence"
                ]
            }
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program": {"type": "string"},
                    "institute": {"type": "string"},
                    "cgpa": {"type": "string"},
                    "year": {"type": "string"}
                },
                "required": [
                    "program",
                    "institute",
                    "cgpa",
                    "year"
                ]
            }
        },
        "certifications": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "candidate_name",
        "headline",
        "technical_skills",
        "languages",
        "frameworks",
        "databases",
        "tools",
        "experience",
        "projects",
        "education",
        "certifications"
    ]
}


@app.post("/analyze-resume")
async def analyze_resume(req: ResumeRequest):

    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: MASTER RESUME PROFILE EXTRACTOR
═══════════════════════════════════════════════════════════════

You are a senior resume analyst at a professional career services firm.
Your task is to parse a LaTeX-formatted master resume and produce a
structured, factual candidate profile.

This profile will be the single source of truth used in all subsequent
resume tailoring operations. Accuracy is critical — fabricated or
inferred data will cause legal and reputational harm to the candidate.

───────────────────────────────────────────────────────────────
EXTRACTION RULES (non-negotiable)
───────────────────────────────────────────────────────────────
WHAT TO EXTRACT:
• candidate_name   — Full name exactly as written in the resume header.
• headline         — Professional tagline or current role title if present.
• technical_skills — All skills explicitly listed in the Skills section.
• languages        — Programming/scripting languages only (from Skills).
• frameworks       — Libraries, frameworks, platforms listed in Skills.
• databases        — Database technologies listed in Skills.
• tools            — DevOps, cloud, IDE, testing, or other tools in Skills.
• experience       — Each job: company, role title, dates, and bullet-point
                     evidence EXACTLY as written in the resume.
• projects         — Each project: name, dates, technologies used, and
                     bullet-point evidence EXACTLY as written.
• education        — Each qualification: program, institution, CGPA/grade,
                     and year EXACTLY as written.
• certifications   — Any certifications listed, verbatim.

WHAT NOT TO DO:
✗ Do NOT infer technologies from job titles (e.g. "Java Developer"
  does not prove Java without an explicit mention).
✗ Do NOT add skills from experience bullets to the skills lists
  unless they are explicitly in the Skills section.
✗ Do NOT create achievements, metrics, or summaries not in the resume.
✗ Do NOT paraphrase or clean up — preserve exact company names,
  dates, job titles, and bullet text.
✗ Do NOT add context, commentary, or recommendations.

IMPORTANT: This profile will be used to match the candidate to job
descriptions and generate tailored resumes. Any invented fact will
appear in a real resume sent to real employers.

───────────────────────────────────────────────────────────────
MASTER RESUME (LaTeX source)
───────────────────────────────────────────────────────────────
{req.master_tex}
""".strip()

    if not GEMINI_API_KEY:
        raise HTTPException(
            500,
            "GEMINI_API_KEY is not configured."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESUME_SCHEMA,
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=90) as client:

        response = await client.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload
        )

    if response.status_code >= 400:
        raise HTTPException(
            502,
            f"Gemini API error: {response.text}"
        )

    data = response.json()

    try:

        result = data[
            "candidates"
        ][0][
            "content"
        ][
            "parts"
        ][0][
            "text"
        ]

        return json.loads(result)

    except Exception as e:

        raise HTTPException(
            502,
            f"Could not parse Gemini response: {e}"
        )


class MatchRequest(BaseModel):
    jd_profile: dict
    resume_profile: dict

class GenerateResumeRequest(BaseModel):
    master_tex: str
    jd_profile: dict
    match_result: dict

GENERATE_RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "latex": {
            "type": "string",
            "description": "Complete tailored LaTeX resume source."
        },
        "changes": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "preserved": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "ats_score": {
            "type": "number",
            "description": "ATS compatibility score 0-100. Must be >= 85."
        }
    },
    "required": [
        "latex",
        "changes",
        "preserved",
        "ats_score"
    ]
}

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "matched_responsibilities": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "jd_responsibility": {
                "type": "string"
            },
            "resume_evidence": {
                "type": "string"
            },
            "match_type": {
                "type": "string",
                "enum": ["direct", "related", "missing"]
            }
        },
        "required": [
            "jd_responsibility",
            "resume_evidence",
            "match_type"
        ]
    }
},
"keywords_not_supported": {
    "type": "array",
    "items": {
        "type": "string"
    }
},
        "overall_match": {
            "type": "number"
        },
        "matched_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_requirement": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                    "match_type": {"type": "string"}
                },
                "required": [
                    "jd_requirement",
                    "resume_evidence",
                    "match_type"
                ]
            }
        },
        "missing_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "related_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_requirement": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": [
                    "jd_requirement",
                    "resume_evidence",
                    "reason"
                ]
            }
        },
        "relevant_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "evidence": {"type": "string"},
                    "relevance": {"type": "string"}
                },
                "required": [
                    "company",
                    "evidence",
                    "relevance"
                ]
            }
        },
        "relevant_projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "evidence": {"type": "string"},
                    "relevance": {"type": "string"}
                },
                "required": [
                    "project",
                    "evidence",
                    "relevance"
                ]
            }
        },
        "keywords_to_emphasize": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "overall_match",
        "matched_skills",
        "missing_skills",
        "related_skills",
        "relevant_experience",
        "relevant_projects",
        "keywords_to_emphasize",
        "matched_responsibilities",
        "keywords_not_supported"

    ]
}

@app.post("/match")
async def match_resume(req: MatchRequest):

    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: CANDIDATE-TO-JOB MATCHING ENGINE
═══════════════════════════════════════════════════════════════

You are a senior ATS specialist and recruiter at a global hiring firm.
Your task is to perform a structured, honest compatibility assessment
between a candidate's resume profile and a job description.

This assessment drives the resume tailoring step — any inaccuracy will
produce a dishonest resume that could get the candidate rejected or
blacklisted. Be precise and conservative.

───────────────────────────────────────────────────────────────
MATCHING RULES
───────────────────────────────────────────────────────────────
WHAT TO MATCH:
• Use ONLY skills, tools, and experience explicitly in the resume profile.
• A skill listed in the JD is a DIRECT match only if it appears verbatim
  or near-verbatim in the resume (e.g. "REST API" = "REST APIs" ✓).
• A skill is a RELATED match if the candidate has a demonstrably
  transferable technology (e.g. MySQL → PostgreSQL, Flask → FastAPI).
  Clearly explain the transferability in the reason field.
• A skill is MISSING if the resume has no evidence for it at all.
• A responsibility is MATCHED if the resume contains explicit
  bullet-point evidence supporting it.
• A responsibility is MISSING if no resume evidence supports it.

WHAT NOT TO DO:
✗ Do NOT claim a skill is present just because the job title implies it.
✗ Do NOT mark "Python" as matched if the resume only lists "Django" without
  Python being explicitly mentioned.
✗ Do NOT create or infer experience not in the resume.
✗ Do NOT add any technologies to keywords_to_emphasize that are not in
  the resume — those would be lies on the final resume.

SCORING (overall_match: 0–100):
Calculate a realistic compatibility score using:
  • Must-have skill coverage (40% weight)
  • Relevant work experience alignment (30% weight)
  • Relevant project alignment (20% weight)
  • ATS keyword overlap (10% weight)
This is a compatibility estimate, NOT an employment prediction.

keywords_not_supported: List every JD keyword that has NO resume evidence.
  These will be explicitly excluded from the tailored resume.

keywords_to_emphasize: List only keywords that ARE in the resume and
  align with the JD. These will be naturally woven into the resume.

───────────────────────────────────────────────────────────────
JOB DESCRIPTION PROFILE
───────────────────────────────────────────────────────────────
{json.dumps(req.jd_profile, indent=2)}

───────────────────────────────────────────────────────────────
CANDIDATE RESUME PROFILE
───────────────────────────────────────────────────────────────
{json.dumps(req.resume_profile, indent=2)}
""".strip()

    if not GEMINI_API_KEY:
        raise HTTPException(
            500,
            "GEMINI_API_KEY is not configured."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": MATCH_SCHEMA,
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=90) as client:

        response = await client.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload
        )

    if response.status_code >= 400:
        raise HTTPException(
            502,
            f"Gemini API error: {response.text}"
        )

    data = response.json()

    try:

        result = data[
            "candidates"
        ][0][
            "content"
        ][
            "parts"
        ][0][
            "text"
        ]

        return json.loads(result)

    except Exception as e:

        raise HTTPException(
            502,
            f"Could not parse Gemini response: {e}"
        )

@app.post("/generate-resume")
async def generate_resume(req: GenerateResumeRequest):

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured."
        )

    prompt = (
        "You are an expert resume editor and LaTeX engineer.\n\n"
        "Your task is to tailor an existing resume to a specific job\n"
        "description while preserving the candidate's factual information.\n\n"
        "============================================================\n"
        "JOB DESCRIPTION\n"
        "============================================================\n\n"
        f"{json.dumps(req.jd_profile, indent=2)}\n\n"
        "============================================================\n"
        "MATCH ANALYSIS\n"
        "============================================================\n\n"
        f"{json.dumps(req.match_result, indent=2)}\n\n"
        "============================================================\n"
        "MASTER LATEX RESUME\n"
        "============================================================\n\n"
        f"{req.master_tex}\n\n"
        "============================================================\n"
        "OBJECTIVE\n"
        "============================================================\n\n"
        "Create a highly ATS-friendly version of the MASTER LATEX RESUME\n"
        "for the supplied job description.\n\n"
        "The result must remain truthful.\n\n"
        "============================================================\n"
        "STRICT LATEX OUTPUT RULES\n"
        "============================================================\n\n"
        "The output MUST be pure, valid LaTeX.\n\n"
        "The generated content will be saved directly as a `.tex` file\n"
        "and compiled using pdflatex.\n\n"
        "Therefore, DO NOT use Markdown syntax anywhere in the LaTeX.\n\n"
        "============================================================\n"
        "1. NO MARKDOWN\n"
        "============================================================\n\n"
        "NEVER use Markdown bold syntax:\n\n"
        "WRONG:\n"
        "**Java**\n\n"
        "CORRECT:\n"
        "\\textbf{Java}\n\n"
        "WRONG:\n"
        "**HARSHITH MARIDE**\n\n"
        "CORRECT:\n"
        "\\textbf{HARSHITH MARIDE}\n\n"
        "NEVER use Markdown italic syntax:\n\n"
        "WRONG:\n"
        "*Software Engineer*\n\n"
        "CORRECT:\n"
        "\\textit{Software Engineer}\n\n"
        "NEVER use Markdown links:\n\n"
        "WRONG:\n"
        "[LinkedIn](https://www.linkedin.com/...)\n\n"
        "CORRECT:\n"
        "\\href{https://www.linkedin.com/...}{LinkedIn}\n\n"
        "NEVER use Markdown code fences.\n\n"
        "WRONG:\n\n"
        "```latex\n"
        "\\documentclass{article}\n"
        "...\n\n"
        "CORRECT:\n\n"
        "\\documentclass{article}\n"
        "...\n\n"
        "Do NOT output ```latex.\n\n"
        "Do NOT output ```.\n\n"
        "Do NOT output Markdown headings.\n\n"
        "Do NOT output Markdown tables.\n\n"
        "============================================================\n"
        "2. LATEX DOCUMENT STRUCTURE\n\n"
        "The latex field MUST contain a complete LaTeX document.\n\n"
        "It MUST begin with:\n\n"
        "\\documentclass\n\n"
        "It MUST contain:\n\n"
        "\\begin{document}\n\n"
        "It MUST end with:\n\n"
        "\\end{document}\n\n"
        "The output must be directly usable as a .tex file.\n\n"
        "Do not add any explanation before \\documentclass.\n\n"
        "Do not add any explanation after \\end{document}.\n\n"
        "============================================================\n"
        "3. BOLD TEXT\n\n"
        "Use LaTeX commands for bold text.\n\n"
        "WRONG:\n\n"
        "\\textbf{Java}\n\n"
        "CORRECT:\n\n"
        "\\textbf{Java}\n\n"
        "WRONG:\n\n"
        "Spring Boot\n\n"
        "CORRECT:\n\n"
        "\\textbf{Spring Boot}\n\n"
        "Do not place Markdown ** characters inside LaTeX.\n\n"
        "============================================================\n"
        "4. ITALIC TEXT\n\n"
        "Use:\n\n"
        "\\textit{Text}\n\n"
        "Do not use Markdown *text*.\n\n"
        "============================================================\n"
        "5. HYPERLINKS\n\n"
        "All hyperlinks MUST use:\n\n"
        "\\href{URL}{display text}\n\n"
        "Example:\n\n"
        "\\href{https://www.linkedin.com/in/example/}{LinkedIn}\n\n"
        "Email:\n\n"
        "\\href{mailto:example@gmail.com}{example@gmail.com}\n\n"
        "GitHub:\n\n"
        "\\href{https://github.com/example}{GitHub}\n\n"
        "Do NOT use:\n\n"
        "LinkedIn\n\n"
        "Do NOT use:\n\n"
        "\\href{URL}\n\n"
        "Do NOT modify valid URLs unnecessarily.\n\n"
        "Preserve existing URLs from the master resume.\n\n"
        "============================================================\n"
        "6. LATEX SPECIAL CHARACTERS\n\n"
        "Escape LaTeX special characters when they appear as normal text.\n\n"
        "Use:\n\n"
        "%\n\n"
        "for percentage signs.\n\n"
        "Use:\n\n"
        "&\n\n"
        "for ampersands.\n\n"
        "Use:\n\n"
        "#\n\n"
        "for hash symbols.\n\n"
        "Use:\n\n"
        "_\n\n"
        "for underscores.\n\n"
        "Use:\n\n"
        "$\n\n"
        "for dollar signs.\n\n"
        "Use:\n\n"
        "{\n\n"
        "for literal opening braces.\n\n"
        "Use:\n\n"
        "}\n\n"
        "for literal closing braces.\n\n"
        "Use:\n\n"
        "\\textbackslash{}\n\n"
        "for a literal backslash when necessary.\n\n"
        "Example:\n\n"
        "WRONG:\n\n"
        "90% accuracy\n\n"
        "CORRECT:\n\n"
        "90% accuracy\n\n"
        "Example:\n\n"
        "WRONG:\n\n"
        "C++ & Java\n\n"
        "CORRECT:\n\n"
        "C++ & Java\n\n"
        "============================================================\n"
        "7. PRESERVE EXISTING LATEX COMMANDS\n\n"
        "The MASTER RESUME is the source template.\n\n"
        "Preserve existing custom commands such as:\n\n"
        "\\resumesection\n\n"
        "\\entry\n\n"
        "and existing formatting commands whenever possible.\n\n"
        "Do not redesign the resume.\n\n"
        "Do not replace the existing document structure unnecessarily.\n\n"
        "Do not introduce a completely different LaTeX template.\n\n"
        "============================================================\n"
        "8. PRESERVE PACKAGES\n\n"
        "Keep the existing packages from the master resume unless a\n"
        "package is genuinely required for a valid modification.\n\n"
        "Do not unnecessarily add packages.\n\n"
        "Do not remove packages that are required by existing commands.\n\n"
        "The generated document should remain compatible with pdflatex.\n\n"
        "============================================================\n"
        "9. PRESERVE ONE-PAGE DESIGN\n\n"
        "The master resume is intentionally designed to fit on one A4 page.\n\n"
        "Keep the resume to ONE PAGE.\n\n"
        "Do not add large spacing.\n\n"
        "Do not add unnecessary paragraphs.\n\n"
        "Do not add unnecessary sections.\n\n"
        "Do not increase font sizes significantly.\n\n"
        "Do not introduce graphics or images.\n\n"
        "Do not add a profile photo.\n\n"
        "Do not introduce large tables.\n\n"
        "Do not introduce multi-column layouts unless they already exist.\n\n"
        "Keep the existing compact layout.\n\n"
        "============================================================\n"
        "10. PRESERVE HEADER\n\n"
        "Preserve:\n\n"
        "Candidate name\n\n"
        "Phone number\n\n"
        "Email address\n\n"
        "LinkedIn URL\n\n"
        "Do not invent contact information.\n\n"
        "Do not change contact information.\n\n"
        "Do not remove existing valid contact information.\n\n"
        "============================================================\n"
        "11. PRESERVE EDUCATION\n\n"
        "Do not invent education.\n\n"
        "Do not change:\n\n"
        "University names\n\n"
        "Degree names\n\n"
        "CGPA\n\n"
        "Graduation years\n\n"
        "School names\n\n"
        "Academic scores\n\n"
        "Only modify formatting if necessary.\n\n"
        "============================================================\n"
        "12. PRESERVE EXPERIENCE\n\n"
        "Do not invent:\n\n"
        "Companies\n\n"
        "Job titles\n\n"
        "Employment dates\n\n"
        "Responsibilities\n\n"
        "Achievements\n\n"
        "Technologies\n\n"
        "Metrics\n\n"
        "Client names\n\n"
        "Projects\n\n"
        "Experience duration\n\n"
        "The existing master resume is the source of truth.\n\n"
        "Only rewrite an experience bullet when the new wording is\n"
        "supported by evidence already present in the master resume.\n\n"
        "============================================================\n"
        "13. EVIDENCE BOUNDARY\n\n"
        "A technology appearing in the SKILLS section does NOT\n"
        "automatically prove that the candidate used that technology\n"
        "in a specific job or project.\n\n"
        "For example, if the resume contains:\n\n"
        "Experience:\n"
        "\"Contributing to enterprise banking applications across\n"
        "frontend and backend modules.\"\n\n"
        "Skills:\n"
        "\"Java, Spring Boot\"\n\n"
        "DO NOT create:\n\n"
        "\"Developed backend applications using Java and Spring Boot.\"\n\n"
        "unless the master resume explicitly provides evidence connecting\n"
        "Java and Spring Boot to that experience.\n\n"
        "Instead, preserve the factual evidence.\n\n"
        "You may emphasize Java and Spring Boot in the SKILLS section.\n\n"
        "Do not create false experience claims.\n\n"
        "============================================================\n"
        "14. PROJECTS\n\n"
        "The master resume contains a verified 9-project catalog with 4-5 bullet points each.\n\n"
        "SELECT the top 3-4 most relevant projects for the target JD.\n\n"
        "Selection & Formatting criteria:\n"
        "- Prioritize projects whose tech stack and domain overlap with the JD keywords.\n"
        "- Prioritize projects from keywords_to_emphasize in the match analysis.\n"
        "- For each chosen project, include 3-4 strong, quantifiable bullet points (STAR format).\n"
        "- Maintain ATS-friendly keyword spellings (FastAPI, Scikit-learn, Hugging Face Transformers, BLIP-2, Spring Boot).\n"
        "- Format concisely so that the full resume fits on exactly ONE PAGE.\n\n"
        "Preserve actual project names.\n\n"
        "Preserve actual project dates.\n\n"
        "Preserve actual project technologies.\n\n"
        "Preserve actual project achievements.\n\n"
        "You may:\n\n"
        "reorder projects by relevance\n"
        "reorder bullets\n"
        "rewrite existing evidence for clarity\n"
        "emphasize supported JD terminology\n\n"
        "You may NOT:\n\n"
        "invent project features\n"
        "invent technologies\n"
        "invent metrics\n"
        "invent users\n"
        "invent performance improvements\n"
        "invent deployment details\n"
        "invent architecture\n"
        "============================================================\n"
        "15. SKILLS\n\n"
        "Prioritize skills that are already present in the master resume\n"
        "and relevant to the JD.\n\n"
        "For example, if the master resume contains:\n\n"
        "Java\n"
        "Spring Boot\n"
        "REST APIs\n"
        "SQL\n"
        "Git\n"
        "React.js\n\n"
        "and the JD requests these skills, they may be placed earlier\n"
        "in the Skills section.\n\n"
        "Do NOT add:\n\n"
        "Docker\n\n"
        "AWS\n\n"
        "Microservices\n\n"
        "or any other technology unless it is explicitly supported\n"
        "by the master resume.\n\n"
        "Do not add a missing JD technology simply to increase ATS score.\n\n"
        "============================================================\n"
        "16. ATS OPTIMIZATION\n\n"
        "Use supported JD keywords naturally.\n\n"
        "Prioritize:\n\n"
        "keywords_to_emphasize\n\n"
        "from the match analysis.\n\n"
        "A keyword may be used in:\n\n"
        "Skills\n"
        "Experience\n"
        "Projects\n\n"
        "ONLY when the master resume provides evidence supporting it.\n\n"
        "Do not keyword stuff.\n\n"
        "Do not repeat the same keyword unnaturally.\n\n"
        "Do not insert unsupported keywords simply because they appear\n"
        "in the job description.\n\n"
        "TARGET ATS SCORE: >= 85/100.\n\n"
        "Achieve this by:\n"
        "- Maximising JD keyword coverage from supported evidence.\n"
        "- Using strong action verbs (Architected, Engineered, Developed, Optimized).\n"
        "- Including quantifiable achievements wherever present in the master resume.\n"
        "- Using standard ATS-readable section headings.\n"
        "- Prioritising the most JD-relevant projects (select top 3-4 from the master resume).\n\n"
        "============================================================\n"
        "17. MISSING SKILLS\n\n"
        "Never add items from:\n\n"
        "missing_skills\n\n"
        "to the resume.\n\n"
        "Never add items from:\n\n"
        "keywords_not_supported\n\n"
        "to the resume.\n\n"
        "For example, if:\n\n"
        "missing_skills:\n"
        "Docker\n"
        "AWS\n"
        "Microservices\n\n"
        "then the generated resume MUST NOT claim:\n\n"
        "Docker experience\n\n"
        "AWS experience\n\n"
        "Microservices experience\n\n"
        "============================================================\n"
        "18. RELATED SKILLS\n\n"
        "A related skill is NOT the same as a direct skill.\n\n"
        "Do not convert a related skill into a direct claim.\n\n"
        "Example:\n\n"
        "JD:\n"
        "AWS\n\n"
        "Resume:\n"
        "Google Cloud\n"
        "Azure\n\n"
        "Do NOT write:\n\n"
        "\"AWS experience\"\n\n"
        "Do NOT write:\n\n"
        "\"Developed applications on AWS\"\n\n"
        "unless AWS is explicitly supported by the master resume.\n\n"
        "============================================================\n"
        "19. RESPONSIBILITIES\n\n"
        "Use matched responsibilities only when the resume evidence\n"
        "supports the responsibility.\n\n"
        "Do not convert a JD responsibility into a claimed achievement.\n\n"
        "Example:\n\n"
        "JD:\n"
        "\"Write clean and maintainable code.\"\n\n"
        "If the resume contains no evidence supporting this,\n"
        "do NOT create:\n\n"
        "\"Wrote clean and maintainable code.\"\n\n"
        "============================================================\n"
        "20. METRICS\n\n"
        "NEVER invent metrics.\n\n"
        "Do not invent:\n\n"
        "percentages\n\n"
        "performance improvements\n\n"
        "latency\n\n"
        "users\n\n"
        "revenue\n\n"
        "accuracy\n\n"
        "cost savings\n\n"
        "team size\n\n"
        "deployment counts\n\n"
        "API counts\n\n"
        "response times\n\n"
        "If the master resume says:\n\n"
        "\"90% accuracy\"\n\n"
        "you may preserve:\n\n"
        "\"90% accuracy\"\n\n"
        "But you may not change it to:\n\n"
        "\"95% accuracy\"\n\n"
        "============================================================\n"
        "21. DATES\n\n"
        "Preserve existing dates exactly.\n\n"
        "Do not invent dates.\n\n"
        "Do not change employment dates.\n\n"
        "Do not change project dates.\n\n"
        "Do not change graduation dates.\n\n"
        "============================================================\n"
        "22. EMPLOYERS AND CLIENTS\n\n"
        "Preserve existing employer and client names.\n\n"
        "Do not invent clients.\n\n"
        "Do not infer clients.\n\n"
        "Do not replace one employer with another.\n\n"
        "============================================================\n"
        "23. CERTIFICATIONS\n\n"
        "Preserve existing certifications.\n\n"
        "Do not invent certifications.\n\n"
        "Do not add JD-required certifications unless they already\n"
        "exist in the master resume.\n\n"
        "Preserve certification links.\n\n"
        "============================================================\n"
        "24. LINKS\n\n"
        "Preserve valid existing links.\n\n"
        "For existing links use:\n\n"
        "\\href{URL}{[Link]}\n\n"
        "or an appropriate existing display label.\n\n"
        "Do not convert URLs into Markdown.\n\n"
        "Do not duplicate URLs.\n\n"
        "Do not remove valid project links.\n\n"
        "Do not invent URLs.\n\n"
        "============================================================\n"
        "25. SECTION ORDER\n\n"
        "Prefer preserving the master resume's section order.\n\n"
        "Do not create unnecessary new sections.\n\n"
        "Do not create:\n\n"
        "OBJECTIVE\n\n"
        "DECLARATION\n\n"
        "REFERENCES\n\n"
        "unless they already exist in the master resume.\n\n"
        "============================================================\n"
        "26. CONTENT PRIORITIZATION\n\n"
        "When space is limited, prioritize:\n\n"
        "Relevant professional experience\n"
        "Relevant technical skills\n"
        "Relevant projects\n"
        "Education\n"
        "Certifications\n"
        "Activities\n\n"
        "Do not remove critical professional experience.\n\n"
        "Do not remove contact information.\n\n"
        "Do not remove education.\n\n"
        "============================================================\n"
        "27. ONE-PAGE SPACE MANAGEMENT\n\n"
        "If the generated resume becomes too long:\n\n"
        "First reduce unnecessary wording.\n\n"
        "Then shorten verbose bullet points.\n\n"
        "Then remove redundant phrases.\n\n"
        "Then reduce unnecessary vertical spacing.\n\n"
        "Do NOT fabricate information.\n\n"
        "Do NOT remove important evidence merely to save space.\n\n"
        "Do NOT create a second page.\n\n"
        "============================================================\n"
        "28. OUTPUT FORMAT\n\n"
        "Return ONLY valid JSON according to the provided response\n"
        "schema.\n\n"
        "The latex property must contain ONLY the complete LaTeX\n"
        "document.\n\n"
        "The changes property should contain a short list describing\n"
        "the modifications.\n\n"
        "The preserved property should contain important information\n"
        "that was preserved.\n\n"
        "The ats_score property must be a number 0-100 representing the\n"
        "ATS compatibility of the tailored resume. It MUST be >= 85.\n"
        "Calculate it based on: JD keyword coverage, section structure,\n"
        "action verb strength, quantifiable achievements, and formatting.\n\n"
        "Do not place Markdown fences around the LaTeX.\n\n"
        "============================================================\n"
        "29. FINAL LATEX VALIDATION\n\n"
        "Before returning the response, internally validate the\n"
        "generated LaTeX.\n\n"
        "Check all of the following:\n\n"
        "Starts with \\documentclass.\n"
        "Contains \\begin{document}.\n"
        "Ends with \\end{document}.\n"
        "Contains no Markdown code fences.\n"
        "Contains no ** Markdown bold markers.\n"
        "Contains no Markdown links.\n"
        "Contains no [text](URL) syntax.\n"
        "Contains no unnecessary Markdown headings.\n"
        "Every \\href uses:\n\n"
        "\\href{URL}{display text}\n\n"
        "Percentage signs are escaped:\n\n"
        "%\n\n"
        "Ampersands used as normal text are escaped:\n\n"
        "&\n\n"
        "Existing custom commands remain valid.\n"
        "Existing packages remain available.\n"
        "Braces are balanced.\n"
        "The document remains a complete LaTeX document.\n"
        "The resume remains designed for one A4 page.\n\n"
        "If any Markdown syntax is present, remove it before returning\n"
        "the response.\n\n"
        "If any invalid LaTeX syntax is present, correct it before\n"
        "returning the response.\n\n"
        "============================================================\n"
        "30. FINAL OUTPUT REQUIREMENT\n\n"
        "The latex value MUST be directly saveable as:\n\n"
        "tailored_resume.tex\n\n"
        "and passed directly to:\n\n"
        "pdflatex tailored_resume.tex\n\n"
        "without requiring manual editing.\n\n"
        "Do not return explanations inside the LaTeX.\n\n"
        "Do not return Markdown.\n\n"
        "Do not return code fences.\n\n"
        "Return the complete LaTeX document only inside the JSON\n"
        "latex property.\n\n"
        "============================================================\n"
        "31. LATEX SANITIZATION CONTRACT\n\n"
        "The returned latex field is passed through a strict validator\n"
        "and then directly to pdflatex.\n\n"
        "The latex field MUST:\n\n"
        "1. Be a complete LaTeX document.\n"
        "2. Start with \\documentclass.\n"
        "3. Contain \\begin{document}.\n"
        "4. Contain \\end{document}.\n"
        "5. Use ONLY LaTeX syntax.\n"
        "6. NEVER contain Markdown.\n"
        "7. NEVER contain Markdown links.\n"
        "8. NEVER contain Markdown bold/italic syntax.\n"
        "9. NEVER contain code fences.\n"
        "10. NEVER contain explanations outside the LaTeX document.\n"
        "11. NEVER contain ```latex or ```.\n"
        "12. NEVER use **text**.\n"
        "13. NEVER use [text](url).\n"
        "14. Use \\textbf{text}, \\textit{text}, and\n"
        "    \\href{url}{text} instead.\n"
        "15. Preserve existing LaTeX commands whenever possible.\n"
        "16. Do not rewrite the document into a different template.\n"
        "17. Keep all candidate facts grounded in the MASTER RESUME.\n\n"
        "Return the complete LaTeX document in the latex JSON property.\n"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": GENERATE_RESUME_SCHEMA,
            "temperature": 0.1
        }
    }

    try:

        async with httpx.AsyncClient(timeout=180) as client:

            response = await client.post(
                url,
                params={
                    "key": GEMINI_API_KEY
                },
                json=payload
            )

    except httpx.RequestError as e:

        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to Gemini API: {str(e)}"
        )

    if response.status_code >= 400:

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Gemini API request failed",
                "status_code": response.status_code,
                "response": response.text
            }
        )

    try:

        data = response.json()

        result = (
            data["candidates"][0]
            ["content"]
            ["parts"][0]
            ["text"]
        )

        generated = json.loads(result)

    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Could not parse generated resume",
                "error": str(e),
                "raw_response": response.text
            }
        )

    if not generated.get("latex"):
        raise HTTPException(
            status_code=502,
            detail="Gemini returned empty LaTeX."
        )

    try:
        generated["latex"] = sanitize_latex(generated["latex"], master_tex=req.master_tex)
    except LatexValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Gemini generated malformed LaTeX.",
                "error": str(exc),
                "stage": "latex_sanitization"
            }
        )

    return generated

@app.get("/health")
def health():
    key_set = bool(os.getenv("GEMINI_API_KEY", GEMINI_API_KEY))
    return {
        "ok": True,
        "gemini_model": os.getenv("GEMINI_MODEL", GEMINI_MODEL),
        "pdflatex": bool(shutil.which("pdflatex")),
        "pdfinfo": bool(shutil.which("pdfinfo")),
        "pdftotext": bool(shutil.which("pdftotext")),
        "gemini_key_configured": key_set
    }

@app.get("/master-resume")
def get_master_resume():
    master_path = Path(__file__).parent / "master_resume.tex"
    if not master_path.exists():
        raise HTTPException(status_code=404, detail="master_resume.tex not found on server.")
    return {"latex": master_path.read_text(encoding="utf-8")}

class ExtractTextRequest(BaseModel):
    filename: str
    content_base64: str

@app.post("/extract-text")
async def extract_text_endpoint(req: ExtractTextRequest):
    try:
        raw_bytes = base64.b64decode(req.content_base64)
    except Exception as e:
        raise HTTPException(400, f"Invalid base64 content: {e}")

    ext = Path(req.filename).suffix.lower()

    if ext in [".txt", ".text"]:
        try:
            return {"text": raw_bytes.decode("utf-8")}
        except UnicodeDecodeError:
            return {"text": raw_bytes.decode("latin-1", errors="ignore")}

    elif ext in [".docx", ".doc"]:
        try:
            import io
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                xml_content = z.read("word/document.xml").decode("utf-8")
                text = re.sub(r"<[^>]+>", " ", xml_content)
                text = re.sub(r"\s+", " ", text).strip()
                return {"text": text}
        except Exception as e:
            raise HTTPException(422, f"Failed to extract text from DOCX: {e}")

    elif ext == ".pdf":
        if not shutil.which("pdftotext"):
            raise HTTPException(500, "pdftotext is not installed on the server.")
        with tempfile.TemporaryDirectory() as td:
            pdf_path = Path(td) / "input.pdf"
            txt_path = Path(td) / "output.txt"
            pdf_path.write_bytes(raw_bytes)
            res = subprocess.run(
                ["pdftotext", str(pdf_path), str(txt_path)],
                capture_output=True, text=True, timeout=30
            )
            if res.returncode != 0 or not txt_path.exists():
                raise HTTPException(422, f"pdftotext failed: {res.stderr}")
            return {"text": txt_path.read_text(encoding="utf-8", errors="ignore")}

    else:
        raise HTTPException(400, f"Unsupported file type: {ext}")

@app.post("/generate")
async def generate(req: GenerateRequest):
    result = await call_gemini(prompt_for(req.jd, req.master_tex, req.target_role))
    
    try:
        latex = sanitize_latex(result["latex"], master_tex=req.master_tex)
    except LatexValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Gemini generated malformed LaTeX.",
                "error": str(exc),
                "stage": "latex_sanitization"
            }
        )

    pdf_path, pages, log = compile_tex(latex)

    # Extract clean text directly from the compiled PDF for genuine ATS audit
    pdf_text = ""
    if shutil.which("pdftotext"):
        with tempfile.TemporaryDirectory() as td:
            txt_out = Path(td) / "text.txt"
            subprocess.run(["pdftotext", str(pdf_path), str(txt_out)], capture_output=True, timeout=15)
            if txt_out.exists():
                pdf_text = txt_out.read_text(encoding="utf-8", errors="ignore")
    if not pdf_text:
        pdf_text = re.sub(r"\\[a-zA-Z]+(\{[^}]*\})?", " ", latex)

    # Run genuine client-grade ATS audit
    audit = calculate_ats_audit(pdf_text, req.jd, pages=pages)

    # Balance between LLM semantic score and genuine ATS text parsing score
    llm_score = result.get("ats_score")
    if llm_score is not None:
        computed_ats = round(0.5 * float(llm_score) + 0.5 * float(audit["ats_score"]))
    else:
        computed_ats = audit["ats_score"]

    matched = audit["matched"]
    missing = audit["missing"]

    ats_insights = result.get("ats_notes", [])
    ats_insights.append(f"ATS Parseability: {audit['breakdown']['parseability']}/35 | Structure: {audit['breakdown']['structure']}/20 | Keyword Match: {audit['breakdown']['keywords']}/20")
    if audit["quant_rate"] > 0:
        ats_insights.append(f"Quantification metric density: {audit['quant_rate']}% of bullet points contain numbers/metrics.")
    if pages == 1:
        ats_insights.append("PDF length: Exactly 1 page (optimal single-page ATS budget).")
    elif pages:
        ats_insights.append(f"PDF length: {pages} pages (target is 1 page).")

    import base64
    pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")

    return {
        "latex": latex,
        "keyword_match": matched,
        "missing_keywords": missing,
        "changes": result["changes"],
        "ats_score": computed_ats,
        "ats_notes": ats_insights,
        "page_count": pages,
        "compile_log": log[-4000:],
        "pdf_base64": pdf_b64,
    }