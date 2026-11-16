import sys
from pathlib import Path

# Ensure server module can be imported regardless of execution working directory
sys.path.insert(0, str(Path(__file__).parent))

from main import sanitize_latex, LatexValidationError


TESTS = [
    (
        "markdown bold",
        r"""
\documentclass{article}
\begin{document}

**Java**
**Spring Boot**

\end{document}
""",
        True,
    ),

    (
        "markdown link",
        r"""
\documentclass{article}
\usepackage{hyperref}
\begin{document}

[LinkedIn](https://www.linkedin.com/in/example)

\end{document}
""",
        True,
    ),

    (
        "valid latex",
        r"""
\documentclass{article}
\usepackage{hyperref}

\begin{document}

\textbf{HARSHITH MARIDE}

Java | Spring Boot | REST APIs

\href{https://github.com/example}{GitHub}

\end{document}
""",
        True,
    ),

    (
        "broken braces",
        r"""
\documentclass{article}
\begin{document}

\textbf{Java

\end{document}
""",
        False,
    ),

    (
        "broken environment",
        r"""
\documentclass{article}
\begin{document}

\begin{itemize}
\item Java

\end{document}
""",
        False,
    ),

    (
        "markdown link left malformed",
        r"""
\documentclass{article}
\begin{document}

\href{[https://github.com/example](https://github.com/example)}
{GitHub}

\end{document}
""",
        False,
    ),

    (
        "corrupted line break dimension",
        r"""
\documentclass{article}
\begin{document}

Item 1 & Value 1
\[-1pt]
\hline

\end{document}
""",
        True,
    ),

    (
        "nested href rejected",
        r"""
\documentclass{article}
\begin{document}

\href{\href{https://example.com}{link}}{label}

\end{document}
""",
        False,
    ),
]


failures = 0
for name, tex, should_pass in TESTS:

    print("=" * 60)
    print(name)

    try:
        cleaned = sanitize_latex(tex)

        if should_pass:
            print("PASS")
            print(cleaned[:500])
        else:
            print("FAIL: malformed LaTeX was accepted")
            failures += 1

    except LatexValidationError as exc:

        if should_pass:
            print("FAIL:", exc)
            failures += 1
        else:
            print("PASS: correctly rejected")
            print("Reason:", exc)

if failures:
    print(f"\n{failures} test(s) failed!")
    sys.exit(1)
else:
    print("\nAll tests passed successfully!")

if failures:
    print(f"\n{failures} test(s) failed!")
    sys.exit(1)
else:
    print("\nAll tests passed successfully!")

