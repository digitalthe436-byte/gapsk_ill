"""Application configuration settings for Skill-Gap Analyzer."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "skill_gap.db"

# File upload constraints
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Weights for gap calculation
REQUIRED_SKILL_WEIGHT = 2.0
PREFERRED_SKILL_WEIGHT = 1.0

# Composite score weights (Skill Match vs Semantic Vector Similarity)
SKILL_MATCH_RATIO = 0.70
SEMANTIC_SIMILARITY_RATIO = 0.30

# Web Scraper User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 SkillGapAnalyzer/1.0"
)
