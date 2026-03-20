# Phase 1: Database Design (AI-Ready CRM)

This design document finalizes the SQL schema for the SQLite database. The structure is optimized for Salesforce-like CRM functionality with built-in AI enhancement fields.

## 1. Contacts Table
The core entity for customer management.

```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    account_id INTEGER, -- Placeholder for future Account expansion
    
    -- 영업/마케팅 정보
    lead_source TEXT DEFAULT 'Manual', -- Web, Referral, Manual
    status TEXT DEFAULT 'New', -- New, Contacted, Qualified, Junk
    
    -- AI 및 데이터 관리 (AI Ready)
    description TEXT, -- Free-form notes for Groq summarization
    ai_summary TEXT, -- One-line summary for Cerebras
    last_interaction_at DATETIME, -- Updated by SureM/UI
    
    -- Standard timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 2. Messages Table
Tracking SMS interactions via SureM.

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    direction TEXT CHECK(direction IN ('Inbound', 'Outbound')),
    content TEXT NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, Sent, Failed
    provider_message_id TEXT, -- SureM API response ID
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);
```

## 3. Atomic Design Principles
- **Modularity**: Database initialization is separated from the CRUD logic.
- **Validation**: Strict unique constraints on email and phone to prevent duplicate leads.
- **Traceability**: `last_interaction_at` ensures AI can prioritize follow-ups.
