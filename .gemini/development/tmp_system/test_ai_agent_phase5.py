import asyncio
import os
import sys
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), ".gemini", "skills"))

from db.database import Base
from ask_agent.ask_agent_service import AskAgentService
from db.models import VehicleSpecification, Model, Task

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_phase5.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_phase5_crud():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing BRAND CREATE ---")
        brand_res = await AskAgentService.process_query(db, "Create a new brand named Tesla")
        print(f"Intent: {brand_res.get('intent')}")
        print(f"Text: {brand_res.get('text')}")
        tesla = db.query(VehicleSpecification).filter(VehicleSpecification.name == "Tesla").first()
        if tesla: print(f"Verified Tesla in DB: {tesla.id}")

        print("\n--- Testing MODEL CREATE ---")
        model_res = await AskAgentService.process_query(db, f"Create a model named Model 3 for brand {tesla.id if tesla else 'tesla_id'}")
        print(f"Intent: {model_res.get('intent')}")
        print(f"Text: {model_res.get('text')}")
        m3 = db.query(Model).filter(Model.name == "Model 3").first()
        if m3: print(f"Verified Model 3 in DB: {m3.id}")

        print("\n--- Testing TASK CREATE ---")
        task_res = await AskAgentService.process_query(db, "Create a task: 'Call John Wick about the Model 3'")
        print(f"Intent: {task_res.get('intent')}")
        print(f"Text: {task_res.get('text')}")
        t = db.query(Task).filter(Task.subject.like("%John Wick%")).first()
        if t: print(f"Verified Task in DB: {t.id} - {t.subject}")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test_ai_agent_phase5.db"):
            os.remove("./test_ai_agent_phase5.db")

if __name__ == "__main__":
    asyncio.run(test_phase5_crud())
