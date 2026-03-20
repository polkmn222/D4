from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .lead_service import LeadService
from .opportunity_service import OpportunityService
from .contact_service import ContactService

class SearchService:
    @staticmethod
    def global_search(db: Session, query: str) -> List[Dict[str, Any]]:
        if not query:
            return []
            
        results = []
        q_lower = query.lower()
        
        # Search Leads
        leads = LeadService.get_leads(db)
        for l in leads:
            if q_lower in f"{l.first_name} {l.last_name}".lower() or q_lower in (l.email or "").lower():
                results.append({"type": "Lead", "name": f"{l.first_name} {l.last_name}", "id": l.id, "url": f"/leads/{l.id}", "info": l.email})
                
        # Search Opportunities
        opps = OpportunityService.get_opportunities(db)
        for o in opps:
            if q_lower in o.name.lower():
                results.append({"type": "Opportunity", "name": o.name, "id": o.id, "url": f"/opportunities/{o.id}", "info": o.stage})
                
        # Search Contacts
        contacts = ContactService.get_contacts(db)
        for c in contacts:
            if q_lower in f"{c.first_name} {c.last_name}".lower() or q_lower in (c.email or "").lower() or q_lower in (c.name or "").lower():
                results.append({"type": "Contact", "name": f"{c.first_name} {c.last_name}" if not c.name else c.name, "id": c.id, "url": f"/contacts/{c.id}", "info": c.email})
                
        return results
