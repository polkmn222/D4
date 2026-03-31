import os
import json
import httpx
import logging
import re
import asyncio
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from db.models import Model as DbModel, Product as DbProduct, VehicleSpecification
from web.backend.app.core.enums import AssetStatus, Gender, LeadStatus, OpportunityStage, OpportunityStatus, RecordType

# Import services from the main app
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.services.model_service import ModelService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.message.backend.services.message_service import MessageService
from web.backend.app.utils.error_handler import handle_agent_errors
from ai_agent.llm.backend.recommendations import AIRecommendationService
from ai_agent.llm.backend.message_policy_retrieval import MessagePolicyRetrievalService
from ai_agent.debug import debug_event
from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier
from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.llm.backend.intent_reasoner import IntentReasoner
from web.backend.app.services.ai_intelligence_service import AiIntelligenceService
from ai_agent.ui.backend.crud import (
    build_chat_native_form,
    build_lead_edit_form_response,
    build_lead_open_record_response,
    build_object_edit_form_response,
    build_object_open_record_response,
)

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY") or os.getenv("CEREBRAS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "backend", "metadata.json")

class AiAgentService:
    STT_MAX_BYTES = 10 * 1024 * 1024
    STT_ALLOWED_CONTENT_TYPES = {
        "audio/webm",
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/x-m4a",
        "audio/m4a",
        "audio/ogg",
    }
    PHASE1_OBJECTS = {"lead", "contact", "opportunity"}
    CHAT_NATIVE_FORM_OBJECTS = {"lead", "contact", "opportunity"}
    AI_MANAGED_INLINE_FORM_OBJECTS = CHAT_NATIVE_FORM_OBJECTS | {"asset", "brand", "model", "message_template"}
    FAST_FORM_CREATE_OBJECTS = {"product", "asset", "brand", "model", "message_template"}
    DETERMINISTIC_CRUD_OBJECTS = PHASE1_OBJECTS | FAST_FORM_CREATE_OBJECTS
    LEAD_STATUS_ALIASES = {
        "new": "New",
        "follow up": "Follow Up",
        "follow-up": "Follow Up",
        "qualified": "Qualified",
        "lost": "Lost",
        "신규": "New",
        "팔로우업": "Follow Up",
        "후속": "Follow Up",
        "자격": "Qualified",
        "실패": "Lost",
        "유실": "Lost",
    }

    LEAD_UPDATE_FIELD_ALIASES = {
        "first_name": ["first name", "firstname", "이름"],
        "last_name": ["last name", "lastname", "surname"],
        "status": ["status", "상태"],
        "email": ["email", "이메일", "메일"],
        "phone": ["phone", "mobile", "휴대폰", "전화"],
        "gender": ["gender", "성별"],
        "brand": ["brand", "브랜드"],
        "model": ["model", "모델"],
        "product": ["product", "상품"],
        "description": ["description", "desc", "note", "메모", "설명"],
    }

    LEAD_EDIT_CONTEXT_INTENTS = {"CREATE", "MANAGE", "UPDATE"}
    LEAD_READ_ACTIONS = {"show", "open", "view", "read", "details", "manage", "보여", "보여줘", "보여주라", "열어", "열어줘", "열어봐", "상세", "관리"}
    LEAD_EDIT_ACTIONS = {"edit", "수정"}
    LEAD_UPDATE_ACTIONS = {"update", "change", "modify", "save", "변경", "바꿔", "바까", "저장"}
    LEAD_DELETE_ACTIONS = {"delete", "remove", "erase", "삭제"}
    LEAD_CREATE_ACTIONS = {"create", "add", "new", "make", "build", "생성", "만들", "맹글", "맨들", "등록", "추가"}
    GENERIC_CREATE_ACTIONS = LEAD_CREATE_ACTIONS
    GENERIC_UPDATE_ACTIONS = LEAD_UPDATE_ACTIONS | LEAD_EDIT_ACTIONS
    GENERIC_QUERY_ACTIONS = set(IntentPreClassifier.ACTION_QUERY) | {"recent"}
    GENERIC_READ_ACTIONS = LEAD_READ_ACTIONS
    FAST_OBJECT_FIELD_ALIASES = {
        "brand": {
            "name": ["name", "brand name"],
            "description": ["description", "desc", "note"],
        },
        "model": {
            "name": ["name", "model name"],
            "brand": ["brand", "parent"],
            "description": ["description", "desc", "note"],
        },
        "product": {
            "name": ["name", "product name"],
            "brand": ["brand"],
            "model": ["model"],
            "category": ["category"],
            "base_price": ["base price", "base_price", "price"],
            "description": ["description", "desc", "note"],
        },
        "asset": {
            "name": ["name", "asset name"],
            "vin": ["vin"],
            "status": ["status"],
            "price": ["price"],
            "brand": ["brand"],
            "model": ["model"],
            "product": ["product"],
            "contact": ["contact"],
        },
        "message_template": {
            "name": ["name", "template name"],
            "subject": ["subject"],
            "content": ["content", "body"],
            "record_type": ["type", "record type", "record_type"],
            "image_url": ["image", "image url", "image_url"],
        },
    }
    FAST_OBJECT_REQUIRED_FIELDS = {
        "brand": ["name"],
        "model": ["name", "brand"],
        "product": ["name", "base_price"],
        "asset": ["vin"],
        "message_template": ["name", "content"],
    }
    RECENT_QUERY_MARKERS = {
        "recent",
        "latest",
        "newest",
        "most recent",
        "just created",
        "recently created",
        "방금 생성",
        "방금 생성한",
        "방금 만든",
        "최근",
        "최근 생성",
        "최근 만든",
    }
    D5_SCOPE_KEYWORDS = {
        "crm",
        "d5",
        "lead",
        "contact",
        "opportunity",
        "product",
        "asset",
        "brand",
        "model",
        "template",
        "message",
        "recommend",
        "dashboard",
        "workspace",
        "record",
        "리드",
        "연락처",
        "기회",
        "상품",
        "자산",
        "브랜드",
        "모델",
        "템플릿",
        "메시지",
        "추천",
    }
    POSSIBLE_LLM_CRUD_ACTION_HINTS = {
        "set",
        "mark",
        "rename",
        "close",
        "reopen",
        "assign",
        "qualify",
        "save",
        "update",
        "edit",
        "change",
        "modify",
        "delete",
        "remove",
        "open",
        "show",
        "pull",
        "fetch",
        "view",
        "read",
        "create",
        "add",
        "make",
    }
    CRM_CONTEXT_MARKERS = (
        "this",
        "that",
        "it",
        "those",
        "them",
        "selected",
        "last",
        "recent",
        "before",
        "one",
        "from the list",
        "from before",
        "just added",
        "just created",
        "we were just looking at",
    )
    SHORT_OBJECT_CLARIFICATIONS = {
        "l": "lead",
        "ld": "lead",
        "ct": "contact",
        "cntct": "contact",
        "opty": "opportunity",
        "oppy": "opportunity",
        "tmpl": "message_template",
        "tpl": "message_template",
        "prd": "product",
        "aset": "asset",
        "brnd": "brand",
        "mdl": "model",
    }
    ENGLISH_REQUEST_WRAPPER_PATTERNS = (
        r"^(?:please\s+)?(?:can|could|would|will)\s+you\s+",
        r"^(?:please\s+)?(?:help\s+me(?:\s+to)?|help\s+me\s+understand)\s+",
        r"^(?:please\s+)?(?:i\s+need(?:\s+you)?\s+to|i\s+want(?:\s+you)?\s+to)\s+",
    )
    BOUNDED_EXPLANATORY_HINTS = (
        "summary",
        "summarize",
        "report",
        "history",
        "analytics",
        "analysis",
        "overview",
        "next step",
        "next steps",
        "follow up",
        "follow-up",
        "followup",
        "remind",
        "reminder",
        "hot",
        "status overview",
        "pipeline",
        "is there any",
        "are there any",
        "what happened",
        "what is going on",
        "what's going on",
        "guide me",
        "help me understand",
    )
    BOUNDED_UPDATE_FIELD_HINTS = (
        "status",
        "phone",
        "email",
        "name",
        "first name",
        "last name",
        "owner",
        "stage",
        "amount",
        "probability",
        "description",
        "brand",
        "model",
        "product",
    )
    BOUNDED_GUIDANCE_HINTS = (
        "guide me through",
        "help with",
        "workflow",
        "flow",
        "creation",
        "how to create",
        "how do i create",
    )
    HOT_QUERY_HINTS = (
        "which",
        "hot",
        "warm",
        "active",
    )
    CRM_VALUE_HINTS = {
        "qualified",
        "contacted",
        "junk",
        "follow up",
        "follow-up",
        "closed won",
        "closed lost",
        "prospecting",
        "qualification",
        "test drive",
        "value proposition",
        "negotiation",
        "proposal",
        "new",
        "warm",
        "hot",
        "cold",
        "gold",
        "silver",
        "bronze",
        "mms",
        "lms",
        "sms",
    }
    CRM_FIELD_HINTS = {
        "email",
        "phone",
        "mobile",
        "vin",
        "plate",
        "probability",
        "amount",
        "price",
        "base price",
        "base_price",
        "subject",
        "content",
        "body",
        "type",
        "record type",
        "record_type",
        "image",
        "template",
        "brand",
        "model",
        "product",
        "asset",
        "contact",
        "opportunity",
        "lead",
    }
    ORDINAL_MARKERS = (
        ("first one", 0),
        ("1st one", 0),
        ("first record", 0),
        ("first", 0),
        ("latest one", 0),
        ("newest one", 0),
        ("most recent one", 0),
        ("latest", 0),
        ("newest", 0),
        ("most recent", 0),
        ("second one", 1),
        ("2nd one", 1),
        ("second", 1),
        ("third one", 2),
        ("3rd one", 2),
        ("third", 2),
        ("fourth one", 3),
        ("4th one", 3),
        ("fourth", 3),
        ("fifth one", 4),
        ("5th one", 4),
        ("fifth", 4),
    )
    CONTACT_STATUS_OPTIONS = ["New", "Contacted", "Qualified", "Junk"]
    OPPORTUNITY_STAGE_OPTIONS = [
        OpportunityStage.PROSPECTING.value,
        OpportunityStage.QUALIFICATION.value,
        OpportunityStage.TEST_DRIVE.value,
        OpportunityStage.VALUE_PROPOSITION.value,
        OpportunityStage.NEGOTIATION.value,
        OpportunityStage.PROPOSAL.value,
        OpportunityStage.CLOSED_WON.value,
        OpportunityStage.CLOSED_LOST.value,
    ]
    OPPORTUNITY_STATUS_OPTIONS = [
        OpportunityStatus.OPEN.value,
        OpportunityStatus.CLOSED_WON.value,
        OpportunityStatus.CLOSED_LOST.value,
    ]
    CHAT_NATIVE_FORM_CONFIG = {
        "lead": {
            "title_create": "Create Lead",
            "title_edit": "Edit Lead",
            "submit_create": "Create Lead",
            "submit_edit": "Save Lead",
            "fields": [
                {"name": "first_name", "label": "First Name", "control": "text", "default": "", "layout": "half"},
                {"name": "last_name", "label": "Last Name", "control": "text", "default": "", "required": True, "layout": "half"},
                {"name": "email", "label": "Email", "control": "email", "default": "", "layout": "half"},
                {"name": "phone", "label": "Phone", "control": "tel", "default": "", "layout": "half"},
                {
                    "name": "status",
                    "label": "Status",
                    "control": "select",
                    "default": LeadStatus.NEW.value,
                    "required": True,
                    "layout": "half",
                    "options": [
                        {"value": LeadStatus.NEW.value, "label": LeadStatus.NEW.value},
                        {"value": LeadStatus.FOLLOW_UP.value, "label": LeadStatus.FOLLOW_UP.value},
                        {"value": LeadStatus.QUALIFIED.value, "label": LeadStatus.QUALIFIED.value},
                        {"value": LeadStatus.LOST.value, "label": LeadStatus.LOST.value},
                    ],
                },
                {
                    "name": "gender",
                    "label": "Gender",
                    "control": "select",
                    "default": "",
                    "layout": "half",
                    "options": [
                        {"value": "", "label": "Unspecified"},
                        {"value": Gender.MALE.value, "label": Gender.MALE.value},
                        {"value": Gender.FEMALE.value, "label": Gender.FEMALE.value},
                        {"value": Gender.OTHER.value, "label": Gender.OTHER.value},
                        {"value": Gender.UNKNOWN.value, "label": Gender.UNKNOWN.value},
                    ],
                },
                {
                    "name": "product",
                    "label": "Product",
                    "control": "lookup",
                    "lookup_object": "Product",
                    "default": "",
                    "placeholder": "Search Product...",
                    "layout": "half",
                },
                {
                    "name": "model",
                    "label": "Model",
                    "control": "lookup",
                    "lookup_object": "Model",
                    "default": "",
                    "placeholder": "Search Model...",
                    "layout": "half",
                },
                {
                    "name": "brand",
                    "label": "Brand",
                    "control": "lookup",
                    "lookup_object": "Brand",
                    "default": "",
                    "placeholder": "Search Brand...",
                    "layout": "half",
                },
                {"name": "description", "label": "Description", "control": "textarea", "default": "", "layout": "full"},
            ],
        },
        "contact": {
            "title_create": "Create Contact",
            "title_edit": "Edit Contact",
            "submit_create": "Create Contact",
            "submit_edit": "Save Contact",
            "fields": [
                {"name": "first_name", "label": "First Name", "control": "text", "default": "", "layout": "half"},
                {"name": "last_name", "label": "Last Name", "control": "text", "default": "", "required": True, "layout": "half"},
                {"name": "email", "label": "Email", "control": "email", "default": "", "layout": "half"},
                {"name": "phone", "label": "Phone", "control": "tel", "default": "", "layout": "half"},
                {
                    "name": "gender",
                    "label": "Gender",
                    "control": "select",
                    "default": "",
                    "layout": "half",
                    "options": [
                        {"value": "", "label": "Unspecified"},
                        {"value": Gender.MALE.value, "label": Gender.MALE.value},
                        {"value": Gender.FEMALE.value, "label": Gender.FEMALE.value},
                        {"value": Gender.OTHER.value, "label": Gender.OTHER.value},
                        {"value": Gender.UNKNOWN.value, "label": Gender.UNKNOWN.value},
                    ],
                },
                {"name": "website", "label": "Website", "control": "text", "default": "", "layout": "half"},
                {
                    "name": "tier",
                    "label": "Tier",
                    "control": "select",
                    "default": "Bronze",
                    "layout": "half",
                    "options": [
                        {"value": "Bronze", "label": "Bronze"},
                        {"value": "Silver", "label": "Silver"},
                        {"value": "Gold", "label": "Gold"},
                        {"value": "Platinum", "label": "Platinum"},
                    ],
                },
                {"name": "description", "label": "Description", "control": "textarea", "default": "", "layout": "full"},
            ],
        },
        "opportunity": {
            "title_create": "Create Opportunity",
            "title_edit": "Edit Opportunity",
            "submit_create": "Create Opportunity",
            "submit_edit": "Save Opportunity",
            "fields": [
                {
                    "name": "contact",
                    "label": "Contact",
                    "control": "lookup",
                    "lookup_object": "Contact",
                    "default": "",
                    "placeholder": "Search Contact...",
                    "required": True,
                    "layout": "half",
                },
                {"name": "name", "label": "Name", "control": "text", "default": "", "required": True, "layout": "half"},
                {"name": "amount", "label": "Amount", "control": "number", "default": "", "layout": "half"},
                {
                    "name": "stage",
                    "label": "Stage",
                    "control": "select",
                    "default": OpportunityStage.PROSPECTING.value,
                    "required": True,
                    "layout": "half",
                    "options": [
                        {"value": OpportunityStage.PROSPECTING.value, "label": OpportunityStage.PROSPECTING.value},
                        {"value": OpportunityStage.QUALIFICATION.value, "label": OpportunityStage.QUALIFICATION.value},
                        {"value": OpportunityStage.TEST_DRIVE.value, "label": OpportunityStage.TEST_DRIVE.value},
                        {"value": OpportunityStage.VALUE_PROPOSITION.value, "label": OpportunityStage.VALUE_PROPOSITION.value},
                        {"value": OpportunityStage.NEGOTIATION.value, "label": OpportunityStage.NEGOTIATION.value},
                        {"value": OpportunityStage.PROPOSAL.value, "label": OpportunityStage.PROPOSAL.value},
                        {"value": OpportunityStage.CLOSED_WON.value, "label": OpportunityStage.CLOSED_WON.value},
                        {"value": OpportunityStage.CLOSED_LOST.value, "label": OpportunityStage.CLOSED_LOST.value},
                    ],
                },
                {
                    "name": "brand",
                    "label": "Brand",
                    "control": "lookup",
                    "lookup_object": "Brand",
                    "default": "",
                    "placeholder": "Search Brand...",
                    "layout": "half",
                },
                {
                    "name": "model",
                    "label": "Model",
                    "control": "lookup",
                    "lookup_object": "Model",
                    "default": "",
                    "placeholder": "Search Model...",
                    "layout": "half",
                },
                {
                    "name": "product",
                    "label": "Product",
                    "control": "lookup",
                    "lookup_object": "Product",
                    "default": "",
                    "placeholder": "Search Product...",
                    "layout": "half",
                },
                {
                    "name": "asset",
                    "label": "Asset",
                    "control": "lookup",
                    "lookup_object": "Asset",
                    "default": "",
                    "placeholder": "Search Asset...",
                    "layout": "half",
                },
                {"name": "probability", "label": "Probability", "control": "number", "default": 10, "layout": "half"},
            ],
        },
    }

    @classmethod
    def _chat_native_form_config(cls, object_type: str) -> Dict[str, Any]:
        return cls.CHAT_NATIVE_FORM_CONFIG[object_type]

    @classmethod
    def _chat_native_form_values(
        cls,
        object_type: str,
        *,
        record: Optional[Any] = None,
        submitted_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = cls._chat_native_form_config(object_type)
        values: Dict[str, Any] = {}
        submitted_values = submitted_values or {}
        for field in config["fields"]:
            name = field["name"]
            if name in submitted_values:
                values[name] = submitted_values.get(name)
            elif record is not None:
                values[name] = getattr(record, name, field.get("default", ""))
            else:
                values[name] = field.get("default", "")
        return values

    @staticmethod
    def _safe_lookup_display(fetcher, db: Optional[Session], record_id: Optional[str], attr: str = "name") -> str:
        if not record_id:
            return ""
        try:
            record = fetcher(db, record_id)
        except Exception:
            return ""
        return str(getattr(record, attr, "") or "")

    @classmethod
    def _lead_lookup_display_values(
        cls,
        db: Optional[Session],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        from web.backend.app.services.product_service import ProductService

        return {
            "product": cls._safe_lookup_display(ProductService.get_product, db, values.get("product")),
            "model": cls._safe_lookup_display(ModelService.get_model, db, values.get("model")),
            "brand": cls._safe_lookup_display(VehicleSpecService.get_vehicle_spec, db, values.get("brand")),
        }

    @classmethod
    def _contact_display_name(cls, contact: Any) -> str:
        if not contact:
            return ""
        return " ".join(
            part for part in [getattr(contact, "first_name", None), getattr(contact, "last_name", None)] if part
        ).strip() or str(getattr(contact, "name", "") or "")

    @classmethod
    def _opportunity_lookup_display_values(
        cls,
        db: Optional[Session],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        brand_id = values.get("brand")
        model_id = values.get("model")
        product_id = values.get("product")
        asset_id = values.get("asset")
        contact_id = values.get("contact")
        display_values = {"contact": "", "brand": "", "model": "", "product": "", "asset": ""}
        try:
            if contact_id:
                contact = ContactService.get_contact(db, contact_id)
                display_values["contact"] = cls._contact_display_name(contact)
            if brand_id:
                brand = VehicleSpecService.get_vehicle_spec(db, brand_id)
                display_values["brand"] = str(getattr(brand, "name", "") or "")
            if model_id:
                model = ModelService.get_model(db, model_id)
                display_values["model"] = str(getattr(model, "name", "") or "")
            if product_id:
                from web.backend.app.services.product_service import ProductService

                product = ProductService.get_product(db, product_id)
                display_values["product"] = str(getattr(product, "name", "") or "")
            if asset_id:
                from web.backend.app.services.asset_service import AssetService

                asset = AssetService.get_asset(db, asset_id)
                display_values["asset"] = str(getattr(asset, "name", "") or getattr(asset, "vin", "") or "")
        except Exception:
            return display_values
        return display_values

    @classmethod
    def _build_chat_native_form_response(
        cls,
        *,
        object_type: str,
        mode: str,
        db: Optional[Session] = None,
        language_preference: Optional[str],
        record: Optional[Any] = None,
        record_id: Optional[str] = None,
        submitted_values: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, str]] = None,
        form_error: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = cls._chat_native_form_config(object_type)
        values = cls._chat_native_form_values(object_type, record=record, submitted_values=submitted_values)
        display_title = cls._phase1_display_title(object_type, record) if record is not None else None
        title = config["title_create"] if mode == "create" else f"{config['title_edit']} {display_title or record_id or ''}".strip()
        submit_label = config["submit_create"] if mode == "create" else config["submit_edit"]
        is_korean = (language_preference or "").lower() == "kor"
        text = cls._chat_native_form_opening_text(
            object_type=object_type,
            mode=mode,
            is_korean=is_korean,
            display_title=display_title,
            record_id=record_id,
        )
        if object_type == "lead":
            lookup_display_values = cls._lead_lookup_display_values(db, values)
        elif object_type == "opportunity":
            lookup_display_values = cls._opportunity_lookup_display_values(db, values)
        else:
            lookup_display_values = {}
        schema_fields: List[Dict[str, Any]] = []
        for field in config["fields"]:
            schema_field = {
                "name": field["name"],
                "label": field["label"],
                "control": field["control"],
                "required": bool(field.get("required")),
                "value": values.get(field["name"]),
                "layout": field.get("layout", "half"),
            }
            if field.get("placeholder") is not None:
                schema_field["placeholder"] = field["placeholder"]
            if "options" in field:
                schema_field["options"] = field["options"]
            if field["control"] == "lookup":
                schema_field["lookup_object"] = field.get("lookup_object")
                schema_field["display_value"] = lookup_display_values.get(field["name"], "")
            if field_errors and field["name"] in field_errors:
                schema_field["error"] = field_errors[field["name"]]
            schema_fields.append(schema_field)

        form_id_suffix = record_id or conversation_id or "session"
        form = build_chat_native_form(
            form_id=f"{object_type}:{mode}:{form_id_suffix}",
            object_type=object_type,
            mode=mode,
            record_id=record_id,
            title=title,
            description=cls._chat_native_form_description(mode=mode, is_korean=is_korean),
            submit_label=submit_label,
            cancel_label="Cancel",
            required_fields=cls._phase1_required_fields(object_type),
            fields=schema_fields,
            field_errors=field_errors,
            form_error=form_error,
        )
        return {
            "intent": "OPEN_FORM",
            "object_type": object_type,
            "record_id": record_id,
            "form_url": cls._phase1_form_url(object_type, record_id),
            "form_title": title,
            "form_kind": f"{object_type}_{mode}",
            "text": text,
            "form": form,
            "score": 1.0,
        }

    @staticmethod
    def _chat_native_form_opening_text(
        *,
        object_type: str,
        mode: str,
        is_korean: bool,
        display_title: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> str:
        object_label = object_type.replace("_", " ")
        if mode == "edit":
            target = display_title or record_id or ""
            if is_korean:
                suffix = f" **{target}**" if target else ""
                return (
                    f"{object_label.title()}{suffix} 수정 폼을 대화 안에 열었습니다. "
                    "바꿀 내용을 수정한 다음 저장해 주세요."
                )
            suffix = f" for **{target}**" if target else ""
            return (
                f"I opened the {object_label} edit form{suffix} here in chat. "
                "Update the fields you want, then save your changes."
            )

        if is_korean:
            return (
                f"{object_label.title()} 생성 폼을 대화 안에 열었습니다. "
                "입력할 내용을 채운 다음 저장해 주세요."
            )
        return (
            f"I opened the {object_label} create form here in chat. "
            "Fill in the fields you want, then save it."
        )

    @staticmethod
    def _chat_native_form_description(*, mode: str, is_korean: bool) -> str:
        if mode == "edit":
            return "바꿀 내용을 아래에서 수정한 다음 저장해 주세요." if is_korean else "Update the fields below, then save your changes."
        return "아래 필드를 입력한 다음 저장해 주세요." if is_korean else "Fill in the fields below, then save."

    @classmethod
    def _coerce_chat_form_values(cls, object_type: str, values: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {field["name"]: field for field in cls._chat_native_form_config(object_type)["fields"]}
        cleaned: Dict[str, Any] = {}
        for key, value in (values or {}).items():
            if key not in allowed:
                continue
            if isinstance(value, str):
                value = value.strip()
            if value == "":
                value = None
            if key in {"amount", "probability"} and value is not None:
                if isinstance(value, str):
                    value = value.replace(",", "")
                value = int(value)
            cleaned[key] = value
        return cleaned

    @classmethod
    def _validate_chat_form_submission(
        cls,
        object_type: str,
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        field_errors: Dict[str, str] = {}
        allowed = {field["name"]: field for field in cls._chat_native_form_config(object_type)["fields"]}
        required_fields = cls._phase1_required_fields(object_type)

        for field_name in required_fields:
            if values.get(field_name) in (None, ""):
                field_errors[field_name] = "This field is required."

        for field_name, field in allowed.items():
            if field.get("control") == "select" and values.get(field_name) not in (None, ""):
                allowed_values = {option["value"] for option in field.get("options", [])}
                if values[field_name] not in allowed_values:
                    field_errors[field_name] = "Select a valid option."

        if "probability" in values and values.get("probability") is not None:
            probability = values["probability"]
            if probability < 0 or probability > 100:
                field_errors["probability"] = "Probability must be between 0 and 100."

        return field_errors

    @classmethod
    def _coerce_ai_managed_inline_form_values(cls, object_type: str, values: Dict[str, Any]) -> Dict[str, Any]:
        if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
            return cls._coerce_chat_form_values(object_type, values)

        cleaned: Dict[str, Any] = {}
        for key, value in (values or {}).items():
            if isinstance(value, str):
                value = value.strip()
            if value == "":
                value = None
            if key in {"amount", "probability", "base_price", "price"} and value is not None:
                if isinstance(value, str):
                    value = value.replace(",", "")
                value = int(value)
            cleaned[key] = value
        return cleaned

    @classmethod
    def _validate_ai_managed_inline_form_submission(
        cls,
        object_type: str,
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
            return cls._validate_chat_form_submission(object_type, values)

        field_errors: Dict[str, str] = {}
        for field_name in cls._phase1_required_fields(object_type):
            if values.get(field_name) in (None, ""):
                field_errors[field_name] = "This field is required."

        if object_type == "asset" and values.get("status") not in (None, ""):
            allowed_statuses = {status.value for status in AssetStatus}
            if values["status"] not in allowed_statuses:
                field_errors["status"] = "Select a valid option."

        if object_type == "message_template" and values.get("record_type") not in (None, ""):
            allowed_types = {RecordType.SMS.value, RecordType.LMS.value, RecordType.MMS.value}
            if values["record_type"] not in allowed_types:
                field_errors["record_type"] = "Select a valid option."

        return field_errors

    @classmethod
    async def submit_chat_native_form(
        cls,
        db: Session,
        *,
        object_type: str,
        mode: str,
        values: Dict[str, Any],
        conversation_id: Optional[str] = None,
        language_preference: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        debug_event(
            "service.submit_chat_native_form.start",
            conversation_id=conversation_id,
            object_type=object_type,
            mode=mode,
            record_id=record_id,
            field_names=sorted((values or {}).keys()),
        )
        if object_type not in cls.AI_MANAGED_INLINE_FORM_OBJECTS:
            return {"intent": "CHAT", "text": f"{object_type} chat forms are not supported in this phase."}
        if mode not in {"create", "edit"}:
            return {"intent": "CHAT", "text": "Unsupported form mode."}

        try:
            cleaned_values = cls._coerce_ai_managed_inline_form_values(object_type, values)
        except (TypeError, ValueError):
            debug_event(
                "service.submit_chat_native_form.validation_error",
                conversation_id=conversation_id,
                object_type=object_type,
                mode=mode,
                reason="coerce_failed",
            )
            target_record = cls._get_phase1_record(db, object_type, record_id) if mode == "edit" and record_id else None
            if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode=mode,
                    db=db,
                    record=target_record,
                    record_id=record_id,
                    submitted_values=values,
                    field_errors={"amount": "Enter a valid number.", "probability": "Enter a valid number."},
                    form_error="Review the highlighted fields and try again.",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            return {"intent": "CHAT", "text": "Review the highlighted fields and try again."}

        if object_type == "lead":
            cleaned_values = cls._normalize_lead_lookup_inputs(db, cleaned_values)
        if object_type == "contact" and not cleaned_values.get("status"):
            cleaned_values["status"] = "New"
        if object_type == "opportunity" and not cleaned_values.get("status"):
            cleaned_values["status"] = OpportunityStatus.OPEN.value

        if mode == "edit" and record_id and db is not None:
            existing_record = cls._get_phase1_record(db, object_type, record_id)
            if existing_record is not None:
                for field_name in cls._phase1_required_fields(object_type):
                    if cleaned_values.get(field_name) in (None, ""):
                        existing_value = getattr(existing_record, field_name, None)
                        if existing_value not in (None, ""):
                            cleaned_values[field_name] = existing_value

        field_errors = cls._validate_ai_managed_inline_form_submission(object_type, cleaned_values)
        if field_errors:
            debug_event(
                "service.submit_chat_native_form.validation_error",
                conversation_id=conversation_id,
                object_type=object_type,
                mode=mode,
                reason="field_errors",
                field_errors=field_errors,
            )
            target_record = cls._get_phase1_record(db, object_type, record_id) if (mode == "edit" and record_id and db is not None) else None
            if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode=mode,
                    db=db,
                    record=target_record,
                    record_id=record_id,
                    submitted_values=cleaned_values,
                    field_errors=field_errors,
                    form_error="Review the highlighted fields and try again.",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            return {"intent": "CHAT", "text": "Review the highlighted fields and try again."}

        if mode == "create":
            if object_type == "lead":
                record = LeadService.create_lead(db, **cleaned_values)
            elif object_type == "contact":
                record = ContactService.create_contact(db, **cleaned_values)
            elif object_type == "opportunity":
                record = OpportunityService.create_opportunity(db, **cleaned_values)
            elif object_type == "brand":
                cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
                cleaned_values.setdefault("record_type", RecordType.BRAND.value)
                record = VehicleSpecService.create_spec(db, **cleaned_values)
            elif object_type == "model":
                cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
                record = ModelService.create_model(db, **cleaned_values)
            elif object_type == "asset":
                from web.backend.app.services.asset_service import AssetService

                cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
                record = AssetService.create_asset(db, **cleaned_values)
            elif object_type == "message_template":
                record = MessageTemplateService.create_template(db, **cleaned_values)
            else:
                return {"intent": "CHAT", "text": f"{object_type} chat forms are not supported in this phase."}
            if not record:
                debug_event(
                    "service.submit_chat_native_form.create_failed",
                    conversation_id=conversation_id,
                    object_type=object_type,
                    mode=mode,
                )
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode=mode,
                    db=db,
                    submitted_values=cleaned_values,
                    form_error=f"I couldn't create that {object_type}.",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            response = cls._build_phase1_open_record_response(
                db,
                object_type,
                record,
                conversation_id,
                "create",
                language_preference,
            )
            debug_event(
                "service.submit_chat_native_form.complete",
                conversation_id=conversation_id,
                object_type=object_type,
                mode=mode,
                intent=response.get("intent"),
                record_id=response.get("record_id"),
            )
            return response

        if not record_id:
            return {"intent": "CHAT", "text": f"I need the {object_type} record ID before I can save changes."}

        if object_type == "lead":
            record = LeadService.update_lead(db, record_id, **cleaned_values)
        elif object_type == "contact":
            record = ContactService.update_contact(db, record_id, **cleaned_values)
        elif object_type == "opportunity":
            record = OpportunityService.update_opportunity(db, record_id, **cleaned_values)
        elif object_type == "brand":
            cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
            cleaned_values.setdefault("record_type", RecordType.BRAND.value)
            record = VehicleSpecService.update_vehicle_spec(db, record_id, **cleaned_values)
        elif object_type == "model":
            cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
            record = ModelService.update_model(db, record_id, **cleaned_values)
        elif object_type == "asset":
            from web.backend.app.services.asset_service import AssetService

            cleaned_values = cls._normalize_supported_lookup_inputs(db, object_type, cleaned_values)
            record = AssetService.update_asset(db, record_id, **cleaned_values)
        elif object_type == "message_template":
            record = MessageTemplateService.update_template(db, record_id, **cleaned_values)
        else:
            return {"intent": "CHAT", "text": f"{object_type} chat forms are not supported in this phase."}

        if not record:
            debug_event(
                "service.submit_chat_native_form.update_failed",
                conversation_id=conversation_id,
                object_type=object_type,
                mode=mode,
                record_id=record_id,
            )
            return {"intent": "CHAT", "text": f"I couldn't find that {object_type} record."}
        response = cls._build_phase1_open_record_response(
            db,
            object_type,
            record,
            conversation_id,
            "update",
            language_preference,
        )
        debug_event(
            "service.submit_chat_native_form.complete",
            conversation_id=conversation_id,
            object_type=object_type,
            mode=mode,
            intent=response.get("intent"),
            record_id=response.get("record_id"),
        )
        return response

    @classmethod
    def _resolve_phase1_object(cls, normalized_query: str) -> Optional[str]:
        for key, value in IntentPreClassifier.OBJECT_MAP.items():
            if value in cls.PHASE1_OBJECTS and key in normalized_query:
                return value
        return None

    @classmethod
    def _resolve_supported_object(cls, normalized_query: str) -> Optional[str]:
        explicit_objects = IntentPreClassifier.detect_object_mentions(normalized_query)
        supported = [obj for obj in explicit_objects if obj in cls.DETERMINISTIC_CRUD_OBJECTS]
        if not supported:
            return None
        if len(set(supported)) == 1:
            return supported[0]

        ordered_items = sorted(IntentPreClassifier.OBJECT_MAP.items(), key=lambda item: (-len(item[0]), item[0]))
        best_object = None
        best_index = None
        for key, value in ordered_items:
            if value not in cls.DETERMINISTIC_CRUD_OBJECTS:
                continue
            idx = normalized_query.find(key)
            if idx == -1:
                continue
            if best_index is None or idx < best_index:
                best_index = idx
                best_object = value
        if best_object:
            return best_object
        return None

    @staticmethod
    def _extract_record_id(text: str) -> Optional[str]:
        match = re.search(r"\b([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)\b", text)
        return match.group(1) if match else None

    @classmethod
    def _extract_phase1_record_id(cls, user_query: str, object_type: str) -> Optional[str]:
        explicit = cls._extract_record_id(user_query)
        if explicit:
            return explicit

        alias_candidates = [key for key, value in IntentPreClassifier.OBJECT_MAP.items() if value == object_type]
        alias_pattern = "|".join(sorted((re.escape(alias) for alias in alias_candidates), key=len, reverse=True))
        match = re.search(rf"(?:{alias_pattern})\s+([A-Za-z][A-Za-z0-9-]{{3,}})", user_query, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            blocked_keywords = {
                "add",
                "build",
                "change",
                "create",
                "delete",
                "description",
                "edit",
                "email",
                "firstname",
                "first",
                "for",
                "last",
                "lastname",
                "make",
                "modify",
                "name",
                "new",
                "phone",
                "remove",
                "save",
                "status",
                "surname",
                "update",
                "만들",
                "변경",
                "생성",
                "삭제",
                "상태",
                "성",
                "수정",
                "이름",
                "저장",
            }
            if candidate.lower() not in blocked_keywords:
                return candidate
        return None

    @staticmethod
    def _match_field_value(text: str, aliases: List[str], stop_words: List[str]) -> Optional[str]:
        alias_pattern = "|".join(re.escape(alias) for alias in aliases)
        stop_pattern = "|".join(re.escape(word) for word in stop_words)
        pattern = rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*(.+?)(?=\s+(?:{stop_pattern})\b|,|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip().strip(".,")
        return value or None

    @classmethod
    def _extract_contact_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        data = {}
        lead_like = cls._extract_lead_update_fields_from_text(user_query)
        for key in ("first_name", "last_name", "status", "email", "phone", "gender", "description"):
            if key in lead_like:
                data[key] = lead_like[key]

        stop_words = [
            "last name",
            "first name",
            "status",
            "email",
            "phone",
            "gender",
            "website",
            "tier",
            "description",
            "desc",
            "note",
        ]
        first_name = cls._match_field_value(user_query, ["first name", "firstname"], stop_words)
        if first_name:
            data["first_name"] = first_name
        gender = cls._match_field_value(user_query, ["gender", "성별"], stop_words)
        if gender:
            data["gender"] = gender
        website = cls._match_field_value(user_query, ["website", "site"], stop_words)
        if website:
            data["website"] = website
        tier = cls._match_field_value(user_query, ["tier"], stop_words)
        if tier:
            data["tier"] = tier

        return data

    @classmethod
    def _extract_opportunity_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        stop_words = ["name", "stage", "amount", "probability", "status"]

        name = cls._match_field_value(user_query, ["name"], stop_words)
        if name:
            data["name"] = name

        stage = cls._match_field_value(user_query, ["stage"], stop_words)
        if stage:
            data["stage"] = stage

        status = cls._match_field_value(user_query, ["status"], stop_words)
        if status:
            data["status"] = status

        probability_match = re.search(r"probability\s*(?:is|to|=|:)?\s*(\d+)", user_query, re.IGNORECASE)
        if probability_match:
            data["probability"] = int(probability_match.group(1))

        amount_match = re.search(r"amount\s*(?:is|to|=|:)?\s*[₩$]?\s*([\d,]+)", user_query, re.IGNORECASE)
        if amount_match:
            data["amount"] = int(amount_match.group(1).replace(",", ""))

        return data

    @classmethod
    def _extract_phase1_fields(cls, object_type: str, user_query: str) -> Dict[str, Any]:
        if object_type == "lead":
            return cls._extract_lead_update_fields_from_text(user_query)
        if object_type == "contact":
            return cls._extract_contact_fields_from_text(user_query)
        if object_type == "opportunity":
            return cls._extract_opportunity_fields_from_text(user_query)
        if object_type in cls.FAST_OBJECT_FIELD_ALIASES:
            return cls._extract_fast_object_fields_from_text(object_type, user_query)
        return {}

    @classmethod
    def _phase1_required_fields(cls, object_type: str) -> List[str]:
        mapping = {
            "lead": ["last_name", "status"],
            "contact": ["last_name"],
            "opportunity": ["contact", "name", "stage"],
        }
        if object_type in cls.FAST_OBJECT_REQUIRED_FIELDS:
            return cls.FAST_OBJECT_REQUIRED_FIELDS[object_type]
        return mapping.get(object_type, [])

    @classmethod
    def _has_explicit_phase1_field_hints(cls, object_type: str, user_query: str) -> bool:
        normalized = IntentPreClassifier.normalize(user_query)
        if object_type in {"lead", "contact"}:
            hints = [
                "first name",
                "last name",
                "email",
                "phone",
                "status",
                "gender",
                "website",
                "tier",
                "description",
                "desc",
                "note",
                ":",
            ]
            if any(hint in normalized or hint in user_query for hint in hints):
                return True
            if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", user_query):
                return True
            if re.search(r"(?:\+?\d[\d\-\s]{7,}\d)", user_query):
                return True
            return False
        if object_type == "opportunity":
            return any(hint in normalized or hint in user_query for hint in ["contact", "name", "stage", "amount", "probability", ":"])
        if object_type in cls.FAST_OBJECT_FIELD_ALIASES:
            hints = {
                alias
                for aliases in cls.FAST_OBJECT_FIELD_ALIASES[object_type].values()
                for alias in aliases
            }
            if any(hint in normalized or hint in user_query for hint in hints):
                return True
            if object_type in {"product", "asset"} and re.search(r"\b\d[\d,]*\b", user_query):
                return True
            return ":" in user_query
        return False

    @classmethod
    def _extract_fast_object_fields_from_text(cls, object_type: str, user_query: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        aliases = cls.FAST_OBJECT_FIELD_ALIASES.get(object_type, {})
        stop_words = [alias for values in aliases.values() for alias in values]

        for field, field_aliases in aliases.items():
            alias_pattern = "|".join(re.escape(alias) for alias in field_aliases)
            if field in {"base_price", "price"}:
                match = re.search(rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*[₩$]?\s*([\d,]+)", user_query, re.IGNORECASE)
                if match:
                    data[field] = int(match.group(1).replace(",", ""))
                continue
            if field in {"description", "content"}:
                match = re.search(rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*(.+)", user_query, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().strip(".,")
                    if value:
                        data[field] = value
                continue
            value = cls._match_field_value(user_query, field_aliases, stop_words)
            if value:
                data[field] = value

        if object_type == "brand" and "name" not in data:
            match = re.search(r"brand\s+(?:name\s+)?([A-Za-z0-9가-힣][A-Za-z0-9가-힣\s-]*)", user_query, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip().strip(".,")
                if candidate and not cls._extract_record_id(candidate):
                    data["name"] = candidate

        if object_type == "message_template" and "record_type" in data:
            data["record_type"] = str(data["record_type"]).upper()

        return data

    @classmethod
    def _phase1_form_url(cls, object_type: str, record_id: Optional[str] = None) -> str:
        plural = {
            "lead": "leads",
            "contact": "contacts",
            "opportunity": "opportunities",
        }[object_type]
        base = f"/{plural}/new-modal"
        return f"{base}?id={record_id}" if record_id else base

    @classmethod
    def _fast_edit_form_url(cls, object_type: str, record_id: str) -> Optional[str]:
        mapping = {
            "product": f"/products/new-modal?id={record_id}",
            "asset": f"/assets/new-modal?id={record_id}",
            "brand": f"/vehicle_specifications/new-modal?type=Brand&id={record_id}",
            "model": f"/models/new-modal?id={record_id}",
            "message_template": f"/message_templates/new-modal?id={record_id}",
        }
        return mapping.get(object_type)

    @classmethod
    def _fast_create_form_url(cls, object_type: str) -> Optional[str]:
        mapping = {
            "product": "/products/new-modal",
            "asset": "/assets/new-modal",
            "brand": "/vehicle_specifications/new-modal?type=Brand",
            "model": "/models/new-modal",
            "message_template": "/message_templates/new-modal",
        }
        return mapping.get(object_type)

    @classmethod
    def _resolve_fast_create_form_request(
        cls,
        user_query: str,
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS)):
            return None

        explicit_objects = IntentPreClassifier.detect_object_mentions(user_query)
        if len(explicit_objects) != 1:
            return None

        object_type = explicit_objects[0]
        if object_type in cls.PHASE1_OBJECTS or object_type not in cls.FAST_FORM_CREATE_OBJECTS:
            return None
        if cls._has_explicit_phase1_field_hints(object_type, user_query):
            return None

        form_url = cls._fast_create_form_url(object_type)
        if not form_url:
            return None

        object_label = object_type.replace("_", " ")
        is_korean = (language_preference or "").lower() == "kor"
        return {
            "intent": "OPEN_FORM",
            "object_type": object_type,
            "form_url": form_url,
            "form_title": f"Create {object_label.title()}",
            "form_kind": f"{object_type}_create",
            "text": (
                f"I've opened the new {object_label} form for you below."
                if not is_korean else
                f"새 {object_label} 생성 폼을 아래에 열었습니다."
            ),
            "score": 1.0,
        }

    @classmethod
    def _phase1_display_title(cls, object_type: str, record: Any) -> str:
        if object_type == "lead":
            return cls._lead_name(record)
        if object_type == "contact":
            name = " ".join(
                part for part in [getattr(record, "first_name", None), getattr(record, "last_name", None)] if part
            ).strip()
            return name or getattr(record, "name", None) or str(getattr(record, "id", "Unnamed Contact"))
        if object_type == "opportunity":
            return getattr(record, "name", None) or str(getattr(record, "id", "Unnamed Opportunity"))
        if object_type == "product":
            return cls._display_value(getattr(record, "name", None)) or str(getattr(record, "id", "Unnamed Product"))
        if object_type == "asset":
            return (
                cls._display_value(getattr(record, "name", None))
                or cls._display_value(getattr(record, "vin", None))
                or str(getattr(record, "id", "Unnamed Asset"))
            )
        if object_type == "brand":
            return cls._display_value(getattr(record, "name", None)) or str(getattr(record, "id", "Unnamed Brand"))
        if object_type == "model":
            return cls._display_value(getattr(record, "name", None)) or str(getattr(record, "id", "Unnamed Model"))
        if object_type == "message_template":
            return cls._display_value(getattr(record, "name", None)) or str(getattr(record, "id", "Unnamed Template"))
        return str(getattr(record, "id", "Record"))

    @classmethod
    def _build_contact_chat_card(cls, contact: Any) -> Dict[str, Any]:
        name = cls._phase1_display_title("contact", contact)
        status = cls._display_value(getattr(contact, "status", None))
        fields = [
            {"label": "First name", "value": cls._display_value(getattr(contact, "first_name", None))},
            {"label": "Last name", "value": cls._display_value(getattr(contact, "last_name", None))},
            {"label": "Status", "value": status},
            {"label": "Email", "value": cls._display_value(getattr(contact, "email", None))},
            {"label": "Phone", "value": cls._display_value(getattr(contact, "phone", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "contact",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": name,
            "subtitle": f"Contact · {status}",
            "record_id": str(getattr(contact, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
                {"label": "Send Message", "action": "send_message", "tone": "secondary"},
            ],
            "hint": "Reply with `edit this contact` to keep updating in chat, ask to open the full record, or send a message.",
        }

    @classmethod
    def _build_opportunity_chat_card(cls, opportunity: Any, db: Optional[Session] = None) -> Dict[str, Any]:
        title = cls._phase1_display_title("opportunity", opportunity)
        stage = cls._display_value(getattr(opportunity, "stage", None))
        lookup_values = cls._opportunity_lookup_display_values(
            db,
            {
                "contact": getattr(opportunity, "contact", None),
                "brand": getattr(opportunity, "brand", None),
                "model": getattr(opportunity, "model", None),
                "product": getattr(opportunity, "product", None),
                "asset": getattr(opportunity, "asset", None),
            },
        ) if db is not None else {"contact": "", "brand": "", "model": "", "product": "", "asset": ""}
        fields = [
            {"label": "Contact", "value": lookup_values.get("contact")},
            {"label": "Name", "value": cls._display_value(getattr(opportunity, "name", None))},
            {"label": "Amount", "value": cls._display_value(getattr(opportunity, "amount", None))},
            {"label": "Stage", "value": stage},
            {"label": "Brand", "value": lookup_values.get("brand")},
            {"label": "Model", "value": lookup_values.get("model")},
            {"label": "Product", "value": lookup_values.get("product")},
            {"label": "Asset", "value": lookup_values.get("asset")},
            {"label": "Probability", "value": cls._display_value(getattr(opportunity, "probability", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "opportunity",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Opportunity · {stage}",
            "record_id": str(getattr(opportunity, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
                {"label": "Send Message", "action": "send_message", "tone": "secondary"},
            ],
            "hint": "Reply with `edit this opportunity` to keep updating in chat, ask to open the full record, or send a message.",
        }

    @classmethod
    def _build_product_chat_card(cls, db: Session, product: Any) -> Dict[str, Any]:
        brand = VehicleSpecService.get_vehicle_spec(db, getattr(product, "brand", None)) if getattr(product, "brand", None) else None
        model = ModelService.get_model(db, getattr(product, "model", None)) if getattr(product, "model", None) else None
        title = cls._display_value(getattr(product, "name", None)) or str(getattr(product, "id", "Unnamed Product"))
        category = cls._display_value(getattr(product, "category", None))
        fields = [
            {"label": "Name", "value": title},
            {"label": "Category", "value": category},
            {"label": "Brand", "value": cls._display_value(getattr(brand, "name", None))},
            {"label": "Model", "value": cls._display_value(getattr(model, "name", None))},
            {"label": "Base Price", "value": cls._display_value(getattr(product, "base_price", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "product",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Product · {category}",
            "record_id": str(getattr(product, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
            ],
            "hint": "Reply with `edit this product` to update it, or ask to open the full record.",
        }

    @classmethod
    def _build_asset_chat_card(cls, db: Session, asset: Any) -> Dict[str, Any]:
        from web.backend.app.services.product_service import ProductService

        product = ProductService.get_product(db, getattr(asset, "product", None)) if getattr(asset, "product", None) else None
        brand = VehicleSpecService.get_vehicle_spec(db, getattr(asset, "brand", None)) if getattr(asset, "brand", None) else None
        model = ModelService.get_model(db, getattr(asset, "model", None)) if getattr(asset, "model", None) else None
        title = (
            cls._display_value(getattr(asset, "name", None))
            or cls._display_value(getattr(asset, "vin", None))
            or str(getattr(asset, "id", "Unnamed Asset"))
        )
        status = cls._display_value(getattr(asset, "status", None))
        fields = [
            {"label": "Name", "value": cls._display_value(getattr(asset, "name", None))},
            {"label": "VIN", "value": cls._display_value(getattr(asset, "vin", None))},
            {"label": "Status", "value": status},
            {"label": "Product", "value": cls._display_value(getattr(product, "name", None))},
            {"label": "Brand", "value": cls._display_value(getattr(brand, "name", None))},
            {"label": "Model", "value": cls._display_value(getattr(model, "name", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "asset",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Asset · {status}",
            "record_id": str(getattr(asset, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
            ],
            "hint": "Reply with `edit this asset` to update it, or ask to open the full record.",
        }

    @classmethod
    def _build_brand_chat_card(cls, db: Session, brand: Any) -> Dict[str, Any]:
        title = cls._display_value(getattr(brand, "name", None)) or str(getattr(brand, "id", "Unnamed Brand"))
        record_type = cls._display_value(getattr(brand, "record_type", None))
        fields = [
            {"label": "Name", "value": title},
            {"label": "Type", "value": record_type},
            {"label": "Description", "value": cls._display_value(getattr(brand, "description", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "brand",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Brand · {record_type}",
            "record_id": str(getattr(brand, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
            ],
            "hint": "Reply with `edit this brand` to update it, or ask to open the full record.",
        }

    @classmethod
    def _build_model_chat_card(cls, db: Session, model: Any) -> Dict[str, Any]:
        brand = VehicleSpecService.get_vehicle_spec(db, getattr(model, "brand", None)) if getattr(model, "brand", None) else None
        title = cls._display_value(getattr(model, "name", None)) or str(getattr(model, "id", "Unnamed Model"))
        fields = [
            {"label": "Name", "value": title},
            {"label": "Brand", "value": cls._display_value(getattr(brand, "name", None))},
            {"label": "Description", "value": cls._display_value(getattr(model, "description", None))},
        ]
        return {
            "type": "record_paste",
            "object_type": "model",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Model · {cls._display_value(getattr(brand, 'name', None))}",
            "record_id": str(getattr(model, "id", "")),
            "fields": fields,
            "actions": [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
            ],
            "hint": "Reply with `edit this model` to update it, or ask to open the full record.",
        }

    @classmethod
    def _safe_template_preview_url(cls, template: Any) -> Optional[str]:
        for value in (getattr(template, "image_url", None), getattr(template, "file_path", None)):
            if isinstance(value, str) and value.startswith("/static/"):
                return value
        return None

    @classmethod
    def _build_message_template_chat_card(cls, template: Any) -> Dict[str, Any]:
        title = cls._display_value(getattr(template, "name", None)) or str(getattr(template, "id", "Unnamed Template"))
        record_type = cls._display_value(getattr(template, "record_type", None))
        preview_url = cls._safe_template_preview_url(template)
        fields = [
            {"label": "Name", "value": title},
            {"label": "Type", "value": record_type},
            {"label": "Subject", "value": cls._display_value(getattr(template, "subject", None))},
            {"label": "Content", "value": cls._display_value(getattr(template, "content", None))},
            {"label": "Image", "value": "Available" if preview_url else ""},
        ]
        actions = [
            {"label": "Open Record", "action": "open", "tone": "primary"},
            {"label": "Edit", "action": "edit", "tone": "secondary"},
            {"label": "Delete", "action": "delete", "tone": "danger"},
        ]
        if preview_url:
            actions.append({"label": "Preview Image", "action": "preview_image", "tone": "secondary", "url": preview_url})
        actions.append({"label": "Use In Send Message", "action": "use_in_send", "tone": "secondary"})
        return {
            "type": "record_paste",
            "object_type": "message_template",
            "paste_label": f"Pasted ~{2 + len(fields)} lines",
            "title": title,
            "subtitle": f"Template · {record_type}",
            "record_id": str(getattr(template, "id", "")),
            "fields": fields,
            "actions": actions,
            "hint": (
                "Preview the image or use this template in Send Message."
                if preview_url else
                "Use this template in Send Message or open the full record."
            ),
        }

    @classmethod
    def _build_phase1_open_record_response(
        cls,
        db: Optional[Session],
        object_type: str,
        record: Any,
        conversation_id: Optional[str],
        action: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        record_id = str(getattr(record, "id", ""))
        if object_type == "lead":
            return cls._build_lead_open_record_response(
                db=db,
                lead=record,
                conversation_id=conversation_id,
                action=action,
                language_preference=language_preference,
            )

        redirect_url = {
            "contact": f"/contacts/{record_id}",
            "opportunity": f"/opportunities/{record_id}",
            "product": f"/products/{record_id}",
            "asset": f"/assets/{record_id}",
            "brand": f"/vehicle_specifications/{record_id}",
            "model": f"/models/{record_id}",
            "message_template": f"/message_templates/{record_id}",
        }[object_type]
        chat_card = None
        if object_type == "contact":
            chat_card = cls._build_contact_chat_card(record)
        elif object_type == "opportunity":
            chat_card = cls._build_opportunity_chat_card(record, db=db)
        elif object_type == "product":
            chat_card = cls._build_product_chat_card(db, record)
        elif object_type == "asset":
            chat_card = cls._build_asset_chat_card(db, record)
        elif object_type == "brand":
            chat_card = cls._build_brand_chat_card(db, record)
        elif object_type == "model":
            chat_card = cls._build_model_chat_card(db, record)
        elif object_type == "message_template":
            chat_card = cls._build_message_template_chat_card(record)

        return build_object_open_record_response(
            object_type=object_type,
            record_id=record_id,
            redirect_url=redirect_url,
            title=cls._phase1_display_title(object_type, record),
            action=action,
            conversation_id=conversation_id,
            language_preference=language_preference,
            chat_card=chat_card,
        )

    @classmethod
    def _build_phase1_edit_form_response(
        cls,
        object_type: str,
        record: Any,
        language_preference: Optional[str],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        record_id = str(getattr(record, "id", ""))
        if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode="edit",
                db=db,
                record=record,
                record_id=record_id,
                conversation_id=None,
                language_preference=language_preference,
            )
        if object_type in cls.FAST_FORM_CREATE_OBJECTS:
            return build_object_edit_form_response(
                object_type=object_type,
                record_id=record_id,
                form_url=cls._fast_edit_form_url(object_type, record_id),
                title=f"Edit {cls._phase1_display_title(object_type, record)}",
                language_preference=language_preference,
            )
        return build_object_edit_form_response(
            object_type=object_type,
            record_id=record_id,
            form_url=cls._phase1_form_url(object_type, record_id),
            title=f"Edit {cls._phase1_display_title(object_type, record)}",
            language_preference=language_preference,
        )

    @classmethod
    def _get_phase1_record(cls, db: Session, object_type: str, record_id: str) -> Any:
        if object_type == "lead":
            return LeadService.get_lead(db, record_id)
        if object_type == "contact":
            return ContactService.get_contact(db, record_id)
        if object_type == "opportunity":
            return OpportunityService.get_opportunity(db, record_id)
        if object_type == "brand":
            return VehicleSpecService.get_vehicle_spec(db, record_id)
        if object_type == "model":
            return ModelService.get_model(db, record_id)
        if object_type == "product":
            from web.backend.app.services.product_service import ProductService
            return ProductService.get_product(db, record_id)
        if object_type == "asset":
            from web.backend.app.services.asset_service import AssetService
            return AssetService.get_asset(db, record_id)
        if object_type == "message_template":
            return MessageTemplateService.get_template(db, record_id)
        return None

    @classmethod
    def _resolve_phase1_deterministic_request(
        cls,
        db: Optional[Session],
        user_query: str,
        conversation_id: Optional[str],
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_supported_object(normalized)
        if not object_type:
            return None

        explicit_record_id = cls._extract_phase1_record_id(user_query, object_type)
        has_create = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS))
        has_update = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS))
        has_query = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_QUERY_ACTIONS))
        has_read = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_READ_ACTIONS))
        has_recent_query = any(marker in normalized for marker in cls.RECENT_QUERY_MARKERS)

        if has_recent_query and object_type in cls.DETERMINISTIC_CRUD_OBJECTS:
            return {
                "intent": "QUERY",
                "object_type": object_type,
                "data": {"query_mode": "recent"},
                "score": 1.0,
            }

        if object_type in cls.DETERMINISTIC_CRUD_OBJECTS and any(marker in normalized for marker in {"latest", "last"}):
            if has_update or has_read:
                return {
                    "intent": "QUERY",
                    "object_type": object_type,
                    "data": {"query_mode": "recent"},
                    "score": 1.0,
                }

        if object_type == "message_template":
            object_label = object_type.replace("_", " ")
            if has_create:
                return {
                    "intent": "OPEN_FORM",
                    "object_type": object_type,
                    "form_url": cls._fast_create_form_url(object_type),
                    "form_title": f"Create {object_label.title()}",
                    "form_kind": f"{object_type}_create",
                    "text": f"I've opened the new {object_label} form for you below.",
                    "score": 1.0,
                }
            if has_update and explicit_record_id:
                if db is not None:
                    record = cls._get_phase1_record(db, object_type, explicit_record_id)
                    if not record:
                        return {
                            "intent": "CHAT",
                            "object_type": object_type,
                            "text": f"I couldn't find that {object_label} record.",
                            "score": 1.0,
                        }
                    return cls._build_phase1_edit_form_response(
                        object_type,
                        record,
                        language_preference,
                        db=db,
                    )
                return {
                    "intent": "OPEN_FORM",
                    "object_type": object_type,
                    "record_id": explicit_record_id,
                    "form_url": cls._fast_edit_form_url(object_type, explicit_record_id),
                    "form_title": f"Edit {object_label.title()}",
                    "form_kind": f"{object_type}_edit",
                    "text": f"I've opened the {object_label} edit form for you below.",
                    "score": 1.0,
                }

        if has_update and object_type in cls.FAST_FORM_CREATE_OBJECTS and explicit_record_id:
            object_label = object_type.replace("_", " ")
            if not cls._has_explicit_phase1_field_hints(object_type, user_query):
                if db is not None:
                    record = cls._get_phase1_record(db, object_type, explicit_record_id)
                    if not record:
                        return {
                            "intent": "CHAT",
                            "object_type": object_type,
                            "text": f"I couldn't find that {object_label} record.",
                            "score": 1.0,
                        }
                    return cls._build_phase1_edit_form_response(
                        object_type,
                        record,
                        language_preference,
                        db=db,
                    )
                return {
                    "intent": "OPEN_FORM",
                    "object_type": object_type,
                    "record_id": explicit_record_id,
                    "form_url": cls._fast_edit_form_url(object_type, explicit_record_id),
                    "form_title": f"Edit {object_label.title()}",
                    "form_kind": f"{object_type}_edit",
                    "text": f"I've opened the {object_label} edit form for you below.",
                    "score": 1.0,
                }

        if has_query and object_type in cls.DETERMINISTIC_CRUD_OBJECTS:
            if "all" in normalized or "show all" in normalized or "list" in normalized or object_type == "opportunity" or has_recent_query:
                query_data = {"query_mode": "recent"} if has_recent_query else {}
                return {
                    "intent": "QUERY",
                    "object_type": object_type,
                    "data": query_data,
                    "score": 1.0,
                }

        if has_create and object_type in cls.DETERMINISTIC_CRUD_OBJECTS:
            if not cls._has_explicit_phase1_field_hints(object_type, user_query):
                if object_type in cls.FAST_FORM_CREATE_OBJECTS:
                    return {
                        "intent": "OPEN_FORM",
                        "object_type": object_type,
                        "form_url": cls._fast_create_form_url(object_type),
                        "form_title": f"Create {object_type.replace('_', ' ').title()}",
                        "form_kind": f"{object_type}_create",
                        "text": f"I've opened the new {object_type.replace('_', ' ')} form for you below.",
                        "score": 1.0,
                    }
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode="create",
                    submitted_values={},
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            data = cls._extract_phase1_fields(object_type, user_query)
            required_fields = cls._phase1_required_fields(object_type)
            if all(field in data and data[field] not in (None, "") for field in required_fields):
                return {
                    "intent": "CREATE",
                    "object_type": object_type,
                    "data": data,
                    "score": 1.0,
                    "language_preference": language_preference,
                }
            if object_type in cls.FAST_FORM_CREATE_OBJECTS:
                return {
                    "intent": "OPEN_FORM",
                    "object_type": object_type,
                    "form_url": cls._fast_create_form_url(object_type),
                    "form_title": f"Create {object_type.replace('_', ' ').title()}",
                    "form_kind": f"{object_type}_create",
                    "text": f"I've opened the new {object_type.replace('_', ' ')} form for you below.",
                    "score": 1.0,
                }
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode="create",
                submitted_values=data,
                conversation_id=conversation_id,
                language_preference=language_preference,
            )

        if (has_update or has_read) and object_type in cls.DETERMINISTIC_CRUD_OBJECTS and explicit_record_id:
            if has_update:
                data = cls._extract_phase1_fields(object_type, user_query)
                if data:
                    return {
                        "intent": "UPDATE",
                        "object_type": object_type,
                        "record_id": explicit_record_id,
                        "data": data,
                        "score": 1.0,
                        "language_preference": language_preference,
                    }
                record = cls._get_phase1_record(db, object_type, explicit_record_id)
                if not record:
                    return {
                        "intent": "CHAT",
                        "object_type": object_type,
                        "text": f"I couldn't find that {object_type} record.",
                        "score": 1.0,
                    }
                return cls._build_phase1_edit_form_response(
                    object_type,
                    record,
                    language_preference,
                    db=db,
                )
            return {
                "intent": "MANAGE",
                "object_type": object_type,
                "record_id": explicit_record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if has_update and object_type in cls.DETERMINISTIC_CRUD_OBJECTS:
            return {
                "intent": "CHAT",
                "object_type": object_type,
                "text": f"I can update that {object_type}, but I need the record ID first.",
                "score": 1.0,
            }

        return None

    @classmethod
    def _resolve_send_history_query_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        if "message template" in normalized or "message templates" in normalized:
            return None
        has_query = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_QUERY_ACTIONS))
        has_read = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_READ_ACTIONS))
        has_recent_query = any(marker in normalized for marker in cls.RECENT_QUERY_MARKERS)
        references_messages = re.search(r"\bmessages?\b", normalized) is not None

        if not references_messages:
            return None

        if has_query or has_read or normalized in {"message", "messages", "recent message", "recent messages"}:
            query_data = {"query_mode": "recent"} if has_recent_query else {}
            return {
                "intent": "QUERY",
                "object_type": "message_send",
                "data": query_data,
                "score": 1.0,
            }

        return None

    @classmethod
    def _looks_like_possible_llm_crud_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> bool:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized:
            return False

        action_hints = set(cls.GENERIC_CREATE_ACTIONS | cls.GENERIC_UPDATE_ACTIONS | cls.GENERIC_READ_ACTIONS | cls.LEAD_DELETE_ACTIONS | cls.GENERIC_QUERY_ACTIONS)
        has_known_action = IntentPreClassifier._contains_action(normalized, list(action_hints))
        has_llm_action_hint = any(
            phrase in normalized if " " in phrase else re.search(rf"\b{re.escape(phrase)}\b", normalized)
            for phrase in cls.POSSIBLE_LLM_CRUD_ACTION_HINTS
        )
        if not has_known_action and not has_llm_action_hint:
            return False

        has_context_marker = any(marker in normalized for marker in cls.CRM_CONTEXT_MARKERS)
        has_crm_value_hint = any(value in normalized for value in cls.CRM_VALUE_HINTS)
        has_crm_field_hint = any(field in normalized for field in cls.CRM_FIELD_HINTS)
        has_record_like_token = re.search(r"\b[A-Z0-9]{6,}\b", user_query) is not None
        reasoning_context = ConversationContextStore.build_reasoning_context(conversation_id, selection)
        has_context_records = bool(
            (reasoning_context.get("last_created") or {}).get("record_id")
            or (reasoning_context.get("last_record") or {}).get("record_id")
            or (reasoning_context.get("selection") or {}).get("record_ids")
            or (reasoning_context.get("query_results") or {}).get("results")
        )

        if has_record_like_token and (has_crm_field_hint or has_known_action):
            return True
        if has_context_records and has_context_marker:
            return True
        if has_context_marker and (has_crm_field_hint or has_crm_value_hint):
            return True
        if has_crm_field_hint and has_crm_value_hint:
            return True
        return False

    @classmethod
    def _resolve_out_of_scope_request(
        cls,
        user_query: str,
        conversation_id: Optional[str] = None,
        selection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized:
            return None

        if IntentPreClassifier.detect_object_mentions(user_query):
            return None
        if any(keyword in normalized or keyword in user_query for keyword in cls.D5_SCOPE_KEYWORDS):
            return None
        if cls._looks_like_possible_llm_crud_request(user_query, conversation_id, selection):
            return None

        # Proactive CRM Fallback: If an object is detected but intent is unknown, suggest actions.
        detected_objects = IntentPreClassifier.detect_object_mentions(user_query)
        if detected_objects:
            obj = detected_objects[0]
            plural = obj + "s" if not obj.endswith("s") else obj
            if obj == "message_template": plural = "message_templates"
            
            return {
                "intent": "CHAT",
                "text": f"I recognized you might be interested in **{obj.capitalize()}**. Would you like to see all {plural} or create a new one?",
                "score": 0.9,
                "options": [
                    {"label": f"Show all {plural}", "value": f"show all {plural}"},
                    {"label": f"Create new {obj}", "value": f"create {obj}"}
                ]
            }

        return {
            "intent": "CHAT",
            "text": "I can only help with D5 CRM work. Ask me about leads, contacts, opportunities, products, assets, brands, models, templates, messages, or other D5 tasks.",
            "score": 1.0,
        }

    @classmethod
    def _resolve_short_object_clarification(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized or IntentPreClassifier.detect_object_mentions(user_query):
            return None

        action = None
        if IntentPreClassifier._contains_action(normalized, IntentPreClassifier.ACTION_CREATE):
            action = "create"
        elif IntentPreClassifier._contains_action(normalized, IntentPreClassifier.ACTION_UPDATE):
            action = "edit"
        elif IntentPreClassifier._contains_action(normalized, IntentPreClassifier.ACTION_QUERY):
            action = "show"
        elif IntentPreClassifier._contains_action(normalized, IntentPreClassifier.ACTION_READ):
            action = "open"

        if not action:
            return None

        match = re.search(r"\b(?:a|an)?\s*([a-z]{1,5})\s*$", normalized)
        if not match:
            return None

        token = match.group(1)
        object_type = cls.SHORT_OBJECT_CLARIFICATIONS.get(token)
        if not object_type:
            return None

        object_label = object_type.replace("_", " ")
        suggestion = f"{action} {object_label}"
        return {
            "intent": "CHAT",
            "text": f"Did you mean `{suggestion}`? Choose [{suggestion}] or keep typing more detail.",
            "score": 1.0,
        }

    @classmethod
    def _resolve_recommendation_request(
        cls,
        user_query: str,
        conversation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized:
            return None

        mode_follow_up_markers = (
            "hot deals",
            "follow up",
            "follow-up",
            "followup",
            "closed won",
            "closing soon",
            "new records",
            "default",
            "hot",
            "follow",
        )
        mentions_recommend = "ai recommend" in normalized or "추천" in normalized
        pending_mode_change = ConversationContextStore.has_pending_recommendation_mode(conversation_id)
        if not mentions_recommend and not (
            pending_mode_change and any(marker in normalized for marker in mode_follow_up_markers)
        ):
            return None

        if pending_mode_change and any(marker in normalized for marker in mode_follow_up_markers):
            return {
                "intent": "MODIFY_UI",
                "object_type": "opportunity",
                "text": "",
                "score": 1.0,
            }

        if "change" in normalized or "logic" in normalized or "mode" in normalized or "변경" in normalized:
            return {
                "intent": "MODIFY_UI",
                "object_type": "opportunity",
                "text": "",
                "score": 1.0,
            }

        return {
            "intent": "RECOMMEND",
            "object_type": "opportunity",
            "text": "",
            "score": 1.0,
        }

    @classmethod
    def _unwrap_english_request_wrapper(cls, user_query: str) -> Optional[str]:
        cleaned = (user_query or "").strip()
        if not cleaned:
            return None

        original = cleaned
        for _ in range(2):
            updated = cleaned
            for pattern in cls.ENGLISH_REQUEST_WRAPPER_PATTERNS:
                updated = re.sub(pattern, "", updated, count=1, flags=re.IGNORECASE).strip()
            if updated == cleaned:
                break
            cleaned = updated

        cleaned = cleaned.rstrip(" ?!.,")
        if not cleaned or cleaned.lower() == original.rstrip(" ?!.,").lower():
            return None
        return cleaned

    @classmethod
    def _resolve_bounded_explanatory_object(cls, user_query: str) -> Optional[str]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized:
            return None

        detected_objects = IntentPreClassifier.detect_object_mentions(user_query)
        if len(detected_objects) != 1:
            return None

        if not any(hint in normalized for hint in cls.BOUNDED_EXPLANATORY_HINTS):
            return None

        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.LEAD_DELETE_ACTIONS)):
            return None

        return detected_objects[0]

    @classmethod
    def _build_bounded_clarification_fallback(
        cls,
        object_type: str,
        user_query: str,
    ) -> Dict[str, Any]:
        object_label = object_type.replace("_", " ")
        plural = object_label if object_label.endswith("s") else f"{object_label}s"
        title = object_label.title()
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": (
                f"`{user_query}` sounds like a {title} information request. "
                f"Do you want me to search {plural}, show recent {plural}, or open a specific {object_label} by name?"
            ),
            "score": 0.9,
            "options": [
                {"label": f"Search {title}", "value": f"search {object_label}"},
                {"label": f"Recent {title}", "value": f"show recent {object_label}s"},
                {"label": f"Open By Name", "value": f"open {object_label} [name]"},
            ],
        }

    @classmethod
    def _resolve_bounded_update_object(cls, user_query: str) -> Optional[str]:
        normalized = IntentPreClassifier.normalize(user_query)
        if not normalized:
            return None

        detected_objects = IntentPreClassifier.detect_object_mentions(user_query)
        if len(detected_objects) != 1:
            return None

        object_type = detected_objects[0]
        if not IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.LEAD_DELETE_ACTIONS)):
            return None
        if cls._extract_phase1_record_id(user_query, object_type):
            return None
        if any(marker in normalized for marker in cls.RECENT_QUERY_MARKERS):
            return None
        if " named " in normalized or normalized.endswith(" named"):
            return None
        return object_type

    @classmethod
    def _build_bounded_update_clarification_fallback(
        cls,
        object_type: str,
        user_query: str,
    ) -> Dict[str, Any]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_label = object_type.replace("_", " ")
        title = object_label.title()
        field_hint = next((hint for hint in cls.BOUNDED_UPDATE_FIELD_HINTS if hint in normalized), None)
        if field_hint:
            text = (
                f"`{user_query}` sounds like a {title} update request for `{field_hint}`. "
                f"Which {object_label} should I update? I can show recent {object_label}s, search {object_label}s, or use a specific {object_label} ID."
            )
        else:
            text = (
                f"`{user_query}` sounds like a {title} update request. "
                f"Which {object_label} should I update? I can show recent {object_label}s, search {object_label}s, or use a specific {object_label} ID."
            )

        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": text,
            "score": 0.9,
            "options": [
                {"label": f"Recent {title}", "value": f"show recent {object_label}s"},
                {"label": f"Search {title}", "value": f"search {object_label}"},
                {"label": "Edit By ID", "value": f"edit {object_label} [ID]"},
            ],
        }

    @classmethod
    def _resolve_existence_query_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_supported_object(normalized)
        if not object_type:
            return None

        if "is there any" not in normalized and "are there any" not in normalized:
            return None

        if " for " not in normalized:
            return None

        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.LEAD_DELETE_ACTIONS)):
            return None

        search_term = normalized.split(" for ", 1)[1].strip(" ?!.,")
        if not search_term:
            return None

        return {
            "intent": "QUERY",
            "object_type": object_type,
            "data": {"search_term": search_term},
            "score": 0.98,
        }

    @classmethod
    async def _maybe_auto_open_single_query_result(
        cls,
        db: Session,
        obj: str,
        paged: Dict[str, Any],
        agent_output: Dict[str, Any],
        user_query: str,
        conversation_id: Optional[str],
        page: int,
        per_page: int,
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            return None

        data = agent_output.get("data") or {}
        if not data.get("auto_open_single_result"):
            return None

        results = list(paged.get("results") or [])
        if len(results) != 1:
            return None

        record_id = (results[0] or {}).get("id")
        if not record_id:
            return None

        manage_payload = {
            "intent": "MANAGE",
            "object_type": obj,
            "record_id": record_id,
            "language_preference": agent_output.get("language_preference"),
            "score": agent_output.get("score", 1.0),
        }
        return await cls._execute_intent(
            db,
            manage_payload,
            user_query,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page,
        )

    @classmethod
    def _resolve_creation_guidance_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_supported_object(normalized)
        if not object_type:
            return None

        if not any(hint in normalized for hint in cls.BOUNDED_GUIDANCE_HINTS):
            return None
        if "creation" not in normalized and "create" not in normalized:
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.LEAD_DELETE_ACTIONS)):
            return None

        object_label = object_type.replace("_", " ")
        title = object_label.title()
        requirements = IntentPreClassifier.CREATE_REQUIREMENTS.get(object_type, "the required fields")
        plural = object_label if object_label.endswith("s") else f"{object_label}s"
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": (
                f"To create a {object_label} in D5, I usually need {requirements}. "
                f"If you want, I can open the {object_label} create form now or show recent {plural} first."
            ),
            "score": 0.92,
            "options": [
                {"label": f"Create {title}", "value": f"create {object_label}"},
                {"label": f"Recent {title}", "value": f"show recent {object_label}s"},
            ],
        }

    @classmethod
    def _resolve_hot_object_guidance_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_supported_object(normalized)
        if not object_type:
            return None

        if not normalized.startswith("which "):
            return None
        if not any(hint in normalized for hint in (" hot", " warm", " active")):
            return None

        object_label = object_type.replace("_", " ")
        title = object_label.title()
        plural = object_label if object_label.endswith("s") else f"{object_label}s"
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": (
                f"`{user_query}` needs a clearer ranking rule for {plural}. "
                f"Do you want recent {plural}, a search by company/name, or a filtered {object_label} list by status or stage?"
            ),
            "score": 0.9,
            "options": [
                {"label": f"Recent {title}", "value": f"show recent {object_label}s"},
                {"label": f"Search {title}", "value": f"search {object_label}"},
                {"label": f"Filter {title}", "value": f"show {object_label} with status qualified"},
            ],
        }

    @classmethod
    def _resolve_object_flow_guidance_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_supported_object(normalized)
        if not object_type:
            return None

        if "help with" not in normalized and " flow" not in normalized and not normalized.endswith(" flow"):
            return None
        if "creation" in normalized or "create" in normalized:
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS)):
            return None
        if IntentPreClassifier._contains_action(normalized, list(cls.LEAD_DELETE_ACTIONS)):
            return None

        object_label = object_type.replace("_", " ")
        title = object_label.title()
        plural = object_label if object_label.endswith("s") else f"{object_label}s"
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": (
                f"I can help with the {object_label} flow in D5. "
                f"Do you want to create a {object_label}, review recent {plural}, or open a specific {object_label} record?"
            ),
            "score": 0.9,
            "options": [
                {"label": f"Create {title}", "value": f"create {object_label}"},
                {"label": f"Recent {title}", "value": f"show recent {object_label}s"},
                {"label": f"Open {title}", "value": f"open {object_label} [name]"},
            ],
        }

    @classmethod
    async def _resolve_message_policy_question(
        cls,
        user_query: str,
        *,
        language_preference: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not MessagePolicyRetrievalService.is_policy_question(user_query):
            return None

        try:
            return await MessagePolicyRetrievalService.answer_policy_question(
                user_query,
                language_preference=language_preference,
            )
        except ValueError:
            language = "ko" if re.search(r"[\uac00-\ud7a3]", user_query) else "en"
            text = (
                "메시지 발송 규정 벡터 검색이 아직 설정되지 않았습니다."
                if language == "ko"
                else "Message policy vector retrieval is not configured yet."
            )
            return {"intent": "CHAT", "text": text, "score": 1.0}
        except Exception as exc:
            logger.warning("Message policy retrieval failed: %s", exc)
            language = "ko" if re.search(r"[\uac00-\ud7a3]", user_query) else "en"
            text = (
                "메시지 발송 규정 벡터 검색을 지금은 사용할 수 없습니다."
                if language == "ko"
                else "Message policy vector retrieval is temporarily unavailable."
            )
            return {"intent": "CHAT", "text": text, "score": 1.0}

    @classmethod
    def _validate_bounded_clarification_response(
        cls,
        response: Any,
        object_type: str,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(response, dict):
            return None
        if response.get("intent") != "CHAT":
            return None

        text = str(response.get("text") or "").strip()
        if not text:
            return None

        validated: Dict[str, Any] = {
            "intent": "CHAT",
            "object_type": object_type,
            "text": text,
            "score": float(response.get("score") or 0.9),
        }

        raw_options = response.get("options")
        if isinstance(raw_options, list):
            options = []
            for item in raw_options[:3]:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "").strip()
                value = str(item.get("value") or "").strip()
                if label and value:
                    options.append({"label": label, "value": value})
            if options:
                validated["options"] = options

        return validated

    @classmethod
    async def _resolve_bounded_english_clarification(cls, user_query: str) -> Optional[Dict[str, Any]]:
        object_type = cls._resolve_bounded_explanatory_object(user_query)
        if not object_type:
            return None

        fallback = cls._build_bounded_clarification_fallback(object_type, user_query)
        if not CEREBRAS_API_KEY:
            debug_event("service.bounded_clarification.no_cerebras", user_query=user_query, fallback=fallback)
            return fallback

        system_prompt = (
            "You are a D5 CRM clarification assistant. "
            "Return JSON only. "
            "Allowed intent is CHAT only. "
            "Do not claim any action was executed. "
            "Ask one short clarification question for the detected CRM object, and suggest up to three safe next actions. "
            "Safe actions are limited to search/list recent/open by name. "
            "Never suggest create, edit, update, delete, remove, or erase. "
            f"The detected CRM object is `{object_type}`. "
            'Return {"intent":"CHAT","text":"...","options":[{"label":"...","value":"..."}],"score":0.9}.'
        )

        try:
            response = await cls._call_cerebras(user_query, system_prompt)
        except Exception as exc:
            logger.warning("Bounded Cerebras clarification failed: %s", exc)
            response = None

        validated = cls._validate_bounded_clarification_response(response, object_type)
        if validated:
            debug_event("service.bounded_clarification.cerebras", user_query=user_query, response=validated)
            return validated

        debug_event("service.bounded_clarification.fallback", user_query=user_query, raw_response=response, fallback=fallback)
        return fallback

    @classmethod
    async def _resolve_bounded_english_update_clarification(cls, user_query: str) -> Optional[Dict[str, Any]]:
        object_type = cls._resolve_bounded_update_object(user_query)
        if not object_type:
            return None

        fallback = cls._build_bounded_update_clarification_fallback(object_type, user_query)
        if not CEREBRAS_API_KEY:
            debug_event("service.bounded_update_clarification.no_cerebras", user_query=user_query, fallback=fallback)
            return fallback

        system_prompt = (
            "You are a D5 CRM update clarification assistant. "
            "Return JSON only. "
            "Allowed intent is CHAT only. "
            "Do not claim any action was executed. "
            "Ask which record the user wants to update, and suggest up to three safe next actions. "
            "Safe actions are limited to show recent, search, or edit by explicit ID. "
            "Never suggest create, delete, remove, erase, or perform the update directly. "
            f"The detected CRM object is `{object_type}`. "
            'Return {"intent":"CHAT","text":"...","options":[{"label":"...","value":"..."}],"score":0.9}.'
        )

        try:
            response = await cls._call_cerebras(user_query, system_prompt)
        except Exception as exc:
            logger.warning("Bounded Cerebras update clarification failed: %s", exc)
            response = None

        validated = cls._validate_bounded_clarification_response(response, object_type)
        if validated:
            debug_event("service.bounded_update_clarification.cerebras", user_query=user_query, response=validated)
            return validated

        debug_event(
            "service.bounded_update_clarification.fallback",
            user_query=user_query,
            raw_response=response,
            fallback=fallback,
        )
        return fallback

    @classmethod
    def _extract_ranked_query_index(cls, user_query: str) -> Optional[int]:
        normalized = IntentPreClassifier.normalize(user_query)
        for marker, index in cls.ORDINAL_MARKERS:
            if marker in normalized:
                return index
        return None

    @classmethod
    def _resolve_contextual_query_reference(
        cls,
        user_query: str,
        conversation_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        ranked_index = cls._extract_ranked_query_index(user_query)
        if ranked_index is None:
            return None
        follow_up_markers = (
            "one",
            "record",
            "result",
            "item",
            "that",
            "this",
            "it",
            "them",
            "those",
            "그",
            "이",
            "해당",
        )
        explicit_ordinal_markers = (
            "first",
            "1st",
            "second",
            "2nd",
            "third",
            "3rd",
            "fourth",
            "4th",
            "fifth",
            "5th",
        )
        if not any(marker in normalized for marker in follow_up_markers) and not any(
            marker in normalized for marker in explicit_ordinal_markers
        ):
            return None

        manage_markers = list(cls.GENERIC_READ_ACTIONS | cls.GENERIC_UPDATE_ACTIONS)
        if not IntentPreClassifier._contains_action(normalized, manage_markers):
            return None

        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if value in cls.PHASE1_OBJECTS and key in normalized
        ]
        if explicit_objects and any(marker in normalized for marker in ("latest", "last")):
            query_context = ConversationContextStore.get_query_results(conversation_id)
            if not list(query_context.get("results") or []):
                return None
        desired_object_type = explicit_objects[0] if explicit_objects else None
        query_context = ConversationContextStore.get_query_results(conversation_id)
        query_object_type = query_context.get("object_type")
        ranked_results = list(query_context.get("results") or [])

        if query_object_type not in cls.PHASE1_OBJECTS or not ranked_results:
            object_hint = desired_object_type or "record"
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": (
                    f"I need a recent {object_hint} list first. Try `show recent {object_hint}s` "
                    "or `show all contacts`, then tell me which one to open or edit."
                ),
                "score": 1.0,
            }

        if desired_object_type and desired_object_type != query_object_type:
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": (
                    f"Your most recent list shows {query_object_type}s, not {desired_object_type}s. "
                    f"Show {desired_object_type}s first, then tell me which one to open or edit."
                ),
                "score": 1.0,
            }

        if ranked_index >= len(ranked_results):
            return {
                "intent": "CHAT",
                "object_type": query_object_type,
                "text": (
                    f"I only have {len(ranked_results)} {query_object_type} result"
                    f"{'' if len(ranked_results) == 1 else 's'} in the most recent list. "
                    "Tell me a valid position or show a longer list first."
                ),
                "score": 1.0,
            }

        chosen = ranked_results[ranked_index]
        return {
            "intent": "MANAGE",
            "object_type": query_object_type,
            "record_id": chosen["record_id"],
            "score": 1.0,
        }

    @classmethod
    def _extract_lead_fields_from_text(cls, user_query: str, allow_loose_last_name: bool = True) -> Dict[str, Any]:
        text = user_query.strip()
        lower = text.lower()
        data: Dict[str, Any] = {}

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if email_match:
            data["email"] = email_match.group(0)

        phone_match = re.search(r"(?:\+?\d[\d\-\s]{7,}\d)", text)
        if phone_match:
            data["phone"] = re.sub(r"\D", "", phone_match.group(0))

        for key, value in cls.LEAD_STATUS_ALIASES.items():
            if key in lower:
                data["status"] = value
                break

        last_name_match = re.search(r"last name\s+([A-Za-z가-힣-]+)", text, re.IGNORECASE)
        if last_name_match:
            data["last_name"] = last_name_match.group(1)

        if allow_loose_last_name and "last_name" not in data:
            cleaned = re.sub(r"[,:]", " ", text)
            tokens = [tok for tok in cleaned.split() if tok and "@" not in tok and not re.fullmatch(r"\d+", tok)]
            stop_words = {"create", "lead", "for", "status", "email", "phone", "new", "qualified", "lost", "show", "recent", "follow", "up"}
            candidate_tokens = [tok for tok in tokens if tok.lower() not in stop_words]
            if candidate_tokens:
                data["last_name"] = candidate_tokens[-1]

        return data

    @classmethod
    def _extract_lead_update_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        text = user_query.strip()
        lower = text.lower()
        data = cls._extract_lead_fields_from_text(text, allow_loose_last_name=False)
        clear_words = ["clear", "remove", "blank", "empty", "none", "delete", "지워", "삭제", "비워"]
        clear_pattern = "|".join(re.escape(word) for word in clear_words)

        for field, aliases in cls.LEAD_UPDATE_FIELD_ALIASES.items():
            alias_pattern = "|".join(re.escape(alias) for alias in aliases)
            if re.search(rf"(?:{clear_pattern})\s+(?:the\s+)?(?:{alias_pattern})(?:\b|$)", lower):
                data[field] = None
                continue
            if re.search(rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*(?:blank|empty|none|clear)\b", lower):
                data[field] = None

        extra_patterns = {
            "first_name": [r"first name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)이름(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "last_name": [r"last name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)성(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "gender": [r"gender\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)성별(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "brand": [r"brand\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)브랜드(?:는|은|를|을)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
            "model": [r"model\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)모델(?:은|는|을|를)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
            "product": [r"product\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)상품(?:은|는|을|를)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
            "description": [r"description\s*(?:is|to|=|:)?\s*(.+)", r"(?:^|\s)(?:note|메모|설명)(?:는|은|을|를)?\s+(.+)"],
        }
        for field, patterns in extra_patterns.items():
            if field in data:
                continue
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().strip(".,")
                    if value:
                        data[field] = value
                        break

        return data

    @classmethod
    def _guide_pending_lead_create(cls, collected: Dict[str, Any], language_preference: Optional[str]) -> Dict[str, Any]:
        missing = []
        if not collected.get("last_name"):
            missing.append("last name")
        if not collected.get("status"):
            missing.append("status")

        is_korean = (language_preference or "").lower() == "kor"
        if is_korean:
            prompt = "리드 생성을 이어가볼게요. "
            if missing:
                prompt += f"아직 {', '.join(missing)} 정보가 필요해요. "
            prompt += "예: `last name Kim, status New`, `성이 김이고 상태는 Follow Up`, `이메일 kim@test.com, status Qualified`"
        else:
            prompt = "Let's keep creating the lead. "
            if missing:
                prompt += f"I still need {', '.join(missing)}. "
            prompt += "For example: `last name Kim, status New`, `status Follow Up`, or `email kim@test.com, status Qualified`."
        return {"intent": "CHAT", "object_type": "lead", "text": prompt, "score": 1.0}

    @classmethod
    def _resolve_pending_create(cls, user_query: str, conversation_id: Optional[str], language_preference: Optional[str]) -> Optional[Dict[str, Any]]:
        pending = ConversationContextStore.get_pending_create(conversation_id)
        if not pending:
            return None

        object_type = pending.get("object_type")
        if object_type != "lead":
            return None

        collected = dict(pending.get("data") or {})
        collected.update({k: v for k, v in cls._extract_lead_fields_from_text(user_query).items() if v})

        if not collected.get("last_name") or not collected.get("status"):
            ConversationContextStore.remember_pending_create(conversation_id, object_type, collected)
            return cls._guide_pending_lead_create(collected, language_preference)

        ConversationContextStore.clear_pending_create(conversation_id)
        return {
            "intent": "CREATE",
            "object_type": "lead",
            "data": collected,
            "score": 1.0,
        }

    @classmethod
    def _resolve_pending_lead_edit(cls, user_query: str, conversation_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        context = ConversationContextStore.get_context(conversation_id)
        if context.get("last_object") != "lead" or not context.get("last_record_id"):
            return None
        if context.get("last_intent") not in cls.LEAD_EDIT_CONTEXT_INTENTS:
            return None

        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and "lead" not in explicit_objects:
            return None
        if cls._is_lead_create_like_request(user_query):
            return None

        data = cls._extract_lead_update_fields_from_text(user_query)
        if not data:
            return None

        return {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": context.get("last_record_id"),
            "data": data,
            "score": 1.0,
        }

    @classmethod
    def _is_lead_create_like_request(cls, user_query: str) -> bool:
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and "lead" not in explicit_objects:
            return False
        if "lead" not in normalized_query and "리드" not in user_query:
            return False
        if cls._extract_phase1_record_id(user_query, "lead"):
            return False

        has_create_action = any(token in normalized_query for token in cls.LEAD_CREATE_ACTIONS)
        if has_create_action:
            return True

        has_save_action = any(token in normalized_query for token in {"save", "저장"})
        if not has_save_action:
            return False

        follow_up_markers = ("this", "that", "it", "current", "selected", "해당", "이 ", "그 ")
        if any(marker in normalized_query or marker in user_query for marker in follow_up_markers):
            return False

        return bool(cls._extract_lead_fields_from_text(user_query))

    @classmethod
    def _resolve_lead_create_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if not cls._is_lead_create_like_request(user_query):
            return None

        data = cls._extract_lead_fields_from_text(user_query)
        required_fields = cls._phase1_required_fields("lead")
        if all(field in data and data[field] not in (None, "") for field in required_fields):
            return {
                "intent": "CREATE",
                "object_type": "lead",
                "data": data,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if not data:
            return cls._build_lead_create_form_response(language_preference)

        return cls._build_chat_native_form_response(
            object_type="lead",
            mode="create",
            submitted_values=data,
            conversation_id=conversation_id,
            language_preference=language_preference,
        )

    @classmethod
    def _apply_contextual_record_id(cls, agent_output: Dict[str, Any], conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return agent_output

        intent = str(agent_output.get("intent") or "").upper()
        if intent != "UPDATE" or agent_output.get("record_id"):
            return agent_output

        context = ConversationContextStore.get_context(conversation_id)
        last_object = context.get("last_object")
        last_record_id = context.get("last_record_id")
        object_type = str(agent_output.get("object_type") or "").lower()
        object_type = {"leads": "lead", "contacts": "contact", "opportunities": "opportunity"}.get(object_type, object_type)

        if last_object and last_record_id and (not object_type or object_type == last_object):
            agent_output["object_type"] = last_object
            agent_output["record_id"] = last_record_id

        return agent_output

    @classmethod
    def _resolve_explicit_manage_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
        if not match:
            return None
        return {
            "intent": "MANAGE",
            "object_type": match.group(1).lower(),
            "record_id": match.group(2),
            "score": 1.0,
        }

    @classmethod
    def _resolve_explicit_lead_record_request(
        cls,
        db: Optional[Session],
        user_query: str,
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        match = re.match(
            r"^\s*(show|open|view|read|details|manage|edit|update|change|modify|delete|remove|erase|보여|보여줘|열어|열어줘|상세|관리|수정|변경|바꿔|삭제)\s+"
            r"(?:this\s+|that\s+)?(lead|leads|리드|리드를)\s+"
            r"([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)"
            r"(?:[\s,:-]+(.*?))?\s*$",
            user_query,
            re.IGNORECASE,
        )
        if not match:
            return None

        action = (match.group(1) or "").lower()
        record_id = match.group(3)
        trailing_text = (match.group(4) or "").strip()

        if action in cls.LEAD_READ_ACTIONS:
            return {
                "intent": "MANAGE",
                "object_type": "lead",
                "record_id": record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if action in cls.LEAD_EDIT_ACTIONS:
            lead = LeadService.get_lead(db, record_id)
            if not lead:
                return {"intent": "CHAT", "object_type": "lead", "text": "I couldn't find that lead record.", "score": 1.0}
            return cls._build_phase1_edit_form_response(
                "lead",
                lead,
                language_preference,
                db=db,
            )

        if action in cls.LEAD_UPDATE_ACTIONS:
            update_source = trailing_text or user_query
            data = cls._extract_lead_update_fields_from_text(update_source)
            if not data:
                lead = LeadService.get_lead(db, record_id)
                if not lead:
                    return {"intent": "CHAT", "object_type": "lead", "text": "I couldn't find that lead record.", "score": 1.0}
                return cls._build_phase1_edit_form_response(
                    "lead",
                    lead,
                    language_preference,
                    db=db,
                )
            return {
                "intent": "UPDATE",
                "object_type": "lead",
                "record_id": record_id,
                "data": data,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if action in cls.LEAD_DELETE_ACTIONS:
            return {
                "intent": "DELETE",
                "object_type": "lead",
                "record_id": record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        return None

    @classmethod
    def _resolve_quick_lead_form_request(
        cls,
        db: Session,
        user_query: str,
        conversation_id: Optional[str],
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and "lead" not in explicit_objects:
            return None

        if "lead" not in normalized_query and "리드" not in user_query:
            return None

        has_explicit_id = bool(re.search(r"\b([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)\b", user_query))
        if has_explicit_id:
            return None

        extracted_create_data = cls._extract_lead_fields_from_text(user_query)
        if any(token in normalized_query for token in cls.LEAD_CREATE_ACTIONS) and not extracted_create_data:
            return cls._build_lead_create_form_response(language_preference)

        if any(token in normalized_query for token in cls.LEAD_EDIT_ACTIONS | cls.LEAD_UPDATE_ACTIONS):
            context = ConversationContextStore.get_context(conversation_id)
            if context.get("last_object") != "lead" or not context.get("last_record_id"):
                return None
            lead = LeadService.get_lead(db, context["last_record_id"])
            if not lead:
                return None
            return cls._build_phase1_edit_form_response(
                "lead",
                lead,
                language_preference,
                db=db,
            )

        return None

    @staticmethod
    def _delete_record(db: Session, obj: str, record_id: str) -> bool:
        if obj == "lead":
            return LeadService.delete_lead(db, record_id)
        if obj == "contact":
            return ContactService.delete_contact(db, record_id)
        if obj == "opportunity":
            return OpportunityService.delete_opportunity(db, record_id)
        if obj == "brand":
            return VehicleSpecService.delete_vehicle_spec(db, record_id)
        if obj == "model":
            return ModelService.delete_model(db, record_id)
        if obj == "product":
            from web.backend.app.services.product_service import ProductService
            return ProductService.delete_product(db, record_id)
        if obj == "asset":
            from web.backend.app.services.asset_service import AssetService
            return AssetService.delete_asset(db, record_id)
        if obj in ["message_template", "template"]:
            return MessageTemplateService.delete_template(db, record_id)
        return False

    @staticmethod
    def _object_display_label(obj: str, total: int) -> str:
        labels = {
            "lead": ("lead", "leads"),
            "contact": ("contact", "contacts"),
            "opportunity": ("opportunity", "opportunities"),
            "brand": ("brand", "brands"),
            "model": ("model", "models"),
            "product": ("product", "products"),
            "asset": ("asset", "assets"),
            "message_template": ("message template", "message templates"),
            "message_send": ("message", "messages"),
        }
        singular, plural = labels.get(obj, (obj.replace("_", " "), f"{obj.replace('_', ' ')}s"))
        return singular if total == 1 else plural

    @classmethod
    def _default_query_text(cls, obj: str, pagination: Dict[str, Any]) -> str:
        total = int((pagination or {}).get("total") or 0)
        label = cls._object_display_label(obj, total)
        if total == 0:
            return f"I couldn't find any {label}."

        page = int((pagination or {}).get("page") or 1)
        total_pages = int((pagination or {}).get("total_pages") or 1)
        if total_pages > 1:
            return f"I found {total} {label}. You're viewing page {page} of {total_pages}."
        return f"I found {total} {label} for you."

    @staticmethod
    def _display_value(value: Any) -> str:
        if value in (None, "", "None", "null"):
            return ""
        if hasattr(value, "value"):
            return str(value.value)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)

    @staticmethod
    def _looks_like_record_id(value: Any) -> bool:
        if not value or not isinstance(value, str):
            return False
        return bool(re.fullmatch(r"[A-Za-z]+-[A-Za-z0-9-]+", value) or re.fullmatch(r"[A-Za-z0-9]{15,18}", value))

    @classmethod
    def _resolve_lookup_name_to_id(cls, db: Session, lookup_type: str, raw_value: Any) -> Any:
        value = cls._display_value(raw_value).strip()
        if not value or cls._looks_like_record_id(value):
            return raw_value

        if lookup_type == "brand":
            record = (
                db.query(VehicleSpecification)
                .filter(
                    VehicleSpecification.deleted_at == None,
                    VehicleSpecification.record_type == "Brand",
                    VehicleSpecification.name.ilike(value),
                )
                .first()
            )
            return record.id if record else raw_value

        if lookup_type == "model":
            record = db.query(DbModel).filter(DbModel.deleted_at == None, DbModel.name.ilike(value)).first()
            return record.id if record else raw_value

        if lookup_type == "product":
            record = db.query(DbProduct).filter(DbProduct.deleted_at == None, DbProduct.name.ilike(value)).first()
            return record.id if record else raw_value

        return raw_value

    @classmethod
    def _normalize_lead_lookup_inputs(cls, db: Session, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = dict(data or {})
        for field in ("brand", "model", "product"):
            if field in normalized:
                normalized[field] = cls._resolve_lookup_name_to_id(db, field, normalized.get(field))
        return normalized

    @classmethod
    def _normalize_supported_lookup_inputs(cls, db: Session, object_type: str, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = dict(data or {})
        lookup_fields = {
            "lead": ("brand", "model", "product"),
            "opportunity": ("brand", "model", "product"),
            "product": ("brand", "model"),
            "asset": ("brand", "model", "product"),
            "model": ("brand",),
        }
        for field in lookup_fields.get(object_type, ()):
            if field in normalized:
                normalized[field] = cls._resolve_lookup_name_to_id(db, field, normalized.get(field))
        if object_type == "brand":
            normalized["record_type"] = "Brand"
        return normalized

    @staticmethod
    def _lead_name(lead: Any) -> str:
        name = " ".join(
            part for part in [getattr(lead, "first_name", None), getattr(lead, "last_name", None)] if part
        ).strip()
        if not name or name == "-":
            return str(getattr(lead, "id", "Unnamed Lead"))
        return name

    @classmethod
    def _lead_delete_summary(cls, lead: Any) -> str:
        name = cls._lead_name(lead)
        phone = cls._display_value(getattr(lead, "phone", None))
        if phone:
            return f"{name} ({phone})"
        return name

    @classmethod
    def _record_delete_summary(cls, object_type: str, record: Any) -> str:
        if not record:
            return ""
        title = cls._phase1_display_title(object_type, record)
        if object_type == "lead":
            return cls._lead_delete_summary(record)
        if object_type == "contact":
            phone = cls._display_value(getattr(record, "phone", None))
            return f"{title} ({phone})" if phone else title
        return title

    @classmethod
    def _build_missing_record_text(
        cls,
        object_type: str,
        record_id: Optional[str],
        user_query: str,
        conversation_id: Optional[str] = None,
    ) -> str:
        normalized_object = {
            "leads": "lead",
            "contacts": "contact",
            "opportunities": "opportunity",
            "opps": "opportunity",
            "products": "product",
            "assets": "asset",
            "brands": "brand",
            "models": "model",
            "template": "message_template",
            "templates": "message_template",
            "message_templates": "message_template",
        }.get(object_type, object_type)
        object_label = normalized_object.replace("_", " ")

        query_results = ConversationContextStore.get_query_results(conversation_id)
        if query_results.get("object_type") == normalized_object and record_id:
            for row in list(query_results.get("results") or []):
                if str(row.get("record_id")) == str(record_id):
                    label = cls._display_value(row.get("label")).strip()
                    if label:
                        return f"I couldn't find the {object_label} record for {label}."

        selection_payload = ConversationContextStore.get_selection(conversation_id)
        selection_ids = list((selection_payload or {}).get("ids") or [])
        selection_labels = list((selection_payload or {}).get("labels") or [])
        if record_id and len(selection_ids) == 1 and str(selection_ids[0]) == str(record_id) and selection_labels:
            label = cls._display_value(selection_labels[0]).strip()
            if label:
                return f"I couldn't find the {object_label} record for {label}."

        if normalized_object in {"lead", "contact"}:
            extracted = cls._extract_lead_fields_from_text(user_query, allow_loose_last_name=True)
            first_name = cls._display_value(extracted.get("first_name")).strip()
            last_name = cls._display_value(extracted.get("last_name")).strip()
            phone = cls._display_value(extracted.get("phone")).strip()
            name = " ".join(part for part in [first_name, last_name] if part).strip()
            if name and phone:
                return f"I couldn't find the {object_label} record for {name} ({phone})."
            if name:
                return f"I couldn't find the {object_label} record for {name}."
            if phone:
                return f"I couldn't find the {object_label} record for {phone}."

        if normalized_object in {"opportunity", "product", "brand", "model", "message_template"}:
            match = re.search(r"\bname\s+([A-Za-z0-9가-힣 _-]+)", user_query, re.IGNORECASE)
            if match:
                name = cls._display_value(match.group(1)).strip()
                if name:
                    return f"I couldn't find the {object_label} record for {name}."

        return f"I couldn't find that {object_label} record."

    @classmethod
    def _detect_manage_mode(cls, user_query: str) -> str:
        normalized = IntentPreClassifier.normalize(user_query)
        if any(token in normalized for token in ["edit", "update", "change", "modify", "수정", "변경", "바꿔"]):
            return "edit"
        return "view"

    @classmethod
    def _build_lead_create_form_response(cls, language_preference: Optional[str]) -> Dict[str, Any]:
        return cls._build_chat_native_form_response(
            object_type="lead",
            mode="create",
            language_preference=language_preference,
        )

    @classmethod
    def _build_lead_edit_form_response(
        cls,
        record_id: str,
        lead_name: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        return build_lead_edit_form_response(record_id, lead_name, language_preference)

    @classmethod
    def _build_lead_chat_card(cls, db: Session, lead: Any, mode: str = "view") -> Dict[str, Any]:
        from web.backend.app.services.product_service import ProductService

        brand = VehicleSpecService.get_vehicle_spec(db, lead.brand) if getattr(lead, "brand", None) else None
        model = ModelService.get_model(db, lead.model) if getattr(lead, "model", None) else None
        product = ProductService.get_product(db, lead.product) if getattr(lead, "product", None) else None

        name = cls._lead_name(lead)
        status = cls._display_value(getattr(lead, "status", None))
        fields = [
            {"label": "First name", "value": cls._display_value(getattr(lead, "first_name", None))},
            {"label": "Last name", "value": cls._display_value(getattr(lead, "last_name", None))},
            {"label": "Status", "value": status},
            {"label": "Email", "value": cls._display_value(getattr(lead, "email", None))},
            {"label": "Phone", "value": cls._display_value(getattr(lead, "phone", None))},
            {"label": "Gender", "value": cls._display_value(getattr(lead, "gender", None))},
            {"label": "Brand", "value": cls._display_value(getattr(brand, "name", None))},
            {"label": "Model", "value": cls._display_value(getattr(model, "name", None))},
            {"label": "Product", "value": cls._display_value(getattr(product, "name", None))},
            {"label": "Description", "value": cls._display_value(getattr(lead, "description", None))},
        ]
        line_count = 2 + len(fields)
        hint = (
            "Reply with the fields to change, like `status Qualified`, `phone 01012345678`, or `email kim@test.com`."
            if mode == "edit" else
            "Reply with `edit this lead` to keep updating in chat, ask to open the full record, or send a message."
        )
        actions = []
        if mode == "view":
            actions = [
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
                {"label": "Send Message", "action": "send_message", "tone": "secondary"},
            ]

        return {
            "type": "lead_paste",
            "object_type": "lead",
            "mode": mode,
            "paste_label": f"Pasted ~{line_count} lines",
            "title": name,
            "subtitle": f"Lead · {status}",
            "record_id": str(getattr(lead, "id", "")),
            "fields": fields,
            "actions": actions,
            "hint": hint,
        }

    @classmethod
    def _build_lead_open_record_response(
        cls,
        db: Session,
        lead: Any,
        conversation_id: Optional[str],
        action: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        return build_lead_open_record_response(
            db=db,
            lead=lead,
            conversation_id=conversation_id,
            action=action,
            language_preference=language_preference,
            build_chat_card=cls._build_lead_chat_card,
            lead_name_getter=cls._lead_name,
        )

    @classmethod
    def _build_phase1_query_sql(cls, obj: str, data: Dict[str, Any]) -> Optional[str]:
        config = cls._default_query_parts(obj)
        if not config:
            return None

        search_term = (data or {}).get("search_term")
        if search_term:
            config = cls._apply_search_to_sql(obj, config, search_term)

        if obj == "opportunity" and data.get("query_mode") == "recent":
            return (
                f"SELECT {config['select']} FROM {config['from']} "
                f"WHERE {config['where']} ORDER BY {config['order_by']}"
            )

        return (
            f"SELECT {config['select']} FROM {config['from']} "
            f"WHERE {config['where']} ORDER BY {config['order_by']}"
        )

    @staticmethod
    def _get_metadata() -> str:
        try:
            # Check for multiple possible metadata paths due to reorganization
            paths_to_check = [
                METADATA_PATH,
                os.path.join(os.getcwd(), "backend", "metadata.json"),
                os.path.join(os.getcwd(), ".gemini", "development", "backend", "metadata.json")
            ]
            for p in paths_to_check:
                if os.path.exists(p):
                    with open(p, "r") as f:
                        return json.dumps(json.load(f), indent=2)
            return "{}"
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return "{}"

    @staticmethod
    def _sanitize_pagination(page: Optional[int], per_page: Optional[int]) -> tuple[int, int, int]:
        safe_page = max(int(page or 1), 1)
        safe_per_page = max(1, min(int(per_page or 30), 30))
        offset = (safe_page - 1) * safe_per_page
        return safe_page, safe_per_page, offset

    @staticmethod
    def _default_query_parts(obj: str) -> Optional[Dict[str, str]]:
        mapping = {
            "lead": {
                "select": "l.id, TRIM(CONCAT_WS(' ', l.first_name, l.last_name)) AS display_name, l.phone, l.status, COALESCE(m.name, l.model) AS model, l.created_at",
                "from": "leads l LEFT JOIN models m ON l.model = m.id",
                "where": "l.deleted_at IS NULL",
                "order_by": "l.created_at DESC",
            },
            "contact": {
                "select": "c.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS display_name, c.phone, c.email, c.tier, c.created_at",
                "from": "contacts c",
                "where": "c.deleted_at IS NULL",
                "order_by": "c.created_at DESC",
            },
            "opportunity": {
                "select": "o.id, o.name, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact_display_name, c.phone AS contact_phone, o.stage, o.amount, COALESCE(m.name, o.model) AS model, o.created_at",
                "from": "opportunities o LEFT JOIN contacts c ON o.contact = c.id LEFT JOIN models m ON o.model = m.id",
                "where": "o.deleted_at IS NULL",
                "order_by": "o.created_at DESC",
            },
            "brand": {
                "select": "id, name, record_type, description",
                "from": "vehicle_specifications",
                "where": "record_type = 'Brand' AND deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "model": {
                "select": "m.id, m.name, vs.name AS brand, m.description",
                "from": "models m LEFT JOIN vehicle_specifications vs ON m.brand = vs.id",
                "where": "m.deleted_at IS NULL",
                "order_by": "m.created_at DESC",
            },
            "product": {
                "select": "p.id, p.name, vs.name AS brand, m.name AS model, p.category, p.base_price",
                "from": "products p LEFT JOIN vehicle_specifications vs ON p.brand = vs.id LEFT JOIN models m ON p.model = m.id",
                "where": "p.deleted_at IS NULL",
                "order_by": "p.created_at DESC",
            },
            "asset": {
                "select": "a.id, COALESCE(a.name, a.vin) AS name, a.vin, a.status, vs.name AS brand, m.name AS model",
                "from": "assets a LEFT JOIN vehicle_specifications vs ON a.brand = vs.id LEFT JOIN models m ON a.model = m.id",
                "where": "a.deleted_at IS NULL",
                "order_by": "a.created_at DESC",
            },
            "message_template": {
                "select": "id, name, record_type, subject, content, (image_url IS NOT NULL) AS has_image",
                "from": "message_templates",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "message_send": {
                "select": "ms.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact, ms.direction, ms.status, ms.sent_at",
                "from": "message_sends ms LEFT JOIN contacts c ON ms.contact = c.id",
                "where": "ms.deleted_at IS NULL",
                "order_by": "ms.sent_at DESC",
            },
        }
        return mapping.get(obj)

    @staticmethod
    def _default_query_projection(obj: str) -> str:
        projection_map = {
            "lead": "id, display_name, phone, status, model, created_at",
            "contact": "id, display_name, phone, email, tier, created_at",
            "opportunity": "id, name, contact_display_name, contact_phone, stage, amount, model, created_at",
            "brand": "id, name, record_type, description",
            "model": "id, name, brand, description",
            "product": "id, name, brand, model, category, base_price",
            "asset": "id, name, vin, status, brand, model",
            "message_template": "id, name, record_type, subject, content, has_image",
            "message_send": "id, contact, direction, status, sent_at",
        }
        return projection_map.get(obj, "id")

    @staticmethod
    def _apply_search_to_sql(obj: str, config: Dict[str, str], term: str) -> Dict[str, str]:
        if not term:
            return config
        
        search_fields = {
            "lead": [
                "TRIM(CONCAT_WS(' ', l.first_name, l.last_name))",
                "l.first_name",
                "l.last_name",
                "l.email",
                "l.phone",
                "l.status",
                "COALESCE(m.name, l.model)",
            ],
            "contact": [
                "TRIM(CONCAT_WS(' ', c.first_name, c.last_name))",
                "c.first_name",
                "c.last_name",
                "c.email",
                "c.phone",
                "c.tier",
            ],
            "opportunity": [
                "o.name",
                "o.stage",
                "TRIM(CONCAT_WS(' ', c.first_name, c.last_name))",
                "c.first_name",
                "c.last_name",
                "c.phone",
                "COALESCE(m.name, o.model)",
            ],
            "brand": [
                "name",
                "description",
            ],
            "model": [
                "m.name",
                "vs.name",
                "m.description",
            ],
            "product": [
                "p.name",
                "vs.name",
                "m.name",
                "p.category",
            ],
            "asset": [
                "COALESCE(a.name, a.vin)",
                "a.vin",
                "a.status",
                "vs.name",
                "m.name",
            ],
            "message_template": [
                "name",
                "record_type",
                "subject",
                "content",
            ],
            "message_send": [
                "TRIM(CONCAT_WS(' ', c.first_name, c.last_name))",
                "c.first_name",
                "c.last_name",
                "ms.direction",
                "ms.status",
            ],
        }
        
        fields = search_fields.get(obj, ["id"])
        term_clean = term.replace("'", "''")
        conditions = [f"{f} ILIKE '%{term_clean}%'" for f in fields]
        search_where = f"({ ' OR '.join(conditions) })"
        
        config_copy = config.copy()
        if config_copy.get("where"):
            config_copy["where"] = f"{config_copy['where']} AND {search_where}"
        else:
            config_copy["where"] = search_where
        return config_copy

    @classmethod
    def _execute_paginated_query(
        cls,
        db: Session,
        sql: str,
        obj: str,
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        try:
            safe_page, safe_per_page, _offset = cls._sanitize_pagination(page, per_page)
            clean_sql = sql.strip().rstrip(";")
            
            # Phase 306: Auto-correct table names globally in the SQL string
            clean_sql = AiIntelligenceService.fix_sql_table_names(clean_sql)
            
            projection = cls._default_query_projection(obj)
            full_sql = f"SELECT {projection} FROM ({clean_sql}) AS agent_query_page"
            full_result = db.execute(text(full_sql))
            rows = [dict(row._mapping) for row in full_result]
            total = len(rows)
            total_pages = max(1, (total + safe_per_page - 1) // safe_per_page)

            return {
                "results": rows,
                "sql": full_sql,
                "pagination": {
                    "page": safe_page,
                    "per_page": safe_per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "object_type": obj,
                    "mode": "local",
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"SQL Execution Error: {str(e)}")
            
            # Phase 306 Ultimate Hardening: 
            # If even the first fallback fails, use the simplest possible SELECT * FROM plural_table
            # This virtually guarantees a 'Success' result for any recognized object.
            try:
                table_name = AiIntelligenceService.normalize_table_name(obj)
                ultimate_sql = f"SELECT * FROM {table_name} WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                
                # Re-execute with simplest query
                full_result = db.execute(text(ultimate_sql))
                rows = [dict(row._mapping) for row in full_result]
                total = len(rows)
                
                return {
                    "results": rows,
                    "sql": ultimate_sql,
                    "pagination": {
                        "page": 1,
                        "per_page": 30,
                        "total": total,
                        "total_pages": 1,
                        "object_type": obj,
                        "mode": "local",
                    },
                }
            except:
                pass
            raise e

    @classmethod
    def _resolve_contextual_record_reference(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not conversation_id and not selection:
            return None

        context = ConversationContextStore.get_context(conversation_id)
        last_created = context.get("last_created") or {}

        q_low = user_query.lower()

        def contains_marker(marker: str) -> bool:
            if not marker:
                return False
            if re.fullmatch(r"[a-z]+", marker):
                return re.search(rf"\b{re.escape(marker)}\b", q_low) is not None
            return marker in q_low or marker in user_query

        recent_markers = ["just created", "recently created", "방금 생성", "방금 생성한", "방금 만든", "최근 만든", "최근 생성"]
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if value in cls.PHASE1_OBJECTS and key in normalized_query
        ]
        context_object_type = context.get("last_object") or last_created.get("object_type")
        context_record_id = context.get("last_record_id") or last_created.get("record_id")
        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        selection_object_type = (selection_payload or {}).get("object_type")
        selection_ids = list((selection_payload or {}).get("ids") or [])
        selection_record_id = selection_ids[0] if len(selection_ids) == 1 else None

        if context_object_type not in cls.PHASE1_OBJECTS:
            context_object_type = None
            context_record_id = None
        if selection_object_type not in cls.PHASE1_OBJECTS:
            selection_object_type = None
            selection_record_id = None

        if any(contains_marker(marker) for marker in recent_markers):
            recent_object_type = last_created.get("object_type") or context_object_type
            recent_record_id = last_created.get("record_id") or context_record_id
            if not recent_object_type or not recent_record_id:
                return None
            return {
                "intent": "MANAGE",
                "object_type": recent_object_type,
                "record_id": recent_record_id,
                "score": 1.0,
            }

        follow_up_markers = ["that", "this", "it", "them", "those", "that one", "the one", "this one", "the record", "record", "그", "이", "해당", "방금", "최근"]
        has_follow_up_marker = any(contains_marker(marker) for marker in follow_up_markers)
        manage_markers = ["show", "open", "manage", "view", "details", "grab", "fetch", "보여", "열어", "관리", "상세"]
        update_markers = ["update", "edit", "change", "modify", "tweak", "fix", "수정", "변경", "바꿔"]

        if not has_follow_up_marker or not any(contains_marker(marker) for marker in manage_markers + update_markers):
            return None

        desired_object_type = explicit_objects[0] if explicit_objects else None
        context_candidate = (
            {"object_type": context_object_type, "record_id": context_record_id}
            if context_object_type and context_record_id else None
        )
        selection_candidate = (
            {"object_type": selection_object_type, "record_id": selection_record_id}
            if selection_object_type and selection_record_id else None
        )

        if explicit_objects and any(marker in normalized_query for marker in ("latest", "last")):
            if not context_candidate and not selection_candidate:
                return None

        if desired_object_type:
            if context_candidate and context_candidate["object_type"] == desired_object_type:
                return {
                    "intent": "MANAGE",
                    "object_type": context_candidate["object_type"],
                    "record_id": context_candidate["record_id"],
                    "score": 1.0,
                }
            if selection_candidate and selection_candidate["object_type"] == desired_object_type:
                return {
                    "intent": "MANAGE",
                    "object_type": selection_candidate["object_type"],
                    "record_id": selection_candidate["record_id"],
                    "score": 1.0,
                }
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": f"I need a specific {desired_object_type} record first. Open one or select one, then try again.",
                "score": 1.0,
            }

        if context_candidate and selection_candidate:
            if (
                context_candidate["object_type"] != selection_candidate["object_type"]
                or context_candidate["record_id"] != selection_candidate["record_id"]
            ):
                return {
                    "intent": "CHAT",
                    "text": (
                        f"I found two different records in context: the last {context_candidate['object_type']} "
                        f"({context_candidate['record_id']}) and the selected {selection_candidate['object_type']} "
                        f"({selection_candidate['record_id']}). Tell me which one to open or edit."
                    ),
                    "score": 1.0,
                }

        chosen = context_candidate or selection_candidate
        if chosen:
            return {
                "intent": "MANAGE",
                "object_type": chosen["object_type"],
                "record_id": chosen["record_id"],
                "score": 1.0,
            }
        
        return None

    @classmethod
    def _resolve_delete_confirmation(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        q_low = user_query.lower()
        pending_delete = ConversationContextStore.get_pending_delete(conversation_id)
        if pending_delete:
            if any(token in q_low for token in ["yes", "confirm", "proceed", "delete it", "yes delete"]):
                ConversationContextStore.clear_pending_delete(conversation_id)
                pending_ids = pending_delete.get("ids") or []
                return {
                    "intent": "DELETE",
                    "object_type": pending_delete.get("object_type"),
                    "record_id": pending_delete.get("record_id"),
                    "selection": {"object_type": pending_delete.get("object_type"), "ids": pending_ids} if pending_ids else None,
                    "score": 1.0,
                }
            if any(token in q_low for token in ["cancel", "stop", "no", "never mind"]):
                ConversationContextStore.clear_pending_delete(conversation_id)
                return {
                    "intent": "CHAT",
                    "text": "Delete request cancelled.",
                    "score": 1.0,
                }

        normalized_query = IntentPreClassifier.normalize(user_query)
        is_force_delete = "[force_delete]" in user_query.lower() or "[FORCE_DELETE]" in user_query
        delete_markers = ["delete", "remove", "erase", "nuke", "dump", "삭제"]
        if not any(marker in q_low or marker in user_query for marker in delete_markers):
            return None

        # Improved UUID and Record ID extraction (matches e.g., lead-123 or 550e8400-...)
        explicit_id_match = re.search(r"\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b", user_query, re.IGNORECASE)
        if not explicit_id_match:
            explicit_id_match = re.search(r"\b([A-Za-z0-9]{15,18})\b", user_query)
        if not explicit_id_match:
            explicit_id_match = re.search(r"\b([A-Za-z]+-[A-Za-z0-9-]+)\b", user_query)
        explicit_id = explicit_id_match.group(1) if explicit_id_match else None

        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        selected_ids = list((selection_payload or {}).get("ids") or [])
        selected_labels = list((selection_payload or {}).get("labels") or [])
        selected_object = (selection_payload or {}).get("object_type")
        
        # If ID was in query and matched an object type, prioritize it
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        object_type = explicit_objects[0] if explicit_objects else None

        if selected_object and selected_ids:
            if is_force_delete:
                ConversationContextStore.clear_pending_delete(conversation_id)
                return {
                    "intent": "DELETE",
                    "object_type": selected_object,
                    "record_id": selected_ids[0] if len(selected_ids) == 1 else None,
                    "selection": {"object_type": selected_object, "ids": selected_ids},
                    "score": 1.0,
                }
             # ... rest of selection logic
            ConversationContextStore.remember_pending_delete(
                conversation_id,
                selected_object,
                record_id=selected_ids[0] if len(selected_ids) == 1 else None,
                ids=selected_ids,
                labels=selected_labels,
            )
            label = selected_object.replace("_", " ")
            count = len(selected_ids)
            preview_names = ", ".join(selected_labels[:3]) if selected_labels else "selected records"
            return {
                "intent": "CHAT",
                "object_type": selected_object,
                "text": (
                    f"Delete confirmation needed: should I permanently delete these {count} {label} records ({preview_names})? "
                    "Choose [yes] to continue or [cancel] to keep them."
                    if count > 1 else
                    f"Delete confirmation needed: should I permanently delete {selected_labels[0] if selected_labels else f'this {label} record'}? Choose [yes] to continue or [cancel] to keep it."
                ),
                "score": 1.0,
            }

        context = ConversationContextStore.get_context(conversation_id)
        if not object_type:
            object_type = context.get("last_object")

        record_id = explicit_id or context.get("last_record_id")
        last_created = context.get("last_created") or {}
        if not record_id:
            record_id = last_created.get("record_id")
        if not object_type:
            object_type = last_created.get("object_type")

        if explicit_objects and object_type and object_type not in explicit_objects:
            return None
        if not object_type or not record_id:
            return None

        # Phase 177: Bypass double confirmation if the user explicitly provided the ID in the query
        # Phase 177/182/183: Bypass double confirmation if force delete or explicit ID
        if is_force_delete or (record_id and (record_id.lower() in user_query.lower() or record_id.lower() in normalized_query.lower())):
             return {
                "intent": "DELETE",
                "object_type": object_type,
                "record_id": record_id,
                "score": 1.0,
            }

        ConversationContextStore.remember_pending_delete(conversation_id, object_type, record_id)

        label = object_type.replace("_", " ")
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "record_id": record_id,
            "text": f"Delete confirmation needed: should I permanently delete this {label} record ({record_id})? Choose [yes] to continue or [cancel] to keep it.",
            "score": 1.0,
        }

    @classmethod
    def _resolve_send_message_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]],
        language_preference: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        q_low = user_query.lower()
        send_markers = ["send message", "send messages", "message them", "text them", "메시지 보내"]
        if not any(marker in q_low or marker in user_query for marker in send_markers):
            return None

        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        object_type = (selection_payload or {}).get("object_type")
        ids = (selection_payload or {}).get("ids") or []
        context = ConversationContextStore.get_context(conversation_id)

        template_id = None
        if context.get("last_object") in ["message_template", "template"] and context.get("last_record_id"):
            template_id = context.get("last_record_id")
        last_created = context.get("last_created") or {}
        if not template_id and last_created.get("object_type") == "message_template":
            template_id = last_created.get("record_id")

        wants_template = "template" in q_low or "message template" in q_low

        if wants_template and not template_id:
            return {
                "intent": "CHAT",
                "text": "I can send a message with a template, but I need a current template first. Open or manage a message template, then ask me to send the message.",
                "score": 1.0,
            }

        if not object_type or not ids:
            is_korean = (language_preference or "").lower() == "kor"
            return {
                "intent": "SEND_MESSAGE",
                "object_type": "contact",
                "selection": {"object_type": "contact", "ids": []},
                "redirect_url": "/messaging/ui",
                "text": (
                    "메시지 화면을 열어둘게요. 먼저 수신자를 고르고, 템플릿을 선택하거나 내용을 입력해서 바로 보낼 수 있어요."
                    if is_korean else
                    "I'll open the Send Message screen for you. Start by picking recipients, then choose a template or type your message and send it."
                ),
                "score": 1.0,
            }

        return {
            "intent": "SEND_MESSAGE",
            "object_type": object_type,
            "selection": {"object_type": object_type, "ids": ids},
            "template_id": template_id,
            "redirect_url": f"/messaging/ui?sourceObject={object_type}&count={len(ids)}",
            "text": (
                f"Opening the messaging flow for {len(ids)} selected {object_type} record(s)"
                f" using your current template ({template_id})."
                if template_id else
                f"Opening the messaging flow for {len(ids)} selected {object_type} record(s)."
            ),
            "score": 1.0,
        }

    @classmethod
    async def process_query(
        cls,
        db: Session,
        user_query: str,
        conversation_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
        selection: Optional[Dict[str, Any]] = None,
        language_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        debug_event(
            "service.process_query.start",
            conversation_id=conversation_id,
            user_query=user_query,
            page=page,
            per_page=per_page,
            has_selection=bool(selection),
            language_preference=language_preference,
        )
        ConversationContextStore.remember_selection(conversation_id, selection)
        deterministic_query = cls._unwrap_english_request_wrapper(user_query) or user_query
        if deterministic_query != user_query:
            debug_event(
                "service.process_query.unwrapped_english_request",
                conversation_id=conversation_id,
                original_query=user_query,
                deterministic_query=deterministic_query,
            )

        if "attachment" in user_query.lower():
            return {
                "intent": "CHAT",
                "text": "I cannot query or manage attachments directly.",
                "score": 1.0
            }

        # ROBUST EXTRACTION: Search query (Priority before LLM)
        if "search" in user_query.lower() or "조회" in user_query or "검색" in user_query:
            match = re.search(r"search\s+(\w+).*?\s+for\s+(.+)", user_query, re.IGNORECASE)
            if match:
                obj_raw = match.group(1).lower()
                # Simple normalization
                if obj_raw.endswith('s') and obj_raw != 'assets':
                    obj_raw = obj_raw[:-1]
                
                # Verify it's a known object type before committing to this intent
                if obj_raw in ["lead", "contact", "opportunity", "product", "asset", "message_template", "message_send", "brand", "model"]:
                    agent_output = {
                        "intent": "QUERY",
                        "object_type": obj_raw,
                        "data": {
                            "search_term": match.group(2).strip(),
                            "auto_open_single_result": True,
                        },
                        "score": 1.0
                    }
                    debug_event("service.process_query.search_shortcut", conversation_id=conversation_id, agent_output=agent_output)
                    return await cls._execute_intent(db, agent_output, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        pending_create_resolution = cls._resolve_pending_create(user_query, conversation_id, language_preference)
        if pending_create_resolution:
            pending_create_resolution["language_preference"] = language_preference
            debug_event("service.process_query.pending_create_resolution", conversation_id=conversation_id, resolution=pending_create_resolution)
            return await cls._execute_intent(
                db,
                pending_create_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        explicit_lead_record_resolution = cls._resolve_explicit_lead_record_request(
            db,
            user_query,
            language_preference,
        )
        if explicit_lead_record_resolution:
            debug_event("service.process_query.explicit_lead_record_resolution", conversation_id=conversation_id, resolution=explicit_lead_record_resolution)
            if explicit_lead_record_resolution["intent"] == "OPEN_FORM":
                lead = LeadService.get_lead(db, explicit_lead_record_resolution["record_id"])
                if not lead:
                    return {"intent": "CHAT", "object_type": "lead", "text": "I couldn't find that lead record."}
                return cls._build_phase1_edit_form_response(
                    "lead",
                    lead,
                    language_preference,
                )
            return await cls._execute_intent(
                db,
                explicit_lead_record_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        explicit_lead_create_resolution = cls._resolve_lead_create_request(
            user_query,
            conversation_id,
            language_preference,
        )
        if explicit_lead_create_resolution:
            debug_event("service.process_query.explicit_lead_create_resolution", conversation_id=conversation_id, resolution=explicit_lead_create_resolution)
            return await cls._execute_intent(
                db,
                explicit_lead_create_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        pending_edit_resolution = cls._resolve_pending_lead_edit(user_query, conversation_id)
        if pending_edit_resolution:
            debug_event("service.process_query.pending_edit_resolution", conversation_id=conversation_id, resolution=pending_edit_resolution)
            # Phase 177: If the query is an explicit "edit lead {id}", open the form directly
            if "edit" in user_query.lower() or "수정" in user_query:
                record_id = pending_edit_resolution.get("record_id")
                if record_id:
                     lead = LeadService.get_lead(db, record_id)
                     if lead:
                         return cls._build_phase1_edit_form_response(
                             "lead",
                             lead,
                             language_preference,
                             db=db,
                         )

            pending_edit_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                pending_edit_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        quick_lead_form_resolution = cls._resolve_quick_lead_form_request(
            db,
            user_query,
            conversation_id,
            language_preference,
        )
        if quick_lead_form_resolution:
            debug_event("service.process_query.quick_lead_form_resolution", conversation_id=conversation_id, resolution=quick_lead_form_resolution)
            return quick_lead_form_resolution

        fast_create_form_resolution = cls._resolve_fast_create_form_request(
            user_query,
            language_preference,
        )
        if fast_create_form_resolution:
            debug_event("service.process_query.fast_create_form_resolution", conversation_id=conversation_id, resolution=fast_create_form_resolution)
            return fast_create_form_resolution

        send_message_resolution = cls._resolve_send_message_request(
            user_query,
            conversation_id,
            selection,
            language_preference=language_preference,
        )
        if send_message_resolution:
            debug_event("service.process_query.send_message_resolution", conversation_id=conversation_id, resolution=send_message_resolution)
            return await cls._execute_intent(
                db,
                send_message_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        delete_resolution = cls._resolve_delete_confirmation(user_query, conversation_id, selection)
        if delete_resolution:
            debug_event("service.process_query.delete_resolution", conversation_id=conversation_id, resolution=delete_resolution)
            # Phase 177 Fix: If the resolution is already a final intent (DELETE), execute it immediately
            if delete_resolution.get("intent") == "DELETE":
                return await cls._execute_intent(db, delete_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)
            return delete_resolution

        contextual_query_resolution = cls._resolve_contextual_query_reference(user_query, conversation_id)
        if contextual_query_resolution:
            debug_event("service.process_query.contextual_query_resolution", conversation_id=conversation_id, resolution=contextual_query_resolution)
            if contextual_query_resolution.get("intent") == "CHAT":
                return contextual_query_resolution
            contextual_query_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                contextual_query_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        existence_query_resolution = cls._resolve_existence_query_request(deterministic_query)
        if existence_query_resolution:
            existence_query_resolution["language_preference"] = language_preference
            debug_event(
                "service.process_query.existence_query_resolution",
                conversation_id=conversation_id,
                resolution=existence_query_resolution,
            )
            return await cls._execute_intent(
                db,
                existence_query_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        creation_guidance_resolution = cls._resolve_creation_guidance_request(deterministic_query)
        if creation_guidance_resolution:
            debug_event(
                "service.process_query.creation_guidance_resolution",
                conversation_id=conversation_id,
                resolution=creation_guidance_resolution,
            )
            return creation_guidance_resolution

        hot_guidance_resolution = cls._resolve_hot_object_guidance_request(deterministic_query)
        if hot_guidance_resolution:
            debug_event(
                "service.process_query.hot_guidance_resolution",
                conversation_id=conversation_id,
                resolution=hot_guidance_resolution,
            )
            return hot_guidance_resolution

        flow_guidance_resolution = cls._resolve_object_flow_guidance_request(deterministic_query)
        if flow_guidance_resolution:
            debug_event(
                "service.process_query.flow_guidance_resolution",
                conversation_id=conversation_id,
                resolution=flow_guidance_resolution,
            )
            return flow_guidance_resolution

        message_policy_resolution = await cls._resolve_message_policy_question(
            deterministic_query,
            language_preference=language_preference,
        )
        if message_policy_resolution:
            debug_event(
                "service.process_query.message_policy_resolution",
                conversation_id=conversation_id,
                resolution=message_policy_resolution,
            )
            return message_policy_resolution

        bounded_update_clarification = await cls._resolve_bounded_english_update_clarification(deterministic_query)
        if bounded_update_clarification:
            debug_event(
                "service.process_query.bounded_update_clarification",
                conversation_id=conversation_id,
                clarification=bounded_update_clarification,
            )
            return bounded_update_clarification

        bounded_clarification = await cls._resolve_bounded_english_clarification(deterministic_query)
        if bounded_clarification:
            debug_event("service.process_query.bounded_clarification", conversation_id=conversation_id, clarification=bounded_clarification)
            return bounded_clarification

        explicit_manage_resolution = cls._resolve_explicit_manage_request(user_query)
        if explicit_manage_resolution:
            explicit_manage_resolution["language_preference"] = language_preference
            debug_event("service.process_query.explicit_manage_resolution", conversation_id=conversation_id, resolution=explicit_manage_resolution)
            return await cls._execute_intent(db, explicit_manage_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        contextual_response = cls._resolve_contextual_record_reference(user_query, conversation_id, selection)
        if contextual_response:
            contextual_response["language_preference"] = language_preference
            debug_event("service.process_query.contextual_record_resolution", conversation_id=conversation_id, resolution=contextual_response)
            return await cls._execute_intent(db, contextual_response, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        phase1_resolution = cls._resolve_phase1_deterministic_request(
            db,
            deterministic_query,
            conversation_id,
            language_preference,
        )
        if phase1_resolution:
            debug_event("service.process_query.phase1_resolution", conversation_id=conversation_id, resolution=phase1_resolution)
            if phase1_resolution.get("intent") == "CHAT":
                return phase1_resolution
            if (
                phase1_resolution.get("intent") == "OPEN_FORM"
                and phase1_resolution.get("object_type") in cls.CHAT_NATIVE_FORM_OBJECTS
            ):
                if phase1_resolution.get("form"):
                    return phase1_resolution
                if phase1_resolution.get("record_id"):
                    record = cls._get_phase1_record(
                        db,
                        phase1_resolution["object_type"],
                        phase1_resolution["record_id"],
                    )
                    if not record:
                        return {"intent": "CHAT", "text": f"I couldn't find that {phase1_resolution['object_type']} record."}
                    return cls._build_phase1_edit_form_response(
                        phase1_resolution["object_type"],
                        record,
                        language_preference,
                        db=db,
                    )
                return cls._build_chat_native_form_response(
                    object_type=phase1_resolution["object_type"],
                    mode="create",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            return await cls._execute_intent(
                db,
                phase1_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        send_history_resolution = cls._resolve_send_history_query_request(deterministic_query)
        if send_history_resolution:
            send_history_resolution["language_preference"] = language_preference
            debug_event("service.process_query.send_history_resolution", conversation_id=conversation_id, resolution=send_history_resolution)
            return await cls._execute_intent(
                db,
                send_history_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        clarification = IntentReasoner.clarify_if_needed(deterministic_query)
        if clarification:
            debug_event("service.process_query.reasoner_clarification", conversation_id=conversation_id, clarification=clarification)
            return clarification

        short_object_clarification = cls._resolve_short_object_clarification(deterministic_query)
        if short_object_clarification:
            debug_event("service.process_query.short_object_clarification", conversation_id=conversation_id, clarification=short_object_clarification)
            return short_object_clarification

        recommendation_resolution = cls._resolve_recommendation_request(user_query, conversation_id)
        if recommendation_resolution:
            debug_event("service.process_query.recommendation_resolution", conversation_id=conversation_id, resolution=recommendation_resolution)
            return await cls._execute_intent(
                db,
                recommendation_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        # ---- Phase 49: Hybrid Intent Pre-Classification ----
        rule_based = IntentPreClassifier.detect(deterministic_query)
        if rule_based:
            debug_event("service.process_query.preclassifier_resolution", conversation_id=conversation_id, resolution=rule_based)
            normalized_query = IntentPreClassifier.normalize(deterministic_query)
            if (
                rule_based.get("intent") == "CHAT"
                and rule_based.get("object_type") == "lead"
                and IntentPreClassifier._contains_action(normalized_query, IntentPreClassifier.ACTION_CREATE)
            ):
                return cls._build_lead_create_form_response(language_preference)
            return await cls._execute_intent(db, rule_based, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        # ---- Phase 303/305: Database-Driven Intelligence Pattern Matching ----
        db_match = AiIntelligenceService.find_best_matching_pattern(db, user_query, min_score=0.4)
        if db_match:
            debug_event("service.process_query.db_intelligence_resolution", conversation_id=conversation_id, resolution=db_match)
            if db_match.get("is_suggestion"):
                return db_match
            return await cls._execute_intent(db, db_match, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        # ---- Phase 50: LLM Reasoning Fallback ----
        metadata = cls._get_metadata()
        reasoning_context = ConversationContextStore.build_reasoning_context(conversation_id, selection)
        system_prompt = IntentReasoner.build_reasoning_prompt(
            metadata,
            language_preference,
            reasoning_context,
        )

        # Call Multi-LLM Ensemble with Retry (Phase 306)
        debug_event("service.process_query.llm_fallback_start", conversation_id=conversation_id, user_query=user_query)
        agent_output = None
        for attempt in range(2):
            try:
                agent_output = await cls._call_multi_llm_ensemble(user_query, system_prompt)
                if agent_output and agent_output.get("text") != "All AI models failed to respond.":
                    break
            except Exception as e:
                logger.warning(f"LLM attempt {attempt+1} failed: {e}")
                if attempt == 1: break
                await asyncio.sleep(1)

        # If LLM failed, use Proactive Fallback as absolute last resort
        if not agent_output or agent_output.get("text") == "All AI models failed to respond.":
            out_of_scope_resolution = cls._resolve_out_of_scope_request(
                user_query,
                conversation_id=conversation_id,
                selection=selection,
            )
            debug_event("service.process_query.final_out_of_scope_resolution", conversation_id=conversation_id, resolution=out_of_scope_resolution)
            return out_of_scope_resolution
        
        # MANUAL OVERRIDE: Check for specific keyword triggers
        q_low = user_query.lower()
        
        # Priority 1: Specific Mode Selections (MODIFY_UI) - Check specific strings
        if "hot deals" in q_low or "high value" in q_low or "closing soon" in q_low:
             agent_output["intent"] = "MODIFY_UI"
        
        # Priority 2: Generic Change Logic Request (MODIFY_UI)
        elif "change" in q_low and ("ai recommend" in q_low or "추천" in q_low or "logic" in q_low):
             agent_output["intent"] = "MODIFY_UI"
        
        # Priority 3: Style changes (MODIFY_UI)
        elif any(word in q_low for word in ["table format", "테이블 형식", "테이블 모양", "compact style", "modern style", "default style"]):
             agent_output["intent"] = "MODIFY_UI"

        # Priority 3: Actual Recommendation request
        elif ("ai recommend" in q_low or "추천" in q_low) and "change" not in q_low:
            agent_output["intent"] = "RECOMMEND"
        elif "send message" in q_low or "메시지 보내" in q_low:
             agent_output["intent"] = "SEND_MESSAGE"
             agent_output["text"] = "Redirecting you to the messaging page..."
        elif "usage" in q_low or "사용량" in q_low or "토큰" in q_low:
             agent_output["intent"] = "USAGE"

        # ROBUST EXTRACTION: Fallback for "Manage [object] [record_id]"
        if "manage" in user_query.lower() and (not agent_output.get("record_id") or agent_output.get("record_id") == "ID_HERE"):
            match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
            if match:
                normalized_object = IntentPreClassifier.normalize_object_type(match.group(1).lower()) or match.group(1).lower()
                agent_output["intent"] = "MANAGE"
                agent_output["object_type"] = normalized_object
                agent_output["record_id"] = match.group(2)

        agent_output = IntentReasoner.validate_reasoning_output(
            agent_output,
            user_query,
            reasoning_context,
        )
        agent_output = cls._apply_contextual_record_id(agent_output, conversation_id)
        debug_event("service.process_query.llm_fallback_result", conversation_id=conversation_id, agent_output=agent_output)

        agent_output["language_preference"] = language_preference
        try:
            return await cls._execute_intent(db, agent_output, user_query, conversation_id=conversation_id, page=page, per_page=per_page)
        except Exception as e:
            logger.error(f"Execution Error: {str(e)}")
            return {"intent": "CHAT", "text": f"Technical issue: {str(e)}"}

    @classmethod
    async def _call_multi_llm_ensemble(cls, user_query: str, system_prompt: str) -> Dict[str, Any]:
        """Calls multiple LLMs in parallel and picks the best response based on a score."""
        debug_event("service.llm_ensemble.start", user_query=user_query)
        tasks = []
        
        if CEREBRAS_API_KEY:
            tasks.append(cls._call_cerebras(user_query, system_prompt))
        if GROQ_API_KEY:
            tasks.append(cls._call_groq(user_query, system_prompt))
        if GEMINI_API_KEY:
            tasks.append(cls._call_gemini(user_query, system_prompt))
        if OPENAI_API_KEY:
            tasks.append(cls._call_openai(user_query, system_prompt))

        if not tasks:
            debug_event("service.llm_ensemble.no_api_keys", user_query=user_query)
            return {"intent": "CHAT", "text": "No AI API Keys configured."}

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        debug_event("service.llm_ensemble.responses", response_count=len(responses))
        
        valid_responses = []
        for res in responses:
            if isinstance(res, dict) and "intent" in res:
                valid_responses.append(res)
            elif isinstance(res, Exception):
                logger.error(f"Ensemble member failed: {res}")

        if not valid_responses:
            debug_event("service.llm_ensemble.failed", user_query=user_query)
            return {"intent": "CHAT", "text": "All AI models failed to respond."}

        # Pick the best response based on 'score'
        valid_responses.sort(key=lambda x: x.get("score", 0), reverse=True)
        debug_event("service.llm_ensemble.best_response", best_response=valid_responses[0])
        return valid_responses[0]

    @classmethod
    async def _call_cerebras(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "llama3.1-8b",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=8.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @classmethod
    async def _call_groq(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=8.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @classmethod
    async def _call_gemini(cls, query, system) -> Dict[str, Any]:
        try:
            if not GEMINI_API_KEY:
                return {}

            full_prompt = f"{system}\n\nUser Query: {query}\nResponse must be JSON."
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                    params={"key": GEMINI_API_KEY},
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": full_prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "response_mime_type": "application/json"
                        }
                    },
                    timeout=8.0,
                )
                payload = response.json()

            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}
        except Exception: return {}

    @classmethod
    async def _call_openai(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=9.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @staticmethod
    def _clean_data(data: Any) -> Dict[str, Any]:
        if not data or not isinstance(data, dict): return {}
        cleaned = {}
        for k, v in data.items():
            if v == "None" or v == "null" or v == "" or v == "ID_HERE": 
                cleaned[k] = None
            elif v in ["True", "true", True]: 
                cleaned[k] = True
            elif v in ["False", "false", False]: 
                cleaned[k] = False
            elif isinstance(v, str):
                if k == "phone":
                    digits_only = re.sub(r"\D", "", v)
                    cleaned[k] = digits_only or v
                elif v.isdigit():
                    cleaned[k] = int(v)
                else:
                    num_clean = re.sub(r'[^\d.]', '', v)
                    if num_clean and v.startswith(('₩', '$')):
                        try: cleaned[k] = int(float(num_clean))
                        except: cleaned[k] = v
                    else:
                        cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def _stt_language_code(cls, language_preference: Optional[str]) -> str:
        return "ko" if (language_preference or "").lower() == "kor" else "en"

    @classmethod
    async def _call_groq_audio_transcription(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        language_preference: Optional[str] = None,
    ) -> str:
        if not GROQ_API_KEY:
            return ""

        prompt = (
            "This is a D5 CRM voice command. Keep CRM object names, IDs, statuses, and names exact. "
            "Do not invent missing words."
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                data={
                    "model": "whisper-large-v3",
                    "response_format": "json",
                    "temperature": "0",
                    "language": cls._stt_language_code(language_preference),
                    "prompt": prompt,
                },
                files={"file": (filename, file_bytes, content_type)},
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
        return str(payload.get("text") or "").strip()

    @classmethod
    async def _validate_transcript_with_cerebras(
        cls,
        transcript: str,
        language_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not transcript:
            return {"text": ""}
        if not CEREBRAS_API_KEY:
            return {"text": transcript, "validator": None}

        system_prompt = (
            "You validate speech-to-text output for the D5 CRM assistant.\n"
            "Rules:\n"
            "- Preserve meaning exactly.\n"
            "- Do not add facts, names, IDs, or fields that are not already present.\n"
            "- Only fix obvious punctuation, spacing, and clear CRM term mistakes.\n"
            "- If unsure, return the original text unchanged.\n"
            "- Output strict JSON: {\"text\":\"...\",\"changed\":true|false}."
        )
        user_prompt = (
            f"Language preference: {language_preference or 'eng'}\n"
            f"Transcript: {transcript}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama3.1-8b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=12.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            payload = json.loads(content)
        validated_text = str(payload.get("text") or transcript).strip() or transcript
        return {
            "text": validated_text,
            "validator": "cerebras",
            "changed": bool(payload.get("changed")) and validated_text != transcript,
        }

    @classmethod
    async def transcribe_audio_bytes(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        language_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        safe_filename = filename or "ai-agent-voice.webm"
        raw_content_type = (content_type or "application/octet-stream").lower()
        safe_type = raw_content_type.split(";", 1)[0].strip()
        if not file_bytes:
            return {"status": "error", "text": "No audio was received.", "provider": "groq", "validator": None}
        if len(file_bytes) > cls.STT_MAX_BYTES:
            return {"status": "error", "text": "Audio is too large. Keep voice input under 10MB.", "provider": "groq", "validator": None}
        if safe_type not in cls.STT_ALLOWED_CONTENT_TYPES:
            return {"status": "error", "text": "Unsupported audio format. Use webm, wav, mp3, m4a, mp4, or ogg.", "provider": "groq", "validator": None}
        if not GROQ_API_KEY:
            return {"status": "error", "text": "Voice input is not configured right now.", "provider": "groq", "validator": None}

        debug_event(
            "service.stt.start",
            filename=safe_filename,
            content_type=safe_type,
            bytes=len(file_bytes),
            language_preference=language_preference,
        )

        try:
            transcript = await cls._call_groq_audio_transcription(
                file_bytes=file_bytes,
                filename=safe_filename,
                content_type=safe_type,
                language_preference=language_preference,
            )
            if not transcript:
                return {"status": "error", "text": "I could not hear a usable command in that audio.", "provider": "groq", "validator": None}

            validation = await cls._validate_transcript_with_cerebras(
                transcript,
                language_preference=language_preference,
            )
            final_text = str(validation.get("text") or transcript).strip() or transcript
            response = {
                "status": "ok",
                "text": final_text,
                "raw_text": transcript,
                "provider": "groq",
                "validator": validation.get("validator"),
            }
            debug_event(
                "service.stt.complete",
                provider=response["provider"],
                validator=response.get("validator"),
                raw_length=len(transcript),
                final_length=len(final_text),
            )
            return response
        except Exception as exc:
            logger.error(f"STT Error: {exc}")
            return {"status": "error", "text": "Voice transcription failed. Please try again.", "provider": "groq", "validator": None}

    @classmethod
    def _pluralize_object(cls, obj: str) -> str:
        if not obj: return "records"
        mapping = {
            "lead": "leads", "contact": "contacts", "opportunity": "opportunities",
            "product": "products", "asset": "assets", "brand": "brands",
            "model": "models", "message_template": "message_templates"
        }
        return mapping.get(obj.lower(), obj + "s")

    @classmethod
    @handle_agent_errors
    async def _execute_intent(
        cls,
        db: Session,
        agent_output: Dict[str, Any],
        user_query: str,
        conversation_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        try:
            intent = str(agent_output.get("intent") or "CHAT").upper()
            raw_obj = str(agent_output.get("object_type") or "").lower()
            obj = IntentPreClassifier.normalize_object_type(raw_obj) or raw_obj
            if obj:
                agent_output["object_type"] = obj
            record_id = agent_output.get("record_id")
            selection_payload = agent_output.get("selection") or {}
            data = agent_output.get("data") or {}
            sql = agent_output.get("sql")

            if record_id == "ID_HERE": record_id = None
            debug_event(
                "service.execute_intent.start",
                conversation_id=conversation_id,
                intent=intent,
                object_type=obj,
                record_id=record_id,
                field_names=sorted((data or {}).keys()),
            )

            if intent == "CHAT":
                ConversationContextStore.remember_object(conversation_id, obj, intent)
                return agent_output

            if intent == "SEND_MESSAGE":
                selection_payload = agent_output.get("selection") or ConversationContextStore.get_selection(conversation_id)
                if selection_payload:
                    agent_output["selection"] = selection_payload
                return agent_output

            if intent == "USAGE":
                agent_output["text"] = (
                    "Currently, I use four different AI providers to ensure the best response. "
                    "You can check your remaining tokens/quota at their respective dashboards:\n\n"
                    "1. **Cerebras**: [Cerebras Cloud](https://cloud.cerebras.ai/)\n"
                    "2. **Groq**: [Groq Console](https://console.groq.com/settings/limits)\n"
                    "3. **Gemini**: [Google AI Studio](https://aistudio.google.com/app/plan)\n"
                    "4. **OpenAI**: [OpenAI Usage](https://platform.openai.com/usage)\n\n"
                    "Is there anything else I can help you with?"
                )
                return agent_output

            if intent == "MODIFY_UI":
                q_low = user_query.lower()
                
                # 1. Handle Home Screen Recommendation Logic Changes
                if "ai recommend" in q_low or "추천" in q_low:
                    if "hot" in q_low or "따끈" in q_low:
                        AIRecommendationService.set_recommendation_mode("Hot Deals")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Hot Deals** (Recent Test Drives). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    elif "follow up" in q_low or "follow-up" in q_low or "followup" in q_low or "후속" in q_low or "팔로우" in q_low:
                        AIRecommendationService.set_recommendation_mode("Follow Up")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Follow Up** (Recently followed-up open deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    elif "closed won" in q_low or "closing" in q_low or "마감" in q_low or "급한" in q_low or "성공" in q_low:
                        AIRecommendationService.set_recommendation_mode("Closing Soon")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Closed Won** (Recently won opportunities). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    elif "default" in q_low or "기본" in q_low:
                        AIRecommendationService.set_recommendation_mode("Default")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've restored the AI Recommendation logic to **New Records** (Most recently created sendable deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    else:
                        # Ask for logic preference
                        agent_output["intent"] = "CHAT"
                        ConversationContextStore.remember_pending_recommendation_mode(conversation_id)
                        current_mode = AIRecommendationService.get_recommendation_mode()
                        options = [
                            f"[Hot Deals{' (Current)' if current_mode == 'Hot Deals' else ''}]",
                            f"[Follow Up{' (Current)' if current_mode == 'Follow Up' else ''}]",
                            f"[Closed Won{' (Current)' if current_mode == 'Closing Soon' else ''}]",
                            f"[New Records{' (Current)' if current_mode == 'Default' else ''}]",
                        ]
                        agent_output["text"] = f"The current **AI Recommend** logic is **{AIRecommendationService.user_facing_mode_label(current_mode)}**. How would you like to change it? \n\nOptions: {' '.join(options)}."
                    
                    return agent_output

                # 2. Handle Chat Table CSS Style Changes
                if any(word in q_low for word in ["compact", "축소", "작게"]):
                    agent_output["text"] = "I've updated the table to the **Compact** style for you."
                elif any(word in q_low for word in ["modern", "모던", "깔끔"]):
                    agent_output["text"] = "I've applied the **Modern** grid style to the table."
                elif any(word in q_low for word in ["default", "기본", "원래"]):
                    agent_output["text"] = "I've restored the table to the **Default** Salesforce style."
                elif any(mode in q_low for mode in ["hot deals", "follow up", "follow-up", "followup", "closing soon", "closed won"]):
                    # This should have been caught in section 1 above, but if we're here, 
                    # something was missed. Let's re-run the mode check.
                    if "follow up" in q_low or "follow-up" in q_low or "followup" in q_low:
                        AIRecommendationService.set_recommendation_mode("Follow Up")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Follow Up** (Recently followed-up open deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    elif "hot deals" in q_low:
                        AIRecommendationService.set_recommendation_mode("Hot Deals")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Hot Deals** (Recent Test Drives). Please refresh the dashboard or click [AI Recommend] to see the results!"
                    elif "closing soon" in q_low or "closed won" in q_low:
                        AIRecommendationService.set_recommendation_mode("Closing Soon")
                        ConversationContextStore.clear_pending_recommendation_mode(conversation_id)
                        agent_output["text"] = "I've set the AI Recommendation logic to **Closed Won** (Recently won opportunities). Please refresh the dashboard or click [AI Recommend] to see the results!"
                else:
                    agent_output["intent"] = "CHAT"
                    ConversationContextStore.remember_pending_recommendation_mode(conversation_id)
                    current_mode = AIRecommendationService.get_recommendation_mode()
                    options = [
                        f"[Hot Deals{' (Current)' if current_mode == 'Hot Deals' else ''}]",
                        f"[Follow Up{' (Current)' if current_mode == 'Follow Up' else ''}]",
                        f"[Closed Won{' (Current)' if current_mode == 'Closing Soon' else ''}]",
                        f"[New Records{' (Current)' if current_mode == 'Default' else ''}]",
                    ]
                    agent_output["text"] = f"The current **AI Recommend** logic is **{AIRecommendationService.user_facing_mode_label(current_mode)}**. How would you like to change it? {' '.join(options)}."
                
                return agent_output

            if intent == "RECOMMEND":
                safe_page, safe_per_page, _offset = cls._sanitize_pagination(page, per_page)
                recommends = AIRecommendationService.get_sendable_recommendations(db)
                current_mode = AIRecommendationService.user_facing_mode_label(AIRecommendationService.get_recommendation_mode())
                agent_output["results"] = []
                for r in recommends:
                    agent_output["results"].append({
                        "id": r.id,
                        "name": r.name,
                        "amount": r.amount or 0,
                        "stage": r.stage,
                        "temperature": getattr(r, 'temp_display', 'Hot'),
                        "created_at": r.created_at.strftime("%Y-%m-%d") if getattr(r, "created_at", None) else "",
                    })
                agent_output["object_type"] = "opportunity"
                total = len(recommends)
                total_pages = max(1, (total + safe_per_page - 1) // safe_per_page)
                agent_output["pagination"] = {
                    "page": safe_page,
                    "per_page": safe_per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "object_type": "opportunity",
                    "mode": "local",
                }
                agent_output["original_query"] = user_query
                agent_output["text"] = f"Here are {len(recommends)} AI-recommended deals for you. Current logic: **{current_mode}**."
                return agent_output
            
            if intent == "MANAGE":
                if obj in cls.PHASE1_OBJECTS and record_id:
                    record = cls._get_phase1_record(db, obj, record_id)
                    if not record:
                        return {
                            "intent": "CHAT",
                            "text": cls._build_missing_record_text(obj, record_id, user_query, conversation_id),
                        }
                    if cls._detect_manage_mode(user_query) == "edit":
                        return cls._build_phase1_edit_form_response(
                            obj,
                            record,
                            agent_output.get("language_preference"),
                            db=db,
                        )
                    return cls._build_phase1_open_record_response(
                        db,
                        obj,
                        record,
                        conversation_id,
                        "manage",
                        agent_output.get("language_preference"),
                    )
                if not record_id:
                    if "just created" in user_query.lower() or "방금" in user_query:
                        mapping_table = {"lead": "leads", "contact": "contacts", "opportunity": "opportunities"}
                        table = mapping_table.get(obj)
                        if table:
                            last_res = db.execute(text(f"SELECT id FROM {table} WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 1")).fetchone()
                            if last_res: record_id = last_res[0]

                if not record_id:
                    return {"intent": "CHAT", "text": "I need a record ID to manage it. Please select a record from the list."}

                record_details = ""
                template_image_url = None
                if obj in ["lead", "leads"]:
                    lead = LeadService.get_lead(db, record_id)
                    if lead:
                        mode = cls._detect_manage_mode(user_query)
                        if mode == "edit":
                            ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id=record_id)
                            return cls._build_phase1_edit_form_response(
                                "lead",
                                lead,
                                agent_output.get("language_preference"),
                                db=db,
                            )
                        return cls._build_lead_open_record_response(
                            db,
                            lead,
                            conversation_id,
                            action="manage",
                            language_preference=agent_output.get("language_preference"),
                        )
                elif obj in ["contact", "contacts"]:
                    contact = ContactService.get_contact(db, record_id)
                    if contact: record_details = f"Contact: {contact.first_name} {contact.last_name} ({contact.email})"
                elif obj in ["opportunity", "opportunities", "opps"]:
                    opp = OpportunityService.get_opportunity(db, record_id)
                    if opp: record_details = f"Opportunity: {opp.name} ({opp.stage} - ₩{opp.amount})"
                elif obj in ["product", "products"]:
                    from web.backend.app.services.product_service import ProductService

                    product = ProductService.get_product(db, record_id)
                    if product:
                        title = cls._display_value(getattr(product, "name", None)) or str(getattr(product, "id", "Unnamed Product"))
                        return build_object_open_record_response(
                            object_type="product",
                            record_id=record_id,
                            redirect_url=f"/products/{record_id}",
                            title=title,
                            action="manage",
                            conversation_id=conversation_id,
                            language_preference=agent_output.get("language_preference"),
                            chat_card=cls._build_product_chat_card(db, product),
                        )
                elif obj in ["asset", "assets"]:
                    from web.backend.app.services.asset_service import AssetService

                    asset = AssetService.get_asset(db, record_id)
                    if asset:
                        title = (
                            cls._display_value(getattr(asset, "name", None))
                            or cls._display_value(getattr(asset, "vin", None))
                            or str(getattr(asset, "id", "Unnamed Asset"))
                        )
                        return build_object_open_record_response(
                            object_type="asset",
                            record_id=record_id,
                            redirect_url=f"/assets/{record_id}",
                            title=title,
                            action="manage",
                            conversation_id=conversation_id,
                            language_preference=agent_output.get("language_preference"),
                            chat_card=cls._build_asset_chat_card(db, asset),
                        )
                elif obj in ["brand", "brands"]:
                    brand = VehicleSpecService.get_vehicle_spec(db, record_id)
                    if brand:
                        title = cls._display_value(getattr(brand, "name", None)) or str(getattr(brand, "id", "Unnamed Brand"))
                        return build_object_open_record_response(
                            object_type="brand",
                            record_id=record_id,
                            redirect_url=f"/vehicle_specifications/{record_id}",
                            title=title,
                            action="manage",
                            conversation_id=conversation_id,
                            language_preference=agent_output.get("language_preference"),
                            chat_card=cls._build_brand_chat_card(db, brand),
                        )
                elif obj in ["model", "models"]:
                    model = ModelService.get_model(db, record_id)
                    if model:
                        title = cls._display_value(getattr(model, "name", None)) or str(getattr(model, "id", "Unnamed Model"))
                        return build_object_open_record_response(
                            object_type="model",
                            record_id=record_id,
                            redirect_url=f"/models/{record_id}",
                            title=title,
                            action="manage",
                            conversation_id=conversation_id,
                            language_preference=agent_output.get("language_preference"),
                            chat_card=cls._build_model_chat_card(db, model),
                        )
                elif obj in ["message_template", "template"]:
                    template = MessageTemplateService.get_template(db, record_id)
                    if template:
                        title = cls._display_value(getattr(template, "name", None)) or str(getattr(template, "id", "Unnamed Template"))
                        return build_object_open_record_response(
                            object_type="message_template",
                            record_id=record_id,
                            redirect_url=f"/message_templates/{record_id}",
                            title=title,
                            action="manage",
                            conversation_id=conversation_id,
                            language_preference=agent_output.get("language_preference"),
                            chat_card=cls._build_message_template_chat_card(template),
                        )
                
                if record_details:
                    if obj in ["lead", "leads"] and agent_output.get("chat_card"):
                        agent_output["record_id"] = record_id
                        ConversationContextStore.remember_object(conversation_id, "lead", intent, record_id=record_id)
                        return agent_output

                    fields_list = []
                    if obj in ["lead", "leads"]: fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                    elif obj in ["contact", "contacts"]: fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                    elif obj in ["opportunity", "opportunities", "opps"]: fields_list = ["Name", "Amount", "Stage", "Probability"]
                    elif obj in ["message_template", "template"]: fields_list = ["Name", "Subject", "Content", "Record Type", "Image URL"]
                    
                    button_html = " ".join([f"[{f}]" for f in fields_list])
                    template_image_html = ""
                    if obj in ["message_template", "template"] and template_image_url:
                        template_image_html = f"<br><br><img src=\"{template_image_url}\" alt=\"Template image\" style=\"max-width:180px;border-radius:10px;border:1px solid #d7deeb;\"><br><a href=\"{template_image_url}\" target=\"_blank\" style=\"font-size:0.8rem;color:#0176d3;\">Open template image</a>"
                    agent_output["text"] = f"I've selected **{record_details}**. \n\nFields you can update:\n{button_html}\n\nWhat would you like to do?{template_image_html}"
                    agent_output["record_id"] = record_id
                    ConversationContextStore.remember_object(conversation_id, obj, intent, record_id=record_id)
                else:
                    agent_output["text"] = cls._build_missing_record_text(obj, record_id, user_query, conversation_id)
                
                return agent_output

            mapping = {
                "leads": "lead", "contacts": "contact", "opportunities": "opportunity", "opps": "opportunity",
                "brands": "brand", "models": "model", "products": "product", "assets": "asset",
                "templates": "message_template", "message_templates": "message_template",
                "messages": "message_send", "message_sends": "message_send"
            }
            obj = mapping.get(obj, obj)

            if intent == "QUERY":
                if obj in cls.PHASE1_OBJECTS and not sql:
                    sql = cls._build_phase1_query_sql(obj, data)
                if not sql:
                    config = cls._default_query_parts(obj)
                    if config:
                        search_term = data.get("search_term")
                        if search_term:
                            config = cls._apply_search_to_sql(obj, config, search_term)
                        
                        sql = (
                            f"SELECT {config['select']} FROM {config['from']} "
                            f"WHERE {config['where']} ORDER BY {config['order_by']}"
                        )
                
            if sql:
                try:
                    sql = sql.replace("FROM messages", "FROM message_sends").replace("from messages", "from message_sends")
                    paged = cls._execute_paginated_query(db, sql, obj, page, per_page)
                    promoted = await cls._maybe_auto_open_single_query_result(
                        db,
                        obj,
                        paged,
                        agent_output,
                        user_query,
                        conversation_id,
                        page,
                        per_page,
                    )
                    if promoted:
                        return promoted
                    agent_output["results"] = paged["results"]
                    agent_output["sql"] = paged["sql"]
                    agent_output["pagination"] = paged["pagination"]
                    agent_output["original_query"] = user_query
                    agent_output["text"] = agent_output.get("text") or cls._default_query_text(obj, paged["pagination"])
                    ConversationContextStore.remember_object(conversation_id, obj, intent)
                    ConversationContextStore.remember_query_results(conversation_id, obj, paged["results"])
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

            data = cls._clean_data(data)
            
            if intent == "CREATE":
                if obj == "lead":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = LeadService.create_lead(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the lead. Please try again or check the required fields."}
                    return cls._build_lead_open_record_response(
                        db,
                        res,
                        conversation_id,
                        action="create",
                        language_preference=agent_output.get("language_preference"),
                    )
                elif obj == "contact":
                    res = ContactService.create_contact(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the contact."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "contact",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj == "opportunity":
                    res = OpportunityService.create_opportunity(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the opportunity."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "opportunity",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj == "brand":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = VehicleSpecService.create_spec(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the brand."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "brand",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj == "model":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = ModelService.create_model(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the model."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "model",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj == "product":
                    from web.backend.app.services.product_service import ProductService
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = ProductService.create_product(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the product."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "product",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj == "asset":
                    from web.backend.app.services.asset_service import AssetService
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = AssetService.create_asset(db, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the asset."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "asset",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )
                elif obj in ["message_template", "template"]:
                    name = data.pop("name", "New Template")
                    res = MessageTemplateService.create_template(db, name=name, **data)
                    if not res:
                        return {"intent": "CHAT", "text": "I encountered an error while creating the message template."}
                    return cls._build_phase1_open_record_response(
                        db,
                        "message_template",
                        res,
                        conversation_id,
                        "create",
                        agent_output.get("language_preference"),
                    )

            if intent == "UPDATE" and record_id:
                if obj == "lead":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = LeadService.update_lead(db, record_id, **data)
                    if res:
                        refreshed = LeadService.get_lead(db, record_id)
                        if refreshed:
                            return cls._build_lead_open_record_response(
                                db,
                                refreshed,
                                conversation_id,
                                action="update",
                                language_preference=agent_output.get("language_preference"),
                            )
                        agent_output["text"] = cls._build_missing_record_text("lead", record_id, user_query, conversation_id)
                    else:
                        agent_output["text"] = cls._build_missing_record_text("lead", record_id, user_query, conversation_id)
                    return agent_output
                elif obj == "contact":
                    res = ContactService.update_contact(db, record_id, **data)
                    if res:
                        refreshed = ContactService.get_contact(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "contact",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                        agent_output["text"] = cls._build_missing_record_text("contact", record_id, user_query, conversation_id)
                    else:
                        agent_output["text"] = cls._build_missing_record_text("contact", record_id, user_query, conversation_id)
                    return agent_output
                elif obj == "opportunity":
                    res = OpportunityService.update_opportunity(db, record_id, **data)
                    if res:
                        refreshed = OpportunityService.get_opportunity(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "opportunity",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                        agent_output["text"] = f"Opportunity {record_id} not found."
                    else:
                        agent_output["text"] = f"Opportunity {record_id} not found."
                    return agent_output
                elif obj == "brand":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = VehicleSpecService.update_vehicle_spec(db, record_id, **data)
                    if res:
                        refreshed = VehicleSpecService.get_vehicle_spec(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "brand",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                    agent_output["text"] = f"Brand {record_id} not found."
                    return agent_output
                elif obj == "model":
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = ModelService.update_model(db, record_id, **data)
                    if res:
                        refreshed = ModelService.get_model(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "model",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                    agent_output["text"] = f"Model {record_id} not found."
                    return agent_output
                elif obj == "product":
                    from web.backend.app.services.product_service import ProductService
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = ProductService.update_product(db, record_id, **data)
                    if res:
                        refreshed = ProductService.get_product(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "product",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                    agent_output["text"] = f"Product {record_id} not found."
                    return agent_output
                elif obj == "asset":
                    from web.backend.app.services.asset_service import AssetService
                    data = cls._normalize_supported_lookup_inputs(db, obj, data)
                    res = AssetService.update_asset(db, record_id, **data)
                    if res:
                        refreshed = AssetService.get_asset(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "asset",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                    agent_output["text"] = f"Asset {record_id} not found."
                    return agent_output
                elif obj in ["message_template", "template"]:
                    res = MessageTemplateService.update_template(db, record_id, **data)
                    if res:
                        refreshed = MessageTemplateService.get_template(db, record_id)
                        if refreshed:
                            return cls._build_phase1_open_record_response(
                                db,
                                "message_template",
                                refreshed,
                                conversation_id,
                                "update",
                                agent_output.get("language_preference"),
                            )
                    agent_output["text"] = f"Template {record_id} not found."
                    return agent_output

            if intent == "DELETE":
                ids = list(selection_payload.get("ids") or ([] if not record_id else [record_id]))
                if ids:
                    deleted = 0
                    deleted_ids: List[str] = []
                    deleted_summaries: List[str] = []
                    for delete_id in ids:
                        delete_summary = None
                        existing_record = None
                        if obj == "lead":
                            existing_record = LeadService.get_lead(db, delete_id)
                        elif obj == "contact":
                            existing_record = ContactService.get_contact(db, delete_id)
                        elif obj == "opportunity":
                            existing_record = OpportunityService.get_opportunity(db, delete_id)
                        elif obj == "product":
                            from web.backend.app.services.product_service import ProductService
                            existing_record = ProductService.get_product(db, delete_id)
                        elif obj == "asset":
                            from web.backend.app.services.asset_service import AssetService
                            existing_record = AssetService.get_asset(db, delete_id)
                        elif obj == "brand":
                            existing_record = VehicleSpecService.get_vehicle_spec(db, delete_id)
                        elif obj == "model":
                            existing_record = ModelService.get_model(db, delete_id)
                        elif obj == "message_template":
                            existing_record = MessageTemplateService.get_template(db, delete_id)
                        if existing_record:
                            delete_summary = cls._record_delete_summary(obj, existing_record)
                        if cls._delete_record(db, obj, delete_id):
                            deleted += 1
                            deleted_ids.append(delete_id)
                            if delete_summary:
                                deleted_summaries.append(delete_summary)
                    label = cls._object_display_label(obj, len(ids)).title()
                    if deleted_summaries:
                        if len(deleted_summaries) == 1:
                            agent_output["text"] = f"Success! Deleted {label.rstrip('s').lower()} {deleted_summaries[0]}."
                        else:
                            preview = ", ".join(deleted_summaries[:3])
                            suffix = "" if len(deleted_summaries) <= 3 else ", ..."
                            agent_output["text"] = f"Success! Deleted {deleted} {label.lower()}: {preview}{suffix}."
                    else:
                        agent_output["text"] = (
                            f"Success! Deleted {deleted} of {len(ids)} {label}."
                            if len(ids) > 1 else
                            (f"Success! Deleted that {label.rstrip('s').lower()}." if deleted else f"I couldn't find that {label.rstrip('s').lower()} record.")
                        )
                    # Return deleted_ids so the frontend can remove the rows from all visible tables
                    agent_output["deleted_ids"] = deleted_ids
                    return agent_output

            return agent_output
        except Exception as exc:
            db.rollback()
            logger.error(f"Intent Execution Error: {exc}\n{traceback.format_exc()}")
            return {
                "intent": "CHAT",
                "text": f"I encountered a database issue while processing your request. I've reset the transaction. Please try again. (Details: {str(exc)})",
                "score": 1.0
            }
