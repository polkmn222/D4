# NotebookLM Presentation Guide: From Code to PowerPoint

This guide explains how to use the generated **Architecture** and **ERD** documentation to create a professional PowerPoint presentation using **Google NotebookLM**.

## Workflow Overview

1.  **Upload Sources**: Upload `docs/architecture.md` and `docs/erd.md` to a new notebook in NotebookLM.
2.  **Generate Content**: Use the prompts below to extract structured slide content.
3.  **Refine & Export**: Copy the generated outlines into a PowerPoint template or use an AI PowerPoint generator (like Gamma.app or Tome.app) with the refined text.

---

## Strategic Prompts for NotebookLM

To get the best results, use these specific prompts in the NotebookLM chat:

### Prompt 1: High-Level Presentation Outline
> "Based on the provided architecture and ERD documents, create a 10-slide presentation outline for a technical review meeting. Ensure the outline covers the project overview, the layered architecture, core database entities (Contact, Lead, Opportunity), and key design principles like AI integration and modularity."

### Prompt 2: Slide-by-Slide Detailed Content
> "For each slide in the previous outline, provide the following:
> 1. A catchy title.
> 2. 3-4 concise bullet points explaining the technical details.
> 3. A suggestion for a visual or diagram (e.g., 'A flow chart showing the Request -> Router -> Service -> DB path')."

### Prompt 3: Explaining the Data Model (ERD)
> "Explain the relationship between 'Contacts', 'Leads', and 'Opportunities' in simple terms for a business stakeholder. Format this as a single slide with clear 'Before' (Lead) and 'After' (Contact/Opportunity) states."

### Prompt 4: Technical Deep Dive (Internal Team)
> "Identify the 3 most critical architectural decisions mentioned in the docs (e.g., Soft Deletion, Modularization, FastAPI) and explain why they were chosen to ensure long-term stability. Format this as a 'Technical Excellence' slide."

---

## Pro-Tips for PowerPoint Success

*   **Mermaid Diagrams**: Since PowerPoint doesn't native support Mermaid, you can take a screenshot of the diagrams in VS Code or GitHub and paste them directly into your slides.
*   **AI Design Pairing**: Once you have the text from NotebookLM, paste it into **Gamma.app** or **Canva Magic Design** to automatically generate a beautiful slide deck.
*   **Audio Overview**: Use NotebookLM's "Notebook Guide" -> "Deep Dive Conversation" to generate an AI podcast of two people discussing your project's architecture. This is a great way to rehearse or share a summary.

---

## Sample Slide Map

| Slide # | Focus | Key Content from Docs |
| :--- | :--- | :--- |
| 1 | Title | AI Ready CRM (D4) - Technical Architecture Review |
| 2 | Project Overview | Modernized CRM with Automotive focus & AI insights. |
| 3 | Ecosystem | FastAPI + SQLite + SQLAlchemy + Jinja2/HTMX. |
| 4 | Architecture Layers | Presentation -> Application -> Service -> Data Access. |
| 5 | AI Engine | Cerebras/Groq integration for real-time summaries. |
| 6 | Core Schema (ERD) | High-level overview of the relational model. |
| 7 | Contact Centricity | Explanation of the Account-to-Contact consolidation. |
| 8 | Asset Management | VIN-based tracking and Product mapping. |
| 9 | Sales Workflow | Lead qualification and Opportunity tracking. |
| 10 | Next Steps | Modular expansions and AI enhancements. |
