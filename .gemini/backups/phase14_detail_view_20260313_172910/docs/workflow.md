# Orchestration Workflow

## Phase-Based Execution Sequence
Every development phase must follow this strict sequence to ensure quality and traceability:

### 1. Planning Phase
- **Update `task.md`**: Define specific goals.
- **Review `blueprint.md`**: Ensure design aligns with architecture.
- **Consult `spec.md`**: Define what success looks like for the new feature.

### 2. Execution Phase
- **Atomic Implementation**: Code changes in small, logical chunks (Models -> Services -> Routes -> UI).
- **Proactive Documentation**: Update relevant documentation as the code evolves.

### 3. Verification Phase
- **Unit Testing**: Run `pytest` for all core services.
- **Manual Verification**: Test UI flows (Modals, Buttons, Forms).
- **Quality Assurance**: Check for Salesforce-style validation and aesthetics.

### 4. Completion Phase
- **Walkthrough Generation**: Document what was done and provide proof of work.
- **Global Backup**: Run `backups/global_backup.py` with the appropriate Phase label.
- **User Notification**: Inform the user of completion and request feedback.
