from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from .lead_service import LeadService
from .account_service import AccountService
from .opportunity_service import OpportunityService
from .contact_service import ContactService

class DashboardService:
    @staticmethod
    def get_dashboard_data(db: Session) -> Dict[str, Any]:
        """
        Gathers all necessary data for the dashboard.
        """
        # Recent Records (Mixed)
        leads = LeadService.get_leads(db)
        accounts = AccountService.get_accounts(db)
        opps = OpportunityService.get_opportunities(db)
        contacts = ContactService.get_contacts(db)
        
        all_records = []
        
        def safe_date(obj):
            if not obj.created_at: return datetime.min
            if isinstance(obj.created_at, datetime): return obj.created_at
            try: return datetime.fromisoformat(str(obj.created_at))
            except: return datetime.min

        for l in leads:
            all_records.append({"type": "Lead", "name": f"{l.first_name} {l.last_name}", "url": f"/leads/{l.id}", "date": safe_date(l)})
        for a in accounts:
            all_records.append({"type": "Account", "name": a.name, "url": f"/accounts/{a.id}", "date": safe_date(a)})
        for o in opps:
            all_records.append({"type": "Opportunity", "name": o.name, "url": f"/opportunities/{o.id}", "date": safe_date(o)})
        for c in contacts: 
            all_records.append({"type": "Contact", "name": f"{c.first_name} {c.last_name}", "url": f"/contacts/{c.id}", "date": safe_date(c)})
        
        all_records.sort(key=lambda x: x["date"], reverse=True)
        
        performance = OpportunityService.get_performance_stats(db, horizon_days=7)
        recent_opps_clicked = OpportunityService.get_recent_clicked(db, limit=5)
        recommended_opps = OpportunityService.get_ai_recommendations(db, limit=5)

        return {
            "recent_records": all_records[:5],
            "opportunities": recent_opps_clicked,
            "recommended_opportunities": recommended_opps,
            "performance": performance
        }
