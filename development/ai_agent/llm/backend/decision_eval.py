from __future__ import annotations

import argparse
import asyncio
import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, patch

from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier
from ai_agent.ui.backend.service import AiAgentService


REQUIRED_DATASET_FIELDS = {
    "id",
    "user_input",
    "expected_object",
    "expected_action",
    "expected_tool",
    "expected_retrieval_needed",
}
RETRIEVAL_TOOLS = {"vector_retrieval", "message_history_query"}
REFUSAL_TEXT_MARKERS = (
    "i can only help with d5 crm work",
    "i cannot query or manage attachments directly",
)
REFUSAL_QUERY_MARKERS = (
    "encrypted admin passwords",
    "drop the database",
    "wipe the",
    "mass deletion",
)


@dataclass(frozen=True)
class EvalDatasetRow:
    id: str
    user_input: str
    expected_object: str
    expected_action: str
    expected_tool: str
    expected_retrieval_needed: bool
    source_file: Optional[str] = None
    phase: Optional[str] = None
    context: str = ""
    difficulty: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class EvalDecision:
    raw_intent: str
    normalized_action: str
    object_type: Optional[str]
    tool: str
    retrieval_needed: bool
    source: str
    raw_output: dict[str, Any]


def load_eval_dataset(dataset_path: str | Path) -> list[EvalDatasetRow]:
    rows: list[EvalDatasetRow] = []
    path = Path(dataset_path)

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            payload = json.loads(line)
            missing = sorted(REQUIRED_DATASET_FIELDS - payload.keys())
            if missing:
                raise ValueError(
                    f"{path}:{line_number} is missing required fields: {', '.join(missing)}"
                )

            rows.append(
                EvalDatasetRow(
                    id=str(payload["id"]),
                    user_input=str(payload["user_input"]),
                    expected_object=str(payload["expected_object"]).lower(),
                    expected_action=str(payload["expected_action"]).upper(),
                    expected_tool=str(payload["expected_tool"]),
                    expected_retrieval_needed=bool(payload["expected_retrieval_needed"]),
                    source_file=payload.get("source_file"),
                    phase=payload.get("phase"),
                    context=str(payload.get("context") or ""),
                    difficulty=payload.get("difficulty"),
                    notes=payload.get("notes"),
                )
            )

    return rows


