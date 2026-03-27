# Accuracy-First CRM AI Agent Architecture

This document outlines the strategic design for a high-precision CRM AI Agent utilizing a dual-API ensemble (Cerebras & Groq) and a multi-layered processing pipeline. The primary goal is to prioritize absolute accuracy and logical consistency over raw speed.

---

## 1. Core Principle: Hierarchical Filtering
To ensure 99.9% accuracy, every user query passes through four distinct layers of validation and reasoning.

### Layer 1: High-Speed Pattern Matching (Python/Regex)
*   **Latency:** < 10ms
*   **Method:** Uses hardcoded commands and regular expressions derived from `agent.txt` patterns.
*   **Scope:** Simple, unambiguous commands like "Show all leads" or "Search ID 1234".
*   **Action:** Returns an immediate response if a perfect match is found, bypassing API costs.

### Layer 2: Intent Drafting (Cerebras 8B - Llama 3.1)
*   **Latency:** ~200ms
*   **Role:** The "Drafter".
*   **Action:** Rapidly extracts basic entities (Names, Models, Brands) and suggests an initial intent.
*   **Data Source:** Uses 20,000+ examples from `agent.txt` and `agent2.txt` as background knowledge for entity recognition.

### Layer 3: Deep Reasoning & Judgment (Groq 70B - Llama 3.3)
*   **Latency:** 1s ~ 2s
*   **Role:** The "Final Judge & Architect".
*   **Action:** Performs a "Chain-of-Verification" (CoVe). It receives the user query, the draft from Cerebras, the CRM database schema (`models.py`), and the conversation context.
*   **Reasoning:** It cross-references the draft with business logic. For example, if Cerebras suggests a "Lead" lookup but the query mentions a "VIN", Groq corrects it to an "Asset" lookup.
*   **Context Resolution:** It resolves ambiguous pronouns like "that person" or "the car" by analyzing the `agent_flows.md` multi-turn scenarios.

### Layer 4: Logic Validation & Clarification
*   **Action:** A final Python-based check to ensure the LLM's output matches the system's executable capabilities.
*   **Clarification Gate:** If the `confidence_score` from Groq is below 0.95, the agent will not execute but will instead ask a clarification question: *"I'm 80% sure you want to update the status, but which record should I apply this to?"*

---

## 2. API Ensemble Strategy: Draft & Judge

| API | Model | Role | Why? |
| :--- | :--- | :--- | :--- |
| **Cerebras** | Llama 3.1 8B | **Drafter** | Exceptional speed for initial entity extraction. |
| **Groq** | Llama 3.3 70B | **Final Judge** | Superior reasoning and zero-shot/few-shot accuracy for complex logic. |

---

## 3. Step-by-Step High-Precision Workflow

1.  **Pre-processing:** Clean input, fix typos, and check for high-frequency direct commands.
2.  **Entity Extraction (Cerebras):** Identify keywords like `Name: John`, `Model: GV80`, `Brand: Genesis`.
3.  **Context Enrichment:** Fetch previous conversation state (e.g., the last viewed Lead ID).
4.  **Deep Reasoning (Groq):**
    *   Step A: Analyze user intent based on `agent_flows.md` logic.
    *   Step B: Map entities to the actual DB schema (`models.py`).
    *   Step C: Generate a structured JSON output with a confidence score.
5.  **Logic Guardrail:** Ensure all required fields for the intent are present.
6.  **Final Execution:** Return the structured data to the frontend for action.

---

## 4. Training Data Integration Strategy
*   **`agent.txt` / `agent2.txt`:** Used to build the Regex patterns for Layer 1 and the embedding index for Layer 2.
*   **`agent_flows.md`:** Used as "Few-shot" examples in the Groq 70B system prompt to teach the model how to maintain state and handle conversational flows.
*   **`agent_structure.md`:** Serves as the master mapping guide to ensure the AI uses the correct terminology across both English and Korean.

---

## 5. Expected Outcome
By using Groq 70B as a "Judge" over the Cerebras "Drafter," the system minimizes hallucinations and ensures that even ambiguous or multi-step requests are handled with professional-grade accuracy, providing a reliable experience for CRM power users.
