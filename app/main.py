"""FastAPI Application Entrypoint for Skill-Gap Analyzer.

Provides REST APIs for document ingestion, web scraping, NLP skill extraction,
similarity matching, personalized learning path generation, and history persistence.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from backend.config import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
from backend.database import init_db, save_analysis, get_history, get_analysis_by_id, delete_analysis
from backend.parsers.resume_parser import parse_resume, DocumentParsingError
from backend.parsers.jd_scraper import scrape_job_description_url, ScrapingError
from backend.parsers.text_cleaner import clean_text
from backend.engine.gap_analyzer import perform_gap_analysis
from backend.engine.learning_path import generate_learning_path
from backend.engine.job_matcher import find_matching_jobs_for_resume
from backend.samples import SAMPLE_PROFILES

app = FastAPI(
    title="Skill-Gap Analyzer API",
    description="End-to-end NLP & Machine Learning Engine for Resume-to-Job Skill Gap Analysis and Personalized Curriculum Generation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR if FRONTEND_DIR.exists() else (Path(__file__).resolve().parent / "static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database on module import to ensure tables exist
init_db()


@app.on_event("startup")
def startup_event():
    """Initialize database on server boot."""
    init_db()


class ScrapeRequest(BaseModel):
    url: str


class DirectAnalyzeRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = None
    jd_url: Optional[str] = None
    candidate_name: Optional[str] = "Candidate Profile"
    job_title: Optional[str] = "Target Job Role"


class JobRecommendationRequest(BaseModel):
    resume_text: str
    limit: Optional[int] = 6


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Skill-Gap Analyzer"}


@app.get("/api/samples")
def get_samples():
    """Retrieve preloaded industry sample profiles for instant testing."""
    return SAMPLE_PROFILES


@app.post("/api/scrape-jd")
def scrape_jd_endpoint(request: ScrapeRequest):
    """Scrape job description text from an active web posting URL."""
    try:
        scraped = scrape_job_description_url(request.url)
        return scraped
    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error scraping job posting: {str(e)}")


def get_benchmark_job_description(job_title: str = "", resume_text: str = "") -> str:
    """Provide a domain-tailored benchmark Job Description when none or a short one is supplied."""
    combined = f"{job_title} {resume_text[:200]}".lower()
    if any(w in combined for w in ["data", "ml", "mle", "ai", "machine learning", "analyst", "vision", "nlp"]):
        return (
            "REQUIRED QUALIFICATIONS:\n"
            "- Strong programming experience in Python and SQL.\n"
            "- Practical expertise in Machine Learning, Pandas, NumPy, and Scikit-learn.\n"
            "- Experience designing data pipelines and performing exploratory data analysis.\n\n"
            "PREFERRED QUALIFICATIONS:\n"
            "- Deep Learning experience with PyTorch or TensorFlow.\n"
            "- Cloud platforms (AWS or GCP) and Docker containerization.\n"
            "- Git version control, CI/CD, and REST APIs."
        )
    elif any(w in combined for w in ["devops", "cloud", "infra", "sre", "platform", "kubernetes", "docker", "terraform"]):
        return (
            "REQUIRED QUALIFICATIONS:\n"
            "- Hands-on Linux systems administration and Bash/Shell scripting.\n"
            "- Containerization and orchestration with Docker and Kubernetes.\n"
            "- Cloud infrastructure management with AWS or GCP.\n"
            "- Infrastructure as Code with Terraform and CI/CD automation.\n\n"
            "PREFERRED QUALIFICATIONS:\n"
            "- Python or Go automation scripting.\n"
            "- Observability, Nginx reverse proxy configuration, and System Design."
        )
    elif any(w in combined for w in ["backend", "api", "server", "microservices", "java", "node", "django", "fastapi"]):
        return (
            "REQUIRED QUALIFICATIONS:\n"
            "- Production experience developing scalable REST APIs and microservices.\n"
            "- Proficiency in backend languages: Python, Node.js, Java, or Go.\n"
            "- Relational databases (PostgreSQL or MySQL) and query optimization.\n"
            "- Docker containerization and Git version control.\n\n"
            "PREFERRED QUALIFICATIONS:\n"
            "- In-memory caching with Redis and message brokers.\n"
            "- Cloud deployment on AWS and automated CI/CD pipelines."
        )
    else:
        return (
            "REQUIRED QUALIFICATIONS:\n"
            "- Foundations in modern programming: JavaScript, TypeScript, or Python.\n"
            "- Experience building applications with React, Node.js, FastAPI, or Django.\n"
            "- Working knowledge of SQL, database modeling, and REST APIs.\n"
            "- Git version control and collaborative development practices.\n\n"
            "PREFERRED QUALIFICATIONS:\n"
            "- Cloud infrastructure (AWS, GCP, or Azure).\n"
            "- Containerization with Docker and automated CI/CD workflows."
        )


@app.post("/api/analyze/direct")
def analyze_direct_endpoint(request: DirectAnalyzeRequest):
    """Direct JSON endpoint to analyze plain text inputs."""
    resume_text = clean_text(request.resume_text)
    if len(resume_text) < 15:
        raise HTTPException(status_code=400, detail="Resume text is too short or empty. Please provide readable resume content.")

    jd_text = ""
    if request.jd_url:
        try:
            scraped = scrape_job_description_url(request.jd_url)
            jd_text = scraped["text"]
            if not request.job_title or request.job_title == "Target Job Role":
                request.job_title = scraped.get("title", "Target Job Role")
        except ScrapingError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif request.jd_text and len(clean_text(request.jd_text)) >= 20:
        jd_text = clean_text(request.jd_text)
    else:
        # Fallback to role-tailored benchmark JD
        jd_text = get_benchmark_job_description(request.job_title or "", resume_text)

    # 1. Run Gap Analysis Engine
    gap_result = perform_gap_analysis(resume_text, jd_text)

    # 2. Run Learning Path Recommendation Engine
    learning_path = generate_learning_path(
        missing_required=gap_result["skills"]["missing_required"],
        missing_preferred=gap_result["skills"]["missing_preferred"],
        matched_skills=gap_result["skills"]["matched"]
    )

    # 3. Match resume competencies against active company jobs & portals
    job_recommendations = find_matching_jobs_for_resume(resume_text, top_limit=6)

    full_report = {
        **gap_result,
        "learning_path": learning_path,
        "job_recommendations": job_recommendations,
        "meta": {
            "candidate_name": request.candidate_name or "Candidate Profile",
            "job_title": request.job_title or "Target Job Role",
            "resume_snippet": resume_text[:300],
            "jd_snippet": jd_text[:300]
        }
    }

    # 3. Persist to SQLite
    record_id = save_analysis(
        report=full_report,
        candidate_name=request.candidate_name or "Candidate Profile",
        job_title=request.job_title or "Target Job Role",
        resume_preview=resume_text,
        jd_preview=jd_text
    )
    full_report["id"] = record_id

    return full_report


@app.post("/api/analyze")
async def analyze_form_endpoint(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    jd_text: Optional[str] = Form(None),
    jd_url: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form("Candidate Profile"),
    job_title: Optional[str] = Form("Target Job Role")
):
    """Multipart form endpoint supporting .pdf, .docx, .txt uploads or pasted text."""
    extracted_resume = ""

    if resume_file and resume_file.filename:
        filename = resume_file.filename
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{ext}'. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await resume_file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB.")

        try:
            extracted_resume = parse_resume(content, filename=filename)
        except DocumentParsingError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing resume file: {str(e)}")
    elif resume_text and resume_text.strip():
        extracted_resume = clean_text(resume_text)
    else:
        raise HTTPException(status_code=400, detail="Please upload a resume file (.pdf, .docx, .txt) or paste resume text.")

    if len(extracted_resume) < 15:
        raise HTTPException(status_code=400, detail="Extracted resume text is too short or empty. Please ensure the document contains readable text.")

    # Process Job Description
    final_jd_text = ""
    if jd_url and jd_url.strip():
        try:
            scraped = scrape_job_description_url(jd_url.strip())
            final_jd_text = scraped["text"]
            if not job_title or job_title == "Target Job Role":
                job_title = scraped.get("title", "Target Job Role")
        except ScrapingError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif jd_text and len(clean_text(jd_text)) >= 20:
        final_jd_text = clean_text(jd_text)
    else:
        # Fallback to domain-tailored benchmark JD
        final_jd_text = get_benchmark_job_description(job_title or "", extracted_resume)

    # 1. Run Gap Analysis Engine
    gap_result = perform_gap_analysis(extracted_resume, final_jd_text)

    # 2. Run Learning Path Recommendation Engine
    learning_path = generate_learning_path(
        missing_required=gap_result["skills"]["missing_required"],
        missing_preferred=gap_result["skills"]["missing_preferred"],
        matched_skills=gap_result["skills"]["matched"]
    )

    # 3. Match resume competencies against active company jobs & portals
    job_recommendations = find_matching_jobs_for_resume(extracted_resume, top_limit=6)

    full_report = {
        **gap_result,
        "learning_path": learning_path,
        "job_recommendations": job_recommendations,
        "meta": {
            "candidate_name": candidate_name or "Candidate Profile",
            "job_title": job_title or "Target Job Role",
            "resume_snippet": extracted_resume[:300],
            "jd_snippet": final_jd_text[:300]
        }
    }

    # 4. Persist to SQLite
    record_id = save_analysis(
        report=full_report,
        candidate_name=candidate_name or "Candidate Profile",
        job_title=job_title or "Target Job Role",
        resume_preview=extracted_resume,
        jd_preview=final_jd_text
    )
    full_report["id"] = record_id

    return full_report


@app.post("/api/jobs/recommendations")
def job_recommendations_endpoint(request: JobRecommendationRequest):
    """Generate matching company job openings and direct portal search links for a resume."""
    cleaned = clean_text(request.resume_text)
    if len(cleaned) < 20:
        raise HTTPException(status_code=400, detail="Resume text is too short or empty.")
    return find_matching_jobs_for_resume(cleaned, top_limit=request.limit or 6)


@app.get("/api/history")
def history_endpoint(limit: int = Query(50, ge=1, le=100)):
    """Fetch historical analysis runs."""
    return get_history(limit)


@app.get("/api/history/{record_id}")
def history_detail_endpoint(record_id: int):
    """Fetch full analysis report for a past run."""
    record = get_analysis_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return record


@app.delete("/api/history/{record_id}")
def history_delete_endpoint(record_id: int):
    """Delete an analysis run from history."""
    deleted = delete_analysis(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return {"status": "deleted", "id": record_id}


# Mount static assets and root dashboard
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_dashboard():
    """Serve the single-page skill gap analyzer dashboard UI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={"message": "Skill Gap Analyzer API is running. Build static UI in app/static/index.html"},
        status_code=200
    )
