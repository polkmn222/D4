# Phase 222 Task

## Goal

Stop the standalone lead workspace from flashing the web lead detail screen during save redirects and make the standalone shell keep the latest interaction visible.

## Scope

- Hide the embedded iframe while redirect transitions are happening.
- Reveal the iframe only for stable embedded lead form routes.
- Auto-scroll the standalone main workspace toward the latest form or post-save card state.
- Update focused unit tests and docs for the redirect/scroll contract.

## Constraints

- Keep the shared embedded lead form and post-save card flow intact.
- Validate with unit tests only.
