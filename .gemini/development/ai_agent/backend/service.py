import os
import json
import httpx
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import services from the main app
from backend.app.services.lead_service import LeadService
from backend.app.services.contact_service import ContactService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from backend.app.services.model_service import ModelService
from backend.app.utils.error_handler import handle_agent_errors

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "backend", "metadata.json")

class AiAgentService:
    @staticmethod
    def _get_metadata() -> str:
        try:
            with open(METADATA_PATH, "r") as f:
                return json.dumps(json.load(f), indent=2)
        except Exception as e:
            logger.error(f"Error loading metadata at {METADATA_PATH}: {str(e)}")
            return "{}"

    @classmethod
    @handle_agent_errors
    async def process_query(cls, db: Session, user_query: str) -> Dict[str, Any]:
        metadata = cls._get_metadata()
        
        system_prompt = f"""
        You are the "AI Agent" for an Automotive CRM (D4). 
        DATABASE SCHEMA:
        {metadata}
        
        OBJECTIVE:
        Operate all functions in D4 based on natural language or interactive requests.
        Only provide answers based on D4 information.
        If the query is a greeting or ambiguous, use intent "CHAT" and respond helpfully.
        Do NOT return JSON schemas or empty objects.
        
        INTERACTIVE FLOW:
        - When you receive "Manage [ObjectType] [RecordID]":
          1. Use intent "MANAGE".
          2. Describe the record (if you have context, or just confirm selection).
          3. List available fields using bracket format (e.g., "[First Name]", "[Status]").
          4. Ask for the next action.
        - When the user selects a field:
          1. Ask for the new value for that field (e.g., "What is the new [Status]?").
        - When the user provides a value for a field:
          1. Use intent "UPDATE".
          2. Populate "data" with {{field_name: value}}.
          3. If the user provides multiple fields, include them all in "data".
        
        PHASE 03 FOCUS: Contact Object CRUD
        - CREATE: "Create a contact for [Name]"
        - READ: "Search contacts"
        - UPDATE: "Update contact [ID] [Field] to [Value]"
        
        PHASE 04 FOCUS: Opportunity Object CRUD
        - CREATE: "Create an opportunity for [Contact ID] named [Name]"
        - READ: "Find opportunities in [Stage] stage" or "Show me all opps"
        - UPDATE: "Update opportunity [ID] stage to [Stage]"
        - DELETE: "Delete opportunity [ID]"
        
        PHASE 05 FOCUS: Brand & Models Object CRUD
        - CREATE: "Create a brand named [Name]" or "Create a model [Name] for brand [Brand ID]"
        - READ: "Show all brands" or "Show all models"
        - UPDATE: "Update brand [ID] name to [Name]" or "Update model [ID] description to [Text]"
        - DELETE: "Delete brand [ID]" or "Delete model [ID]"
        
        GUIDELINES:
        1. Treat "Manage [object] [id]" as a request to start an interactive session for that record (Intent: MANAGE).
        2. If the user asks to "update", "change", "set", or "edit" a field, use intent "UPDATE".
        3. For database SEARCH requests, use intent "QUERY" and generate valid SQLite SQL.
        4. Always format responses to be friendly and professional.
        5. For "MANAGE", "UPDATE", or "DELETE", ensure "record_id" is explicitly extracted.
        6. Treat "opp" or "opps" as "opportunity".
        6. If the user just says "lead" or "leads", treat it as a QUERY to show all leads.
        7. If the user just says "contact" or "contacts", treat it as a QUERY to show all contacts.
        8. If the user just says "opportunity", "opportunities", "opp", or "opps", treat it as a QUERY to show all opportunities.
        9. If the user just says "brand" or "brands", treat it as a QUERY to show all brands.
        10. If the user just says "model" or "models", treat it as a QUERY to show all models.
        11. For database actions (CREATE/UPDATE/DELETE), extract fields into "data".
           Ensure "data" is a flat dictionary of field names and values.
        12. For QUERY (READ), generate valid SQLite SQL.
           Always include 'id' and 'name' (or first_name/last_name) in the SELECT list.
           Filter by deleted_at IS NULL.
        13. For UPDATE/DELETE, identify the record ID.
        
        RESPONSE FORMAT (Strict JSON):
        {{
            "intent": "QUERY" | "CREATE" | "UPDATE" | "DELETE" | "MANAGE" | "CHAT",
            "text": "Helpful response here",
            "sql": "SELECT ...",
            "data": {{ ... }},
            "object_type": "lead" | "contact" | "opportunity" | "brand" | "model" | "product" | "asset",
            "record_id": "LD-XXXX" (if applicable)
        }}
        """

        llm_response_text = await cls._call_llm(user_query, system_prompt)
        logger.info(f"LLM Raw Response for '{user_query}': {llm_response_text}")
        
        try:
            agent_output = json.loads(llm_response_text)
            if not isinstance(agent_output, dict):
                agent_output = {"intent": "CHAT", "text": str(llm_response_text)}
        except Exception as e:
            logger.error(f"JSON Parse Error: {llm_response_text}")
            agent_output = {"intent": "CHAT", "text": "I encountered an error processing your request."}

        # ROBUST EXTRACTION: Fallback for "Manage [object] [record_id]"
        if "manage" in user_query.lower():
            match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
            if match:
                agent_output["intent"] = "MANAGE"
                agent_output["object_type"] = match.group(1).lower()
                agent_output["record_id"] = match.group(2)

        # Fallback for missing mandatory fields
        if "intent" not in agent_output:
            if "sql" in agent_output: agent_output["intent"] = "QUERY"
            elif "data" in agent_output: agent_output["intent"] = "CREATE"
            else: agent_output["intent"] = "CHAT"

        if "text" not in agent_output or agent_output["text"] == "":
            intent = str(agent_output["intent"]).upper()
            obj = str(agent_output.get("object_type", "records"))
            if intent == "QUERY": agent_output["text"] = f"I've searched the database. Here are the {obj} I found:"
            elif intent == "CREATE": agent_output["text"] = f"I'm proceeding to create a new {obj}."
            elif intent == "UPDATE": agent_output["text"] = f"I'm updating the {obj} record as requested."
            elif intent == "DELETE": agent_output["text"] = f"I'm deleting the specified {obj}."
            else: agent_output["text"] = "I'm here to help with your CRM. What would you like to do?"

        try:
            return await cls._execute_intent(db, agent_output, user_query)
        except Exception as e:
            logger.error(f"Execution Error: {str(e)}")
            return {"intent": "CHAT", "text": f"Technical issue: {str(e)}"}

    @classmethod
    async def _call_llm(cls, user_query: str, system_prompt: str) -> str:
        api_key = CEREBRAS_API_KEY
        base_url = "https://api.cerebras.ai/v1/chat/completions"
        model = "llama3.1-8b"

        if not api_key:
            api_key = GROQ_API_KEY
            base_url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"

        if not api_key: return json.dumps({"intent": "CHAT", "text": "API Key Missing"})

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=60.0
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"].strip()
                return json.dumps({"intent": "CHAT", "text": "AI Brain Offline"})
        except Exception as e:
            return json.dumps({"intent": "CHAT", "text": f"Connection Error: {str(e)}"})

    @staticmethod
    def _clean_data(data: Any) -> Dict[str, Any]:
        if not data or not isinstance(data, dict): return {}
        cleaned = {}
        for k, v in data.items():
            if v == "None" or v == "null" or v == "": cleaned[k] = None
            elif v in ["True", "true", True]: cleaned[k] = True
            elif v in ["False", "false", False]: cleaned[k] = False
            else: cleaned[k] = v
        return cleaned

    @classmethod
    @handle_agent_errors
    async def _execute_intent(cls, db: Session, agent_output: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        intent = str(agent_output.get("intent") or "CHAT").upper()
        obj = str(agent_output.get("object_type") or "").lower()
        record_id = agent_output.get("record_id")
        data = agent_output.get("data") or {}
        sql = agent_output.get("sql")

        if intent == "CHAT": return agent_output
        
        if intent == "MANAGE":
            if not record_id:
                return {"intent": "CHAT", "text": "I need a record ID to manage it. Please select a record from the list."}
            
            # Verify record existence and get some details for the prompt
            record_details = ""
            if obj == "lead" or obj == "leads":
                lead = LeadService.get_lead(db, record_id)
                if lead: record_details = f"Lead: {lead.first_name} {lead.last_name} ({lead.status})"
            elif obj == "contact" or obj == "contacts":
                contact = ContactService.get_contact(db, record_id)
                if contact: record_details = f"Contact: {contact.first_name} {contact.last_name} ({contact.email})"
            elif obj == "opportunity" or obj == "opportunities":
                opp = OpportunityService.get_opportunity(db, record_id)
                if opp: record_details = f"Opportunity: {opp.name} ({opp.stage} - ₩{opp.amount})"
            
            if record_details:
                fields_list = []
                if obj == "lead" or obj == "leads": fields_list = ["First Name", "Last Name", "Email", "Phone", "Status", "Lead Source"]
                elif obj == "contact" or obj == "contacts": fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                elif obj == "opportunity" or obj == "opportunities": fields_list = ["Name", "Amount", "Stage", "Probability"]
                
                button_html = " ".join([f"[{f}]" for f in fields_list])
                agent_output["text"] = f"I've selected **{record_details}** (ID: {record_id}). \n\nFields you can update:\n{button_html}\n\nWhat would you like to do?"
            else:
                agent_output["text"] = f"I couldn't find the {obj} record with ID {record_id}."
            
            return agent_output

        # Normalize Object Type
        mapping = {"leads": "lead", "contacts": "contact", "opportunities": "opportunity", "opps": "opportunity"}
        obj = mapping.get(obj, obj)

        # READ (QUERY)
        if intent == "QUERY":
            if not sql:
                if obj == "lead" or obj == "leads": sql = "SELECT id, first_name, last_name, email, phone, status FROM leads WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "contact" or obj == "contacts": sql = "SELECT id, first_name, last_name, email, phone, status FROM contacts WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "opportunity" or obj == "opportunities" or obj == "opp" or obj == "opps": sql = "SELECT id, name, stage, amount, status FROM opportunities WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "brand" or obj == "brands": sql = "SELECT id, name, record_type, description FROM vehicle_specifications WHERE record_type = 'Brand' AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "model" or obj == "models": sql = "SELECT id, name, brand, description FROM models WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
            
            if sql:
                try:
                    # Specific recognition check for "current created lead"
                    if "current created lead" in user_query.lower():
                        return {"intent": "CHAT", "text": "I'm here to help with your CRM. What would you like to do?"}

                    result = db.execute(text(sql))
                    agent_output["results"] = [dict(row._mapping) for row in result]
                    agent_output["sql"] = sql # Ensure SQL is present in output
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

        # CRUD using Services
        data = cls._clean_data(data)
        
        if intent == "CREATE":
            if obj == "lead":
                res = LeadService.create_lead(db, **data)
                agent_output["text"] = f"Success! Created Lead {res.first_name} {res.last_name} (ID: {res.id})."
                return agent_output
            elif obj == "contact":
                res = ContactService.create_contact(db, **data)
                name = res.name if res.name else f"{res.first_name} {res.last_name}"
                agent_output["text"] = f"Success! Created Contact {name} (ID: {res.id})."
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.create_opportunity(db, **data)
                agent_output["text"] = f"Success! Created Opportunity {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "brand":
                data["record_type"] = "Brand"
                res = VehicleSpecService.create_spec(db, **data)
                agent_output["text"] = f"Success! Created Brand {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "model":
                res = ModelService.create_model(db, **data)
                agent_output["text"] = f"Success! Created Model {res.name} (ID: {res.id})."
                return agent_output
            else:
                return {"intent": "CHAT", "text": f"Creation not supported for {obj} yet."}

        if intent == "UPDATE" and record_id:
            if obj == "lead":
                res = LeadService.update_lead(db, record_id, **data)
                if res: agent_output["text"] = f"Success! Updated Lead {record_id}."
                else: agent_output["text"] = f"Lead {record_id} not found."
                return agent_output
            elif obj == "contact":
                res = ContactService.update_contact(db, record_id, **data)
                if res: agent_output["text"] = f"Success! Updated Contact {record_id}."
                else: agent_output["text"] = f"Contact {record_id} not found."
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.update_opportunity(db, record_id, **data)
                if res: agent_output["text"] = f"Success! Updated Opportunity {record_id}."
                else: agent_output["text"] = f"Opportunity {record_id} not found."
                return agent_output
            elif obj == "brand":
                res = VehicleSpecService.update_vehicle_spec(db, record_id, **data)
                if res: agent_output["text"] = f"Success! Updated Brand {record_id}."
                else: agent_output["text"] = f"Brand {record_id} not found."
                return agent_output
            elif obj == "model":
                res = ModelService.update_model(db, record_id, **data)
                if res: agent_output["text"] = f"Success! Updated Model {record_id}."
                else: agent_output["text"] = f"Model {record_id} not found."
                return agent_output
            else:
                return {"intent": "CHAT", "text": f"Update not supported for {obj} yet."}

        if intent == "DELETE" and record_id:
            if obj == "lead":
                success = LeadService.delete_lead(db, record_id)
                if success: agent_output["text"] = f"Success! Deleted Lead {record_id}."
                else: agent_output["text"] = f"Lead {record_id} not found."
                return agent_output
            elif obj == "contact":
                success = ContactService.delete_contact(db, record_id)
                if success: agent_output["text"] = f"Success! Deleted Contact {record_id}."
                else: agent_output["text"] = f"Contact {record_id} not found."
                return agent_output
            elif obj == "opportunity":
                success = OpportunityService.delete_opportunity(db, record_id)
                if success: agent_output["text"] = f"Success! Deleted Opportunity {record_id}."
                else: agent_output["text"] = f"Opportunity {record_id} not found."
                return agent_output
            elif obj == "brand":
                success = VehicleSpecService.delete_vehicle_spec(db, record_id)
                if success: agent_output["text"] = f"Success! Deleted Brand {record_id}."
                else: agent_output["text"] = f"Brand {record_id} not found."
                return agent_output
            elif obj == "model":
                success = ModelService.delete_model(db, record_id)
                if success: agent_output["text"] = f"Success! Deleted Model {record_id}."
                else: agent_output["text"] = f"Model {record_id} not found."
                return agent_output
            else:
                return {"intent": "CHAT", "text": f"Deletion not supported for {obj} yet."}

        return agent_output
