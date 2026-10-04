import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent
import web_app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "jobs.sqlite3"
        self.config = Path(self.temp_dir.name) / "config.json"
        self.config.write_text(json.dumps(agent.DEFAULT), encoding="utf-8")
        with patch.object(agent, "DB", self.db), patch.object(agent, "CFG", self.config):
            with sqlite3.connect(self.db) as connection:
                agent.init_db(connection)
                connection.execute(
                    "INSERT INTO jobs VALUES(?,?,?,?,?,?,?)",
                    ("Remotive:1", "Remotive", "Python developer", "Acme", "Remote", "https://example.com/1", "2026-10-03T20:00:00+00:00"),
                )
        self.patches = [patch.object(agent, "DB", self.db), patch.object(agent, "CFG", self.config)]
        for item in self.patches:
            item.start()
        web_app.app.config.update(TESTING=True)
        self.client = web_app.app.test_client()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp_dir.cleanup()

    def test_dashboard_and_filter(self):
        response = self.client.get("/?q=python")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Python developer", response.data)
        self.assertEqual(self.client.get("/?q=wordpress").status_code, 200)
        self.assertNotIn(b"Python developer", self.client.get("/?q=wordpress").data)

    def test_reports_have_expected_formats(self):
        csv_response = self.client.get("/reports/csv")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b"text/csv", csv_response.content_type.encode())
        self.assertIn("Python developer".encode(), csv_response.data)

        json_response = self.client.get("/reports/json")
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.json["count"], 1)

        html_response = self.client.get("/reports/html")
        self.assertEqual(html_response.status_code, 200)
        self.assertIn(b"Relat\xc3\xb3rio de oportunidades", html_response.data)

    def test_health_and_api(self):
        self.assertEqual(self.client.get("/health").json["status"], "ok")
        self.assertEqual(self.client.get("/api/jobs").json["count"], 1)


if __name__ == "__main__":
    unittest.main()
