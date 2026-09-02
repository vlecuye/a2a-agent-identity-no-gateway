import json
import os
import unittest


class TestAgentCardsAndConfigs(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_agent_b_identity_config(self):
        config_path = os.path.join(self.base_dir, "agent_b", ".agent_engine_config.json")
        self.assertTrue(os.path.exists(config_path), ".agent_engine_config.json missing for agent_b")
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("identity_type"), "AGENT_IDENTITY")

    def test_agent_a_identity_config(self):
        config_path = os.path.join(self.base_dir, "agent_a", ".agent_engine_config.json")
        self.assertTrue(os.path.exists(config_path), ".agent_engine_config.json missing for agent_a")
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("identity_type"), "AGENT_IDENTITY")

    def test_agent_b_agent_card(self):
        card_path = os.path.join(self.base_dir, "agent_b", "agent_card.json")
        self.assertTrue(os.path.exists(card_path), "agent_card.json missing for agent_b")
        with open(card_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "agent_b")
        self.assertTrue(data.get("capabilities", {}).get("streaming"))

    def test_agent_a_agent_card(self):
        card_path = os.path.join(self.base_dir, "agent_a", "agent_card.json")
        self.assertTrue(os.path.exists(card_path), "agent_card.json missing for agent_a")
        with open(card_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "agent_a")


if __name__ == "__main__":
    unittest.main()
