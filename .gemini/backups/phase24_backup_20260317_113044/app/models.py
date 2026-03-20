from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base
from .core.enums import RecordType, AccountStatus, AccountTier, LeadStatus, OpportunityStage, OpportunityStatus, CampaignStatus, TaskStatus, TaskPriority, MessageDirection, MessageStatus
from .utils.timezone import get_kst_now_naive

class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=get_kst_now_naive)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), default=get_kst_now_naive)
    deleted_at = Column(DateTime, nullable=True)

class VehicleSpecification(BaseModel):
    __tablename__ = "vehicle_specifications"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    record_type = Column(String, default=RecordType.MODEL) # Brand, Model
    parent = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)

class Model(BaseModel):
    __tablename__ = "models"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)

class Campaign(BaseModel):
    __tablename__ = "campaigns"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    status = Column(String, default=CampaignStatus.PLANNED)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

class Account(BaseModel):
    __tablename__ = "accounts"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    is_person_account = Column(Boolean, default=False)
    record_type = Column(String, default=RecordType.INDIVIDUAL) # Individual, Corporate
    status = Column(String, default=AccountStatus.ACTIVE) # Active, Inactive, Prospect
    industry = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    tier = Column(String, default=AccountTier.BRONZE)
    description = Column(Text, nullable=True)

class Contact(BaseModel):
    __tablename__ = "contacts"

    id = Column(String(18), primary_key=True, index=True)
    account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
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
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default=LeadStatus.NEW) # New, Follow Up, Qualified, Lost
    is_converted = Column(Boolean, default=False)
    converted_account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    converted_opportunity = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    campaign = Column(String(18), ForeignKey("campaigns.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_followed = Column(Boolean, default=False)

class Product(BaseModel):
    __tablename__ = "products"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    category = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)

class Opportunity(BaseModel):
    __tablename__ = "opportunities"

    id = Column(String(18), primary_key=True, index=True)
    account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    lead = Column(String(18), ForeignKey("leads.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    asset = Column(String(18), ForeignKey("assets.id"), nullable=True)
    name = Column(String, nullable=True)
    amount = Column(Integer, default=0)
    stage = Column(String, default=OpportunityStage.PROSPECTING)
    status = Column(String, default=OpportunityStatus.OPEN) # Open, Closed Won, Closed Lost
    probability = Column(Integer, default=10)
    temperature = Column(String, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    is_followed = Column(Boolean, default=False)

class Asset(BaseModel):
    __tablename__ = "assets"

    id = Column(String(18), primary_key=True, index=True)
    account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    name = Column(String, nullable=True)
    vin = Column(String, nullable=True)
    status = Column(String, default=AccountStatus.ACTIVE)
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)

class Task(BaseModel):
    __tablename__ = "tasks"

    id = Column(String(18), primary_key=True, index=True)
    account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    opportunity = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    subject = Column(String, nullable=True)
    status = Column(String, default=TaskStatus.NOT_STARTED) # Not Started, In Progress, Completed
    priority = Column(String, default=TaskPriority.NORMAL)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    message = Column(String(18), ForeignKey("messages.id"), nullable=True)

class Message(BaseModel):
    __tablename__ = "messages"

    id = Column(String(18), primary_key=True, index=True)
    contact = Column(String(18), ForeignKey("contacts.id"), nullable=True)
    account = Column(String(18), ForeignKey("accounts.id"), nullable=True)
    template = Column(String(18), ForeignKey("message_templates.id"), nullable=True)
    direction = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String, default=MessageStatus.PENDING)
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(direction.in_([MessageDirection.INBOUND, MessageDirection.OUTBOUND]), name='check_direction'),
    )

class MessageTemplate(BaseModel):
    __tablename__ = "message_templates"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    record_type = Column(String, default="SMS")
