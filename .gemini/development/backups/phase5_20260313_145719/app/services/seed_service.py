import json
from .ai_service import AIService
from .contact_service import ContactService
from sqlalchemy.orm import Session
import logging

class SeedService:
    @staticmethod
    async def generate_theme_data(db: Session, theme: str, count: int = 5):
        """
        Generates realistic CRM data based on a theme using AI and injects it into the DB.
        """
        prompt = f"""
        Generate {count} realistic CRM contacts for a '{theme}' business.
        Each contact must have:
        - first_name, last_name
        - email (unique)
        - phone
        - lead_source (Web, Referral, or Manual)
        - status (New, Contacted, or Qualified)
        - description (a 2-3 sentence business context)
        
        Return ONLY a JSON list of objects.
        """
        
        # Use Groq/Cerebras via AIService to get JSON
        # We'll use a raw call for structured output
        from .ai_service import GROQ_API_KEY, CEREBRAS_API_KEY
        import httpx
        
        api_key = GROQ_API_KEY # Groq is better for structured JSON at high volume
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                base_url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                raw_json = response.json()["choices"][0]["message"]["content"]
                data = json.loads(raw_json)
                contacts = data.get("contacts", []) if isinstance(data, dict) else data
                
                # Ingest into DB
                created_count = 0
                for c_data in contacts:
                    try:
                        # Auto-summarize description using AI
                        ai_summary = await AIService.generate_summary(c_data.get("description", ""))
                        
                        ContactService.create_contact(
                            db,
                            first_name=c_data["first_name"],
                            last_name=c_data["last_name"],
                            email=c_data["email"],
                            phone=c_data["phone"],
                            lead_source=c_data.get("lead_source", "Manual"),
                            status=c_data.get("status", "New"),
                            description=c_data.get("description", ""),
                            ai_summary=ai_summary
                        )
                        created_count += 1
                    except Exception as e:
                        logging.error(f"Failed to seed contact: {e}")
                
                return created_count
            return 0
