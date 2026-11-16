import asyncio
import httpx
import json

prompt = """You are an expert resume editor and LaTeX engineer.

Your task is to tailor an existing resume to a specific job
description while preserving the candidate's factual information.

============================================================
JOB DESCRIPTION
============================================================

{
  "job_title": "Senior Software Engineer",
  "experience_level": "Senior",
  "must_have_skills": [
    "Python",
    "JavaScript",
    "SQL"
  ],
  "nice_to_have_skills": [
    "AWS",
    "GCP",
    "Docker",
    "Kubernetes"
  ],
  "responsibilities": [
    "Designing scalable systems",
    "Mentoring junior engineers",
    "Collaborating with cross-functional teams"
  ],
  "keywords": [
    "Software Engineer",
    "Python",
    "JavaScript",
    "SQL",
    "AWS",
    "GCP",
    "Docker",
    "Kubernetes",
    "Scalable Systems",
    "Mentorship"
  ]
}

============================================================
MATCH ANALYSIS
============================================================

{
  "matched_skills": [
    "Python",
    "JavaScript",
    "SQL"
  ],
  "missing_skills": [
    "AWS",
    "GCP",
    "Docker",
    "Kubernetes"
  ],
  "keywords_to_emphasize": [
    "Python",
    "JavaScript",
    "SQL",
    "Scalable Systems",
    "Mentorship"
  ],
  "keywords_not_supported": [
    "AWS",
    "GCP",
    "Docker",
    "Kubernetes"
  ]
}

============================================================
MASTER LATEX RESUME
============================================================

\\documentclass{article}
\\usepackage[margin=1in]{geometry}
\\begin{document}
\\section*{Test Resume}
\\textbf{Name:} John Doe
\\textbf{Email:} john@example.com
\\textbf{Skills:} Python, JavaScript, SQL
\\textbf{Experience:} Software Engineer at ABC Corp (2020-2023)
\\end{document}

============================================================
OBJECTIVE
============================================================

Create a highly ATS-friendly version of the MASTER LATEX RESUME
for the supplied job description.

The result must remain truthful.

============================================================
STRICT LATEX OUTPUT RULES
============================================================

The output MUST be pure, valid LaTeX.

The generated content will be saved directly as a .tex file
and compiled using pdflatex.

Therefore, DO NOT use Markdown syntax anywhere in the LaTeX.

============================================================
1. NO MARKDOWN
============================================================

NEVER use Markdown bold syntax:

WRONG:
**Java**

CORRECT:
\\textbf{Java}

NEVER use Markdown italic syntax:

WRONG:
*Software Engineer*

CORRECT:
\\textit{Software Engineer}

NEVER use Markdown links:

WRONG:
[LinkedIn](https://www.linkedin.com/...)

CORRECT:
\\href{https://www.linkedin.com/...}{LinkedIn}

NEVER use Markdown code fences.

WRONG:

```latex
\\documentclass{article}
...

CORRECT:

\\documentclass{article}
...

Do NOT output ```latex.

Do NOT output ```.

Do NOT output Markdown headings.

Do NOT output Markdown tables.

============================================================
2. LATEX DOCUMENT STRUCTURE
============================================================

The latex field MUST contain a complete LaTeX document.

It MUST begin with:

\\documentclass

It MUST contain:

\\begin{document}

It MUST end with:

\\end{document}

The output must be directly usable as a .tex file.

Do not add any explanation before \\documentclass.

Do not add any explanation after \\end{document}.

============================================================
28. OUTPUT FORMAT
============================================================

Return ONLY valid JSON according to the provided response
schema.

The latex property must contain ONLY the complete LaTeX
document.

The changes property should contain a short list describing
the modifications.

The preserved property should contain important information
that was preserved.

The ats_score property must be a number 0-100 representing the
ATS compatibility of the tailored resume. It MUST be >= 85.

Do not place Markdown fences around the LaTeX.

============================================================
29. FINAL LATEX VALIDATION
============================================================

Before returning the response, internally validate the
generated LaTeX.

Check all of the following:

Starts with \\documentclass.
Contains \\begin{document}.
Ends with \\end{document}.
Contains no Markdown code fences.
Contains no ** Markdown bold markers.
Contains no Markdown links.
Contains no [text](URL) syntax.
Contains no unnecessary Markdown headings.

============================================================
30. FINAL OUTPUT REQUIREMENT
============================================================

The latex value MUST be directly saveable as:

tailored_resume.tex

and passed directly to:

pdflatex tailored_resume.tex

without requiring manual editing.

Do not return explanations inside the LaTeX.

Do not return Markdown.

Do not return code fences.

Return the complete LaTeX document only inside the JSON
latex property.

============================================================
31. LATEX SANITIZATION CONTRACT
============================================================

The returned latex field is passed through a strict validator
and then directly to pdflatex.

The latex field MUST:

1. Be a complete LaTeX document.
2. Start with \\documentclass.
3. Contain \\begin{document}.
4. Contain \\end{document}.
5. Use ONLY LaTeX syntax.
6. NEVER contain Markdown.
7. NEVER contain Markdown links.
8. NEVER contain Markdown bold/italic syntax.
9. NEVER contain code fences.
10. NEVER contain explanations outside the LaTeX document.
11. NEVER contain ```latex or ```.
12. NEVER use **text**.
13. NEVER use [text](url).
14. Use \\textbf{text}, \\textit{text}, and
    \\href{url}{text} instead.
15. Preserve existing LaTeX commands whenever possible.
16. Do not rewrite the document into a different template.
17. Keep all candidate facts grounded in the MASTER RESUME.

Return the complete LaTeX document in the latex JSON property.

Output strictly valid JSON matching the schema:
{
  "latex": "complete LaTeX document",
  "changes": ["change descriptions"],
  "preserved": ["preserved items"],
  "ats_score": 85
}"""


async def test_ollama():
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            'http://127.0.0.1:11434/api/generate',
            json={
                'model': 'llama3.2:latest',
                'prompt': prompt,
                'format': 'json',
                'stream': False,
            }
        )
        print('Status:', resp.status_code)
        result = resp.json()
        raw_response = result.get('response', '{}')
        print('Raw response length:', len(raw_response))
        print('Raw response first 500:', repr(raw_response[:500]))

        parsed = json.loads(raw_response)
        latex = parsed.get('latex', '')
        print('Latex length:', len(latex))
        print('Latex first 500:', repr(latex[:500]))
        print('Latex last 200:', repr(latex[-200:]))

asyncio.run(test_ollama())