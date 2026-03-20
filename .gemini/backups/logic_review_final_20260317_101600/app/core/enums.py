from enum import Enum

class RecordType(str, Enum):
    BRAND = "Brand"
    MODEL = "Model"
    INDIVIDUAL = "Individual"
    CORPORATE = "Corporate"
    SMS = "SMS"
    LMS = "LMS"
    MMS = "MMS"

class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PROSPECT = "Prospect"

class AccountTier(str, Enum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

class LeadStatus(str, Enum):
    NEW = "New"
    FOLLOW_UP = "Follow Up"
    QUALIFIED = "Qualified"
    LOST = "Lost"

class OpportunityStage(str, Enum):
    PROSPECTING = "Prospecting"
    QUALIFICATION = "Qualification"
    NEEDS_ANALYSIS = "Needs Analysis"
    VALUE_PROPOSITION = "Value Proposition"
    TEST_DRIVE = "Test Drive" # Special case for Automotive
    NEGOTIATION = "Negotiation/Review"
    PROPOSAL = "Proposal/Price Quote"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"

class OpportunityStatus(str, Enum):
    OPEN = "Open"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"

class CampaignStatus(str, Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ABORTED = "Aborted"

class TaskStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DEFERRED = "Deferred"
    WAITING = "Waiting on someone else"

class TaskPriority(str, Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"

class MessageDirection(str, Enum):
    INBOUND = "Inbound"
    OUTBOUND = "Outbound"

class MessageStatus(str, Enum):
    PENDING = "Pending"
    SENT = "Sent"
    DELIVERED = "Delivered"
    FAILED = "Failed"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"
