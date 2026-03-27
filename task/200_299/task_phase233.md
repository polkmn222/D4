# Phase 233 Task

## Approved Scope
- Lead lookup parity only for:
  - `product`
  - `model`
  - `brand`
- Narrow safe slice only:
  - search
  - select
  - preload
  - clear
  - submit ID

## Constraints
- Do not expand to opportunity lookups.
- Do not turn this into full lead-form parity.
- Unit tests only.
- No manual testing.
- Use a feature branch by default.
- Do not push unless explicitly asked.

## Priority Order
1. `product`
2. `model`
3. `brand`

## Fallback Rule
- If one of the lookup areas did not land cleanly, keep `product` as the priority slice and report the blocker before widening the phase.
