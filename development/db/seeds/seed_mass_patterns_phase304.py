import os
import sys
import re

# Add development directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "development"))

from db.database import SessionLocal
from db.models import AiIntentPattern
from web.backend.app.utils.sf_id import get_id

PROMPT_SOURCE_FILES = [
    "learning/agent.txt",
    "learning/phase1_user_simulation_answers.md",
    "learning/phase5_cycle3_final_results.md",
]


def _discover_prompt_source():
    for file_path in PROMPT_SOURCE_FILES:
        if os.path.exists(file_path):
            return file_path
    return None


def extract_prompts(file_path):
    if not file_path or not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    prompts = re.findall(r'\*\*\d+\. Q: `(.+?)`\*\*', content)
    if prompts:
        return prompts

    fallback_prompts = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('###'):
            continue
        if line.startswith('- '):
            line = line[2:]
        fallback_prompts.append(line)
    return fallback_prompts

def map_intent_and_object(prompt):
    p_low = prompt.lower()
    
    # Default
    intent = "QUERY"
    obj = "lead"
    
    # Object detection
    if "contact" in p_low: obj = "contact"
    elif "opportunit" in p_low or "oppty" in p_low or "opty" in p_low: obj = "opportunity"
    elif "brand" in p_low: obj = "brand"
    elif "model" in p_low: obj = "model"
    elif "product" in p_low: obj = "product"
    elif "asset" in p_low: obj = "asset"
    elif "template" in p_low or "tmpl" in p_low: obj = "message_template"
    
    # Intent detection
    if any(k in p_low for k in ["create", "add", "new", "make"]):
        intent = "OPEN_FORM"
    elif any(k in p_low for k in ["edit", "update", "change", "fix", "tweak"]):
        intent = "UPDATE"
    elif any(k in p_low for k in ["delete", "remove", "nuke"]):
        intent = "DELETE"
    elif any(k in p_low for k in ["show", "list", "all", "view", "find", "search", "pull", "who"]):
        intent = "QUERY"
        
    return intent, obj

def seed_mass_patterns():
    db = SessionLocal()
    input_file = _discover_prompt_source()
    
    try:
        if not input_file:
            raise FileNotFoundError("No learning prompt source was found for AI intent pattern seeding.")
        print(f"Extracting prompts from {input_file}...")
        raw_prompts = extract_prompts(input_file)
        print(f"Found {len(raw_prompts)} prompts.")
        
        patterns_to_add = []
        seen_prompts = set()
        
        # Check existing prompts in DB to avoid duplicates
        existing = db.query(AiIntentPattern.raw_prompt).all()
        seen_prompts.update([e[0] for e in existing])
        
        for prompt in raw_prompts:
            if prompt in seen_prompts: continue
            
            intent, obj = map_intent_and_object(prompt)
            
            patterns_to_add.append(AiIntentPattern(
                id=get_id("AiPat"),
                raw_prompt=prompt,
                mapped_intent=intent,
                object_type=obj,
                is_best_case=False # These are mass injected, not manually curated
            ))
            seen_prompts.add(prompt)
            
            # Batch add every 500
            if len(patterns_to_add) >= 500:
                db.add_all(patterns_to_add)
                db.commit()
                print(f"Committed {len(patterns_to_add)} patterns...")
                patterns_to_add = []
        
        if patterns_to_add:
            db.add_all(patterns_to_add)
            db.commit()
            print(f"Committed final {len(patterns_to_add)} patterns.")
            
        print("Mass seeding completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during mass seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_mass_patterns()
