"""Unit tests for Personalized Learning Path & Topological Sorting."""

import unittest
from app.engine.learning_path import topological_sort_skills, generate_learning_path


class TestLearningPath(unittest.TestCase):

    def test_topological_sort_prerequisites(self):
        # When learning React, JavaScript, and Next.js:
        # JavaScript must come before React, and React before Next.js
        missing = ["Next.js", "React", "JavaScript"]
        sorted_skills = topological_sort_skills(missing, known_skills=set())

        js_idx = sorted_skills.index("JavaScript")
        react_idx = sorted_skills.index("React")
        next_idx = sorted_skills.index("Next.js")

        self.assertLess(js_idx, react_idx, "JavaScript should precede React in roadmap")
        self.assertLess(react_idx, next_idx, "React should precede Next.js in roadmap")

    def test_topological_sort_data_science(self):
        # Python must precede Machine Learning, which precedes Deep Learning
        missing = ["Deep Learning", "Python", "Machine Learning"]
        sorted_skills = topological_sort_skills(missing, known_skills=set())

        py_idx = sorted_skills.index("Python")
        ml_idx = sorted_skills.index("Machine Learning")
        dl_idx = sorted_skills.index("Deep Learning")

        self.assertLess(py_idx, ml_idx)
        self.assertLess(ml_idx, dl_idx)

    def test_generate_learning_path_milestones(self):
        missing_req = [
            {"name": "Docker", "importance": "required", "weight": 2.0},
            {"name": "Kubernetes", "importance": "required", "weight": 2.0}
        ]
        missing_pref = [
            {"name": "Terraform", "importance": "preferred", "weight": 1.0}
        ]
        matched = [
            {"name": "Linux", "importance": "required", "weight": 2.0}
        ]

        path = generate_learning_path(missing_req, missing_pref, matched)
        self.assertGreater(path["summary"]["total_estimated_hours"], 0)
        self.assertGreaterEqual(len(path["milestones"]), 2)

        # First step should be Docker (prereq for Kubernetes)
        step_names = [s["skill_name"] for s in path["ordered_steps"]]
        self.assertIn("Docker", step_names)
        self.assertIn("Kubernetes", step_names)
        self.assertLess(step_names.index("Docker"), step_names.index("Kubernetes"))


if __name__ == "__main__":
    unittest.main()
