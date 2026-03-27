# Walkthrough Phase 225: Create a general-purpose CRUD AI Agent in `agent_gem`

## Overview
In this phase, we have created a new AI agent in `development/agent_gem` that provides a conversational interface for CRUD operations on all CRM objects.

## Steps Taken

### 1. Initial Research and Backup
- Reviewed project documentation.
- Created a backup of the current project state in `backups/200_299/phase225/`.
- Initialized phase tracking files.

### 2. Implementation of `agent_gem`
- Created sub-app structure in `development/agent_gem/`.
- Implemented `AgentGemService` to handle CRUD operations on all objects (Lead, Contact, Opportunity, etc.).
- Integrated with `Gemini` LLM for intent detection and data extraction.
- Developed a modern chat UI with card and table views.
- Mounted the sub-app at `/agent-gem` in the main FastAPI application.

### 3. Verification
- Wrote unit tests in `development/agent_gem/test/test_agent_gem_service.py`.
- Verified intents for CHAT, QUERY (listing), and READ (detail card).
- All tests passed successfully.

## How to use
- The agent can be accessed at `/agent-gem/api/ui`.
- It supports natural language queries like "Show all leads", "Create a lead for John Doe", "Update lead lead-123 status to Qualified", etc.
- After create/edit, it automatically shows the record's detail view.
