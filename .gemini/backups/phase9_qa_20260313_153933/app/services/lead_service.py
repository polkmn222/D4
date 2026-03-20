from sqlalchemy.orm import Session
from ..models import Lead, Account, Opportunity, Contact
from ..utils.sf_id import get_id
from typing import List, Optional

class LeadService:
    @staticmethod
    def create_lead(db: Session, **kwargs) -> Lead:
        db_lead = Lead(id=get_id("Lead"), **kwargs)
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        return db_lead

    @staticmethod
    def get_leads(db: Session, converted: bool = False) -> List[Lead]:
        return db.query(Lead).filter(Lead.is_converted == converted).all()

    @staticmethod
    def convert_lead(db: Session, lead_id: str, product_id: Optional[str] = None) -> Optional[Account]:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or lead.is_converted:
            return None

        # 1. Create Account (Individual if no company, otherwise Corporate)
        is_person = not bool(lead.company)
        acc_name = f"{lead.first_name} {lead.last_name}" if is_person else lead.company
        
        account = Account(
            id=get_id("Account"),
            name=acc_name,
            is_person_account=is_person,
            record_type="Individual" if is_person else "Corporate",
            description=f"Converted from Lead: {lead.first_name} {lead.last_name}"
        )
        db.add(account)

        # 2. If Individual, also create/link a Contact
        contact = Contact(
            id=get_id("Contact"),
            account_id=account.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            description=lead.description
        )
        db.add(contact)

        # 3. Create Opportunity
        opportunity = Opportunity(
            id=get_id("Opportunity"),
            account_id=account.id,
            product_id=product_id,
            lead_id=lead.id,
            name=f"{acc_name} - New Deal",
            amount=0,
            stage="Qualification"
        )
        db.add(opportunity)

        # 4. Mark Lead as converted
        lead.is_converted = True
        lead.converted_account_id = account.id
        lead.converted_opportunity_id = opportunity.id
        lead.status = "Closed - Converted"

        db.commit()
        db.refresh(account)
        return account
