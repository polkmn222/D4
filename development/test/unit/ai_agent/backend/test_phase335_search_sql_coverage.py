import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.ui.backend.service import AiAgentService


def test_phase1_query_sql_applies_search_term_for_lead():
    sql = AiAgentService._build_phase1_query_sql("lead", {"search_term": "Tesla"})

    assert "l.deleted_at IS NULL" in sql
    assert "ILIKE '%Tesla%'" in sql
    assert "l.first_name ILIKE '%Tesla%'" in sql
    assert "COALESCE(m.name, l.model) ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_contact():
    sql = AiAgentService._build_phase1_query_sql("contact", {"search_term": "Tesla"})

    assert "c.deleted_at IS NULL" in sql
    assert "c.email ILIKE '%Tesla%'" in sql
    assert "TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_opportunity():
    sql = AiAgentService._build_phase1_query_sql("opportunity", {"search_term": "Tesla"})

    assert "o.deleted_at IS NULL" in sql
    assert "o.name ILIKE '%Tesla%'" in sql
    assert "TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) ILIKE '%Tesla%'" in sql
    assert "COALESCE(m.name, o.model) ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_brand():
    sql = AiAgentService._build_phase1_query_sql("brand", {"search_term": "Tesla"})

    assert "record_type = 'Brand' AND deleted_at IS NULL" in sql
    assert "name ILIKE '%Tesla%'" in sql
    assert "description ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_model():
    sql = AiAgentService._build_phase1_query_sql("model", {"search_term": "Tesla"})

    assert "m.deleted_at IS NULL" in sql
    assert "m.name ILIKE '%Tesla%'" in sql
    assert "vs.name ILIKE '%Tesla%'" in sql
    assert "m.description ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_product():
    sql = AiAgentService._build_phase1_query_sql("product", {"search_term": "Tesla"})

    assert "p.deleted_at IS NULL" in sql
    assert "p.name ILIKE '%Tesla%'" in sql
    assert "vs.name ILIKE '%Tesla%'" in sql
    assert "m.name ILIKE '%Tesla%'" in sql
    assert "p.category ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_asset():
    sql = AiAgentService._build_phase1_query_sql("asset", {"search_term": "Tesla"})

    assert "a.deleted_at IS NULL" in sql
    assert "COALESCE(a.name, a.vin) ILIKE '%Tesla%'" in sql
    assert "a.status ILIKE '%Tesla%'" in sql
    assert "vs.name ILIKE '%Tesla%'" in sql
    assert "m.name ILIKE '%Tesla%'" in sql


def test_phase1_query_sql_applies_search_term_for_message_template():
    sql = AiAgentService._build_phase1_query_sql("message_template", {"search_term": "Tesla"})

    assert "deleted_at IS NULL" in sql
    assert "name ILIKE '%Tesla%'" in sql
    assert "record_type ILIKE '%Tesla%'" in sql
    assert "subject ILIKE '%Tesla%'" in sql
    assert "content ILIKE '%Tesla%'" in sql
