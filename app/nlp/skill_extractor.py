"""Named Entity & Skill Extraction Engine.

Identifies and normalizes technical competencies, soft skills, and toolsets
from unstructured resume and job description text.
"""

import re
from typing import Dict, List, Set, Tuple, Any

from app.nlp.taxonomy import SYNONYM_MAP, MASTER_TAXONOMY, CATEGORY_META, get_skill_metadata
from app.parsers.text_cleaner import segment_job_description, clean_text


def build_skill_patterns() -> List[Tuple[re.Pattern, str]]:
    """Build compiled regex patterns for all synonyms sorted by length descending.

    Sorting by length descending prevents shorter substrings from eagerly masking
    longer compound terms (e.g. 'machine learning' matched before 'machine', 'c++' before 'c').
    """
    sorted_synonyms = sorted(SYNONYM_MAP.keys(), key=len, reverse=True)
    patterns = []

    for term in sorted_synonyms:
        escaped = re.escape(term)
        # Use boundary logic that handles trailing punctuation like ++ or # or .
        if term in {"c++", "c#", ".net", "ci/cd", "node.js", "vue.js", "next.js", "asp.net", "power-bi"}:
            pattern_str = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
        elif term == "c":
            pattern_str = r"(?<![a-zA-Z0-9])c(?![a-zA-Z0-9+#])"
        elif term == "r":
            pattern_str = r"(?<![a-zA-Z0-9])r(?![a-zA-Z0-9])"
        elif len(term) <= 2:
            # Stricter boundaries for 1-2 letter acronyms (e.g. 'go', 'js', 'ts', 'py', 'qa')
            pattern_str = r"\b" + escaped + r"\b"
        else:
            pattern_str = r"\b" + escaped + r"\b"

        patterns.append((re.compile(pattern_str, re.IGNORECASE), term))

    return patterns


# Precompile patterns once at module import
COMPILED_PATTERNS = build_skill_patterns()


def extract_skills_from_text(text: str) -> Dict[str, Dict[str, Any]]:
    """Extract and normalize all skills present in a text string.

    Args:
        text: Arbitrary text string.

    Returns:
        Dict of canonical skill names -> {
            'canonical_name': str,
            'category': str,
            'category_label': str,
            'description': str,
            'count': int,
            'variants_found': list[str]
        }
    """
    if not text:
        return {}

    cleaned = clean_text(text)
    extracted: Dict[str, Dict[str, Any]] = {}

    for pattern, term in COMPILED_PATTERNS:
        matches = pattern.findall(cleaned)
        if matches:
            canonical = SYNONYM_MAP[term]
            meta = get_skill_metadata(canonical)
            cat_key = meta.get("category", "languages")
            cat_label = CATEGORY_META.get(cat_key, {}).get("label", cat_key.capitalize())

            if canonical not in extracted:
                extracted[canonical] = {
                    "canonical_name": canonical,
                    "category": cat_key,
                    "category_label": cat_label,
                    "description": meta.get("description", ""),
                    "count": len(matches),
                    "variants_found": [term]
                }
            else:
                extracted[canonical]["count"] += len(matches)
                if term not in extracted[canonical]["variants_found"]:
                    extracted[canonical]["variants_found"].append(term)

    return extracted


def extract_job_skills_with_weighting(jd_text: str) -> Dict[str, Dict[str, Any]]:
    """Extract skills from a Job Description and tag them as Required or Preferred.

    Args:
        jd_text: Raw or clean job description prose.

    Returns:
        Dict of canonical skill names -> {
            'canonical_name': str,
            'category': str,
            'category_label': str,
            'description': str,
            'importance': 'required' | 'preferred',
            'weight': float
        }
    """
    segments = segment_job_description(jd_text)

    # Extract skills from segmented subsections
    required_skills = extract_skills_from_text(segments["required"])
    preferred_skills = extract_skills_from_text(segments["preferred"])
    general_skills = extract_skills_from_text(segments["general"])

    combined_job_skills: Dict[str, Dict[str, Any]] = {}

    # Skills appearing in preferred section
    for name, data in preferred_skills.items():
        combined_job_skills[name] = {
            **data,
            "importance": "preferred",
            "weight": 1.0
        }

    # Skills appearing in required or general section (defaults to required)
    for name, data in required_skills.items():
        combined_job_skills[name] = {
            **data,
            "importance": "required",
            "weight": 2.0
        }

    for name, data in general_skills.items():
        if name not in combined_job_skills:
            combined_job_skills[name] = {
                **data,
                "importance": "required",
                "weight": 2.0
            }

    return combined_job_skills
