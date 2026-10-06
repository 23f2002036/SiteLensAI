import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ai_service import generate_ai_companion_response


class GenerateAiCompanionResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_placeholder_vlm_credentials_are_rejected(self):
        with patch.dict(
            os.environ,
            {
                "OLLAMA_HOST": "",
                "GROQ_API_KEY": "your-groq-api-key-here",
                "GROK_API_KEY": "your-grok-api-key-here",
                "OPENAI_API_KEY": "",
            },
            clear=False,
        ):
            with patch("services.ai_service.httpx.AsyncClient") as mock_async_client:
                await generate_ai_companion_response("Check current site conditions")

        mock_async_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
