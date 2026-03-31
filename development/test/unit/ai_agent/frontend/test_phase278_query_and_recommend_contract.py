from pathlib import Path


AI_AGENT_JS = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js")
AI_AGENT_SERVICE = Path("development/ai_agent/ui/backend/service.py")
RECOMMEND_FRAGMENT = Path("development/web/frontend/templates/dashboard/dashboard_ai_recommend_fragment.html")
RECOMMENDATIONS_SERVICE = Path("development/ai_agent/llm/backend/recommendations.py")
DASHBOARD_ROUTER = Path("development/web/backend/app/api/routers/dashboard_router.py")
MESSAGING_ROUTER = Path("development/web/message/backend/router.py")


def test_query_pagination_contract_uses_explicit_projection_instead_of_select_star():
    source = AI_AGENT_SERVICE.read_text(encoding="utf-8")

    assert 'def _default_query_projection(obj: str) -> str:' in source
    assert 'full_sql = f"SELECT {projection} FROM ({clean_sql}) AS agent_query_page"' in source
    assert '"mode": "local",' in source
    assert '"select": "o.id, o.name, TRIM(CONCAT_WS(' in source
    assert 'COALESCE(m.name, o.model) AS model, o.created_at' in source
    assert 'SELECT * FROM ({clean_sql}) AS agent_query_page' not in source


def test_local_agent_table_search_filters_full_result_set_with_persisted_search_term():
    source = AI_AGENT_JS.read_text(encoding="utf-8")

    assert "const activeResults = Array.isArray(tableState.filteredResults) ? tableState.filteredResults : tableState.results;" in source
    assert "tableState.filteredResults = term" in source
    assert "tableState.results.filter(row => JSON.stringify(row || {}).toLowerCase().includes(term))" in source
    assert 'value="${escapeAgentHtml(pagination?.search_term || \'\')}"' in source
    assert 'class="agent-table-search-clear ${pagination?.search_term ? \'is-visible\' : \'\'}"' in source
    assert "Search matches all loaded records. Press Enter to run a full query." not in source
    assert "function clearAgentTableSearch(button) {" in source


def test_ai_recommend_contract_matches_home_fragment_columns_and_created_date():
    service_source = AI_AGENT_SERVICE.read_text(encoding="utf-8")
    js_source = AI_AGENT_JS.read_text(encoding="utf-8")
    fragment_source = RECOMMEND_FRAGMENT.read_text(encoding="utf-8")
    recommendations_source = RECOMMENDATIONS_SERVICE.read_text(encoding="utf-8")
    dashboard_router_source = DASHBOARD_ROUTER.read_text(encoding="utf-8")
    messaging_router_source = MESSAGING_ROUTER.read_text(encoding="utf-8")

    assert "def get_sendable_recommendations(" in recommendations_source
    assert "limit: Optional[int] = None" in recommendations_source
    assert "scan_limit: Optional[int] = None" in recommendations_source
    assert "AIRecommendationService.get_sendable_recommendations(db)" in service_source
    assert '"temperature": getattr(r, \'temp_display\', \'Hot\'),' in service_source
    assert '"created_at": r.created_at.strftime("%Y-%m-%d") if getattr(r, "created_at", None) else "",' in service_source
    assert "opportunity: ['name', 'amount', 'stage', 'temperature', 'created_at'" in js_source
    assert "<th onclick=\"sortTable(this, 0)\">Name</th>" in fragment_source
    assert "<th onclick=\"sortTable(this, 1)\">Amount</th>" in fragment_source
    assert "<th onclick=\"sortTable(this, 2)\">Stage</th>" in fragment_source
    assert "<th onclick=\"sortTable(this, 3)\">Temperature</th>" in fragment_source
    assert "<th onclick=\"sortTable(this, 4)\">Created</th>" in fragment_source
    assert "AIRecommendationService.get_sendable_recommendations(db)" in dashboard_router_source
    assert "AIRecommendationService.get_sendable_recommendations(db)" in messaging_router_source
