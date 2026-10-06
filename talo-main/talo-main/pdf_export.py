"""
Renders the JSON report from report.py into a PDF a compliance officer
can hand directly to an examiner.
"""
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

SECTION_TITLES = {
    "system_overview": "1. System Overview",
    "data_and_inputs": "2. Data and Inputs",
    "drift_summary": "3. Drift Summary",
    "performance_summary": "4. Performance Summary",
    "decision_logic_summary": "5. Decision Logic Summary",
}


def build_pdf(report: dict, institution_name: str = "Institution") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"AI System Audit Report \u2014 {institution_name}", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Rows analyzed: {report.get('row_count_analyzed', 'N/A')}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 20))

    sections = report.get("sections", {})
    for key, title in SECTION_TITLES.items():
        if key in sections:
            story.append(Paragraph(title, styles["Heading1"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(sections[key], styles["Normal"]))
            story.append(Spacer(1, 16))

    story.append(Paragraph("6. Bias / Fairness", styles["Heading1"]))
    story.append(Paragraph(report.get("bias_section", "Not included in v1."), styles["Normal"]))
    story.append(Spacer(1, 16))

    overall = report.get("drift_results", {}).get("overall_status", "unknown")
    story.append(Paragraph("Appendix: Drift Detail", styles["Heading1"]))
    story.append(Paragraph(f"Overall drift status: {overall}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
