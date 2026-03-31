from unittest.mock import MagicMock, patch

import pytest

from web.backend.app.api.routers.asset_router import update_asset_endpoint


@pytest.mark.asyncio
async def test_asset_update_endpoint_accepts_shared_form_lookup_names():
    db = MagicMock()

    with patch("web.backend.app.api.routers.asset_router.AssetService.update_asset") as mock_update:
        response = await update_asset_endpoint(
            asset_id="AST326",
            name="Fleet Car",
            contact="CON326",
            product="PRO326",
            brand="BR326",
            model="MOD326",
            vin="VIN326",
            price=42000,
            status="Maintenance",
            db=db,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/assets/AST326?success=Record+updated+successfully"
    mock_update.assert_called_once_with(
        db,
        "AST326",
        name="Fleet Car",
        contact="CON326",
        product="PRO326",
        brand="BR326",
        model="MOD326",
        vin="VIN326",
        price=42000,
        status="Maintenance",
    )
