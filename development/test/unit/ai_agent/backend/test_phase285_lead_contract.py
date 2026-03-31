from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


def test_lead_chat_native_form_exposes_half_width_lookup_fields_and_full_description():
    response = AiAgentService._build_chat_native_form_response(
        object_type="lead",
        mode="create",
        db=None,
        language_preference="eng",
    )

    fields = {field["name"]: field for field in response["form"]["fields"]}

    assert fields["product"]["layout"] == "half"
    assert fields["model"]["layout"] == "half"
    assert fields["brand"]["layout"] == "half"
    assert fields["description"]["layout"] == "full"


@pytest.mark.asyncio
async def test_delete_model_uses_human_friendly_title_not_raw_id():
    record = SimpleNamespace(id="MODEL285", name="Test Model")

    with patch("web.backend.app.services.model_service.ModelService.get_model", return_value=record), patch.object(
        AiAgentService,
        "_delete_record",
        return_value=True,
    ):
        response = await AiAgentService._execute_intent(
            db=None,
            agent_output={"intent": "DELETE", "object_type": "model", "record_id": "MODEL285"},
            user_query="delete model Test Model",
            conversation_id="phase285-delete-model",
        )

    assert response["intent"] == "DELETE"
    assert "Test Model" in response["text"]
    assert "MODEL285" not in response["text"]
