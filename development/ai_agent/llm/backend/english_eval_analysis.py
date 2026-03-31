from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QUESTION_WORD_RE = re.compile(r"\b(can you|could you|what|which|who|how|is|are|do|does)\b", re.I)
TYPO_OR_ALIAS_RE = re.compile(r"\b(cntct|contct|opty|oppy|opp|prodcut|aseet|brnad|tmpl|tpl)\b", re.I)
SHORT_QUERY_RE = re.compile(r"^\s*\S+(?:\s+\S+){0,2}\s*$")
RETRIEVAL_HINT_RE = re.compile(
    r"\b(summary|report|history|analytics|next steps|guide me|help me understand|workflow)\b",
    re.I,
)
DESTRUCTIVE_HINT_RE = re.compile(r"\b(delete|remove|wipe|drop|mass deletion|encrypted admin passwords)\b", re.I)
AMBIGUOUS_UPDATE_RE = re.compile(r"\b(update|edit|change)\b", re.I)


@dataclass(frozen=True)
class EnglishMismatchClassification:
    bucket: str
    reason: str


def is_english_query(user_input: str) -> bool:
    return all(ord(char) < 128 for char in user_input)


def classify_mismatch(result: dict[str, Any]) -> EnglishMismatchClassification:
    row = result["dataset_row"]
    actual = result["actual"]
    query = row["user_input"]
    expected_action = row["expected_action"]
    actual_action = actual["normalized_action"]
    expected_tool = row["expected_tool"]
    actual_tool = actual["tool"]

    if not is_english_query(query):
        return EnglishMismatchClassification("review", "non_english")

    if expected_action == "REFUSE" or DESTRUCTIVE_HINT_RE.search(query):
        return EnglishMismatchClassification("safety_hold", "destructive_or_refusal_path")

    if expected_action == "RETRIEVE_AND_ANSWER" or expected_tool in {"vector_retrieval", "message_history_query"}:
        return EnglishMismatchClassification("llm_clarification", "retrieval_or_explanatory_request")

    if TYPO_OR_ALIAS_RE.search(query):
        return EnglishMismatchClassification("deterministic", "common_typo_or_alias")

    if SHORT_QUERY_RE.match(query) and actual_action == "ASK_CLARIFICATION":
        return EnglishMismatchClassification("deterministic", "short_command_normalization")

    if expected_action in {"QUERY", "OPEN_FORM", "OPEN_RECORD"} and actual_action == "ASK_CLARIFICATION":
        if QUESTION_WORD_RE.search(query):
            return EnglishMismatchClassification("llm_clarification", "question_shaped_candidate_ranking")
        return EnglishMismatchClassification("deterministic", "under_normalized_crm_request")

    if expected_action == "CREATE" and actual_action == "OPEN_FORM":
        return EnglishMismatchClassification("deterministic", "create_vs_form_threshold")

    if expected_action == "ASK_CLARIFICATION" and actual_action in {"QUERY", "OPEN_FORM", "OPEN_RECORD"}:
        return EnglishMismatchClassification("review", "dataset_vs_runtime_policy_gap")

    if expected_action == "OPEN_RECORD" and actual_action == "QUERY":
        return EnglishMismatchClassification("deterministic", "recent_record_resolution")

    if AMBIGUOUS_UPDATE_RE.search(query) and actual_action == "ASK_CLARIFICATION":
        return EnglishMismatchClassification("llm_clarification", "ambiguous_update_wording")

    if RETRIEVAL_HINT_RE.search(query):
        return EnglishMismatchClassification("llm_clarification", "retrieval_hint")

    if expected_tool != actual_tool and actual_tool == "none":
        return EnglishMismatchClassification("llm_clarification", "tool_mapping_gap")

    return EnglishMismatchClassification("review", "unclassified")


def build_english_analysis(eval_results_dir: str | Path) -> dict[str, Any]:
    base = Path(eval_results_dir)
    files = sorted(path for path in base.glob("batch_*.json") if path.name != "batch_index.json")

    all_results: list[dict[str, Any]] = []
    buckets: dict[str, list[dict[str, Any]]] = {
        "deterministic": [],
        "llm_clarification": [],
        "safety_hold": [],
        "review": [],
    }
    reason_counts: Counter[str] = Counter()

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for result in payload["results"]:
            row = result["dataset_row"]
            if result["comparison"]["all_match"] or not is_english_query(row["user_input"]):
                continue
            classification = classify_mismatch(result)
            enriched = {
                "classification": classification.bucket,
                "classification_reason": classification.reason,
                **result,
            }
            all_results.append(enriched)
            buckets[classification.bucket].append(enriched)
            reason_counts[classification.reason] += 1

    return {
        "summary": {
            "english_mismatches": len(all_results),
            "bucket_counts": {name: len(items) for name, items in buckets.items()},
            "reason_counts": dict(reason_counts.most_common()),
        },
        "buckets": buckets,
    }


def write_english_analysis(analysis: dict[str, Any], output_dir: str | Path) -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "english_mismatch_summary.json").write_text(
        json.dumps(analysis["summary"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for bucket_name, items in analysis["buckets"].items():
        jsonl_path = out_dir / f"{bucket_name}.jsonl"
        jsonl_path.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items),
            encoding="utf-8",
        )

    markdown_lines = [
        "# English Eval Analysis",
        "",
        f"- english mismatches: `{analysis['summary']['english_mismatches']}`",
    ]
    for bucket, count in analysis["summary"]["bucket_counts"].items():
        markdown_lines.append(f"- {bucket}: `{count}`")
    markdown_lines.append("")
    markdown_lines.append("## Top Reasons")
    markdown_lines.append("")
    for reason, count in list(analysis["summary"]["reason_counts"].items())[:15]:
        markdown_lines.append(f"- {reason}: `{count}`")

    (out_dir / "english_mismatch_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )
