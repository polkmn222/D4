import pytest
import uuid
from datetime import timedelta
from sqlalchemy.orm import Session

from db.models import Opportunity
from ai_agent.llm.backend.recommendations import AIRecommendationService
from web.backend.app.utils.timezone import get_kst_now_naive


pytestmark = pytest.mark.integration


def test_refresh_temperature_throttling(db: Session):
    unique_id = f"TEST_OPP_{uuid.uuid4().hex[:8]}"

    db.query(Opportunity).filter(Opportunity.id == unique_id).delete()
    db.commit()

    opp = Opportunity(
        id=unique_id,
        name="Test Opportunity",
        stage="Prospecting",
        created_at=get_kst_now_naive() - timedelta(days=1),
    )
    db.add(opp)
    db.commit()

    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)
    assert opp.updated_by == AIRecommendationService.AI_AGENT_USER

    opp.temperature = "Modified Manually"
    db.commit()

    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)
    assert opp.temperature == "Modified Manually"

    opp.updated_by = "Human User"
    db.commit()

    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)

    assert opp.updated_by == AIRecommendationService.AI_AGENT_USER
    assert opp.temperature in ["Hot", "Warm", "Cold"]

    db.delete(opp)
    db.commit()
