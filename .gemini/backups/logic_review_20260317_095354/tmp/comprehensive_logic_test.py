import os
import sys

# Add the project root to sys.path
sys.path.append("/Users/sangyeol.park@gruve.ai/D4")

from backend.app.database import SessionLocal, engine
from backend.app.services.lead_service import LeadService
from backend.app.services.account_service import AccountService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.asset_service import AssetService
from backend.app.services.product_service import ProductService
from backend.app.services.model_service import ModelService
from backend.app.services.task_service import TaskService
from backend.app.services.message_service import MessageService
from backend.app.services.message_template_service import MessageTemplateService
from backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService

def test_logic():
    db = SessionLocal()
    print("Starting Comprehensive Logic Tests...\n")
    
    try:
        # 1. Data Presence Check
        counts = {
            "Brands": len(BrandService.get_vehicle_specs(db, record_type="Brand")),
            "Models": len(ModelService.get_models(db)),
            "Products": len(ProductService.get_products(db)),
            "Accounts": len(AccountService.get_accounts(db)),
            "Leads": len(LeadService.get_leads(db)),
            "Opportunities": len(OpportunityService.get_opportunities(db)),
            "Assets": len(AssetService.get_assets(db)),
            "Tasks": len(TaskService.get_tasks(db)),
            "MessageTemplates": len(MessageTemplateService.get_templates(db)),
            "Messages": len(MessageService.get_messages(db)),
        }
        
        print("--- Table Counts ---")
        for table, count in counts.items():
            print(f"{table}: {count}")
            assert count > 0, f"Error: {table} has no data!"
        print("Data presence check: PASSED\n")

        # 2. Relationship Integrity Check
        print("--- Integrity Check ---")
        # Check an Opportunity has a Brand/Model
        opp = OpportunityService.get_opportunities(db)[0]
        print(f"Sample Opp: {opp.name}, BrandID: {opp.brand_id}, ModelID: {opp.model_id}")
        assert opp.brand_id is not None, "Error: Opportunity missing Brand lookup!"
        assert opp.model_id is not None, "Error: Opportunity missing Model lookup!"

        # Check an Asset has Brand/Product/Account/Model
        asset = AssetService.get_assets(db)[0]
        print(f"Sample Asset: {asset.name}, ProductID: {asset.product_id}, BrandID: {asset.brand_id}, AccountID: {asset.account_id}")
        assert asset.brand_id is not None, "Error: Asset missing Brand lookup!"
        assert asset.product_id is not None, "Error: Asset missing Product lookup!"
        assert asset.account_id is not None, "Error: Asset missing Account lookup!"
        print("Relationship integrity check: PASSED\n")

        # 3. Create Logic Check (Non-mandatory fields)
        print("--- Creation Logic Check (Name-only) ---")
        # Asset
        new_asset = AssetService.create_asset(db, name="TEST_MANDATORY_ONLY_ASSET")
        print(f"New Asset Created: {new_asset.name} (ID: {new_asset.id})")
        assert new_asset.id is not None
        
        # Product
        new_prod = ProductService.create_product(db, name="TEST_MANDATORY_ONLY_PROD")
        print(f"New Product Created: {new_prod.name} (ID: {new_prod.id})")
        assert new_prod.id is not None

        # Task with new lookups
        new_task = TaskService.create_task(db, subject="TEST_TASK_WITH_LOOKUPS", opportunity_id=opp.id, account_id=asset.account_id)
        print(f"New Task Created: {new_task.subject} (ID: {new_task.id}, OppRef: {new_task.opportunity_id})")
        assert new_task.opportunity_id == opp.id
        print("Creation logic check: PASSED\n")

        print("ALL COMPREHENSIVE LOGIC TESTS: PASSED")

    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_logic()
