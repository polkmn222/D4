import re
from typing import Dict, Any, Optional

from ai_agent.debug import debug_event


class IntentPreClassifier:

    TYPO_MAP = {
        "laed": "lead",
        "leed": "lead",
        "leda": "lead",
        "contcat": "contact",
        "contax": "contact",
        "cntact": "contact",
        "cntct": "contact",
        "oportunity": "opportunity",
        "opportunitys": "opportunities",
        "oppty": "opportunity",
        "opty": "opportunity",
        "oppy": "opportunity",
        "opp": "opportunity",
        "opps": "opportunity",
        "templt": "message_template",
        "templat": "message_template",
        "tmpl": "message_template",
        "tpl": "message_template",
        "lds": "lead",
        "prodcut": "product",
        "brnad": "brand",
        "modle": "model",
        "aseet": "asset",
    }

    ACTION_CREATE = ["create", "add", "make", "build", "snag", "gimme", "spin up", "만들", "맹글", "맨들", "생성", "등록", "추가"]
    ACTION_READ = ["open", "show", "view", "read", "details", "grab", "fetch", "check", "inspect", "info", "lemme see", "열어", "열어봐", "보여", "보여주라", "보기", "상세"]
    ACTION_UPDATE = ["edit", "update", "change", "modify", "save", "tweak", "fix", "수정", "변경", "바꿔", "바까", "저장"]
    ACTION_DELETE = ["delete", "remove", "erase", "nuke", "dump", "삭제"]
    ACTION_QUERY = ["show", "list", "all", "every", "search", "find", "pull", "export", "전체", "목록", "보여", "불러", "조회"]

    OBJECT_MAP = {
        "lead": "lead",
        "leads": "lead",
        "leed": "lead",
        "laed": "lead",
        "리드": "lead",
        "리드를": "lead",
        "contact": "contact",
        "contacts": "contact",
        "contax": "contact",
        "contcat": "contact",
        "cntact": "contact",
        "cntct": "contact",
        "연락처": "contact",
        "연락처를": "contact",
        "opportunity": "opportunity",
        "opportunities": "opportunity",
        "oppty": "opportunity",
        "opty": "opportunity",
        "oppy": "opportunity",
        "oportunity": "opportunity",
        "기회": "opportunity",
        "기회를": "opportunity",
        "product": "product",
        "products": "product",
        "prod": "product",
        "prodcut": "product",
        "상품": "product",
        "상품을": "product",
        "asset": "asset",
        "assets": "asset",
        "aseet": "asset",
        "aset": "asset",
        "자산": "asset",
        "자산을": "asset",
        "brand": "brand",
        "brands": "brand",
        "brnad": "brand",
        "brnd": "brand",
        "브랜드": "brand",
        "model": "model",
        "models": "model",
        "modle": "model",
        "mdl": "model",
        "모델": "model",
        "template": "message_template",
        "templates": "message_template",
        "tmpl": "message_template",
        "tpl": "message_template",
        "message template": "message_template",
        "message templates": "message_template",
    }

    CREATE_REQUIREMENTS = {
        "lead": "last name and status",
        "contact": "last name and status",
        "opportunity": "name, stage, and amount",
        "brand": "name",
        "model": "name and brand",
        "product": "name and base price",
        "asset": "VIN",
    }

    CREATE_FIELD_HINTS = {
        "lead": ["last name", "last_name", "status", "email", "phone"],
        "contact": ["last name", "last_name", "status", "email", "phone"],
        "opportunity": ["name", "stage", "amount", "probability"],
        "brand": ["name", "description"],
        "model": ["name", "brand", "description"],
        "product": ["name", "price", "base price", "base_price"],
        "asset": ["vin", "status", "plate"],
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""
        t = text.lower().strip()
        t = re.sub(r"\'s\b", "", t)
        for typo, correct in cls.TYPO_MAP.items():
            t = re.sub(rf"\b{typo}\b", correct, t)
        return t

    @classmethod
    def _contains_action(cls, normalized: str, candidates: list[str]) -> bool:
        english_tokens = set(re.findall(r"[a-z]+", normalized))
        for word in candidates:
            if re.fullmatch(r"[a-z ]+", word):
                if " " in word:
                    if word in normalized:
                        return True
                elif word in english_tokens:
                    return True
            elif word in normalized:
                return True
        return False

    @classmethod
    def _extract_query_tail(cls, normalized: str, detected_key: str) -> Optional[str]:
        match = re.search(rf"\b{re.escape(detected_key)}\b(.*)$", normalized)
        if not match:
            return None

        tail = match.group(1).strip(" ?.!,:")
        if not tail:
            return None

        tail = re.sub(r"^(?:named|with|for)\s+", "", tail).strip()
        if tail in {"table", "list", "data", "record", "records"}:
            return None

        return tail or None

    @classmethod
    def normalize_object_type(cls, value: Any) -> Optional[str]:
        if not value:
            return None
        normalized = cls.normalize(str(value))
        return cls.OBJECT_MAP.get(normalized, normalized if normalized in set(cls.OBJECT_MAP.values()) else None)

    @classmethod
    def detect_object_mentions(cls, text: str) -> list[str]:
        normalized = cls.normalize(text)
        english_tokens = set(re.findall(r"[a-z]+", normalized))
        objects: list[str] = []
        ordered_items = sorted(cls.OBJECT_MAP.items(), key=lambda item: (-len(item[0]), item[0]))
        for key, value in ordered_items:
            if re.fullmatch(r"[a-z ]+", key):
                matched = key in english_tokens if " " not in key else key in normalized
            else:
                matched = key in normalized
            if matched and value not in objects:
                objects.append(value)
        return objects

    @classmethod
    def detect(cls, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None

        normalized = cls.normalize(text)
        english_tokens = set(re.findall(r"[a-z]+", normalized))

        ordered_items = sorted(cls.OBJECT_MAP.items(), key=lambda item: (-len(item[0]), item[0]))
        detected_object = None
        detected_key = None
        for key, value in ordered_items:
            if re.fullmatch(r"[a-z ]+", key):
                matched = key in english_tokens if " " not in key else key in normalized
            else:
                matched = key in normalized
            if matched:
                detected_object = value
                detected_key = key
                break

        # ---- Phase 50: Confidence Guardrails ----
        tokens = re.findall(r"\w+", normalized)
        noun_stack_query_markers = ("reddit", "google", "thread", "summary", "report", "history")
        has_simple_action = (
            cls._contains_action(normalized, cls.ACTION_CREATE)
            or cls._contains_action(normalized, cls.ACTION_QUERY)
            or cls._contains_action(normalized, cls.ACTION_READ)
            or cls._contains_action(normalized, cls.ACTION_UPDATE)
            or cls._contains_action(normalized, cls.ACTION_DELETE)
            or "form" in normalized
            or any(marker in normalized for marker in noun_stack_query_markers)
        )

        # Too long → likely complex sentence → send to LLM
        if len(tokens) > 7 and not (detected_object and has_simple_action):
            debug_event("preclassifier.skip_long_query", query=text, token_count=len(tokens))
            return None

        # Contains time/date/condition keywords → likely complex query
        complex_markers = [
            "today", "tomorrow", "yesterday", "this week", "last week",
            "이번", "저번", "내일", "어제", "조건", "where", "if",
            "just created", "recently created", "방금 생성", "방금 만든", "최근 생성", "최근 만든"
        ]
        if any(marker in normalized for marker in complex_markers):
            recent_object = None
            for key, value in cls.OBJECT_MAP.items():
                if key in normalized:
                    recent_object = value
                    break
            if recent_object and cls._contains_action(normalized, cls.ACTION_QUERY):
                result = {
                    "intent": "QUERY",
                    "object_type": recent_object,
                    "sql": None,
                    "score": 0.99,
                }
                debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
                return result
            return None

        if not detected_object:
            return None

        is_create = cls._contains_action(normalized, cls.ACTION_CREATE)
        is_query = cls._contains_action(normalized, cls.ACTION_QUERY)
        has_read = cls._contains_action(normalized, cls.ACTION_READ)
        has_update = cls._contains_action(normalized, cls.ACTION_UPDATE)
        has_recent_marker = any(marker in normalized for marker in ["latest", "last", "recent"])

        recent_query_markers = [
            "just created", "recently created", "방금 생성", "방금 만든", "최근 생성", "최근 만든"
        ]
        if any(marker in normalized for marker in recent_query_markers):
            return {
                "intent": "QUERY",
                "object_type": detected_object,
                "sql": None,
                "score": 0.99,
            }

        if is_create:
            # Phase 177: Always try to open form for Create if object is detected
            # unless specific data is already provided (then send to LLM)
            field_hints = cls.CREATE_FIELD_HINTS.get(detected_object, [])
            if any(hint in normalized for hint in field_hints) or ":" in text:
                return None
            
            plural = detected_object + "s" if not detected_object.endswith("s") else detected_object
            if detected_object == "message_template": plural = "message_templates"
            
            result = {
                "intent": "OPEN_FORM",
                "object_type": detected_object,
                "form_url": f"/{plural}/new-modal",
                "text": f"I've opened the new {detected_object} form for you below.",
                "score": 0.99,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if "form" in normalized and detected_object and any(token in normalized for token in ["fresh", "gimme", "spin up", "new"]):
            plural = detected_object + "s" if not detected_object.endswith("s") else detected_object
            if detected_object == "message_template":
                plural = "message_templates"
            result = {
                "intent": "OPEN_FORM",
                "object_type": detected_object,
                "form_url": f"/{plural}/new-modal",
                "text": f"I've opened the new {detected_object} form for you below.",
                "score": 0.97,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if is_query or normalized.strip() == detected_key:
            query_data = {}
            query_tail = cls._extract_query_tail(normalized, detected_key or detected_object)
            if query_tail:
                query_data["search_term"] = query_tail
                query_data["auto_open_single_result"] = True
            result = {
                "intent": "QUERY",
                "object_type": detected_object,
                "data": query_data,
                "sql": None,
                "score": 0.99,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        query_tail = cls._extract_query_tail(normalized, detected_key or detected_object)
        if (
            query_tail
            and not is_create
            and not has_update
            and not cls._contains_action(normalized, cls.ACTION_DELETE)
            and not has_read
            and any(marker in normalized for marker in noun_stack_query_markers)
        ):
            result = {
                "intent": "QUERY",
                "object_type": detected_object,
                "data": {"search_term": query_tail, "auto_open_single_result": True},
                "sql": None,
                "score": 0.95,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if has_recent_marker and (has_read or has_update):
            result = {
                "intent": "QUERY",
                "object_type": detected_object,
                "data": {"query_mode": "recent"},
                "sql": None,
                "score": 0.97,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if has_read and "open record for" in normalized:
            result = {
                "intent": "QUERY",
                "object_type": detected_object,
                "data": {},
                "sql": None,
                "score": 0.96,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if has_read and query_tail:
            result = {
                "intent": "QUERY",
                "object_type": detected_object,
                "data": {"search_term": query_tail, "auto_open_single_result": True},
                "sql": None,
                "score": 0.96,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if has_read:
            result = {
                "intent": "CHAT",
                "object_type": detected_object,
                "text": f"I can help you open a {detected_object}. Try `show all {detected_object}s`, `show recent {detected_object}s`, or mention the name you want to open.",
                "score": 0.95,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if has_update:
            # Phase 177: If explicit ID or "it" is mentioned, handled by Service or send to LLM
            # but for generic "edit lead", let's suggest selecting one first
            result = {
                "intent": "CHAT",
                "object_type": detected_object,
                "text": f"I can help update a {detected_object}. First show the record you want, select it, then tell me what to change. Or type `edit {detected_object} [ID]`.",
                "score": 0.95,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        if cls._contains_action(normalized, cls.ACTION_DELETE):
            result = {
                "intent": "CHAT",
                "object_type": detected_object,
                "text": f"I can help delete a {detected_object}. First show the record you want, select it, and then confirm the delete action.",
                "score": 0.95,
            }
            debug_event("preclassifier.detect", query=text, normalized=normalized, result=result)
            return result

        debug_event("preclassifier.no_match", query=text, normalized=normalized)
        return None
