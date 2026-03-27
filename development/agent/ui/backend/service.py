from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


OBJECT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "lead": {
        "key": "lead",
        "label": "Lead",
        "plural_label": "Leads",
        "aliases": ("lead", "leads"),
        "list_url": "/leads",
        "new_url": "/leads/embedded-form",
        "detail_prefix": "/leads/",
        "edit_url_template": "/leads/embedded-form?id={id}",
        "quick_commands": ["all leads", "new lead", "open lead 00Q...", "edit lead 00Q..."],
    },
    "contact": {
        "key": "contact",
        "label": "Contact",
        "plural_label": "Contacts",
        "aliases": ("contact", "contacts"),
        "list_url": "/contacts",
        "new_url": "/contacts/new-modal",
        "detail_prefix": "/contacts/",
        "edit_url_template": "/contacts/new-modal?id={id}",
        "quick_commands": ["all contacts", "new contact", "open contact 003...", "edit contact 003..."],
    },
    "opportunity": {
        "key": "opportunity",
        "label": "Opportunity",
        "plural_label": "Opportunities",
        "aliases": ("opportunity", "opportunities", "opp", "opps"),
        "list_url": "/opportunities",
        "new_url": "/opportunities/new-modal",
        "detail_prefix": "/opportunities/",
        "edit_url_template": "/opportunities/new-modal?id={id}",
        "quick_commands": ["all opportunities", "new opportunity", "open opportunity 006...", "edit opportunity 006..."],
    },
    "asset": {
        "key": "asset",
        "label": "Asset",
        "plural_label": "Assets",
        "aliases": ("asset", "assets"),
        "list_url": "/assets",
        "new_url": "/assets/new-modal",
        "detail_prefix": "/assets/",
        "edit_url_template": "/assets/new-modal?id={id}",
        "quick_commands": ["all assets", "new asset", "open asset 02i...", "edit asset 02i..."],
    },
    "product": {
        "key": "product",
        "label": "Product",
        "plural_label": "Products",
        "aliases": ("product", "products"),
        "list_url": "/products",
        "new_url": "/products/new-modal",
        "detail_prefix": "/products/",
        "edit_url_template": "/products/new-modal?id={id}",
        "quick_commands": ["all products", "new product", "open product 01t...", "edit product 01t..."],
    },
    "brand": {
        "key": "brand",
        "label": "Brand",
        "plural_label": "Brands",
        "aliases": ("brand", "brands", "vehicle specification", "vehicle specifications"),
        "list_url": "/vehicle_specifications",
        "new_url": "/vehicle_specifications/new-modal?type=Brand",
        "detail_prefix": "/vehicle_specifications/",
        "edit_url_template": "/vehicle_specifications/new-modal?id={id}",
        "quick_commands": ["all brands", "new brand", "open brand a0B...", "edit brand a0B..."],
    },
    "model": {
        "key": "model",
        "label": "Model",
        "plural_label": "Models",
        "aliases": ("model", "models"),
        "list_url": "/models",
        "new_url": "/models/new-modal",
        "detail_prefix": "/models/",
        "edit_url_template": "/models/new-modal?id={id}",
        "quick_commands": ["all models", "new model", "open model a0M...", "edit model a0M..."],
    },
}

ACTION_ALIASES = {
    "all": "list",
    "list": "list",
    "show": "list",
    "open": "open",
    "show_record": "open",
    "read": "open",
    "new": "create",
    "create": "create",
    "add": "create",
    "edit": "edit",
    "update": "edit",
}

OPEN_PATTERNS = (
    re.compile(r"^(?:open|show|read)\s+(?P<object>[a-z\s]+?)\s+(?P<record_id>[a-z0-9]{3,18})$", re.IGNORECASE),
    re.compile(r"^(?P<object>[a-z\s]+?)\s+(?P<record_id>[a-z0-9]{3,18})$", re.IGNORECASE),
)
EDIT_PATTERNS = (
    re.compile(r"^(?:edit|update)\s+(?P<object>[a-z\s]+?)\s+(?P<record_id>[a-z0-9]{3,18})$", re.IGNORECASE),
)


