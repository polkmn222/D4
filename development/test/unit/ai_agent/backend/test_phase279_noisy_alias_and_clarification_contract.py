from pathlib import Path

from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier


SERVICE_PATH = Path("development/ai_agent/ui/backend/service.py")
REASONER_PATH = Path("development/ai_agent/llm/backend/intent_reasoner.py")


def test_preclassifier_normalizes_salesforce_style_opportunity_and_template_shorthand():
    assert IntentPreClassifier.normalize_object_type("opty") == "opportunity"
    assert IntentPreClassifier.normalize_object_type("oppy") == "opportunity"
    assert IntentPreClassifier.normalize_object_type("tmpl") == "message_template"
    assert IntentPreClassifier.normalize_object_type("tpl") == "message_template"


def test_preclassifier_detects_shortened_opportunity_query_alias():
    result = IntentPreClassifier.detect("show all opty")

    assert result is not None
    assert result["intent"] == "QUERY"
    assert result["object_type"] == "opportunity"


def test_service_source_includes_short_object_clarification_guardrail():
    source = SERVICE_PATH.read_text(encoding="utf-8")

    assert 'SHORT_OBJECT_CLARIFICATIONS = {' in source
    assert '"l": "lead"' in source
    assert '"opty": "opportunity"' in source
    assert 'def _resolve_short_object_clarification(cls, user_query: str) -> Optional[Dict[str, Any]]:' in source
    assert 'Did you mean `{suggestion}`? Choose [{suggestion}] or keep typing more detail.' in source
    assert 'short_object_clarification = cls._resolve_short_object_clarification(user_query)' in source


def test_reasoner_allows_recommend_and_modify_ui_overlap_without_conflict_message():
    source = REASONER_PATH.read_text(encoding="utf-8")

    assert 'if intent == "MODIFY_UI" and action == "recommend":' in source
    assert 'if intent == "RECOMMEND" and action == "modify_ui":' in source
    assert "Please restate the request so I can choose one safe action." in source
