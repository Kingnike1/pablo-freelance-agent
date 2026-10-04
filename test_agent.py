import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(agent.DEFAULT)
        self.cfg.update({
            "keywords_any": ["python", "react"],
            "exclude_keywords": ["senior"],
            "max_results_per_check": 2,
            "desktop_notifications": False,
        })
        self.connection = sqlite3.connect(":memory:")
        agent.init_db(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_normalize_job_rejects_missing_url(self):
        self.assertIsNone(agent.normalize_job("Remotive", {"id": 1, "title": "Python"}))

    def test_normalize_job_rejects_unsafe_url(self):
        self.assertIsNone(agent.normalize_job("Remotive", {"id": 1, "title": "Python", "url": "javascript:alert(1)"}))

    def test_matching_is_case_insensitive_and_excludes_terms(self):
        good = agent.normalize_job("Remotive", {
            "id": 1, "title": "Python developer", "url": "https://example.com/1",
            "description": "Build APIs",
        })
        senior = agent.normalize_job("Remotive", {
            "id": 2, "title": "Senior Python developer", "url": "https://example.com/2",
        })
        self.assertTrue(agent.matching(good, self.cfg))
        self.assertFalse(agent.matching(senior, self.cfg))

    def test_check_once_deduplicates_and_enforces_global_limit(self):
        responses = {
            agent.SOURCES[0][1]: {"jobs": [
                {"id": 1, "title": "Python one", "company_name": "A", "url": "https://a/1"},
                {"id": 2, "title": "React two", "company_name": "B", "url": "https://a/2"},
            ]},
            agent.SOURCES[1][1]: {"data": [
                # A fonte seguinte não deve gerar registros após o limite global.
            ]},
        }
        notified = []
        fetcher = lambda url: responses[url]
        notifier = lambda *args: notified.append(args)

        self.assertEqual(agent.check_once(self.cfg, self.connection, fetcher, notifier), 2)
        self.assertEqual(len(notified), 2)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 2)
        self.assertEqual(agent.check_once(self.cfg, self.connection, fetcher, notifier), 0)
        self.assertEqual(len(notified), 2)

    def test_load_config_merges_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"max_results_per_check": 3}), encoding="utf-8")
            with patch.object(agent, "CFG", path):
                cfg = agent.load_config()
            self.assertEqual(cfg["max_results_per_check"], 3)
            self.assertIn("keywords_any", cfg)

    def test_save_config_rejects_invalid_update_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            original = {"max_results_per_check": 15}
            path.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(agent, "CFG", path):
                with self.assertRaises(RuntimeError):
                    agent.save_config({"budget_min": 500, "budget_max": 100})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()
