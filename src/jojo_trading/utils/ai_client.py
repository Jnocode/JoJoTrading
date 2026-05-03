import os
import time
import json
import logging
import requests
from dotenv import load_dotenv
from jojo_trading.core.stock_database import StockDatabase

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JoJoAI")


class AIClient:
    """
    Robust wrapper for AI APIs with multi-provider support.
    Providers: Google Gemini, Groq, Ollama (local).
    Handles authentication, rate limiting (429), model fallback, and provider routing.

    Provider Selection Priority:
        Database Setting "ai_provider" → User Choice (Gemini | Groq | Ollama)
    """

    # --- Gemini Free Tier Models (via REST API, no deprecated SDK) ---
    MODEL_PRIORITY_GEMINI = [
        "gemini-2.0-flash",          # Stable, fast, free tier friendly
        "gemini-2.0-flash-lite",     # Lighter variant
        "gemini-1.5-flash",          # Proven workhorse
    ]

    # --- Groq Free Tier Models ---
    MODEL_PRIORITY_GROQ = [
        "llama-3.3-70b-versatile",   # Fast logic
        "llama-3.1-8b-instant",      # Backup fast
        "mixtral-8x7b-32768",        # Backup reasoning
    ]

    # --- Ollama Default Models (user-configurable) ---
    OLLAMA_DEFAULT_MODEL = "gemma3:4b"

    def __init__(self):
        load_dotenv()
        self.db = StockDatabase()

        # --- API Keys (Priority: DB > .env) ---
        db_gemini_key = self.db.get_setting("gemini_api_key", "")
        self.gemini_key = db_gemini_key if db_gemini_key else os.getenv("GOOGLE_API_KEY")
        # Strip surrounding quotes if present (common .env issue)
        if self.gemini_key:
            self.gemini_key = self.gemini_key.strip("'\"")

        db_groq_key = self.db.get_setting("groq_api_key", "")
        self.groq_key = db_groq_key if db_groq_key else os.getenv("GROQ_API_KEY")
        if self.groq_key:
            self.groq_key = self.groq_key.strip("'\"")

        # --- Ollama Config ---
        self.ollama_url = self.db.get_setting("ollama_url", "http://localhost:11434")
        self.ollama_model = self.db.get_setting("ollama_model", self.OLLAMA_DEFAULT_MODEL)

        # --- Groq Client (lazy init, only if key exists) ---
        self.groq_client = None

        # --- Retry config ---
        self.max_retries = 1
        self.base_delay = 2  # seconds

        # Log available providers
        providers = []
        if self.gemini_key:
            providers.append("Gemini")
        if self.groq_key:
            providers.append("Groq")
        providers.append("Ollama (local)")
        logger.info(f"AIClient initialized. Available providers: {', '.join(providers)}")

    def generate_content(self, prompt: str) -> str:
        """
        Generate content using the selected provider with automatic fallback and retry.
        Returns: Response text or "Error: ..." message.
        """
        provider = self.db.get_setting("ai_provider", "Gemini")
        logger.info(f"Using AI Provider: {provider}")

        if provider == "Groq":
            return self._generate_with_groq(prompt)
        elif provider == "Ollama":
            return self._generate_with_ollama(prompt)
        else:
            # Default: Gemini
            return self._generate_with_gemini(prompt)

    # =========================================================================
    # Gemini — 使用 REST API (取代已 deprecated 的 google.generativeai SDK)
    # =========================================================================
    def _generate_with_gemini(self, prompt: str) -> str:
        if not self.gemini_key:
            return "Error: GOOGLE_API_KEY missing. 請至 Settings 設定 Gemini API Key。"

        for model_name in self.MODEL_PRIORITY_GEMINI:
            logger.info(f"Attempting Gemini model: {model_name}")

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{model_name}:generateContent?key={self.gemini_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048,
                },
            }

            for attempt in range(self.max_retries + 1):
                try:
                    resp = requests.post(url, json=payload, timeout=30)

                    if resp.status_code == 200:
                        data = resp.json()
                        # Extract text from Gemini REST response
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        return "Error: Gemini returned empty response."

                    elif resp.status_code == 429:
                        # Rate limit
                        if attempt < self.max_retries:
                            wait_time = self.base_delay * (2 ** attempt)
                            logger.warning(
                                f"Rate limit (429) on {model_name}. "
                                f"Retrying in {wait_time}s... ({attempt+1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Rate limit exceeded on {model_name}. Failing over.")
                            break  # Try next model

                    elif resp.status_code in (400, 404):
                        # Model not found or bad request — skip to next model
                        error_msg = resp.json().get("error", {}).get("message", resp.text[:200])
                        logger.warning(f"{model_name} returned {resp.status_code}: {error_msg}")
                        break  # Next model

                    else:
                        error_msg = resp.text[:300]
                        logger.error(f"{model_name} HTTP {resp.status_code}: {error_msg}")
                        break  # Next model

                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout on {model_name}.")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error with {model_name}: {e}")
                    break

        return "Error: All Gemini models failed to generate response."

    # =========================================================================
    # Groq
    # =========================================================================
    def _generate_with_groq(self, prompt: str) -> str:
        if not self.groq_key:
            return "Error: GROQ_API_KEY missing. 請至 Settings 設定 Groq API Key。"

        # Lazy init Groq client
        if not self.groq_client:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
            except ImportError:
                return "Error: groq package not installed."

        for model_name in self.MODEL_PRIORITY_GROQ:
            logger.info(f"Attempting Groq model: {model_name}")
            try:
                for attempt in range(self.max_retries + 1):
                    try:
                        completion = self.groq_client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                            max_tokens=2048,
                            top_p=1,
                            stream=False,
                        )
                        return completion.choices[0].message.content
                    except Exception as e:
                        error_str = str(e).lower()
                        if "429" in error_str or "rate limit" in error_str:
                            if attempt < self.max_retries:
                                wait_time = self.base_delay * (2 ** attempt)
                                logger.warning(
                                    f"Rate limit on Groq {model_name}. "
                                    f"Retrying in {wait_time}s..."
                                )
                                time.sleep(wait_time)
                                continue
                            else:
                                break
                        raise e
            except Exception as e:
                logger.error(f"Failed with Groq {model_name}: {e}")
                continue

        return "Error: All Groq models failed to generate response."

    # =========================================================================
    # Ollama (Local) — 零成本、無限額度、完全離線
    # =========================================================================
    def _generate_with_ollama(self, prompt: str) -> str:
        """
        Call Ollama's local REST API.
        Default: http://localhost:11434/api/generate
        """
        # Re-read settings in case user changed them
        url = self.db.get_setting("ollama_url", self.ollama_url).rstrip("/")
        model = self.db.get_setting("ollama_model", self.ollama_model)

        endpoint = f"{url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 2048,
            },
        }

        logger.info(f"Attempting Ollama model: {model} at {url}")

        try:
            resp = requests.post(endpoint, json=payload, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "")
                if text:
                    return text
                return "Error: Ollama returned empty response."

            elif resp.status_code == 404:
                return (
                    f"Error: Ollama model '{model}' not found. "
                    f"請先執行 `ollama pull {model}` 下載模型。"
                )
            else:
                return f"Error: Ollama HTTP {resp.status_code}: {resp.text[:200]}"

        except requests.exceptions.ConnectionError:
            return (
                "Error: 無法連線 Ollama。請確認 Ollama 已啟動 "
                f"(預設地址: {url})。"
            )
        except requests.exceptions.Timeout:
            return "Error: Ollama 回應逾時 (Timeout)。模型可能太大或正在載入中。"
        except Exception as e:
            return f"Error: Ollama unexpected error: {e}"


if __name__ == "__main__":
    # Self-test
    client = AIClient()
    print(client.generate_content("Hello, are you online? Reply in one sentence."))
