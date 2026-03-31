import json
from pathlib import Path

from ai_agent.llm.backend.english_eval_analysis import (
    build_english_analysis,
    classify_mismatch,
    write_english_analysis,
)


def _result(*, user_input: str, expected_action: str, expected_tool: str, actual_action: str, actual_tool: str):
    return {
        "dataset_row": {
            "user_input": user_input,
            "expected_action": expected_action,
            "expected_tool": expected_tool,
            "expected_object": "lead",
        },
        "actual": {
            "normalized_action": actual_action,
            "tool": actual_tool,
            "object_type": "lead",
        },
        "comparison": {"all_match": False},
    }


def test_classify_mismatch_marks_typo_as_deterministic():
    result = _result(
        user_input="show cntct ada",
        expected_action="QUERY",
        expected_tool="crm_query",
        actual_action="ASK_CLARIFICATION",
        actual_tool="none",
    )

    classified = classify_mismatch(result)

    assert classified.bucket == "deterministic"
    assert classified.reason == "common_typo_or_alias"


def test_classify_mismatch_marks_retrieval_as_llm_clarification():
    result = _result(
        user_input="show lead summary",
        expected_action="RETRIEVE_AND_ANSWER",
        expected_tool="vector_retrieval",
        actual_action="ASK_CLARIFICATION",
        actual_tool="none",
    )

    classified = classify_mismatch(result)

    assert classified.bucket == "llm_clarification"


def test_classify_mismatch_marks_destructive_request_as_safety_hold():
    result = _result(
        user_input="delete the last lead",
        expected_action="REFUSE",
        expected_tool="none",
        actual_action="QUERY",
        actual_tool="crm_query",
    )

    classified = classify_mismatch(result)

    assert classified.bucket == "safety_hold"


def test_build_and_write_english_analysis_outputs_bucket_files(tmp_path: Path):
    eval_dir = tmp_path / "eval_results"
    eval_dir.mkdir()
    payload = {
        "results": [
            _result(
                user_input="show cntct ada",
                expected_action="QUERY",
                expected_tool="crm_query",
                actual_action="ASK_CLARIFICATION",
                actual_tool="none",
            ),
            _result(
                user_input="show lead summary",
                expected_action="RETRIEVE_AND_ANSWER",
                expected_tool="vector_retrieval",
                actual_action="ASK_CLARIFICATION",
                actual_tool="none",
            ),
        ]
    }
    (eval_dir / "batch_0001_0100.json").write_text(json.dumps(payload), encoding="utf-8")

    analysis = build_english_analysis(eval_dir)
    output_dir = tmp_path / "analysis"
    write_english_analysis(analysis, output_dir)

    summary = json.loads((output_dir / "english_mismatch_summary.json").read_text(encoding="utf-8"))
    assert summary["english_mismatches"] == 2
    assert summary["bucket_counts"]["deterministic"] == 1
    assert summary["bucket_counts"]["llm_clarification"] == 1
    assert (output_dir / "deterministic.jsonl").exists()
    assert (output_dir / "llm_clarification.jsonl").exists()
