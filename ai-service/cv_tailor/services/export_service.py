"""
Application Master-Sheet Export Service.
Generates comprehensive CSV and formatted Excel (.xlsx) files of tracked applications
including match data, interview schedules, contacts, notes, and document links.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


EXPORT_COLUMNS = [
    ("id", "App ID", 10),
    ("company_name", "Company", 22),
    ("job_title", "Job Title", 28),
    ("status", "Status", 16),
    ("priority", "Priority", 12),
    ("match_rating", "Match Fit", 14),
    ("location", "Location", 20),
    ("job_type", "Work Mode / Type", 18),
    ("salary_range", "Salary Range", 18),
    ("date_applied", "Date Applied", 14),
    ("follow_up_date", "Follow-up Due", 14),
    ("job_url", "Application / Job URL", 36),
    ("job_source", "Job Source", 16),
    ("notes", "Notes & Contacts", 30),
    ("has_tailored_cv", "Tailored CV Ready", 16),
    ("created_at", "Date Added", 16),
]


def format_cell_value(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)


def export_applications_to_csv(applications: List[Dict[str, Any]]) -> str:
    """Generate RFC 4180 compliant CSV string."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    headers = [col[1] for col in EXPORT_COLUMNS]
    writer.writerow(headers)

    # Rows
    for app in applications:
        row = []
        match_score = app.get("match_score")
        match_rating = f"{match_score}/10" if match_score is not None else "N/A"
        has_cv = "Yes" if (app.get("latex_source") or app.get("has_pdf")) else "No"

        for col_id, _, _ in EXPORT_COLUMNS:
            if col_id == "match_rating":
                row.append(match_rating)
            elif col_id == "has_tailored_cv":
                row.append(has_cv)
            else:
                row.append(format_cell_value(app.get(col_id)))
        writer.writerow(row)

    return output.getvalue()


def export_applications_to_excel(applications: List[Dict[str, Any]]) -> bytes:
    """Generate beautifully styled Excel workbook (.xlsx)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Job Applications Master Sheet"
    ws.views.sheetView[0].showGridLines = True

    # Styling Palette
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Deep Blue
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    link_font = Font(name="Calibri", size=10, color="2563EB", underline="single")

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    # Status fills
    status_fills = {
        "Applied": PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"),
        "Interview": PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid"),
        "Offer": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),
        "Rejected": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),
        "To Review": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),
        "To Apply": PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid"),
    }

    # Write Header
    for col_idx, (_, col_title, col_width) in enumerate(EXPORT_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    ws.row_dimensions[1].height = 28

    # Write Data Rows
    for row_idx, app in enumerate(applications, start=2):
        match_score = app.get("match_score")
        match_rating = f"{match_score}/10" if match_score is not None else "—"
        has_cv = "Yes" if (app.get("latex_source") or app.get("has_pdf")) else "No"
        status_val = app.get("status", "Saved")

        for col_idx, (col_id, _, _) in enumerate(EXPORT_COLUMNS, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

            if col_id == "match_rating":
                cell.value = match_rating
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if match_score and match_score >= 8.0:
                    cell.font = bold_font
            elif col_id == "has_tailored_cv":
                cell.value = has_cv
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_id == "status":
                cell.value = status_val
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if status_val in status_fills:
                    cell.fill = status_fills[status_val]
            elif col_id == "job_url":
                url = app.get("job_url") or ""
                if url.startswith("http"):
                    cell.value = "Open Link"
                    cell.hyperlink = url
                    cell.font = link_font
                else:
                    cell.value = url
            elif col_id in ["date_applied", "follow_up_date", "priority", "id"]:
                cell.value = format_cell_value(app.get(col_id))
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.value = format_cell_value(app.get(col_id))

        ws.row_dimensions[row_idx].height = 22

    # Save to memory stream
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
