"""Unit tests for Gap Analysis Engine, Set Differences, and Vector Cosine Similarity."""

import unittest
from app.engine.vector_similarity import compute_vector_similarity
from app.engine.gap_analyzer import perform_gap_analysis


class TestVectorSimilarity(unittest.TestCase):

    def test_identical_documents_similarity(self):
        doc = "Python developer building REST APIs and microservices using FastAPI and Docker."
        res = compute_vector_similarity(doc, doc)
        self.assertAlmostEqual(res["cosine_similarity"], 1.0, places=2)
        self.assertAlmostEqual(res["match_percentage"], 100.0, places=1)

    def test_disjoint_documents_low_similarity(self):
        doc1 = "Dentist specializing in dental hygiene, teeth whitening, and oral surgery."
        doc2 = "Kubernetes cloud engineer deploying microservices on AWS using Terraform."
        res = compute_vector_similarity(doc1, doc2)
        self.assertLess(res["cosine_similarity"], 0.2)


class TestGapAnalyzer(unittest.TestCase):

    def test_set_difference_logic(self):
        resume = """
        Skilled in Python, PostgreSQL, and Git.
        Experience building REST APIs.
        """
        jd = """
        Required Skills:
        - Python, PostgreSQL, and Docker.
        - REST APIs.

        Preferred Qualifications:
        - Kubernetes.
        """
        result = perform_gap_analysis(resume, jd)

        matched_names = {s["name"] for s in result["skills"]["matched"]}
        missing_req_names = {s["name"] for s in result["skills"]["missing_required"]}
        missing_pref_names = {s["name"] for s in result["skills"]["missing_preferred"]}

        # Matched should include Python, PostgreSQL, REST APIs
        self.assertIn("Python", matched_names)
        self.assertIn("PostgreSQL", matched_names)
        self.assertIn("REST APIs", matched_names)

        # Missing required should be Docker
        self.assertIn("Docker", missing_req_names)

        # Missing preferred should be Kubernetes
        self.assertIn("Kubernetes", missing_pref_names)

        # Candidate additional: Git
        additional_names = {s["name"] for s in result["skills"]["additional"]}
        self.assertIn("Git", additional_names)

        # Verify weights
        # Total job weight = Python(2) + Postgres(2) + REST APIs(2) + Docker(2) + K8s(1) = 9
        # Matched weight = Python(2) + Postgres(2) + REST APIs(2) = 6
        # Expected skill match % = (6 / 9) * 100 = 66.7%
        self.assertAlmostEqual(result["scores"]["weighted_skill_match_pct"], 66.7, delta=1.0)


if __name__ == "__main__":
    unittest.main()
