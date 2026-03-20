from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_person_account = Column(Boolean, default=False)
    record_type = Column(String, default="Individual") # Individual, Corporate
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    tier = Column(String, default="Bronze")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    status = Column(String, default="New")
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(18), primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    status = Column(String, default="Open - Not Contacted")
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    converted_opportunity_id = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, default="Solaris") # Fictional
    category = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    lead_id = Column(String(18), ForeignKey("leads.id"), nullable=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, default=0)
    stage = Column(String, default="Prospecting")
    probability = Column(Integer, default=10)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(18), primary_key=True, index=True)
    contact_id = Column(String(18), ForeignKey("contacts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    name = Column(String, nullable=False)
    vin = Column(String, unique=True, nullable=True)
    status = Column(String, default="Active")
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="Not Started") # Not Started, In Progress, Completed
    priority = Column(String, default="Normal")
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(18), primary_key=True, index=True)
    contact_id = Column(String(18), ForeignKey("contacts.id"), nullable=False)
    direction = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="Pending")
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(direction.in_(['Inbound', 'Outbound']), name='check_direction'),
    )
