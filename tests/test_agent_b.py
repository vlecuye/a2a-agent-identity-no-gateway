import unittest
from agent_b.app.agent import calculate_formula, root_agent, app


class TestAgentB(unittest.TestCase):
    def test_calculate_formula_basic_arithmetic(self):
        result = calculate_formula("42 * 137 + 12")
        self.assertEqual(result, str(42 * 137 + 12))

    def test_calculate_formula_invalid_characters(self):
        result = calculate_formula("import os")
        self.assertIn("invalid characters", result)

    def test_agent_and_app_configuration(self):
        self.assertEqual(root_agent.name, "agent_b")
        self.assertEqual(app.name, "agent_b")
        self.assertEqual(len(root_agent.tools), 1)


if __name__ == "__main__":
    unittest.main()
