import re
from typing import Optional


class LatexValidationError(ValueError):
    """Raised when Gemini returns malformed or unsafe LaTeX."""
    pass


def _strip_code_fences(tex: str) -> str:
    tex = tex.strip()
    tex = re.sub(r"^\s*```(?:latex|tex)?\s*", "", tex, flags=re.IGNORECASE)
    tex = re.sub(r"\s*```\s*$", "", tex)
    return tex.strip()


def _convert_markdown_links(tex: str) -> str:
    pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")

    def replace(match):
        label = match.group(1).strip()
        url = match.group(2).strip()
        label = escape_latex_text(label)
        return rf"\href{{{url}}}{{{label}}}"

    return pattern.sub(replace, tex)


def _remove_markdown_formatting(tex: str) -> str:
    tex = re.sub(r"\*\*(.*?)\*\*", r"\1", tex, flags=re.DOTALL)
    tex = re.sub(r"(?<!\\)__([^_\n]+)__", r"\1", tex)
    tex = re.sub(r"(?<!\\)\*([^*\n]+)\*", r"\1", tex)
    tex = re.sub(r"(?<!\\)_([^_\n]+)_", r"\1", tex)
    tex = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", tex)
    return tex


def _remove_markdown_bullets(tex: str) -> str:
    tex = re.sub(r"(?m)^\s*[-*+]\s+", "", tex)
    return tex


