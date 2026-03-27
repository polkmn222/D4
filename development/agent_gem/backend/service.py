import os
import json
import logging
import re
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import services from the main app
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.asset_service import AssetService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.message.backend.services.message_service import MessageService
from web.backend.app.utils.error_handler import handle_agent_errors

from ai_agent.llm.backend.conversation_context import ConversationContextStore
from agent_gem.backend.llm import AgentGemLLMService

load_dotenv()

logger = logging.getLogger(__name__)

class AgentGemService:
    OBJECT_MAPPING = {
        "lead": LeadService,
        "contact": ContactService,
        "opportunity": OpportunityService,
        "brand": VehicleSpecService,
        "model": ModelService,
        "product": ProductService,
        "asset": AssetService,
        "message_template": MessageTemplateService,
        "template": MessageTemplateService,
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
        """
        Process user query using LLM and execute the detected intent.
        """
        # Remember selection context
        if selection:
            ConversationContextStore.remember_selection(conversation_id, selection)

        # 1. Reason with LLM to get intent and data
        system_prompt = cls._get_system_prompt(language_preference)
        agent_output = await AgentGemLLMService.get_intent(user_query, system_prompt)
        
        # 2. Apply context if needed (e.g. "update it" refers to last record)
        agent_output = cls._apply_context(agent_output, conversation_id)

        # 3. Execute intent
        try:
            return await cls._execute_intent(
                db, 
                agent_output, 
                user_query, 
                conversation_id, 
                page, 
                per_page, 
                language_preference
            )
        except Exception as e:
            logger.error(f"Execution Error in AgentGem: {str(e)}")
            return {"intent": "CHAT", "text": f"Sorry, I encountered an error: {str(e)}"}

    @classmethod
    def _get_system_prompt(cls, language_preference: Optional[str]) -> str:
        # Simplified version of the prompt from AiAgentService but adapted for AgentGem
        return f"""
        You are "Agent Gem", a helpful AI assistant for an Automotive CRM.
        You can handle CRUD operations for: Lead, Contact, Opportunity, Brand, Model, Product, Asset, Message Template.
        
        INTENTS:
        - QUERY: List records (all leads, recent contacts, etc.)
        - CREATE: Add a new record.
        - UPDATE: Modify an existing record.
        - DELETE: Remove a record (ask for confirmation if not explicitly provided).
        - READ: Show details of a specific record.
        - CHAT: General conversation or asking for missing info.
        
        RESPONSE FORMAT (JSON):
        {{
            "intent": "QUERY" | "CREATE" | "UPDATE" | "DELETE" | "READ" | "CHAT",
            "object_type": "lead" | "contact" | "opportunity" | "brand" | "model" | "product" | "asset" | "message_template",
            "record_id": "UUID or ID",
            "data": {{ "field": "value" }},
            "text": "Human-like response text",
            "sql": "SQL query for QUERY intent (if applicable)",
            "score": 0.0 to 1.0
        }}
        
        MANDATORY RULES:
        - Detect user language (English or Korean) and respond in the same language.
        - UI preference: {language_preference or 'auto'}.
        - For CREATE/UPDATE, extract as many fields as possible.
        - For READ/UPDATE/DELETE, try to identify the record ID.
        - If multiple records might match a query, use QUERY to list them.
        """

    @classmethod
    def _apply_context(cls, agent_output: Dict[str, Any], conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return agent_output

        context = ConversationContextStore.get_context(conversation_id)
        intent = agent_output.get("intent")
        
        # If intent is UPDATE/READ/DELETE and no record_id, use last record_id
        if intent in ["UPDATE", "READ", "DELETE"] and not agent_output.get("record_id"):
            agent_output["record_id"] = context.get("last_record_id")
            if not agent_output.get("object_type"):
                agent_output["object_type"] = context.get("last_object")
        
        return agent_output

    @classmethod
    async def _execute_intent(
        cls,
        db: Session,
        agent_output: Dict[str, Any],
        user_query: str,
        conversation_id: Optional[str],
        page: int,
        per_page: int,
        language_preference: Optional[str]
    ) -> Dict[str, Any]:
        intent = agent_output.get("intent", "CHAT").upper()
        obj = agent_output.get("object_type", "").lower()
        record_id = agent_output.get("record_id")
        data = agent_output.get("data") or {}

        if intent == "CHAT":
            return agent_output

        if intent == "QUERY":
            return await cls._handle_query(db, obj, agent_output, user_query, page, per_page)

        if intent == "CREATE":
            return await cls._handle_create(db, obj, data, conversation_id, language_preference)

        if intent == "READ":
            return await cls._handle_read(db, obj, record_id, conversation_id, language_preference)

        if intent == "UPDATE":
            return await cls._handle_update(db, obj, record_id, data, conversation_id, language_preference)

        if intent == "DELETE":
            return await cls._handle_delete(db, obj, record_id, conversation_id, language_preference)

        return agent_output

    @classmethod
    async def _handle_query(cls, db: Session, obj: str, agent_output: Dict[str, Any], user_query: str, page: int, per_page: int) -> Dict[str, Any]:
        # Reuse SQL generation or use a default list query
        from ai_agent.ui.backend.service import AiAgentService
        sql = agent_output.get("sql")
        if not sql:
            config = AiAgentService._default_query_parts(obj)
            if config:
                sql = f"SELECT {config['select']} FROM {config['from']} WHERE {config['where']} ORDER BY {config['order_by']}"
        
        if sql:
            paged = AiAgentService._execute_paginated_query(db, sql, obj, page, per_page)
            agent_output["results"] = paged["results"]
            agent_output["pagination"] = paged["pagination"]
            return agent_output
        
        return {"intent": "CHAT", "text": f"I don't know how to list {obj} yet."}

    @classmethod
    async def _handle_create(cls, db: Session, obj: str, data: Dict[str, Any], conversation_id: Optional[str], lang: Optional[str]) -> Dict[str, Any]:
        from ai_agent.ui.backend.service import AiAgentService
        
        # Check mandatory fields (simplified)
        if obj == "lead" and not data.get("last_name"):
            return {"intent": "CHAT", "text": "I need a last name to create a lead. What is the customer's last name?"}

        # Normalize lookups if lead
        if obj == "lead":
            data = AiAgentService._normalize_lead_lookup_inputs(db, data)

        # Call service
        service = cls.OBJECT_MAPPING.get(obj)
        if not service:
             return {"intent": "CHAT", "text": f"Creation for {obj} is not supported yet."}
        
        # Determine create method name
        method_name = f"create_{obj}"
        if obj == "brand": method_name = "create_spec"
        if obj == "message_template" or obj == "template": 
            method_name = "create_template"
            if "name" not in data: data["name"] = "New Template"
        
        create_method = getattr(service, method_name, None)
        if not create_method:
             return {"intent": "CHAT", "text": f"Could not find creation method for {obj}."}
        
        try:
            res = create_method(db, **data)
            if res:
                record_id = str(res.id)
                ConversationContextStore.remember_created(conversation_id, obj, record_id)
                # Success -> Redirect to READ view as requested by user
                return await cls._handle_read(db, obj, record_id, conversation_id, lang, prefix="Successfully created! ")
        except Exception as e:
            return {"intent": "CHAT", "text": f"Error during creation: {str(e)}"}

        return {"intent": "CHAT", "text": "Failed to create the record."}

    @classmethod
    async def _handle_read(cls, db: Session, obj: str, record_id: str, conversation_id: Optional[str], lang: Optional[str], prefix: str = "") -> Dict[str, Any]:
        if not record_id:
            return {"intent": "CHAT", "text": f"I need a record ID to show the {obj}."}

        from ai_agent.ui.backend.service import AiAgentService
        
        # For leads, use the existing chat card builder
        if obj == "lead":
            lead = LeadService.get_lead(db, record_id)
            if lead:
                ConversationContextStore.remember_object(conversation_id, obj, "READ", record_id=record_id)
                card = AiAgentService._build_lead_chat_card(db, lead)
                return {
                    "intent": "READ",
                    "object_type": "lead",
                    "record_id": record_id,
                    "text": f"{prefix}Here are the details for lead {AiAgentService._lead_name(lead)}.",
                    "card": card
                }
        
        # Generic read for other objects
        # In a real app, we'd build specific cards for each object type.
        # For now, let's return basic info.
        ConversationContextStore.remember_object(conversation_id, obj, "READ", record_id=record_id)
        return {
            "intent": "READ",
            "object_type": obj,
            "record_id": record_id,
            "text": f"{prefix}Opened {obj} record {record_id}."
        }

    @classmethod
    async def _handle_update(cls, db: Session, obj: str, record_id: str, data: Dict[str, Any], conversation_id: Optional[str], lang: Optional[str]) -> Dict[str, Any]:
        if not record_id:
             return {"intent": "CHAT", "text": f"Which {obj} would you like to update?"}
        
        from ai_agent.ui.backend.service import AiAgentService
        if obj == "lead":
            data = AiAgentService._normalize_lead_lookup_inputs(db, data)
        
        service = cls.OBJECT_MAPPING.get(obj)
        method_name = f"update_{obj}"
        if obj == "brand": method_name = "update_vehicle_spec"
        if obj == "message_template" or obj == "template": method_name = "update_template"
        
        update_method = getattr(service, method_name, None)
        if not update_method:
             return {"intent": "CHAT", "text": f"Update for {obj} is not supported yet."}

        try:
            res = update_method(db, record_id, **data)
            if res:
                # Success -> Redirect to READ view as requested by user
                return await cls._handle_read(db, obj, record_id, conversation_id, lang, prefix="Successfully updated! ")
        except Exception as e:
            return {"intent": "CHAT", "text": f"Error during update: {str(e)}"}
        
        return {"intent": "CHAT", "text": "Failed to update the record."}

    @classmethod
    async def _handle_delete(cls, db: Session, obj: str, record_id: str, conversation_id: Optional[str], lang: Optional[str]) -> Dict[str, Any]:
        if not record_id:
             return {"intent": "CHAT", "text": f"Which {obj} would you like to delete?"}
        
        # For now, we'll just ask for confirmation in a real app, 
        # but here we follow AiAgentService's delete confirmation logic if needed.
        # Let's just execute for simplicity in this prototype.
        from ai_agent.ui.backend.service import AiAgentService
        if AiAgentService._delete_record(db, obj, record_id):
            return {"intent": "CHAT", "text": f"Successfully deleted {obj} {record_id}."}
        
        return {"intent": "CHAT", "text": f"Failed to delete {obj} {record_id}."}
