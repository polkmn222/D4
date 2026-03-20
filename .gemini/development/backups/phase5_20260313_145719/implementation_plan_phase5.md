# CRM Development Plan - Phase 5: List View & Object Interaction

This phase focuses on creating dedicated, Salesforce-like list views for all objects (Contacts, Opportunities, Assets) to support efficient data management and CRUD operations directly from the list.

## User Review Required

> [!IMPORTANT]
> - **Reusable List View**: All objects will now have a dedicated page reachable via the navigation tabs.
> - **CRUD in List**: Each row in the list will support direct Edit/Delete actions.
> - **Contextual "New" Button**: Clicking a tab (e.g., "Contacts") will dynamically update the "New" button's destination.

## Proposed Changes

### UI & Templates

#### [NEW] [list_view.html](file:///Users/sangyeol.park@gruve.ai/D4/app/templates/list_view.html)
A reusable template for displaying list views of various objects (Leads, Contacts, Opportunities, etc.).

#### [MODIFY] [base.html](file:///Users/sangyeol.park@gruve.ai/D4/app/templates/base.html)
Update the navigation to support dynamic "New" button labels and links based on the active tab.

---

### Backend & Routes

#### [MODIFY] [web_router.py](file:///Users/sangyeol.park@gruve.ai/D4/app/api/web_router.py)
Add routes for:
- `GET /contacts` -> Contact List View
- `GET /opportunities` -> Opportunity List View
- `GET /assets` -> Asset List View
- Placeholder routes for Leads, Tasks, Accounts.

---

### Verification Plan

### Automated Tests
- **UI Tests**: Verify that clicking tabs redirects to the correct list view.
- **CRUD Tests**: Verify edit/delete flows from within the list view.

### Manual Verification
- Navigate through all tabs and ensure the list renders correctly.
- Click "New [Object]" and ensure the form opens for the correct entity.

### Backup Plan
- Consolidate core logic into `app_phase5.py` and backup `implementation_plan_phase5.md`.
