"""Resume-Based Job Opportunity Matching Engine.

Analyzes candidate resume competencies, identifies candidate domain affinity,
matches candidate profiles against company openings, and generates direct,
parameterized links to live job listings on top job boards.
"""

from typing import Dict, List, Set, Any
from urllib.parse import quote_plus

from backend.nlp.taxonomy import CATEGORY_META
from backend.nlp.skill_extractor import extract_skills_from_text


# Curated live company job openings catalog
COMPANY_JOB_CATALOG: List[Dict[str, Any]] = [
    # Frontend & Full-Stack
    {
        "id": "vercel-fe-nextjs",
        "company": "Vercel",
        "company_logo": "▲",
        "company_color": "#000000",
        "role_title": "Full-Stack / Frontend Engineer (Next.js & React)",
        "domain": "frontend",
        "location": "Remote (Global)",
        "salary_range": "$140,000 - $190,000",
        "required_skills": ["React", "Next.js", "TypeScript", "JavaScript", "Tailwind CSS"],
        "preferred_skills": ["Node.js", "WebSockets", "REST APIs"],
        "company_career_url": "https://vercel.com/careers",
        "description": "Build high-performance web experiences and developer tooling for Vercel's Next.js and frontend cloud platform."
    },
    {
        "id": "stripe-fullstack-dev",
        "company": "Stripe",
        "company_logo": "S",
        "company_color": "#6366f1",
        "role_title": "Full-Stack Software Engineer (Merchant Platform)",
        "domain": "frontend",
        "location": "Remote / San Francisco, CA",
        "salary_range": "$160,000 - $220,000",
        "required_skills": ["JavaScript", "TypeScript", "React", "Node.js", "REST APIs"],
        "preferred_skills": ["PostgreSQL", "Docker", "Git"],
        "company_career_url": "https://stripe.com/jobs",
        "description": "Architect the global economic infrastructure and dashboard tooling powering millions of online businesses."
    },
    {
        "id": "shopify-senior-web",
        "company": "Shopify",
        "company_logo": "🛍️",
        "company_color": "#95bf47",
        "role_title": "Senior Web Developer (Storefront Platform)",
        "domain": "frontend",
        "location": "Remote (US / Canada)",
        "salary_range": "$135,000 - $185,000",
        "required_skills": ["React", "JavaScript", "TypeScript", "HTML5/CSS3", "Redux"],
        "preferred_skills": ["GraphQL", "REST APIs", "Unit Testing"],
        "company_career_url": "https://www.shopify.com/careers",
        "description": "Empower independent commerce globally by developing ultra-fast, accessible storefronts and merchant interfaces."
    },

    # Backend & Distributed Systems
    {
        "id": "amazon-backend-sde2",
        "company": "Amazon Web Services (AWS)",
        "company_logo": "A",
        "company_color": "#ff9900",
        "role_title": "Software Development Engineer II (Cloud Services)",
        "domain": "backend",
        "location": "Seattle, WA / Austin, TX / Remote",
        "salary_range": "$150,000 - $210,000",
        "required_skills": ["Python", "Java", "SQL", "REST APIs", "System Design"],
        "preferred_skills": ["Docker", "AWS", "Microservices", "PostgreSQL"],
        "company_career_url": "https://www.amazon.jobs/",
        "description": "Scale distributed, fault-tolerant backend infrastructure serving billions of requests per minute across AWS services."
    },
    {
        "id": "datadog-backend-eng",
        "company": "Datadog",
        "company_logo": "🐶",
        "company_color": "#632ca6",
        "role_title": "Backend Software Engineer (Platform Infrastructure)",
        "domain": "backend",
        "location": "New York, NY / Remote",
        "salary_range": "$155,000 - $205,000",
        "required_skills": ["Python", "Go", "PostgreSQL", "Redis", "Linux"],
        "preferred_skills": ["Docker", "Kubernetes", "Microservices"],
        "company_career_url": "https://www.datadoghq.com/careers/",
        "description": "Design ultra-low latency observability pipelines and real-time metric ingestion platforms."
    },
    {
        "id": "microsoft-cloud-backend",
        "company": "Microsoft",
        "company_logo": "⊞",
        "company_color": "#00a4ef",
        "role_title": "Software Engineer (Azure Core Backend)",
        "domain": "backend",
        "location": "Redmond, WA / Remote",
        "salary_range": "$145,000 - $195,000",
        "required_skills": ["C#", "Python", "SQL", "REST APIs", "Unit Testing"],
        "preferred_skills": ["Microsoft Azure", "Docker", "Microservices"],
        "company_career_url": "https://careers.microsoft.com/",
        "description": "Build resilient core cloud services and API gateways supporting enterprise mission-critical workloads on Azure."
    },

    # Data Science & AI / ML
    {
        "id": "openai-mle-platform",
        "company": "OpenAI",
        "company_logo": "✦",
        "company_color": "#10a37f",
        "role_title": "Machine Learning Engineer (Inference & Training)",
        "domain": "data_ai",
        "location": "San Francisco, CA / Remote",
        "salary_range": "$200,000 - $320,000",
        "required_skills": ["Python", "PyTorch", "NumPy", "Pandas", "Machine Learning"],
        "preferred_skills": ["Deep Learning", "Large Language Models (LLMs)", "Docker", "Linux"],
        "company_career_url": "https://openai.com/careers",
        "description": "Research, scale, and deploy foundational AI systems and transformer architectures to benefit all of humanity."
    },
    {
        "id": "deepmind-ai-eng",
        "company": "Google DeepMind",
        "company_logo": "G",
        "company_color": "#4285f4",
        "role_title": "Applied Machine Learning Specialist",
        "domain": "data_ai",
        "location": "Mountain View, CA / New York, NY",
        "salary_range": "$175,000 - $250,000",
        "required_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "SQL"],
        "preferred_skills": ["Natural Language Processing (NLP)", "Computer Vision", "Scikit-learn"],
        "company_career_url": "https://careers.google.com/",
        "description": "Bridge foundational intelligence research with real-world applications across multimodal reasoning models."
    },
    {
        "id": "snowflake-data-eng",
        "company": "Snowflake",
        "company_logo": "❄",
        "company_color": "#29b5e8",
        "role_title": "Data Platform Engineer (ETL & Query Optimization)",
        "domain": "data_ai",
        "location": "San Mateo, CA / Remote",
        "salary_range": "$150,000 - $210,000",
        "required_skills": ["Python", "SQL", "Pandas", "Data Pipelines / ETL", "Apache Spark"],
        "preferred_skills": ["PostgreSQL", "AWS", "Docker"],
        "company_career_url": "https://www.snowflake.com/careers/",
        "description": "Construct scalable cloud data warehousing pipelines handling petabytes of analytical queries per day."
    },

    # Cloud, DevOps & Platform
    {
        "id": "hashicorp-cloud-eng",
        "company": "HashiCorp",
        "company_logo": "H",
        "company_color": "#000000",
        "role_title": "Cloud Infrastructure & Platform Engineer (Terraform)",
        "domain": "cloud_devops",
        "location": "Remote (US / EMEA)",
        "salary_range": "$145,000 - $195,000",
        "required_skills": ["Terraform", "Docker", "Kubernetes", "Linux", "AWS"],
        "preferred_skills": ["CI/CD", "GitHub Actions", "Go", "Bash/Shell"],
        "company_career_url": "https://www.hashicorp.com/careers",
        "description": "Empower automated multi-cloud provisioning and infrastructure workflows across thousands of enterprise customers."
    },
    {
        "id": "cloudflare-systems-eng",
        "company": "Cloudflare",
        "company_logo": "☁",
        "company_color": "#f38020",
        "role_title": "DevOps & Cloud Systems Engineer",
        "domain": "cloud_devops",
        "location": "Austin, TX / San Francisco, CA / Remote",
        "salary_range": "$140,000 - $190,000",
        "required_skills": ["Linux", "Docker", "CI/CD", "Nginx", "Bash/Shell"],
        "preferred_skills": ["Kubernetes", "Go", "Terraform", "Rust"],
        "company_career_url": "https://www.cloudflare.com/careers/",
        "description": "Help build a better internet by optimizing edge routing, DDoS mitigation, and global edge container runtimes."
    },
    {
        "id": "gitlab-infra-eng",
        "company": "GitLab",
        "company_logo": "🦊",
        "company_color": "#fc6d26",
        "role_title": "Site Reliability & CI/CD Infrastructure Engineer",
        "domain": "cloud_devops",
        "location": "All-Remote",
        "salary_range": "$130,000 - $180,000",
        "required_skills": ["CI/CD", "Git", "Kubernetes", "Docker", "Linux"],
        "preferred_skills": ["Terraform", "Google Cloud Platform (GCP)", "Python"],
        "company_career_url": "https://about.gitlab.com/jobs/",
        "description": "Drive 99.99% availability and build scalable CI runner orchestration for millions of active software projects."
    }
]


