# Phase 317 Implementation Summary

## What Changed

Updated the active LLM reasoning docs to describe the current local decision eval model.

The docs now explicitly distinguish:

- live runtime intents such as `CHAT`, `QUERY`, `MANAGE`, and `OPEN_FORM`
- eval comparison labels such as `ASK_CLARIFICATION`, `REFUSE`, and `OPEN_RECORD`
- eval-side tool categories such as `crm_query`, `crm_write`, `vector_retrieval`, and `message_history_query`

The docs also now state that eval mismatches must be reviewed as one of:

- runtime defect
- eval-label or eval-mapping defect
- intentional product-policy mismatch
