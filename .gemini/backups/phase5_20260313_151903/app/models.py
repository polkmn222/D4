from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_person_account = Column(Boolean, default=False)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    tier = Column(String, default="Bronze") # Bronze, Silver, Gold, Diamond
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    lead_source = Column(String, nullable=True) # Web, Referral, Manual
    status = Column(String, default="New") # New, Contacted, Qualified, Junk
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    status = Column(String, default="Open - Not Contacted")
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    converted_opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., Ioniq 5
    brand = Column(String, default="Hyundai")
    category = Column(String, nullable=True) # SUV, Sedan, EV
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, default=0)
    stage = Column(String, default="Prospecting")
    probability = Column(Integer, default=10)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    name = Column(String, nullable=False) # Plate or Nickname
    vin = Column(String, unique=True, nullable=True) # Vehicle Identification Number
    status = Column(String, default="Active")
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
