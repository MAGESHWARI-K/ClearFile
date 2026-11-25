# ClearFile Architecture

```mermaid
flowchart TD
    U[Officer / User] --> UI[Streamlit UI]
    UI --> UP[Document Upload & Extraction]
    UP --> DB[(SQLite Application Store)]
    UI --> CHAT[Gemini-powered ClearFile AI Chat]
    CHAT --> GEM[Google Gemini API]
    UI --> SUP[Workflow Supervisor]
    SUP --> VAL[Pydantic Request Validation]
    VAL --> EW[Evidence Worker]
    VAL --> CW[Consistency Worker]
    VAL --> RW[Risk Worker]
    EW --> SH[Shared Workflow State]
    CW --> SH
    RW --> SH
    SH --> CP[(SQLite Checkpoints)]
    SH --> TRACE[JSONL Audit Event Trace]
    UI --> Q[(Persistent Background Job Queue)]
    Q --> W[Background Worker Processes]
    W --> SUP
    MCP[MCP stdio Client] <--> MS[MCP Server]
    MS --> DB
    UI --> HUMAN[Human Officer Review]
    HUMAN --> DEC[Manual decision outside AI workflow]
```

## Trust boundary
- The AI workflow can summarize, compare, and flag evidence. It cannot set an approval/rejection decision.
- Gemini chat requests and selected application context are sent to Google's Gemini API when the feature is used; use fictional sample data in demonstrations.
- MCP tools are read-only and expose only local application summary/field findings.
- Checkpoints, job queue and audit trace are local files under `data/`; do not commit them to Git.
