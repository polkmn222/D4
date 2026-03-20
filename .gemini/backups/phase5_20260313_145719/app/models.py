from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from .database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    account_id = Column(Integer, nullable=True)
    
    # 영업/마케팅 정보
    lead_source = Column(String, default="Manual")
    status = Column(String, default="New")
    
    # AI 및 데이터 관리 (AI Ready)
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    
    # Standard timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    direction = Column(String, nullable=False) # Inbound, Outbound
    content = Column(Text, nullable=False)
    status = Column(String, default="Pending") # Pending, Sent, Failed
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(direction.in_(['Inbound', 'Outbound']), name='check_direction'),
    )

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Integer, default=0)
    stage = Column(String, default="Prospecting") # Prospecting, Qualification, Closed Won, etc.
    probability = Column(Integer, default=10)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="Active") # Active, Expired, Maintenance
    serial_number = Column(String, unique=True, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
