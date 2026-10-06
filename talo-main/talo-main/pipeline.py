"""
Ties ingest -> drift -> report -> PDF into the two endpoints an actual
client uses: upload a baseline period and a current period, get back
either the JSON report or the downloadable PDF.
"""
from fastapi import APIRouter, UploadFile, Query
from fastapi.responses import Response

from ingest import parse_and_map_csv
from drift import drift_report
from report import generate_full_report
from pdf_export import build_pdf

router = APIRouter(prefix="/report", tags=["report"])


async def _run_pipeline(baseline_file: UploadFile, current_file: UploadFile) -> dict:
    baseline_rows, _ = await parse_and_map_csv(baseline_file)
    current_rows, _ = await parse_and_map_csv(current_file)
    drift_results = drift_report(baseline_rows, current_rows)
    return await generate_full_report(drift_results, current_rows)


@router.post("/generate")
async def generate(baseline_file: UploadFile, current_file: UploadFile):
    """
    baseline_file: an earlier period's decision-log CSV (the "normal" period)
    current_file:  the period you want audited, compared against baseline

    Returns the full report as JSON - narrative sections, drift results,
    row count. Use this while iterating; use /report/pdf once you want the
    actual document to hand someone.
    """
    return await _run_pipeline(baseline_file, current_file)


@router.post("/pdf")
async def generate_pdf(
    baseline_file: UploadFile,
    current_file: UploadFile,
    institution_name: str = Query(default="Institution"),
):
    """Same pipeline as /generate, returned as a downloadable PDF."""
    report = await _run_pipeline(baseline_file, current_file)
    pdf_bytes = build_pdf(report, institution_name=institution_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=audit_report.pdf"},
    )
