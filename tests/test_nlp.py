"""Unit tests for Skill Extraction and Master Taxonomy Normalization."""

import unittest
from app.nlp.taxonomy import normalize_skill, MASTER_TAXONOMY, SYNONYM_MAP
from app.nlp.skill_extractor import extract_skills_from_text, extract_job_skills_with_weighting


class TestTaxonomy(unittest.TestCase):

    def test_synonym_normalization(self):
        # Common aliases should resolve to canonical names
        self.assertEqual(normalize_skill("js"), "JavaScript")
        self.assertEqual(normalize_skill("ecmascript"), "JavaScript")
        self.assertEqual(normalize_skill("ts"), "TypeScript")
        self.assertEqual(normalize_skill("k8s"), "Kubernetes")
        self.assertEqual(normalize_skill("postgres"), "PostgreSQL")
        self.assertEqual(normalize_skill("psql"), "PostgreSQL")
        self.assertEqual(normalize_skill("mongo"), "MongoDB")
        self.assertEqual(normalize_skill("reactjs"), "React")
        self.assertEqual(normalize_skill("node.js"), "Node.js")
        self.assertEqual(normalize_skill("cicd"), "CI/CD")
        self.assertEqual(normalize_skill("aws"), "AWS")
        self.assertEqual(normalize_skill("ml"), "Machine Learning")

    def test_canonical_taxonomy_integrity(self):
        # Every synonym must map to a valid master taxonomy key
        for alias, canonical in SYNONYM_MAP.items():
            self.assertIn(canonical, MASTER_TAXONOMY, f"Synonym {alias} points to missing canonical {canonical}")


class TestSkillExtractor(unittest.TestCase):

    def test_extract_skills_from_prose(self):
        prose = """
        Experienced Senior Developer with 5 years building scalable web applications.
        Expert in Python, JavaScript, and TypeScript. Extensive background in React and Next.js.
        Managed relational databases using PostgreSQL and deployed microservices with Docker and Kubernetes.
        Demonstrated leadership and cross-functional collaboration.
        """
        extracted = extract_skills_from_text(prose)
        skill_names = set(extracted.keys())

        expected = {"Python", "JavaScript", "TypeScript", "React", "Next.js", "PostgreSQL", "Docker", "Kubernetes", "Microservices"}
        for s in expected:
            self.assertIn(s, skill_names, f"Expected skill {s} was not extracted.")

    def test_multi_word_skills(self):
        prose = "Experienced in machine learning, system design, test-driven development, and data pipelines."
        extracted = extract_skills_from_text(prose)
        self.assertIn("Machine Learning", extracted)
        self.assertIn("System Design", extracted)
        self.assertIn("Test-Driven Development (TDD)", extracted)
        self.assertIn("Data Pipelines / ETL", extracted)

    def test_word_boundary_safety(self):
        # "Go" or "R" shouldn't match inside random words
        prose = "We are going to improve the algorithm for goods and categories."
        extracted = extract_skills_from_text(prose)
        self.assertNotIn("Go", extracted, "Word boundary check failed for 'Go'.")

    def test_extract_job_skills_weighting(self):
        jd = """
        Required Skills:
        - Python, PostgreSQL, and Docker.

        Preferred Qualifications:
        - Kubernetes and Terraform.
        """
        job_skills = extract_job_skills_with_weighting(jd)
        self.assertEqual(job_skills["Python"]["importance"], "required")
        self.assertEqual(job_skills["Python"]["weight"], 2.0)
        self.assertEqual(job_skills["PostgreSQL"]["importance"], "required")
        self.assertEqual(job_skills["Kubernetes"]["importance"], "preferred")
        self.assertEqual(job_skills["Kubernetes"]["weight"], 1.0)


if __name__ == "__main__":
    unittest.main()