def generate_external_job_links(query_title: str, top_skills: List[str], location: str = "Remote") -> Dict[str, str]:
    """Generate parameterized, direct 1-click links for active job openings across major job providers."""
    # Build query string combining role title and key skill keywords
    skill_keywords = " ".join(top_skills[:3])
    full_query = f"{query_title} {skill_keywords}".strip()
    encoded_query = quote_plus(full_query)
    encoded_loc = quote_plus(location)
    encoded_title = quote_plus(query_title)

    return {
        "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_loc}&f_TPR=r604800&sortBy=DD",
        "google_jobs": f"https://www.google.com/search?ibp=htl;jobs&q={encoded_query}+{encoded_loc}",
        "indeed": f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_loc}&fromage=7",
        "wellfound": f"https://wellfound.com/jobs?role={encoded_title}",
        "remoteok": f"https://remoteok.com/remote-{quote_plus(query_title.lower().replace(' ', '-'))}-jobs"
    }


def find_matching_jobs_for_resume(
    resume_text: str,
    top_limit: int = 6
) -> Dict[str, Any]:
    """Analyze resume skills and match against company openings with direct application links.

    Args:
        resume_text: Raw or clean resume text.
        top_limit: Maximum number of company recommendations to return.

    Returns:
        Dict containing candidate primary domain, recommended company jobs with match scores
        and direct apply links, plus parameterized external search portal links.
    """
    extracted_skills_dict = extract_skills_from_text(resume_text)
    candidate_skills: Set[str] = set(extracted_skills_dict.keys())

    # Count skills per category to determine primary domain affinity
    domain_counts: Dict[str, int] = {}
    for skill_name, data in extracted_skills_dict.items():
        cat = data.get("category", "languages")
        domain_counts[cat] = domain_counts.get(cat, 0) + 1

    # Determine primary domain
    primary_domain = max(domain_counts, key=domain_counts.get) if domain_counts else "frontend"

    # Match against catalog
    scored_jobs = []
    for job in COMPANY_JOB_CATALOG:
        required = set(job["required_skills"])
        preferred = set(job.get("preferred_skills", []))
        all_job_skills = required | preferred

        matched_req = required.intersection(candidate_skills)
        matched_pref = preferred.intersection(candidate_skills)
        all_matched = matched_req | matched_pref

        missing_req = required.difference(candidate_skills)

        # Weighted match formula: required matches carry 2x weight
        total_possible = (len(required) * 2.0) + (len(preferred) * 1.0)
        actual_score = (len(matched_req) * 2.0) + (len(matched_pref) * 1.0)
        match_pct = round((actual_score / total_possible) * 100.0, 1) if total_possible > 0 else 50.0

        # Domain bonus
        if job["domain"] == primary_domain:
            match_pct = min(100.0, match_pct + 5.0)

        # Generate direct search links for this specific role
        portal_links = generate_external_job_links(
            query_title=job["role_title"],
            top_skills=list(all_matched or required),
            location="Remote"
        )

        scored_jobs.append({
            **job,
            "match_pct": round(match_pct, 1),
            "matched_skills": sorted(list(all_matched)),
            "missing_skills": sorted(list(missing_req)),
            "direct_apply_url": job["company_career_url"],
            "portal_links": portal_links
        })

    # Sort jobs by match percentage descending
    scored_jobs.sort(key=lambda x: x["match_pct"], reverse=True)
    top_jobs = scored_jobs[:top_limit]

    # Overall candidate suggested target role
    top_job_title = top_jobs[0]["role_title"] if top_jobs else "Software Engineer"
    candidate_top_skills = list(candidate_skills)[:4]

    # Global search portal links for candidate's top skill profile
    global_portal_links = generate_external_job_links(
        query_title=top_job_title.split("(")[0].strip(),
        top_skills=candidate_top_skills,
        location="Remote"
    )

    return {
        "candidate_primary_domain": primary_domain,
        "candidate_domain_label": CATEGORY_META.get(primary_domain, {}).get("label", primary_domain.capitalize()),
        "recommended_jobs": top_jobs,
        "global_portal_links": global_portal_links,
        "top_matching_keywords": candidate_top_skills
    }
