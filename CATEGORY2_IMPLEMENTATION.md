# ClearFile — Category 2 Agentic AI Engineering Evidence Pack

## What this prototype demonstrates

ClearFile is an explainable document-evidence review prototype. It extracts fields from uploaded applicant documents, compares evidence across documents, highlights anomalies, and leaves the final decision to a human officer. It must be demonstrated only with fictional/sample data.

### Agentic workflow
- A **Supervisor** validates the request, starts three worker agents concurrently, gathers their structured results, builds a summary, and checkpoints progress.
- **EvidenceWorker** counts the extracted evidence and documents.
- **ConsistencyWorker** reports mismatched and not-available fields.
- **RiskWorker** surfaces anomaly items for officer attention.
- Pydantic schemas validate workflow inputs and worker outputs.
- A bounded retry policy (2 attempts), exponential backoff, 12-second worker timeout, concurrency semaphore, explicit failed-worker results, and completion guard make failures visible.
- SQLite stores run checkpoints; a JSONL audit trace records workflow start, worker start/retry/completion/failure, and supervisor completion. Trace records avoid copying document values.
- Every run preserves `human_approval_required=True` and `decision=NOT_DECIDED`.

### Background jobs
- A persistent SQLite queue stores job metadata and application IDs (not duplicate document contents).
- Jobs move through `queued → running → completed/failed` states.
- Atomic SQLite claiming prevents two worker processes from claiming the same queued job.
- Retry attempts are bounded. A stale running lease is recovered after 15 minutes, subject to the attempt limit.
- Run multiple queue workers with `python -m agentic.job_worker --workers 2` (maximum 4). Stop with Ctrl+C.
- The Streamlit Agent Workflow page can enqueue a background review and show recent job states. A separate worker process must be running to process queued jobs.

### MCP
- `mcp_tools/server.py` exposes two read-only MCP tools: `get_application_summary` and `list_field_findings`.
- `mcp_tools/client.py` initializes the MCP session, discovers available tools, and invokes both tools.
- The tools return verification evidence only; they cannot approve or reject an application.

### Telemetry and usage reporting
- `data/agent_workflow.jsonl` contains structured event traces, including successful/failed Gemini chat calls, model name, latency, and provider-reported token counts when available. Prompts and document values are not written to this trace.
- `data/agent_runs.db` contains workflow checkpoints and background job state.
- The supervisor-worker workflow uses deterministic Python workers, not LLM calls. Therefore its token count and model cost are explicitly `Not applicable`; no invented token/cost figures are reported. Gemini chat usage is tracked separately. Monetary cost is not estimated because provider pricing is not configured.

## Run locally (PowerShell)

Run commands from the `ClearFile_Complete` folder after activating the project's virtual environment and installing `requirements.txt`.

```powershell
python -m unittest discover -s tests -v
python -m agentic.demo
```

Start the Streamlit app:

```powershell
python -m streamlit run app.py
```

### Background queue demonstration
1. In the app, open **Agent Workflow**, select a saved application, and click **Queue background review**.
2. Open a second PowerShell window in `ClearFile_Complete`, activate the same environment, and run:

```powershell
python -m agentic.job_worker --workers 2
```

3. Refresh the Agent Workflow page to see the job state update. Stop the worker with Ctrl+C.

### MCP client demonstration
Use a saved application ID from the app (for example, a sample ID displayed in Reports):

```powershell
python -m mcp_tools.client YOUR_APPLICATION_ID
```

The client should print the discovered tools and the result of invoking each tool. The MCP server is launched by the client over stdio; no separate server terminal is needed for this command.

## Evidence checklist for evaluation
- [ ] Screenshot of New Application with four fictional sample documents.
- [ ] Screenshot of a full-match workflow and a mismatch workflow.
- [ ] Screenshot of the three worker results, supervisor summary, run ID, and `NOT_DECIDED` human-review notice.
- [ ] Screenshot of saved checkpoints and JSONL event trace.
- [ ] Terminal output from `python -m unittest discover -s tests -v`.
- [ ] Terminal output from `python -m mcp_tools.client YOUR_APPLICATION_ID` showing tool discovery and both invocations.
- [ ] Screenshot/terminal evidence of background job moving from queued to completed.
- [ ] Include `ARCHITECTURE.md` in the submission.

## Requirement coverage and honest limitations
| Requirement area | Implementation/evidence | Status |
|---|---|---|
| Agent roles, objectives, instructions | Named supervisor and three purpose-specific workers | Implemented |
| Structured output and validation | Pydantic request/result schemas | Implemented |
| Multi-agent orchestration | Async supervisor dispatches concurrent workers | Implemented |
| Shared state and completion conditions | Shared workflow state, completion guard, explicit failures | Implemented |
| State persistence/checkpointing | SQLite checkpoint after start, each worker result, and completion | Implemented |
| MCP server/client and tool discovery | Two read-only tools plus stdio client | Implemented; demonstrate live |
| Async/background execution | Async worker orchestration plus persistent SQLite job queue | Implemented; demonstrate live |
| Retry, timeout, failure visibility | Bounded retries, backoff, timeout, failed-worker records | Implemented |
| Queue recovery and concurrency | Atomic job claiming, stale lease recovery, configurable worker processes | Prototype implementation; test during demo |
| Logging/monitoring | JSONL event trace, timestamps, run/job IDs, worker status/duration | Implemented |
| LLM token/cost reporting | Deterministic workflow uses no LLM; correctly reports N/A | Not applicable to this workflow |
| Model fallback for worker agents | Workers are deterministic Python functions, not LLM calls | Not implemented |
| Distributed production deployment | Local SQLite and local worker processes only | Not implemented |
| Human approval | Always remains `NOT_DECIDED`; officer reviews source evidence | Implemented |

This is a student prototype, not a production banking or lending system. Do not use real applicant data for demonstrations. Verify all source documents manually; the software does not make an eligibility, approval, or rejection decision.

## Additional reliability validation

The extended test suite in `tests/test_resilience.py` exercises persisted job completion, bounded retry exhaustion, stale lease recovery, atomic single-worker claiming under a two-thread race, partial worker failure isolation, and the human-decision gate. Run all tests with:

```powershell
python -m unittest discover -s tests -v
```

These tests validate the local SQLite prototype only. They do not establish distributed/production reliability, provider model fallback, or external MCP deployment. The live MCP client and background worker demonstrations in the evidence checklist remain required on the evaluator's machine.
