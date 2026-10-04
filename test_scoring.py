import unittest

from scoring import score_job


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "keywords_any": ["python", "react", "landing page"],
            "preferred_work_types": ["frontend", "landing page"],
            "preferred_languages": [],
            "preferred_locations": [],
            "budget_min": 1000,
            "budget_max": 5000,
        }

    def job(self, title, description, metadata=None):
        return ("1", title, "Acme", "Remote", "https://example.com", description, metadata or {})

    def test_score_is_bounded_and_explained(self):
        result = score_job(self.job("React landing page", "Python and React project " * 50, {"budget": "2500"}), self.config)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(result["level"], "alta")
        self.assertTrue(result["reasons"])
        self.assertIn("python", result["matched_keywords"])

    def test_missing_budget_is_not_penalized_or_invented(self):
        result = score_job(self.job("Python developer", "Build a Python API."), self.config)
        self.assertTrue(any("não informado" in reason for reason in result["reasons"]))
        self.assertNotIn("Orçamento informado", " ".join(result["reasons"]))

    def test_title_match_scores_better_than_description_only(self):
        title = score_job(self.job("Python developer", "Build a useful API."), self.config)
        description = score_job(self.job("Developer", "Build a Python API."), self.config)
        self.assertGreater(title["score"], description["score"])


if __name__ == "__main__":
    unittest.main()