async def capture_runtime_decision(
    *,
    db: Any,
    user_input: str,
    conversation_id: str,
    selection: Optional[dict[str, Any]] = None,
    language_preference: Optional[str] = None,
) -> tuple[dict[str, Any], str]:
    captured_agent_output: dict[str, Any] | None = None

    async def _capture_execute(
        _db: Any,
        agent_output: dict[str, Any],
        _user_query: str,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        nonlocal captured_agent_output
        captured = deepcopy(agent_output)
        captured["_decision_eval_source"] = "execute_intent_input"
        captured_agent_output = deepcopy(captured)
        return captured

    execute_mock = AsyncMock(side_effect=_capture_execute)
    with patch.object(AiAgentService, "_execute_intent", execute_mock):
        response = await AiAgentService.process_query(
            db=db,
            user_query=user_input,
            conversation_id=conversation_id,
            selection=selection,
            language_preference=language_preference,
        )

    if isinstance(response, dict):
        source = str(response.pop("_decision_eval_source", "direct_response"))
        return response, source

    if isinstance(captured_agent_output, dict):
        source = str(captured_agent_output.pop("_decision_eval_source", "execute_intent_input"))
        return captured_agent_output, source

    return {"intent": "CHAT", "text": "Eval runner could not capture a runtime decision."}, "missing_response"


def normalize_runtime_decision(
    runtime_output: dict[str, Any],
    *,
    user_input: str,
    source: str,
) -> EvalDecision:
    raw_intent = str(runtime_output.get("intent") or "CHAT").upper()
    object_type = runtime_output.get("object_type")
    if object_type is not None:
        raw_object_type = str(object_type).lower()
        object_type = IntentPreClassifier.normalize_object_type(raw_object_type) or raw_object_type
    text = str(runtime_output.get("text") or "")
    normalized_action = _normalize_action(raw_intent, user_input=user_input, text=text)
    tool = _infer_tool(raw_intent, normalized_action, runtime_output, user_input=user_input)
    retrieval_needed = tool in RETRIEVAL_TOOLS

    return EvalDecision(
        raw_intent=raw_intent,
        normalized_action=normalized_action,
        object_type=object_type,
        tool=tool,
        retrieval_needed=retrieval_needed,
        source=source,
        raw_output=deepcopy(runtime_output),
    )


def compare_eval_row(row: EvalDatasetRow, actual: EvalDecision) -> dict[str, Any]:
    comparisons = {
        "expected_object": {
            "expected": row.expected_object,
            "actual": actual.object_type,
            "match": row.expected_object == actual.object_type,
        },
        "expected_action": {
            "expected": row.expected_action,
            "actual": actual.normalized_action,
            "match": row.expected_action == actual.normalized_action,
        },
        "expected_tool": {
            "expected": row.expected_tool,
            "actual": actual.tool,
            "match": row.expected_tool == actual.tool,
        },
        "expected_retrieval_needed": {
            "expected": row.expected_retrieval_needed,
            "actual": actual.retrieval_needed,
            "match": row.expected_retrieval_needed == actual.retrieval_needed,
        },
    }

    return {
        "row_id": row.id,
        "all_match": all(item["match"] for item in comparisons.values()),
        "comparisons": comparisons,
    }


async def run_eval(
    *,
    db: Any,
    dataset_path: str | Path,
    output_path: str | Path,
    limit: Optional[int] = None,
    language_preference: str = "eng",
) -> dict[str, Any]:
    rows = load_eval_dataset(dataset_path)
    if limit is not None:
        rows = rows[:limit]

    results: list[dict[str, Any]] = []
    summary = {
        "rows": len(rows),
        "full_match_rows": 0,
        "field_matches": {
            "expected_object": 0,
            "expected_action": 0,
            "expected_tool": 0,
            "expected_retrieval_needed": 0,
        },
    }

    for index, row in enumerate(rows, start=1):
        runtime_output, source = await capture_runtime_decision(
            db=db,
            user_input=row.user_input,
            conversation_id=f"decision-eval-{row.id}-{index}",
            language_preference=language_preference,
        )
        actual = normalize_runtime_decision(runtime_output, user_input=row.user_input, source=source)
        comparison = compare_eval_row(row, actual)

        if comparison["all_match"]:
            summary["full_match_rows"] += 1
        for field_name, field_result in comparison["comparisons"].items():
            if field_result["match"]:
                summary["field_matches"][field_name] += 1

        results.append(
            {
                "dataset_row": asdict(row),
                "actual": asdict(actual),
                "comparison": comparison,
            }
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_path": str(Path(dataset_path)),
        "output_path": str(Path(output_path)),
        "summary": summary,
        "results": results,
    }
    write_eval_report(report, output_path)
    return report


def write_eval_report(report: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def build_default_output_path() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("learning/eval_results") / f"decision_eval_{timestamp}.json"


def _normalize_action(raw_intent: str, *, user_input: str, text: str) -> str:
    if raw_intent == "MANAGE":
        return "OPEN_RECORD"
    if raw_intent in {"QUERY", "OPEN_FORM", "OPEN_RECORD", "CREATE", "UPDATE"}:
        return raw_intent
    if raw_intent == "CHAT":
        normalized_query = user_input.lower()
        normalized_text = text.lower()
        if any(marker in normalized_text for marker in REFUSAL_TEXT_MARKERS) or any(
            marker in normalized_query for marker in REFUSAL_QUERY_MARKERS
        ):
            return "REFUSE"
        return "ASK_CLARIFICATION"
    return raw_intent


def _infer_tool(
    raw_intent: str,
    normalized_action: str,
    runtime_output: dict[str, Any],
    *,
    user_input: str,
) -> str:
    if "tool" in runtime_output:
        return str(runtime_output["tool"])

    if raw_intent in {"QUERY", "MANAGE"} or normalized_action == "OPEN_RECORD":
        return "crm_query"
    if raw_intent in {"CREATE", "UPDATE", "DELETE"}:
        return "crm_write"
    if normalized_action == "RETRIEVE_AND_ANSWER":
        if "history" in user_input.lower():
            return "message_history_query"
        return "vector_retrieval"
    return "none"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a minimal decision-layer eval for the local AI agent.")
    parser.add_argument(
        "--dataset",
        default="learning/eval_dataset_expanded.jsonl",
        help="Path to the JSONL eval dataset.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to the structured JSON result file. Defaults to learning/eval_results/<timestamp>.json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit for a smaller local run.",
    )
    args = parser.parse_args(argv)

    from db.database import SessionLocal

    output_path = Path(args.output) if args.output else build_default_output_path()
    db = SessionLocal()
    try:
        asyncio.run(
            run_eval(
                db=db,
                dataset_path=args.dataset,
                output_path=output_path,
                limit=args.limit,
            )
        )
    finally:
        db.close()

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
