from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base

class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class VehicleSpecification(BaseModel):
    __tablename__ = "vehicle_specifications"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    record_type = Column(String, default="Model") # Brand, Model
    parent_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True) # For Model -> Brand lookup
    description = Column(Text, nullable=True)

class Campaign(BaseModel):
    __tablename__ = "campaigns"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    status = Column(String, default="Planned")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

class Account(BaseModel):
    __tablename__ = "accounts"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_person_account = Column(Boolean, default=False)
    record_type = Column(String, default="Individual") # Individual, Corporate
    status = Column(String, default="Active") # Active, Inactive, Prospect
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    tier = Column(String, default="Bronze")
    description = Column(Text, nullable=True)

class Contact(BaseModel):
    __tablename__ = "contacts"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    status = Column(String, default="New")
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)

class Lead(BaseModel):
    __tablename__ = "leads"

    id = Column(String(18), primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    status = Column(String, default="New") # New, Follow Up, Qualified, Lost
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    converted_opportunity_id = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    campaign_id = Column(String(18), ForeignKey("campaigns.id"), nullable=True)
    brand_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model_interest_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)

class Product(BaseModel):
    __tablename__ = "products"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, default="Solaris") # Fictional
    category = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)

class Opportunity(BaseModel):
    __tablename__ = "opportunities"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    lead_id = Column(String(18), ForeignKey("leads.id"), nullable=True)
    brand_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model_interest_id = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, default=0)
    stage = Column(String, default="Prospecting")
    status = Column(String, default="Open") # Open, Closed Won, Closed Lost
    probability = Column(Integer, default=10)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)

class Asset(BaseModel):
    __tablename__ = "assets"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    product_id = Column(String(18), ForeignKey("products.id"), nullable=True)
    name = Column(String, nullable=False)
    vin = Column(String, unique=True, nullable=True)
    status = Column(String, default="Active")
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)

class Task(BaseModel):
    __tablename__ = "tasks"

    id = Column(String(18), primary_key=True, index=True)
    account_id = Column(String(18), ForeignKey("accounts.id"), nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="Not Started") # Not Started, In Progress, Completed
    priority = Column(String, default="Normal")
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)

class Message(BaseModel):
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
