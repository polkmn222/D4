import logging
import re
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from db.models import AiIntentPattern, AiSynonym
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)


class AiIntelligenceService:
    @staticmethod
    def _is_optional_intelligence_runtime_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(
            fragment in message
            for fragment in (
                "similarity(",
                "function similarity",
                "ai_intent_patterns",
                "ai_synonyms",
                "does not exist",
                "undefined function",
                "undefined table",
            )
        )

    @classmethod
    def normalize_table_name(cls, token: str) -> str:
        """
        Maps singular or shorthand tokens to actual database table names.
        """
        if not token: return token
        mapping = {
            "lead": "leads",
            "contact": "contacts",
            "opportunity": "opportunities",
            "oppty": "opportunities",
            "opty": "opportunities",
            "brand": "vehicle_specifications",
            "model": "models",
            "product": "products",
            "asset": "assets",
            "message": "message_sends",
            "template": "message_templates"
        }
        return mapping.get(token.lower(), token)

    @classmethod
    def fix_sql_table_names(cls, sql: str) -> str:
        """
        Refined regex to only replace table names after FROM or JOIN keywords.
        Prevents accidental column name changes like l.model -> l.models.
        """
        if not sql: return sql
        
        # Targets words after FROM or JOIN (with optional space/newline)
        targets = ["lead", "contact", "opportunity", "product", "asset", "model", "brand", "template", "message"]
        
        fixed_sql = sql
        for target in targets:
            replacement = cls.normalize_table_name(target)
            if replacement == target: continue
            
            # Regex explanation: (?<=\bFROM\s|\bJOIN\s) matches if preceded by FROM/JOIN
            # \b{target}\b matches the specific table name as a whole word
            pattern = rf"(?<=\bFROM\s)\b{target}\b|(?<=\bJOIN\s)\b{target}\b"
            fixed_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
            
        return fixed_sql

    @classmethod
    @handle_agent_errors
    def find_best_matching_pattern(cls, db: Session, query: str, min_score: float = 0.4) -> Optional[Dict[str, Any]]:
        """
        Uses PostgreSQL pg_trgm similarity to find the closest matching successful prompt.
        If score is medium (0.4-0.7), returns a suggestion instead of direct execution.
        """
        if not query:
            return None
            
        stmt = text("""
            SELECT id, raw_prompt, mapped_intent, object_type, similarity(raw_prompt, :q) as score
            FROM ai_intent_patterns
            WHERE is_active = True
            AND similarity(raw_prompt, :q) > :min_score
            ORDER BY score DESC
            LIMIT 1
        """)
        
        try:
            result = db.execute(stmt, {"q": query, "min_score": min_score}).first()
        except Exception as exc:
            if cls._is_optional_intelligence_runtime_error(exc):
                logger.warning("Skipping DB intelligence pattern matching: %s", exc)
                return None
            raise

        if result:
            score = float(result.score)
            
            # 1. High Confidence -> Direct Execution
            if score >= 0.7:
                db.execute(
                    text("UPDATE ai_intent_patterns SET hit_count = hit_count + 1 WHERE id = :id"),
                    {"id": result.id}
                )
                db.commit()
                
                data = {
                    "id": result.id,
                    "prompt": result.raw_prompt,
                    "intent": result.mapped_intent,
                    "object_type": result.object_type,
                    "score": score
                }

                if result.mapped_intent == "OPEN_FORM" and result.object_type:
                    plural = result.object_type + "s" if not result.object_type.endswith("s") else result.object_type
                    if result.object_type == "message_template": plural = "message_templates"
                    data["form_url"] = f"/{plural}/new-modal"
                    data["text"] = f"I've opened the new {result.object_type} form for you below."

                return data
            
            # 2. Medium Confidence -> Conversational Suggestion
            else:
                return {
                    "intent": "CHAT",
                    "is_suggestion": True,
                    "suggestion_prompt": result.raw_prompt,
                    "text": f"I think you might want to **{result.mapped_intent.lower().replace('_', ' ')}** for **{result.object_type}**. Is that correct? (Suggested: \"{result.raw_prompt}\")",
                    "score": score,
                    "options": [
                        {"label": "Yes, do that", "value": result.raw_prompt},
                        {"label": "No, something else", "value": "help"}
                    ]
                }
                
        return None

    @classmethod
    @handle_agent_errors
    def get_synonym_mapping(cls, db: Session, term: str) -> Optional[str]:
        """
        Looks up a term in the synonym table.
        """
        try:
            synonym = db.query(AiSynonym).filter(
                func.lower(AiSynonym.synonym_term) == term.lower()
            ).first()
        except Exception as exc:
            if cls._is_optional_intelligence_runtime_error(exc):
                logger.warning("Skipping DB synonym lookup: %s", exc)
                return None
            raise
        return synonym.normalized_term if synonym else None

    @classmethod
    @handle_agent_errors
    def normalize_query_with_db(cls, db: Session, query: str) -> str:
        """
        Replaces noisy terms in query with normalized ones from DB.
        """
        words = query.split()
        normalized_words = []
        for word in words:
            norm = cls.get_synonym_mapping(db, word.strip("?,.!"))
            normalized_words.append(norm if norm else word)
        return " ".join(normalized_words)
