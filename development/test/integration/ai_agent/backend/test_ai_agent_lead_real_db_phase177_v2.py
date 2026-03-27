import pytest

from db.models import Lead
from ai_agent.ui.backend.service import AiAgentService
from web.backend.app.services.lead_service import LeadService


pytestmark = pytest.mark.integration


class TestAiAgentLeadIntegration:
    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_real_db_lead_create_and_delete(self, db):
        conversation_id = "integration_test_177"
        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {
                "first_name": "Integration",
                "last_name": "Tester",
                "email": "integration@test.com",
                "status": "New",
            },
            "language_preference": "eng",
        }

        create_response = self._run(AiAgentService._execute_intent(db, agent_output, "create lead", conversation_id=conversation_id))

        assert create_response.get("intent") == "OPEN_RECORD"
        record_id = create_response.get("record_id")
        assert record_id is not None

        lead_in_db = db.query(Lead).filter(Lead.id == record_id).first()
        assert lead_in_db is not None
        assert lead_in_db.first_name == "Integration"

        from ai_agent.llm.backend.conversation_context import ConversationContextStore
        ConversationContextStore.remember_object(conversation_id, "lead", "QUERY", record_id=record_id)

        delete_response = self._run(AiAgentService.process_query(db, f"Delete lead {record_id}", conversation_id=conversation_id))

        assert delete_response.get("intent") == "DELETE"
        db.expire_all()
        lead_after_delete = db.query(Lead).filter(Lead.id == record_id).first()
        assert lead_after_delete.deleted_at is not None

    def test_real_db_lead_query_schema(self, db):
        user_query = "show all leads"
        agent_output = {
            "intent": "QUERY",
            "object_type": "lead",
            "score": 1.0,
        }

        response = self._run(AiAgentService._execute_intent(db, agent_output, user_query))
        results = response.get("results", [])
        if results:
            first = results[0]
            assert "display_name" in first
            assert "model" in first
            assert "phone" in first
            assert "status" in first
            assert "created_at" in first
        else:
            pytest.skip("No leads in DB to verify schema.")

    def test_real_db_lead_update(self, db):
        lead = LeadService.create_lead(db, first_name="Update", last_name="Me", status="New")
        lead_id = lead.id
        agent_output = {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": lead_id,
            "data": {"status": "Qualified"},
            "language_preference": "eng",
        }

        update_response = self._run(AiAgentService._execute_intent(db, agent_output, "update lead", conversation_id="integration_test_update"))

        assert update_response.get("intent") == "OPEN_RECORD"
        db.refresh(lead)
        assert lead.status == "Qualified"

    def test_real_db_explicit_id_crud_flow(self, db):
        conversation_id = "integration_test_explicit_id_203"
        lead = LeadService.create_lead(
            db,
            first_name="Explicit",
            last_name="Flow203",
            email="explicit_flow203@example.com",
            status="New",
        )
        lead_id = lead.id

        show_response = self._run(AiAgentService.process_query(db, f"show lead {lead_id}", conversation_id=conversation_id))
        assert show_response.get("intent") == "OPEN_RECORD"
        assert show_response.get("record_id") == lead_id

        update_response = self._run(AiAgentService.process_query(db, f"update lead {lead_id} status Lost", conversation_id=conversation_id))
        assert update_response.get("intent") == "OPEN_RECORD"

        db.expire_all()
        updated = db.query(Lead).filter(Lead.id == lead_id).first()
        assert updated is not None
        assert updated.status == "Lost"

        delete_response = self._run(AiAgentService.process_query(db, f"delete lead {lead_id}", conversation_id=conversation_id))
        assert delete_response.get("intent") == "DELETE"

        db.expire_all()
        deleted = db.query(Lead).filter(Lead.id == lead_id).first()
        assert deleted is not None
        assert deleted.deleted_at is not None
