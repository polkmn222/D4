import os
import sys
import random
from datetime import datetime, timedelta

# Ensure we can import app modules
# Adding 'development' and 'development/web/backend' to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # development
ROOT_DIR = os.path.dirname(BASE_DIR) # project root
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "web", "backend"))

from db.database import SessionLocal
from db.models import Lead, Contact, Opportunity, Asset, Product, VehicleSpecification, Model
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.core.enums import OpportunityStage, OpportunityStatus, RecordType

def seed_data():
    db = SessionLocal()
    
    # 1. Ensure Brand and Model
    brand_id = "avS_GENESIS_01" # Fixed ID for seeding
    brand = db.query(VehicleSpecification).filter(VehicleSpecification.id == brand_id).first()
    if not brand:
        brand = VehicleSpecification(
            id=brand_id,
            name="Genesis",
            record_type=RecordType.BRAND,
            description="Luxury brand",
            created_by="System",
            updated_by="System"
        )
        db.add(brand)
        db.flush()
    
    model_id = "MOD_GV80_01" # Fixed ID for seeding
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        model = Model(
            id=model_id,
            name="GV80",
            brand=brand_id,
            description="Premium SUV",
            created_by="System",
            updated_by="System"
        )
        db.add(model)
        db.flush()

    # 2. Ensure a Product
    product_id = "01t_GV80_PRESTIGE_01"
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        product = Product(
            id=product_id,
            name="Genesis GV80 3.5T Prestige",
            brand=brand_id,
            model=model_id,
            category="Luxury SUV",
            base_price=90000000,
            description="Genesis GV80 3.5T Prestige AWD",
            created_by="System",
            updated_by="System"
        )
        db.add(product)
        db.flush()

    stages = [
        OpportunityStage.PROSPECTING,
        OpportunityStage.QUALIFICATION,
        OpportunityStage.NEEDS_ANALYSIS,
        OpportunityStage.VALUE_PROPOSITION,
        OpportunityStage.TEST_DRIVE,
        OpportunityStage.NEGOTIATION,
        OpportunityStage.PROPOSAL,
        OpportunityStage.CLOSED_WON,
        OpportunityStage.CLOSED_LOST,
    ]
    # To make 10, repeat one stage
    all_stages = stages + [OpportunityStage.NEGOTIATION]

    first_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
    last_names = ["민수", "서연", "지훈", "하윤", "도윤", "지우", "건우", "서준", "민지", "현우"]

    print("Seeding 10 Opportunities with all fields populated...")
    now = get_kst_now_naive()
    # Override now to March 30, 2026 as per user requirement "오늘자 기준으로"
    now = datetime(2026, 3, 30, 12, 0, 0)

    for i, stage in enumerate(all_stages):
        # Create a contact for each opportunity
        fn = first_names[i]
        ln = last_names[i]
        contact_id = get_id("Contact")
        contact = Contact(
            id=contact_id,
            first_name=fn,
            last_name=ln,
            name=f"{fn}{ln}",
            email=f"user{i}@example.com",
            phone=f"010-{1000+i}-{2000+i}",
            gender="Male" if i % 2 == 0 else "Female",
            created_by="System",
            updated_by="System",
            created_at=now,
            updated_at=now
        )
        db.add(contact)
        db.flush()

        # Create a lead for each opportunity
        lead_id = get_id("Lead")
        lead = Lead(
            id=lead_id,
            first_name=fn,
            last_name=ln,
            email=f"lead{i}@example.com",
            phone=f"010-{1000+i}-{2000+i}",
            status="Qualified",
            is_converted=True,
            converted_contact=contact_id,
            brand=brand_id,
            model=model_id,
            product=product_id,
            description=f"Initial interest from {fn}{ln}",
            created_by="System",
            updated_by="System",
            created_at=now,
            updated_at=now
        )
        db.add(lead)
        db.flush()

        # Create an asset if it's Closed Won
        asset_id = None
        if stage == OpportunityStage.CLOSED_WON:
            asset_id = get_id("Asset")
            asset = Asset(
                id=asset_id,
                contact=contact_id,
                product=product_id,
                brand=brand_id,
                model=model_id,
                name=f"{fn}{ln}'s GV80",
                vin=f"VIN{i}GENESISGV80{i}",
                status="Delivered",
                purchase_date=now.date(),
                price=95000000,
                created_by="System",
                updated_by="System",
                created_at=now,
                updated_at=now
            )
            db.add(asset)
            db.flush()

        # Status logic
        status = OpportunityStatus.OPEN
        if stage == OpportunityStage.CLOSED_WON:
            status = OpportunityStatus.CLOSED_WON
        elif stage == OpportunityStage.CLOSED_LOST:
            status = OpportunityStatus.CLOSED_LOST

        opp_id = get_id("Opportunity")
        opp = Opportunity(
            id=opp_id,
            contact=contact_id,
            product=product_id,
            lead=lead_id,
            brand=brand_id,
            model=model_id,
            asset=asset_id,
            name=f"{fn}{ln} - GV80 Purchase",
            amount=90000000 + (i * 100000),
            stage=stage,
            status=status,
            probability=10 * (i + 1) if i < 9 else 95,
            temperature=random.choice(["Hot", "Warm", "Cold"]),
            last_viewed_at=now,
            close_date=(now + timedelta(days=30)).date(),
            ai_insight=f"High potential for {stage} based on interaction history.",
            is_followed=True if i % 2 == 0 else False,
            created_by="System",
            updated_by="System",
            created_at=now,
            updated_at=now
        )
        db.add(opp)
        
        # Link back lead to opportunity
        lead.converted_opportunity = opp_id

    db.commit()
    print("Seed complete: 10 Opportunities created with various stages.")

if __name__ == "__main__":
    seed_data()
