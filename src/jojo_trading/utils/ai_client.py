
import os
import time
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JoJoAI")

class AIClient:
    """
    Robust wrapper for Google Gemini API.
    Handles authentication, rate limiting (429), and model availability (404).
    """
    
    # Priority list of models to try
    MODEL_PRIORITY = [
        "gemini-2.0-flash-exp", # Newest, fastest
        "gemini-1.5-flash",     # Stable fast
        "gemini-1.5-pro",       # High intelligence
        "gemini-pro"            # Legacy fallback
    ]

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
            
        self.current_model_name = self.MODEL_PRIORITY[0]
        self.max_retries = 3
        self.base_delay = 5 # seconds

    def generate_content(self, prompt):
        """
        Generate content with automatic fallback and retry.
        Returns: Response text or None if all attempts fail.
        """
        if not self.api_key:
             return "Error: API Key missing."

        # Try models in order
        for model_name in self.MODEL_PRIORITY:
            logger.info(f"Attempting with model: {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
                
                # Retry loop for Rate Limits
                for attempt in range(self.max_retries):
                    try:
                        response = model.generate_content(prompt)
                        self.current_model_name = model_name # Remember successful model
                        return response.text
                        
                    except Exception as e:
                        error_str = str(e)
                        
                        # Handle Rate Limit (429)
                        if "429" in error_str or "quota" in error_str.lower():
                            wait_time = self.base_delay * (2 ** attempt) # Exponential backoff
                            logger.warning(f"Rate limit hit on {model_name}. Retrying in {wait_time}s... ({attempt+1}/{self.max_retries})")
                            time.sleep(wait_time)
                            continue
                            
                        # Handle blocked content?
                        if "finish_reason" in error_str.lower():
                             logger.warning(f"Content blocked by safety filters on {model_name}.")
                             break # Try next model
                             
                        raise e # Re-raise other errors to outer loop (Model fallback)
                        
            except Exception as e:
                 logger.error(f"Failed with {model_name}: {e}")
                 # Continue to next model in priority list
                 continue
                 
        return "Error: All AI models failed to generate response."

if __name__ == "__main__":
    # Self-test
    client = AIClient()
    print(client.generate_content("Hello, are you online?"))
