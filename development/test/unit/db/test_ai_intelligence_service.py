from pathlib import Path
from unittest.mock import MagicMock

import pytest

from web.backend.app.services.ai_intelligence_service import AiIntelligenceService


def test_find_best_matching_pattern_returns_none_when_pg_trgm_is_unavailable():
    db = MagicMock()
    db.execute.side_effect = RuntimeError('function similarity(text, unknown) does not exist')

    result = AiIntelligenceService.find_best_matching_pattern(db, "show all leads")

    assert result is None


def test_get_synonym_mapping_returns_none_when_synonym_table_is_missing():
    db = MagicMock()
    query = db.query.return_value
    query.filter.side_effect = RuntimeError('relation "ai_synonyms" does not exist')

    result = AiIntelligenceService.get_synonym_mapping(db, "opty")

    assert result is None


def test_seed_script_source_uses_existing_learning_inputs():
    source = Path("development/db/seeds/seed_mass_patterns_phase304.py").read_text(encoding="utf-8")

    assert "learning/agent.txt" in source
    assert "learning/phase1_user_simulation_answers.md" in source
    assert "learning/phase5_cycle3_final_results.md" in source
    assert "re.findall(r'\\*\\*\\d+\\. Q: `(.+?)`\\*\\*', content)" in source
