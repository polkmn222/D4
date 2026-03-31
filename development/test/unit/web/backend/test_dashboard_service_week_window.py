from datetime import datetime

from web.backend.app.services.dashboard_service import DashboardService


class _FakeRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_dashboard_performance_uses_korean_monday_start_week(monkeypatch):
    monday = datetime(2026, 3, 30, 9, 0, 0)
    sunday_prev = datetime(2026, 3, 29, 18, 0, 0)
    tuesday = datetime(2026, 3, 31, 10, 0, 0)

    monkeypatch.setattr(
        "web.backend.app.services.dashboard_service.get_kst_now_naive",
        lambda: monday,
    )
    monkeypatch.setattr(
        "web.backend.app.services.dashboard_service.LeadService.get_leads",
        lambda db: [],
    )
    monkeypatch.setattr(
        "web.backend.app.services.dashboard_service.ContactService.get_contacts",
        lambda db: [],
    )
    monkeypatch.setattr(
        "web.backend.app.services.dashboard_service.OpportunityService.get_recent_clicked",
        lambda db, limit=5: [],
    )
    monkeypatch.setattr(
        "web.backend.app.services.dashboard_service.OpportunityService.get_opportunities",
        lambda db: [
            _FakeRecord(id="old", name="Old Opp", stage="Closed Won", amount=200, created_at=sunday_prev),
            _FakeRecord(id="new", name="New Opp", stage="Closed Won", amount=300, created_at=tuesday),
        ],
    )

    result = DashboardService.get_dashboard_data(db=None)

    assert result["performance"]["closed_won"] == "300"
