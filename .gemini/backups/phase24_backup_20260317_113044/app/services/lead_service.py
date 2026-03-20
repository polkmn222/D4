from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..models import Lead, Account, Opportunity, Contact
from ..utils.sf_id import get_id
from ..utils.timezone import get_kst_now_naive
from .base_service import BaseService

logger = logging.getLogger(__name__)

class LeadService(BaseService[Lead]):
    model = Lead
    object_name = "Lead"

    @classmethod
    def create_lead(cls, db: Session, **kwargs) -> Lead:
        return cls.create(db, **kwargs)

    @classmethod
    def get_leads(cls, db: Session, converted: bool = False) -> List[Lead]:
        return cls.list(db, is_converted=converted)

    @classmethod
    def get_lead(cls, db: Session, lead_id: str) -> Optional[Lead]:
        return cls.get(db, lead_id)

    @classmethod
    def update_lead(cls, db: Session, lead_id: str, **kwargs) -> Optional[Lead]:
        return cls.update(db, lead_id, **kwargs)

    @classmethod
    def delete_lead(cls, db: Session, lead_id: str) -> bool:
        return cls.delete(db, lead_id)

    @classmethod
    def restore_lead(cls, db: Session, lead_id: str) -> bool:
        return cls.restore(db, lead_id)

    @classmethod
    def update_stage(cls, db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        return cls.update_lead(db, lead_id, status=stage)

    @classmethod
    def toggle_follow(cls, db: Session, lead_id: str, enabled: bool) -> Optional[Lead]:
        return cls.update_lead(db, lead_id, is_followed=enabled)

    @staticmethod
    def _create_converted_account(db: Session, lead: Lead, account_name: str, record_type: str) -> Account:
        is_person = (record_type == "Individual")
        final_name = account_name if account_name else f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "New Account"
        account = Account(
            id=get_id("Account"),
            name=final_name,
            is_person_account=is_person,
            record_type=record_type,
            phone=lead.phone,
            email=lead.email,
            description=f"Converted from Lead: {final_name}",
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(account)
        db.flush()
        return account

    @staticmethod
    def _create_converted_contact(db: Session, lead: Lead, account_id: str) -> Contact:
        contact = Contact(
            id=get_id("Contact"),
            account=account_id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            gender=lead.gender,
            description=lead.description,
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(contact)
        db.flush()
        return contact

    @staticmethod
    def _create_converted_opportunity(db: Session, lead: Lead, account_id: str, opp_name: str) -> Opportunity:
        final_name = opp_name if opp_name else f"{lead.last_name if lead.last_name else 'Lead'} - Deal"
        opportunity = Opportunity(
            id=get_id("Opportunity"),
            account=account_id,
            lead=lead.id,
            brand=lead.brand,
            model=lead.model,
            product=lead.product,
            name=final_name,
            amount=0,
            stage="Qualification",
            status="Open",
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(opportunity)
        db.flush()
        return opportunity

    @classmethod
    def convert_lead(cls, db: Session, lead_id: str) -> Optional[dict]:
        """Simple wrapper for backward compatibility with tests."""
        return cls.convert_lead_advanced(db, lead_id)

    @classmethod
    def convert_lead_advanced(
        cls, db: Session, lead_id: str,
        account_name: str = None,
        account_record_type: str = "Individual",
        opportunity_name: str = None,
        dont_create_opp: bool = False,
        converted_status: str = "Qualified"
    ) -> Optional[dict]:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead or lead.is_converted:
                return None

            account = cls._create_converted_account(db, lead, account_name, account_record_type)
            contact = cls._create_converted_contact(db, lead, account.id)
            
            opportunity = None
            if not dont_create_opp:
                opportunity = cls._create_converted_opportunity(db, lead, account.id, opportunity_name)

            lead.is_converted = True
            lead.converted_account = account.id
            lead.converted_opportunity = opportunity.id if opportunity else None
            lead.status = converted_status
            lead.updated_at = get_kst_now_naive()
            
            db.commit()
            return {"account": account, "contact": contact, "opportunity": opportunity}
        except Exception as e:
            db.rollback()
            logger.error(f"Lead conversion failed: {str(e)}")
            raise e