def _normalize_token(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def supported_object_payloads() -> List[Dict[str, Any]]:
    payloads = []
    for definition in OBJECT_DEFINITIONS.values():
        payloads.append(
            {
                "key": definition["key"],
                "label": definition["label"],
                "plural_label": definition["plural_label"],
                "list_url": definition["list_url"],
                "new_url": definition["new_url"],
                "quick_commands": list(definition["quick_commands"]),
            }
        )
    return payloads


def resolve_object(token: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_token(token)
    for definition in OBJECT_DEFINITIONS.values():
        aliases = [_normalize_token(alias) for alias in definition["aliases"]]
        if normalized in aliases:
            return definition
    if normalized.endswith("s"):
        return resolve_object(normalized[:-1])
    return None


def build_agent_bootstrap_payload() -> Dict[str, Any]:
    starter_prompts = [
        "all leads",
        "new lead",
        "all contacts",
        "new opportunity",
        "open product 01t...",
        "edit model a0M...",
    ]
    return {
        "brand_name": "D5 Command Agent",
        "panel_title": "Object Workspace",
        "welcome_message": "Ask for any supported object in plain English. The agent opens the current D5 list, form, and detail pages in one workspace.",
        "supported_objects": supported_object_payloads(),
        "starter_prompts": starter_prompts,
        "default_command": starter_prompts[0],
    }


def _list_payload(definition: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "success",
        "action": "list",
        "object_key": definition["key"],
        "object_label": definition["plural_label"],
        "workspace_url": definition["list_url"],
        "message": f"Showing {definition['plural_label'].lower()} list view.",
    }


def _create_payload(definition: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "success",
        "action": "create",
        "object_key": definition["key"],
        "object_label": definition["label"],
        "workspace_url": definition["new_url"],
        "message": f"Opening a new {definition['label'].lower()} form.",
    }


def _open_payload(definition: Dict[str, Any], record_id: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "action": "open",
        "object_key": definition["key"],
        "object_label": definition["label"],
        "record_id": record_id,
        "workspace_url": f"{definition['detail_prefix']}{record_id}",
        "message": f"Opening {definition['label'].lower()} {record_id}.",
    }


def _edit_payload(definition: Dict[str, Any], record_id: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "action": "edit",
        "object_key": definition["key"],
        "object_label": definition["label"],
        "record_id": record_id,
        "workspace_url": definition["edit_url_template"].format(id=record_id),
        "message": f"Opening {definition['label'].lower()} {record_id} for edit.",
    }


def _help_payload(command: str) -> Dict[str, Any]:
    examples = [
        "all leads",
        "new contact",
        "open opportunity 006ABC123",
        "edit product 01tABC123",
    ]
    return {
        "status": "error",
        "action": "help",
        "message": f"Could not understand '{command}'. Try one of the supported patterns below.",
        "examples": examples,
    }


def parse_agent_command(command: str) -> Dict[str, Any]:
    raw_command = command.strip()
    normalized = _normalize_token(command)
    if not normalized:
        return _help_payload(command)

    for pattern in EDIT_PATTERNS:
        match = pattern.match(raw_command)
        if match:
            definition = resolve_object(match.group("object"))
            if definition:
                return _edit_payload(definition, match.group("record_id"))

    for pattern in OPEN_PATTERNS:
        match = pattern.match(raw_command)
        if match:
            definition = resolve_object(match.group("object"))
            if definition:
                return _open_payload(definition, match.group("record_id"))

    parts = normalized.split(" ", 1)
    if len(parts) == 2:
        action_token, object_token = parts
        action = ACTION_ALIASES.get(action_token)
        definition = resolve_object(object_token)
        if action == "list" and definition:
            return _list_payload(definition)
        if action == "create" and definition:
            return _create_payload(definition)

    definition = resolve_object(normalized)
    if definition:
        return _list_payload(definition)

    return _help_payload(command)
