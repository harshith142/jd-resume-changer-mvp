"""
Pytest configuration for server tests.
"""
import os
import pytest
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set dummy API keys for tests that need them
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("GROK_API_KEY", "test-grok-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("NVIDIA_API_KEY", "test-nvidia-key")


@pytest.fixture
def sample_latex():
    """Sample valid LaTeX for testing."""
    return r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{hyperref}
\begin{document}
\textbf{John Doe}
\textit{Software Engineer}
\href{mailto:john@example.com}{john@example.com}
\section*{Experience}
Software Engineer at Google (2020-2023)
\begin{itemize}
    \item Developed Python applications using Django
    \item Built React frontend components
\end{itemize}
\section*{Education}
BS Computer Science, Stanford University (2020)
\section*{Skills}
Python, Django, React, JavaScript, SQL
\end{document}
"""


@pytest.fixture
def sample_jd():
    """Sample job description for testing."""
    return """
We are looking for a Senior Software Engineer with 5+ years of experience in Python and React.
Required skills: Python, Django, React, JavaScript, SQL, AWS, Docker.
Preferred: Kubernetes, GraphQL, TypeScript.
"""