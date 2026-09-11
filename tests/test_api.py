"""Integration tests for FastAPI REST API endpoints."""

import io
import unittest
from starlette.testclient import TestClient
from app.main import app


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_get_samples(self):
        response = self.client.get("/api/samples")
        self.assertEqual(response.status_code, 200)
        samples = response.json()
        self.assertIsInstance(samples, list)
        self.assertGreaterEqual(len(samples), 3)
        self.assertIn("frontend-to-fullstack", [s["id"] for s in samples])

    def test_analyze_direct_endpoint(self):
        payload = {
            "resume_text": "Alex Chen is a Frontend developer with React, JavaScript, and Tailwind CSS experience.",
            "jd_text": """
            Required:
            - React, JavaScript, TypeScript, Node.js, and PostgreSQL.
            Preferred:
            - Docker and AWS.
            """,
            "candidate_name": "Alex Chen",
            "job_title": "Full-Stack Engineer"
        }
        response = self.client.post("/api/analyze/direct", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("scores", data)
        self.assertIn("skills", data)
        self.assertIn("category_breakdown", data)
        self.assertIn("learning_path", data)
        self.assertIn("id", data)

        # Matched skills
        matched = [s["name"] for s in data["skills"]["matched"]]
        self.assertIn("React", matched)
        self.assertIn("JavaScript", matched)

        # Missing required
        missing_req = [s["name"] for s in data["skills"]["missing_required"]]
        self.assertIn("TypeScript", missing_req)
        self.assertIn("Node.js", missing_req)
        self.assertIn("PostgreSQL", missing_req)

        # Learning path milestones
        milestones = data["learning_path"]["milestones"]
        self.assertGreaterEqual(len(milestones), 2)

        # Job recommendations verification
        self.assertIn("job_recommendations", data)
        self.assertGreater(len(data["job_recommendations"]["recommended_jobs"]), 0)

    def test_job_recommendations_endpoint(self):
        payload = {
            "resume_text": "Python and Machine Learning engineer with PyTorch, Pandas, and NumPy.",
            "limit": 4
        }
        response = self.client.post("/api/jobs/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommended_jobs", data)
        self.assertIn("global_portal_links", data)
        self.assertGreaterEqual(len(data["recommended_jobs"]), 1)
        self.assertIn("linkedin", data["global_portal_links"])

    def test_history_persistence(self):
        # Fetch history list
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        history = response.json()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

        # Fetch the latest record detail
        latest_id = history[0]["id"]
        detail_res = self.client.get(f"/api/history/{latest_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["id"], latest_id)
        self.assertIn("report", detail)

    def test_backend_package_direct(self):
        """Verify the newly organized backend package works directly."""
        from backend.main import app as backend_app
        backend_client = TestClient(backend_app)
        res = backend_client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

        # Test serving root dashboard from frontend directory
        root_res = backend_client.get("/")
        self.assertEqual(root_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
