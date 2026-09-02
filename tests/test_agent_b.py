import unittest
from agent_b.app.agent import calculate_formula, root_agent, app


class TestAgentB(unittest.TestCase):
    def test_calculate_formula_basic_arithmetic(self):
        res = calculate_formula("42 * 137 + 12")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 42 * 137 + 12)

    def test_calculate_formula_advanced_math(self):
        res = calculate_formula("sqrt(144) + 2 ** 3")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 20.0)

    def test_calculate_formula_invalid_expression(self):
        res = calculate_formula("__import__('os').system('ls')")
        self.assertEqual(res["status"], "error")

    def test_agent_and_app_configuration(self):
        self.assertEqual(root_agent.name, "agent_b")
        self.assertEqual(app.name, "agent_b")
        self.assertEqual(len(root_agent.tools), 1)


if __name__ == "__main__":
    unittest.main()

