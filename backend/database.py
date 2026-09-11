"""SQLite Persistence Layer for Skill-Gap Analyzer.

Stores candidate resumes, job descriptions, analysis metrics,
and historical gap reports for progress tracking over time.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from backend.config import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Establish and return an active connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and schema indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            candidate_name TEXT,
            job_title TEXT,
            composite_score REAL,
            skill_match_pct REAL,
            semantic_sim_pct REAL,
            readiness_tier TEXT,
            readiness_badge TEXT,
            total_job_skills INTEGER,
            matched_count INTEGER,
            missing_required_count INTEGER,
            missing_preferred_count INTEGER,
            additional_count INTEGER,
            report_json TEXT,
            resume_preview TEXT,
            jd_preview TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_created_at
        ON analysis_history (created_at DESC)
    """)

    conn.commit()
    conn.close()


def save_analysis(
    report: Dict[str, Any],
    candidate_name: str = "Candidate Profile",
    job_title: str = "Target Job Role",
    resume_preview: str = "",
    jd_preview: str = ""
) -> int:
    """Persist an analysis run into SQLite history.

    Returns:
        The generated record ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    scores = report.get("scores", {})
    stats = report.get("stats", {})

    cursor.execute("""
        INSERT INTO analysis_history (
            created_at,
            candidate_name,
            job_title,
            composite_score,
            skill_match_pct,
            semantic_sim_pct,
            readiness_tier,
            readiness_badge,
            total_job_skills,
            matched_count,
            missing_required_count,
            missing_preferred_count,
            additional_count,
            report_json,
            resume_preview,
            jd_preview
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        candidate_name,
        job_title,
        scores.get("composite_readiness_score", 0.0),
        scores.get("weighted_skill_match_pct", 0.0),
        scores.get("semantic_vector_sim_pct", 0.0),
        scores.get("readiness_tier", "Unknown"),
        scores.get("readiness_badge", "N/A"),
        stats.get("total_job_skills", 0),
        stats.get("matched_skills_count", 0),
        stats.get("missing_required_count", 0),
        stats.get("missing_preferred_count", 0),
        stats.get("additional_skills_count", 0),
        json.dumps(report),
        resume_preview[:500],
        jd_preview[:500]
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve historical analysis summaries sorted by newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, created_at, candidate_name, job_title,
            composite_score, skill_match_pct, semantic_sim_pct,
            readiness_tier, readiness_badge,
            total_job_skills, matched_count, missing_required_count,
            missing_preferred_count, additional_count
        FROM analysis_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history


def get_analysis_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full analysis report by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM analysis_history WHERE id = ?
    """, (record_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    if "report_json" in data and data["report_json"]:
        data["report"] = json.loads(data["report_json"])
    return data


def delete_analysis(record_id: int) -> bool:
    """Delete a record from history by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
