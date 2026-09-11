"""Gap Analysis & Set Difference Matching Engine.

Computes mathematical set difference, weighted qualification scores,
category-specific coverage, and composite readiness ratings.
"""

from typing import Dict, List, Set, Any

from backend.config import REQUIRED_SKILL_WEIGHT, PREFERRED_SKILL_WEIGHT, SKILL_MATCH_RATIO, SEMANTIC_SIMILARITY_RATIO
from backend.nlp.taxonomy import CATEGORY_META
from backend.nlp.skill_extractor import extract_skills_from_text, extract_job_skills_with_weighting
from backend.engine.vector_similarity import compute_vector_similarity
from backend.parsers.text_cleaner import get_benchmark_job_description


def perform_gap_analysis(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Execute end-to-end skill gap analysis between resume and job description.

    Args:
        resume_text: Extracted plain text of candidate resume.
        jd_text: Extracted plain text of target job description.

    Returns:
        Structured analysis report including set differences, weighted match scores,
        category coverage, and readiness rating.
    """
    # 1. Skill Extraction with Section Weighting
    resume_skills_dict = extract_skills_from_text(resume_text)
    job_skills_dict = extract_job_skills_with_weighting(jd_text)

    # If the target JD contained no recognized skills or was empty,
    # auto-benchmark against standard role requirements to ensure meaningful gap analysis
    if not job_skills_dict:
        benchmark_jd = get_benchmark_job_description("", resume_text)
        job_skills_dict = extract_job_skills_with_weighting(benchmark_jd)
        jd_text = benchmark_jd

    resume_skill_set: Set[str] = set(resume_skills_dict.keys())
    job_skill_set: Set[str] = set(job_skills_dict.keys())

    # 2. Mathematical Set Operations
    matched_names = job_skill_set.intersection(resume_skill_set)
    missing_names = job_skill_set.difference(resume_skill_set)
    additional_names = resume_skill_set.difference(job_skill_set)

    # 3. Weighted Score Computation
    total_possible_weight = 0.0
    matched_weight = 0.0

    matched_skills = []
    missing_required = []
    missing_preferred = []
    additional_skills = []

    for name in matched_names:
        item = job_skills_dict[name]
        weight = item.get("weight", REQUIRED_SKILL_WEIGHT)
        total_possible_weight += weight
        matched_weight += weight
        matched_skills.append({
            "name": name,
            "category": item["category"],
            "category_label": item["category_label"],
            "importance": item["importance"],
            "weight": weight,
            "description": item["description"]
        })

    for name in missing_names:
        item = job_skills_dict[name]
        weight = item.get("weight", REQUIRED_SKILL_WEIGHT)
        total_possible_weight += weight

        record = {
            "name": name,
            "category": item["category"],
            "category_label": item["category_label"],
            "importance": item["importance"],
            "weight": weight,
            "description": item["description"]
        }
        if item["importance"] == "required":
            missing_required.append(record)
        else:
            missing_preferred.append(record)

    for name in additional_names:
        item = resume_skills_dict[name]
        additional_skills.append({
            "name": name,
            "category": item["category"],
            "category_label": item["category_label"],
            "description": item["description"]
        })

    # Sort skill lists alphabetically by name
    matched_skills.sort(key=lambda x: x["name"])
    missing_required.sort(key=lambda x: x["name"])
    missing_preferred.sort(key=lambda x: x["name"])
    additional_skills.sort(key=lambda x: x["name"])

    # Calculate skill match percentage
    if total_possible_weight > 0:
        skill_match_pct = round((matched_weight / total_possible_weight) * 100.0, 1)
    else:
        skill_match_pct = 100.0 if not job_skill_set else 0.0

    # 4. Semantic Vector Cosine Similarity
    vector_result = compute_vector_similarity(resume_text, jd_text)
    cosine_sim = vector_result["cosine_similarity"]
    vector_match_pct = vector_result["match_percentage"]

    # 5. Composite Readiness Score
    composite_score = round(
        (skill_match_pct * SKILL_MATCH_RATIO) + (vector_match_pct * SEMANTIC_SIMILARITY_RATIO),
        1
    )
    composite_score = max(0.0, min(100.0, composite_score))

    # Readiness Tier
    if composite_score >= 85.0:
        readiness_tier = "Job-Ready Candidate"
        readiness_badge = "Excellent Fit"
        readiness_color = "#10b981"
        readiness_desc = "Candidate demonstrates strong alignment with core requirements and tech stack."
    elif composite_score >= 70.0:
        readiness_tier = "Strong Candidate (Minor Gaps)"
        readiness_badge = "High Potential"
        readiness_color = "#3b82f6"
        readiness_desc = "Candidate matches majority of required competencies with minor missing tools or frameworks."
    elif composite_score >= 50.0:
        readiness_tier = "Moderate Gap (Targeted Upskilling Needed)"
        readiness_badge = "Upskilling Required"
        readiness_color = "#f59e0b"
        readiness_desc = "Foundational overlap present, but key required technical qualifications need development."
    else:
        readiness_tier = "Substantial Skill Gap"
        readiness_badge = "Significant Transition"
        readiness_color = "#ef4444"
        readiness_desc = "Significant difference between candidate background and target job requirements."

    # 6. Category-by-Category Coverage
    category_breakdown: Dict[str, Dict[str, Any]] = {}
    for cat_key, meta in CATEGORY_META.items():
        cat_job = [s for s in job_skills_dict.values() if s["category"] == cat_key]
        cat_matched = [s for s in matched_skills if s["category"] == cat_key]
        cat_missing = [s for s in (missing_required + missing_preferred) if s["category"] == cat_key]
        cat_candidate = [s for s in resume_skills_dict.values() if s["category"] == cat_key]

        total_cat_skills = len(cat_job)
        matched_cat_skills = len(cat_matched)
        cand_cat_skills = len(cat_candidate)

        if total_cat_skills > 0:
            coverage_pct = round((matched_cat_skills / total_cat_skills) * 100.0, 1)
        elif cand_cat_skills > 0:
            coverage_pct = 100.0
        else:
            coverage_pct = 0.0

        category_breakdown[cat_key] = {
            "label": meta["label"],
            "color": meta["color"],
            "icon": meta.get("icon", "check"),
            "total_job_skills": total_cat_skills,
            "matched_skills": matched_cat_skills,
            "missing_skills": len(cat_missing),
            "candidate_skills_count": cand_cat_skills,
            "candidate_skill_names": [s.get("canonical_name", s.get("name", "")) for s in cat_candidate],
            "coverage_pct": coverage_pct,
            "matched_names": [s["name"] for s in cat_matched],
            "missing_names": [s["name"] for s in cat_missing]
        }

    return {
        "scores": {
            "composite_readiness_score": composite_score,
            "weighted_skill_match_pct": skill_match_pct,
            "semantic_vector_sim_pct": vector_match_pct,
            "cosine_similarity": cosine_sim,
            "readiness_tier": readiness_tier,
            "readiness_badge": readiness_badge,
            "readiness_color": readiness_color,
            "readiness_desc": readiness_desc
        },
        "stats": {
            "total_job_skills": len(job_skill_set),
            "total_resume_skills": len(resume_skill_set),
            "matched_skills_count": len(matched_skills),
            "missing_required_count": len(missing_required),
            "missing_preferred_count": len(missing_preferred),
            "additional_skills_count": len(additional_skills)
        },
        "skills": {
            "matched": matched_skills,
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
            "additional": additional_skills
        },
        "category_breakdown": category_breakdown,
        "semantic_insights": {
            "overlapping_keywords": vector_result.get("top_overlapping_terms", [])
        }
    }
