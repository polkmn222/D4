import json
import httpx
import logging
from .ai_service import AIService, GROQ_API_KEY
from sqlalchemy.orm import Session

class SeedService:
    @staticmethod
    async def generate_theme_data(db: Session, theme: str, count: int = 5):
        """
        Generates realistic Automotive CRM data (Leads, Products, Accounts) using AI.
        """
        prompt = f"""
        Generate {count} realistic CRM entries for an Automotive business themed around '{theme}'.
        
        Generate:
        1. "leads": list of (first_name, last_name, company, email, phone, status: 'Open', 'Working', 'Nurturing')
        2. "products": list of (name: Car Model like 'Ioniq 5', brand, category: 'EV', 'SUV', 'Sedan', base_price: integer)
        3. "accounts": list of (name, industry: 'Automotive', is_person_account: boolean, tier: 'Bronze', 'Silver', 'Gold')
        
        Return ONLY valid JSON with keys "leads", "products", "accounts".
        """
        
        api_key = GROQ_API_KEY
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
        
        async with httpx.AsyncClient() as client:
            try:
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
                    
                    # 1. Seed Products
                    from .product_service import ProductService
                    for p in data.get("products", []):
                        ProductService.create_product(db, **p)
                        
                    # 2. Seed Leads
                    from .lead_service import LeadService
                    for l in data.get("leads", []):
                        LeadService.create_lead(db, **l)
                        
                    # 3. Seed Accounts
                    from .account_service import AccountService
                    for a in data.get("accounts", []):
                        AccountService.create_account(db, **a)
                        
                    return True
            except Exception as e:
                logging.error(f"Seeding failed: {e}")
                return False
        return False
