# Task Phase 225: Create a general-purpose CRUD AI Agent in `agent_gem`

## Scope
- Create a new AI agent in `development/agent_gem`.
- The agent should support human-like conversation for CRUD operations on all CRM objects.
- Objects include: `Contact`, `Lead`, `Opportunity`, `Asset`, `Product`, `VehicleSpecification`, `Model`, `MessageSend`, `MessageTemplate`, `Attachment`.
- Implement Create -> Read (detail view) and Edit -> Read (refreshed detail view) flows.
- Implement a "List View" feature (e.g., when the user asks "Show all leads").
- Follow the project's architecture and UI standards.
- Ensure the agent integrates well with the existing FastAPI application.

## Constraints
- Unit tests are mandatory.
- Manual testing is forbidden.
- Follow existing UI standards and architectural patterns.
- Do not modify existing code before user confirmation of the plan.
- Perform backups as requested.

## Success Criteria
- A new agent exists in `development/agent_gem`.
- The agent can perform CRUD on all CRM objects via conversation.
- The agent can display list views for all objects.
- All unit tests pass.
