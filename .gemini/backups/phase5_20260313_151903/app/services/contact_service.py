from sqlalchemy.orm import Session
from ..models import Contact
from ..database import engine, Base
from typing import List, Optional

# Initialize database tables
def init_db():
    Base.metadata.create_all(bind=engine)

class ContactService:
    @staticmethod
    def create_contact(db: Session, first_name: str, last_name: str, email: str, phone: str, **kwargs) -> Contact:
        db_contact = Contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            **kwargs
        )
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def get_contact(db: Session, contact_id: int) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()

    @staticmethod
    def get_contacts(db: Session, skip: int = 0, limit: int = 100) -> List[Contact]:
        return db.query(Contact).offset(skip).limit(limit).all()

    @staticmethod
    def update_contact(db: Session, contact_id: int, **updates) -> Optional[Contact]:
        db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            for key, value in updates.items():
                if hasattr(db_contact, key):
                    setattr(db_contact, key, value)
            db.commit()
            db.refresh(db_contact)
        return db_contact

    @staticmethod
    def delete_contact(db: Session, contact_id: int) -> bool:
        db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if db_contact:
            db.delete(db_contact)
            db.commit()
            return True
        return False
