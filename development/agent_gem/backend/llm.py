import os
import json
import httpx
import re
import logging
from typing import Dict, Any, Optional

load_dotenv = lambda: None # placeholder if not already loaded

logger = logging.getLogger(__name__)

class AgentGemLLMService:
    @classmethod
    async def get_intent(cls, query: str, system_prompt: str) -> Dict[str, Any]:
        """
        Uses LLM (Gemini preferred) to determine the intent and extract data from user query.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback to a simple rule-based approach or another LLM if needed
            return {"intent": "CHAT", "text": "API Key not configured.", "score": 0.0}

        try:
            full_prompt = f"{system_prompt}\n\nUser Query: {query}\nResponse must be JSON."
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                    params={"key": api_key},
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": full_prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "response_mime_type": "application/json"
                        }
                    },
                    timeout=10.0,
                )
                payload = response.json()

            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            
            # Extract JSON from response text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            
            return {"intent": "CHAT", "text": "Failed to parse AI response.", "score": 0.0}
            
        except Exception as e:
            logger.error(f"LLM Error in AgentGem: {str(e)}")
            return {"intent": "CHAT", "text": f"AI service error: {str(e)}", "score": 0.0}