def escape_latex_text(value: str) -> str:
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
    if re.search(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\s*\{[^}]*\[[^\]\n]+\]\(", tex):
        raise LatexValidationError("Markdown link syntax remains inside LaTeX.")
    if re.search(r"\\href\s*\{\s*\[", tex):
        raise LatexValidationError("Markdown link syntax remains inside LaTeX.")


def _check_nested_href(tex: str) -> None:
    if re.search(r"\\href\s*\{[^}]*\\href", tex):
        raise LatexValidationError("Nested \\href commands are invalid in LaTeX.")


def _remove_accidental_markdown_links_leftovers(tex: str) -> str:
    if re.search(r"\[[^\]\n]+\]\(\s*https?://[^)\n]+\)", tex, flags=re.IGNORECASE):
        raise LatexValidationError("Markdown link syntax remains after sanitization.")
    if re.search(r"\[[^\]\n]+\]\(", tex):
        raise LatexValidationError("Markdown link syntax remains inside LaTeX.")
    return tex


def _check_balanced_braces(tex: str) -> None:
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
                raise LatexValidationError(f"Unexpected closing brace at character {index}.")
    if depth != 0:
        raise LatexValidationError(f"Unbalanced LaTeX braces: depth={depth}.")


def _check_document_structure(tex: str) -> None:
    if not re.search(r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}", tex):
        raise LatexValidationError("Missing \\documentclass.")
    if not re.search(r"\\begin\{document\}", tex):
        raise LatexValidationError("Missing \\begin{document}.")
    if not re.search(r"\\end\{document\}", tex):
        raise LatexValidationError("Missing \\end{document}.")
    begin_document = tex.find(r"\begin{document}")
    end_document = tex.rfind(r"\end{document}")
    if begin_document >= end_document:
        raise LatexValidationError("Invalid document environment ordering.")


def _check_no_markdown(tex: str) -> None:
    forbidden_patterns = [
        (r"```", "Markdown code fence"),
        (r"\[[^\]]+\]\([^)]+\)", "Markdown link"),
        (r"(?m)^\s*#{1,6}\s+", "Markdown heading"),
    ]
    for pattern, description in forbidden_patterns:
        if re.search(pattern, tex):
            raise LatexValidationError(f"Malformed output contains {description}.")
    if re.search(r"\*\*[^*\n]+\*\*", tex):
        raise LatexValidationError("Markdown bold syntax remains in LaTeX.")


def _check_control_characters(tex: str) -> None:
    for index, char in enumerate(tex):
        code = ord(char)
        if char in "\n\r\t":
            continue
        if code < 32:
            raise LatexValidationError(f"Invalid control character U+{code:04X} at position {index}.")


def _check_environment_balance(tex: str) -> None:
    tokens = re.findall(r"\\(begin|end)\{([^}]+)\}", tex)
    stack = []
    for kind, name in tokens:
        if kind == "begin":
            stack.append(name)
        else:
            if not stack:
                raise LatexValidationError(f"Unexpected \\end{{{name}}}.")
            expected = stack.pop()
            if expected != name:
                raise LatexValidationError(
                    f"Environment mismatch: expected \\end{{{expected}}}, found \\end{{{name}}}."
                )
    if stack:
        raise LatexValidationError("Unclosed LaTeX environment(s): " + ", ".join(stack[-10:]))


def sanitize_latex(tex: str, master_tex: Optional[str] = None) -> str:
    if not isinstance(tex, str):
        raise LatexValidationError("Generated LaTeX is not a string.")
    if not tex.strip():
        raise LatexValidationError("Generated LaTeX is empty.")
    if len(tex) > 50000:
        raise LatexValidationError("Generated LaTeX is unexpectedly large.")

    tex = _strip_code_fences(tex)

    # Fix literal \n, \r, \t sequences in LLM output
    tex = tex.replace(r"\n", "\n").replace(r"\r", "\n").replace(r"\t", " ")

    tex = re.sub(
        r"(?<!\\)\\\[(-?\d+(?:\.\d+)?(?:pt|em|ex|cm|mm|in|bp))\s*\]",
        r"\\\\[\1]",
        tex
    )
    tex = re.sub(r"\\(?:parindent|rindent|[\r\n]\s*indent)\b", r"\\parindent", tex)
    tex = re.sub(r"\\(?:parskip|rskip|[\r\n]\s*skip)\b", r"\\parskip", tex)

    if master_tex and r"\begin{document}" in master_tex and r"\begin{document}" in tex:
        master_preamble = master_tex[:master_tex.find(r"\begin{document}")].strip()
        tex_body = tex[tex.find(r"\begin{document}"):].strip()
        tex = master_preamble + "\n" + tex_body

    _check_malformed_embedded_links(tex)
    tex = re.sub(r"\\dq\b", '"', tex)
    tex = _convert_markdown_links(tex)
    _check_nested_href(tex)
    tex = _remove_markdown_formatting(tex)
    tex = _remove_markdown_bullets(tex)

    # Fix common LLM LaTeX issues
    tex = _fix_unescaped_ampersands(tex)
    tex = _fix_common_llm_issues(tex)

    tex = tex.replace("\r\n", "\n").replace("\r", "\n")
    tex = tex.replace("\ufeff", "").replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    tex = "\n".join(line.rstrip() for line in tex.splitlines()).strip()
    _remove_accidental_markdown_links_leftovers(tex)
    _check_no_markdown(tex)
    _check_control_characters(tex)
    _check_document_structure(tex)
    _check_balanced_braces(tex)
    _check_environment_balance(tex)
    return tex


def _fix_unescaped_ampersands(tex: str) -> str:
    """Escape unescaped & characters outside of tabular/array environments."""
    # Find tabular/array environments
    in_tabular = False
    result = []
    i = 0
    while i < len(tex):
        # Check for \begin{tabular} or \begin{array}
        if tex[i:].startswith(r"\begin{tabular}") or tex[i:].startswith(r"\begin{array}"):
            in_tabular = True
        elif tex[i:].startswith(r"\end{tabular}") or tex[i:].startswith(r"\end{array}"):
            in_tabular = False
        elif tex[i] == "&" and not in_tabular:
            # Check if it's already escaped
            if i == 0 or tex[i-1] != "\\":
                result.append(r"\&")
                i += 1
                continue
        result.append(tex[i])
        i += 1
    return "".join(result)


def _fix_common_llm_issues(tex: str) -> str:
    """Fix common issues from LLM-generated LaTeX."""
    # Fix \textbackslash{} appearing in regular text - it should only be in verbatim
    # Replace \textbackslash{} with a regular backslash in text context
    # But be careful not to break actual verbatim usage
    # This is a heuristic - if it's not in a verbatim environment, replace it

    # Fix \Email, \Phone etc. being treated as commands
    tex = re.sub(r'\\(Email|Phone|PhoneNumber|LinkedIn|GitHub|Website|URL|Software|Experience|Education|Summary|Skills|Projects|Certifications|Experienced|Engineer|Years|With|In|And|The|A|An|Of|To|For|From|Built|Developed|Maintained|Led|Designed|Implemented|Created|Managed|Optimized|Scalable|Applications|Using|Cloud|Platforms|Containerization|Pipelines|REST|APIs|Frontend|Components|Computer|Science|University|Tech|Present|Senior)\b', r'\1', tex)

    # Fix double backslashes in non-newline contexts (e.g., \\textbackslash{})
    tex = re.sub(r'\\\\textbackslash\{\}', r'\\textbackslash{}', tex)

    # Fix missing space after \\ in text (LLMs often do "Text\\More" instead of "Text\\\\ More")
    # But only if not in a command context
    # This is tricky - we'll be conservative

    # Fix \textbackslash{} in the middle of text - replace with just backslash
    tex = re.sub(r'\\textbackslash\{\}', r'\\', tex)

    # Fix \section{...} to \section*{...} for unnumbered sections (common in resumes)
    tex = re.sub(r'\\section\{([^}]+)\}', r'\\section*{\1}', tex)

    return tex


def clean_model_tex(value: str) -> str:
    return sanitize_latex(value)