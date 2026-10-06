"""
CSV ingestion + AI-assisted schema mapping.

Takes whatever CSV export a client's fraud/AML/KYC system produces, in
whatever column names/order it happens to use, and maps it onto the
normalized schema the drift engine and report generator expect. This is
the piece that means a client never has to reformat their export by hand
before uploading it.

Expected target schema per row:
    transaction_id   : str
    timestamp        : ISO 8601 str
    features          : dict (str -> value) - whatever inputs the model saw
    decision          : str  (e.g. "flagged" / "cleared")
    confidence        : float (0-1), optional
    outcome           : str, optional (e.g. "confirmed_fraud" / "false_positive" / unknown)
"""

import csv
import io
import json
from typing import Any
from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
from llm_client import call_llm, extract_json

router = APIRouter(prefix="/ingest", tags=["ingest"])

TARGET_SCHEMA = {
    "transaction_id": "unique identifier for the transaction or case",
    "timestamp": "when the decision was made, ISO 8601 if possible",
    "features": "the input signals the model used to decide - anything that doesn't match another field falls here",
    "decision": "what the model decided - flagged, cleared, approved, declined, etc",
    "confidence": "the model's confidence score, 0 to 1, if present",
    "outcome": "the confirmed real-world result, if the client tracks it - fraud confirmed, false positive, unresolved",
}


class ColumnMapping(BaseModel):
    mapping: dict[str, str]        # target_field -> source_column_name
    unmapped_columns: list[str]    # source columns that didn't map to anything - folded into features


async def infer_column_mapping(headers: list[str], sample_rows: list[dict]) -> ColumnMapping:
    """
    Ask an LLM to map this client's arbitrary CSV headers onto our target
    schema, using a few sample rows for context.

    Wire `call_llm` below to whatever LLM client the drift/report pipeline
    already uses (reuse that client here instead of adding a second one).
    """
    prompt = f"""You are mapping a CSV export from a financial institution's
fraud/AML/KYC system onto a fixed target schema.

Target schema (field: description):
{json.dumps(TARGET_SCHEMA, indent=2)}

Source CSV headers:
{json.dumps(headers)}

Sample rows (first 3):
{json.dumps(sample_rows[:3], indent=2)}

Return ONLY valid JSON in this exact shape, nothing else:
{{
  "mapping": {{"<target_field>": "<source_column_name>", ...}},
  "unmapped_columns": ["<source_column_name>", ...]
}}

Map every target field you can find a reasonable match for. Any source
column that doesn't clearly map to transaction_id, timestamp, decision,
confidence, or outcome should go in unmapped_columns - those get folded
into "features" automatically, so don't force a bad match."""

    raw = await call_llm(prompt)
    parsed = json.loads(extract_json(raw))
    return ColumnMapping(**parsed)


def apply_mapping(rows: list[dict], mapping: ColumnMapping) -> list[dict]:
    """Reshape raw CSV rows into the normalized schema using the inferred mapping."""
    normalized = []
    for row in rows:
        out: dict[str, Any] = {"features": {}}
        for target_field, source_col in mapping.mapping.items():
            out[target_field] = row.get(source_col)
        for col in mapping.unmapped_columns:
            if col in row:
                out["features"][col] = row[col]
        normalized.append(out)
    return normalized


async def parse_and_map_csv(file: UploadFile) -> tuple[list[dict], ColumnMapping]:
    """
    Core logic, reusable outside the /ingest/csv route (the pipeline
    endpoint in pipeline.py calls this directly for both the baseline and
    current-period files).
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Expected a .csv file")

    raw = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    if not rows:
        raise HTTPException(400, "CSV appears to be empty")

    headers = reader.fieldnames or []
    mapping = await infer_column_mapping(headers, rows)
    normalized_rows = apply_mapping(rows, mapping)
    return normalized_rows, mapping


@router.post("/csv")
async def ingest_csv(file: UploadFile):
    """
    Client drops in their export as-is. We infer the mapping, normalize
    the rows, and hand back both the normalized data and the mapping we
    used - so a human can glance at it and correct anything before it
    feeds the drift engine.
    """
    normalized_rows, mapping = await parse_and_map_csv(file)
    return {
        "row_count": len(normalized_rows),
        "inferred_mapping": mapping.mapping,
        "unmapped_columns_folded_into_features": mapping.unmapped_columns,
        "normalized_rows": normalized_rows,
        # Next stop: normalized_rows -> your existing drift engine (Watchtower)
    }