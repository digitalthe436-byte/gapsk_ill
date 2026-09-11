"""Unit tests for Job Matching Engine and Direct Links Generator."""

import unittest
from app.engine.job_matcher import find_matching_jobs_for_resume, generate_external_job_links


class TestJobMatcher(unittest.TestCase):

    def test_frontend_resume_matches_frontend_jobs(self):
        resume = """
        Alex Chen - Frontend Engineer.
        Proficient in React, JavaScript, TypeScript, Next.js, HTML5/CSS3, and Tailwind CSS.
        """
        result = find_matching_jobs_for_resume(resume, top_limit=4)

        self.assertIn("recommended_jobs", result)
        self.assertGreater(len(result["recommended_jobs"]), 0)

        top_job = result["recommended_jobs"][0]
        # Should match frontend companies like Vercel or Stripe
        self.assertIn(top_job["company"], ["Vercel", "Stripe", "Shopify"])
        self.assertGreater(top_job["match_pct"], 60.0)
        self.assertIn("React", top_job["matched_skills"])

        # Check direct apply url and portal links
        self.assertTrue(top_job["direct_apply_url"].startswith("http"))
        self.assertIn("linkedin", top_job["portal_links"])
        self.assertIn("indeed", top_job["portal_links"])
        self.assertIn("google_jobs", top_job["portal_links"])

    def test_ml_resume_matches_ml_jobs(self):
        resume = """
        Maya Patel - Data Scientist & AI Specialist.
        Skills: Python, PyTorch, NumPy, Pandas, Machine Learning, Deep Learning, SQL.
        """
        result = find_matching_jobs_for_resume(resume, top_limit=3)

        top_job = result["recommended_jobs"][0]
        self.assertIn(top_job["company"], ["OpenAI", "Google DeepMind", "Snowflake"])
        self.assertGreater(top_job["match_pct"], 60.0)
        self.assertIn("Python", top_job["matched_skills"])

    def test_portal_links_generation(self):
        links = generate_external_job_links("Full Stack Developer", ["React", "Node.js"], "Remote")
        self.assertIn("linkedin.com/jobs", links["linkedin"])
        self.assertIn("google.com/search", links["google_jobs"])
        self.assertIn("indeed.com/jobs", links["indeed"])
        self.assertIn("wellfound.com/jobs", links["wellfound"])
        self.assertIn("remoteok.com", links["remoteok"])


if __name__ == "__main__":
    unittest.main()
