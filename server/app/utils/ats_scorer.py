"""
ATS Scorer - Client-grade ATS compatibility audit for generated resumes.
Extracted from server/main.py for reuse across the application.
"""
import re
from typing import List, Dict, Any


# Stop words for keyword extraction
STOP_WORDS = {
    'the', 'and', 'with', 'for', 'from', 'this', 'that', 'your', 'you', 'are',
    'our', 'will', 'have', 'has', 'into', 'about', 'role', 'work', 'years',
    'experience', 'using', 'knowledge', 'strong', 'good', 'team', 'including',
    'preferred', 'requirements', 'responsibilities', 'should', 'must', 'looking',
    'candidate', 'opportunity', 'environment', 'solutions', 'culture', 'across',
    'well', 'help', 'come', 'make', 'impact', 'every', 'part', 'teams', 'both',
    'hands', 'candidate', 'candidates', 'building', 'deliver', 'support', 'success',
    'understand', 'understanding', 'responsible', 'verbal', 'written', 'skills',
    'ability', 'working', 'develop', 'developing', 'build', 'conduct', 'provide',
    'overview', 'benefits', 'equal', 'statement', 'privacy', 'policy'
}


def extract_keywords(jd: str) -> List[str]:
    """Extract relevant keywords from job description."""
    # Handle special patterns like C++, C#, .NET, etc.
    # First extract special tech tokens - use lookbehind/lookahead for word boundaries with special chars
    special_patterns = [
        r'(?<!\w)C\+\+(?!\w)',  # C++
        r'(?<!\w)C#(?!\w)',     # C#
        r'(?<!\w)\.NET(?!\w)',    # .NET
        r'(?<!\w)ASP\.NET(?!\w)',
        r'(?<!\w)Node\.js(?!\w)',
        r'(?<!\w)React\.js(?!\w)',
        r'(?<!\w)Vue\.js(?!\w)',
        r'(?<!\w)TypeScript(?!\w)',
        r'(?<!\w)JavaScript(?!\w)',
    ]
    special_tokens = []
    for pattern in special_patterns:
        special_tokens.extend(re.findall(pattern, jd, re.IGNORECASE))

    # Extract regular tokens
    raw_tokens = re.findall(r'\b[A-Za-z][A-Za-z0-9#.\-/]{1,25}\b', jd)
    seen = []
    for t in raw_tokens:
        clean = t.strip('.,;:()')
        low = clean.lower()
        if len(clean) >= 2 and low not in STOP_WORDS and low not in [x.lower() for x in seen]:
            seen.append(clean)
    # Add special tokens at the front (they're more specific)
    for t in special_tokens:
        if t.lower() not in [x.lower() for x in seen]:
            seen.insert(0, t)
    return seen[:80]


def calculate_ats_score(pdf_text: str, jd: str, pages: int = None) -> Dict[str, Any]:
    """
    Calculate genuine client-grade ATS compatibility score.

    Args:
        pdf_text: Extracted text from compiled PDF
        jd: Job description text
        pages: Number of pages in PDF (optional)

    Returns:
        Dictionary with ats_score, matched keywords, missing keywords, and breakdown
    """
    lower_text = pdf_text.lower()
    jd_keywords = extract_keywords(jd)

    # Parseability (35 pts) - basic text extraction quality
    parse_pts = 35
    if len(pdf_text.strip()) < 200:
        parse_pts -= 20
    if pages and pages > 1:
        parse_pts -= 10

    # Structure (20 pts) - required sections present
    structure_pts = 20
    required_sections = ['education', 'experience', 'projects', 'skills']
    for sec in required_sections:
        if sec not in lower_text:
            structure_pts -= 5

    # Keyword matching
    matched_in_body = []
    matched_skills_only = []
    missing_kws = []

    # Separate skills section from body
    skills_match = re.search(r'(?:skills|technical skills)([\s\S]{0,1000})(?:experience|projects|education|$)', lower_text)
    skills_text = skills_match.group(1) if skills_match else ''
    body_text = lower_text.replace(skills_text, '')

    for kw in jd_keywords:
        kw_low = kw.lower()
        pattern = r'\b' + re.escape(kw_low) + r'\b'
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

    # Content quality (15 pts) - quantified achievements
    content_pts = 15
    bullets = [line.strip() for line in pdf_text.splitlines()
               if line.strip().startswith(('-', '•', '*')) or len(line.strip()) > 35]
    quantified = [b for b in bullets if re.search(r'\d+%|\b\d+\b|[\$€₹]', b)]
    quant_rate = (len(quantified) / len(bullets)) if bullets else 0
    if quant_rate < 0.35:
        content_pts -= 5
    elif quant_rate < 0.20:
        content_pts -= 10
    weak_openers = [b for b in bullets if re.match(r'^(responsible for|helped|assisted|worked on|involved in)', b, re.I)]
    if len(weak_openers) > 2:
        content_pts -= 3

    # Formatting (10 pts) - no encoding issues
    formatting_pts = 10
    if re.search(r'[^\x00-\x7F]{5,}', pdf_text):
        formatting_pts -= 4

    overall_score = max(0, min(100, parse_pts + structure_pts + kw_pts + content_pts + formatting_pts))

    return {
        'ats_score': overall_score,
        'matched': matched_in_body + matched_skills_only,
        'matched_in_body': matched_in_body,
        'matched_skills_only': matched_skills_only,
        'missing': missing_kws[:25],
        'quant_rate': round(quant_rate * 100),
        'breakdown': {
            'parseability': parse_pts,
            'structure': structure_pts,
            'keywords': kw_pts,
            'content': content_pts,
            'formatting': formatting_pts
        }
    }