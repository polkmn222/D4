# English Execution Plan

## Goal

Improve English-first AI-agent handling for typo-heavy, abbreviated, short, and ambiguous D5 requests without weakening safety.

## Current English Mismatch Split

- deterministic candidates: `413`
- LLM clarification candidates: `559`
- safety hold: `112`
- review bucket: `256`

## Recommended Order

1. deterministic normalization first
2. candidate ranking and clarification through Cerebras only when deterministic handling still leaves multiple plausible meanings
3. safety gate before any destructive or state-changing execution

## Deterministic First

Use deterministic handling for these buckets first:

- common typo or alias normalization
- short command normalization
- recent-record opening patterns
- create-versus-form threshold tuning
- under-normalized CRM requests that already point clearly to one object and one likely action

Representative examples:

- `show cntct ada`
- `opp recent`
- `open lead form`
- `find latest lead`

## Cerebras Clarification Path

Use Cerebras as a bounded ambiguity resolver and clarification writer, not as an unrestricted executor.

Best-fit cases:

- retrieval or explanatory requests
- question-shaped requests with more than one plausible CRM interpretation
- ambiguous update wording where the object is likely known but the exact requested action is not safe to execute yet
- tool-mapping gaps where the user intent seems CRM-related but the runtime currently falls back too early

Representative examples:

- `which lead is hot`
- `show lead summary`
- `can you get info on lead`
- `update the brand with the new details`

## Safety Gate

Keep these categories out of eager execution even if Cerebras proposes a likely interpretation:

- delete or remove requests without one validated target
- bulk or mass-deletion wording
- encrypted password or database access requests
- short destructive phrases such as `delete last one`

Representative examples:

- `delete the last lead`
- `drop the database`
- `wipe the model table`

## Immediate Next Coding Targets

1. extend English typo and alias normalization in `IntentPreClassifier`
2. add deterministic handling for recent-record open phrases
3. add a bounded Cerebras clarification path for English question-shaped CRM requests
4. preserve deterministic safety validation before any update or delete execution
