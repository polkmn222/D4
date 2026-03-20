# CRM Development Plan - Phase 6: Automotive Transformation & Lead Conversion

This phase pivots the CRM into a specialized Automotive domain and implements the core Salesforce workflow of Lead Conversion.

## User Review Required

> [!IMPORTANT]
> - **Lead Object**: A new entity for tracking potential interests.
> - **Lead Conversion**: A service to transform a Lead into an Account and an Opportunity.
> - **Person Accounts**: Accounts that represent individuals, merging Account/Contact logic.
> - **Reporting Foundation**: Aggregation logic for future dashboards.

## Proposed Changes

### Database & Models [MODIFY]

#### [MODIFY] [models.py](file:///Users/sangyeol.park@gruve.ai/D4/app/models.py)
- **Lead**: `id`, `first_name`, `last_name`, `email`, `phone`, `company`, `status`, `is_converted` (bool).
- **Account**: add `is_person_account` (bool).
- **Product**: `id`, `name` (Model), `brand`, `price`.
- **Opportunity**: Link `lead_id` (source).

---

### Logic & Services [NEW]

#### [NEW] [lead_service.py](file:///Users/sangyeol.park@gruve.ai/D4/app/services/lead_service.py)
- `convert_lead(lead_id)`: Atomic operation that:
  1. Creates an **Account** (Person or Corporate).
  2. Creates an **Opportunity** linked to the account.
  3. Marks the **Lead** as converted.

---

### UI & Templates [MODIFY]

#### [MODIFY] [web_router.py](file:///Users/sangyeol.park@gruve.ai/D4/app/api/web_router.py)
- Routes for `/leads` (List View), `/leads/new`, and `/leads/{id}/convert`.
- Dashboard updates to show "Lead Conversion" activity.

---

### Verification Plan

### Automated Tests
- **Conversion Test**: Create a lead, run conversion, and verify the resulting Account and Opportunity exist.

### Manual Verification
- Navigate to the Leads tab, create a lead, and click "Convert".
- Verify the lead disappears from the active list and the new account appears.

### Backup Plan
- **100% Full Backup**: Every file and the implementation plan will be backed up into `backups/automotive_phase6_[timestamp]/`.
