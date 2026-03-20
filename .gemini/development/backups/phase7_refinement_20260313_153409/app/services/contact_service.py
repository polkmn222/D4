from sqlalchemy.orm import Session
from ..models import Contact
from ..utils.sf_id import get_id
from typing import List, Optional

class ContactService:
    @staticmethod
    def create_contact(db: Session, **kwargs) -> Contact:
        db_contact = Contact(id=get_id("Contact"), **kwargs)
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def get_contacts(db: Session, account_id: Optional[str] = None) -> List[Contact]:
        query = db.query(Contact)
        if account_id:
            query = query.filter(Contact.account_id == account_id)
        return query.all()

    @staticmethod
    def get_contact(db: Session, contact_id: str) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()
