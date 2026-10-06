# Audit MVP — backend (v1)

An AI-decision audit-report generator for Nigerian financial institutions'
fraud/AML/KYC systems. Client uploads a CSV of decision logs; the system
maps it onto a normalized schema, runs drift analysis, and generates a
plain-English audit report — plus a chat endpoint to ask questions about
the data directly.

## Setup (VS Code)

1. Open this folder in VS Code.
2. Open a terminal: `Terminal > New Terminal`.
3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`.
6. Run the server:
   ```
   uvicorn main:app --reload
   ```
7. Open **http://localhost:8000/docs** — FastAPI's built-in interactive
   docs. Upload a CSV to `/ingest/csv` and try the flow end to end.

## What's here

| File            | What it does                                                             |
|-----------------|---------------------------------------------------------------------------|
| `main.py`       | FastAPI entry point, wires everything together                          |
| `ingest.py`     | CSV upload + AI-assisted column mapping (no manual reformatting needed) |
| `drift.py`      | PSI drift detection — pure math, no LLM call, cheap to run              |
| `report.py`     | Generates the plain-English audit report sections                       |
| `pdf_export.py` | Renders the report into a downloadable PDF                              |
| `pipeline.py`   | Ties ingest → drift → report → PDF into two real endpoints              |
| `chat.py`       | Chat endpoint — ask questions about your own uploaded data              |
| `llm_client.py` | The one place that talks to the LLM API — swap providers here only      |

## Try it end to end

1. Open **http://localhost:8000/docs**.
2. `POST /report/generate` — upload a `baseline_file` (an earlier, "normal"
   period) and a `current_file` (the period you're auditing). Get back the
   full JSON report: narrative sections, drift results, row count.
3. `POST /report/pdf` — same two files, returns an actual downloadable PDF.
4. `POST /chat/ask` — paste in the `drift_results` and `normalized_rows`
   from step 2, ask it a question about the data.

`/ingest/csv` still exists on its own too, if you just want to check the
column mapping on a single file without running the full pipeline.

## Deliberately not in v1

- **Frontend** — Next.js app is the next build step, not started yet.
- **Bias/fairness metrics** — deferred to v2. Real fairness metrics need
  protected-attribute data, which NDPA restricts — this needs proper legal
  guidance before it's built, not a quick add.
- **Live API/webhook ingestion** — deferred to v2, on purpose. CSV-first
  keeps the trust bar low for a first pilot; API access is the upgrade a
  client asks *you* for once they already trust the reports.

## Next build step

Start the Next.js frontend: an upload page (two file inputs — baseline +
current), a report view, and a chat panel that calls the endpoints above.
