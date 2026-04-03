import json
import os
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    Integration with Groq API.
    Aims for simplicity, using standard library modules (no third-party HTTP clients).
    """

    def __init__(self) -> None:
        self._api_key = os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            logger.warning(
                "GROQ_API_KEY is not set in the environment. "
                "AIService will fail if an API key is not provided."
            )

        # Using Groq's Responses API which simplifies generating text
        self._base_url = "https://api.groq.com/openai/v1/responses"
        
        # Fast, versatile model recommended by Groq
        self._model = "llama-3.3-70b-versatile"

    def _call_api(self, prompt: str, temperature: float = 0.7) -> str:
        """Helper to invoke the Groq API via HTTP."""
        if not self._api_key:
            raise ValueError("Configuration Error: GROQ_API_KEY environment variable is missing.")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Temperature of 0 is converted to 1e-8 in Groq, but sending a small float is safer.
        safe_temperature = 1e-8 if temperature <= 0 else temperature

        payload = {
            "model": self._model,
            "input": prompt,
            "temperature": safe_temperature,
        }

        request = urllib.request.Request(
            self._base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("output_text", "").strip()
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error("Groq API HTTP Error: %s -> %s", e.status, error_body)
            raise RuntimeError(f"Groq API Error {e.status}: {error_body}") from e
        except Exception as e:
            logger.exception("Unexpected error calling Groq API")
            raise RuntimeError(f"Communication with Groq failed: {e}") from e

    def classify(self, text: str, labels: list[str]) -> str:
        """
        Classify text into one of the provided labels.
        """
        prompt = (
            f"You are a strict classification engine.\n"
            f"Classify the following text into EXACTLY ONE of these categories: {', '.join(labels)}.\n"
            f"RULES:\n"
            f"1. You must respond ONLY with the exact name of the matched category.\n"
            f"2. Provide NO explanations, NO markdown, NO additional text.\n\n"
            f"Text to classify:\n{text}"
        )
        
        # Use a very low temperature for deterministic classification
        result = self._call_api(prompt=prompt, temperature=0.01)
        
        # Basic cleanup just in case the model hallucinates extra whitespace
        return result.strip()

    def generate(self, prompt: str) -> str:
        """
        Generate text based on a given prompt.
        """
        return self._call_api(prompt=prompt, temperature=0.7)
