# ClearFile – Complete Student Prototype

## Run on Windows (VS Code)
1. Extract this ZIP.
2. Open the `ClearFile_Complete` folder in VS Code (the folder containing `app.py` and `requirements.txt`).
3. Open Terminal and run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

Alternatively, double-click `run_clearfile.bat`.

## Enable the Gemini-powered assistant
1. Create a Gemini API key in Google AI Studio.
2. Copy `.env.example` to a new file named `.env` in this folder.
3. Replace `your_gemini_api_key_here` with your key.
4. Save and restart Streamlit.

The ClearFile AI page works in a limited evidence-summary mode without a key; natural-language generative chat requires the Gemini API key and internet access. API availability, quotas and possible charges depend on Google's current terms and your account. Never commit or share your `.env` file.

## Included
- Dashboard, New Application, Reports, ClearFile AI and About pages
- TXT/PDF/image document intake (image OCR requires Tesseract installed separately)
- Field extraction, cross-document consistency checks, mismatch flags and memo generation
- Plotly document relationship map
- SQLite application storage and officer review status/notes
- Stacked-document checkmark brand mark in burgundy, cream, sage and muted gold

## Important
This is a student prototype, not a production banking system. It does not make loan approval/rejection decisions. Review source documents manually. Use fictional sample data for demonstrations. When Gemini is enabled, selected application context and chat messages are sent to Google Gemini. Keep sensitive personal data out of demonstrations.


## ClearFile Intelligence chat
The chat input is available even before you create an application. Choose “General chat” for general questions, or select a saved application to ground answers in its extracted fields, findings and memo. Configure `GEMINI_API_KEY` in `.env` to enable Gemini responses. The default model is `gemini-3.8-flash`. If that model is temporarily busy, ClearFile automatically retries once with `gemini-3.5-flash-lite`.


Gemini availability note: the app tries several supported Flash/Flash-Lite models if a model is temporarily unavailable. A Google API 503 can still affect all models during a service incident; wait briefly and retry. In .env, GEMINI_MODEL=gemini-3.1-flash-lite is a lightweight starting option.


## Category 2 Agentic AI workflow
See `CATEGORY2_IMPLEMENTATION.md` for the supervisor–worker workflow, MCP server/client, checkpointing, event trace, tests and limitations. A new **Agent Workflow** page is available in the app.

## Category 2 background workflow and evidence
- Run the automated checks: `python -m unittest discover -s tests -v`
- Open **Agent Workflow** and run the supervisor-worker review, or queue a background review.
- To process queued jobs, open a second terminal in this folder and run: `python -m agentic.job_worker --workers 2`.
- Demonstrate MCP discovery and tool calls with: `python -m mcp_tools.client YOUR_APPLICATION_ID`.
- See `CATEGORY2_IMPLEMENTATION.md` for the requirement coverage matrix and `ARCHITECTURE.md` for the Mermaid architecture diagram.
- Local workflow checkpoints, background job state, and event logs are created under `data/` at runtime and are excluded from the ZIP/Git.
