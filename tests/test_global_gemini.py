import unittest
from unittest.mock import patch, MagicMock
import tests  # bootstraps mocks
from agent_a.app.models import GlobalGemini


class TestGlobalGemini(unittest.TestCase):
    def test_global_gemini_forces_global_location(self):
        with patch("agent_a.app.models.Client") as mock_client_cls:
            mock_instance = MagicMock()
            mock_client_cls.return_value = mock_instance

            model = GlobalGemini(model="gemini-3.7-flash")
            client = model.api_client

            # Ensure Client is instantiated with enterprise=True and location="global"
            mock_client_cls.assert_called_once_with(enterprise=True, location="global")
            self.assertEqual(client, mock_instance)


if __name__ == "__main__":
    unittest.main()
