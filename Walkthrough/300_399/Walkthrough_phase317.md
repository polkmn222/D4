# Phase 317 Walkthrough

## Overview

This phase refreshed the LLM reasoning documentation to match the current local eval workflow added in phase 316.

The main clarification added in this phase is that the JSONL eval dataset is not the runtime API contract. It is a comparison layer built on top of the live service behavior.

## Updated Topics

- runtime intent versus eval label vocabulary
- current eval normalization assumptions
- how to review mismatches safely
- why batch review in fixed groups such as 100 rows is the preferred local workflow

## Validation

This was a documentation-only phase.

No code tests were run.
