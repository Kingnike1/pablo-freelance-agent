import unittest
from unittest.mock import patch

import start


class StartTests(unittest.TestCase):
    def test_audit_does_not_expose_telegram_token(self):
        config = dict(start.agent.DEFAULT)
        config["telegram_bot_token"] = "token-super-secreto"
        config["telegram_chat_id"] = "123"
        with patch.object(start.agent, "load_config", return_value=config):
            output = "\n".join(start.audit_config())
        self.assertIn("Telegram: token e chat ID configurados", output)
        self.assertNotIn("token-super-secreto", output)

    def test_audit_identifies_incomplete_telegram(self):
        config = dict(start.agent.DEFAULT)
        config["telegram_bot_token"] = "token"
        config["telegram_chat_id"] = ""
        with patch.object(start.agent, "load_config", return_value=config):
            output = "\n".join(start.audit_config())
        self.assertIn("Telegram: preencha token e chat ID juntos", output)

    def test_default_command_is_web(self):
        with patch.object(start, "run", return_value=0) as mocked:
            self.assertEqual(start.main([]), 0)
            mocked.assert_called_once_with("web")


if __name__ == "__main__":
    unittest.main()
