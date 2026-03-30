"""
SAAQ Backend API
================
FastAPI server powering the SkillfullyAware Awareness Quotient platform.

Endpoints:
  GET  /api/v1/questions/{version}     - Get survey questions
  POST /api/v1/intake/submit           - Submit survey responses
  GET  /api/v1/intakes                 - List all intakes (admin)
  POST /api/v1/reports/generate        - Generate report for an intake
  GET  /api/v1/reports/{id}            - Get report data
  GET  /api/v1/reports/{id}/download   - Download DOCX file
  GET  /api/v1/reports                 - List all reports (admin)
  POST /api/v1/reports/batch           - Generate multiple reports
  GET  /api/v1/health                  - Health check

Mobile-ready: All endpoints return JSON, DOCX download is a separate endpoint.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.schemas import (
    IntakeSubmission, IntakeResponse, IntakeVersion,
    ReportRequest, ReportStatusResponse, ReportListItem,
    BatchRequest, DashboardStats, ReportStatus,
    get_questions,
)
from services import database as db
from services.analyzer import analyze_responses

load_dotenv()

app = FastAPI(
    title="SAAQ API",
    description="SkillfullyAware Awareness Quotient - Leadership Diagnostic Platform",
    version="1.0.0",
)

# CORS - allow frontend + mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PIPELINE_DIR = Path(__file__).parent.parent / "pipeline"
OUTPUT_DIR = Path(__file__).parent / "generated_reports"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─── Health ────────────────────────────────────────────────────
@app.get("/api/v1/health")
async def health():
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_supabase = bool(os.getenv("SUPABASE_URL"))
    return {
        "status": "ok",
        "api_key_configured": has_api_key,
        "database_configured": has_supabase,
        "pipeline_available": (PIPELINE_DIR / "build_report.js").exists(),
    }


# ─── Questions ─────────────────────────────────────────────────
@app.get("/api/v1/questions/{version}")
async def get_survey_questions(version: IntakeVersion):
    """Get the list of questions for a given intake version."""
    questions = get_questions(version)
    return {
        "version": version.value,
        "count": len(questions),
        "questions": [{"id": i, "text": q} for i, q in enumerate(questions)],
    }


# ─── Intake ────────────────────────────────────────────────────
@app.post("/api/v1/intake/submit", response_model=IntakeResponse)
async def submit_intake(submission: IntakeSubmission):
    """Submit survey responses. Returns intake ID for report generation."""
    if not submission.responses:
        raise HTTPException(400, "No responses provided")

    record = await db.save_intake(
        first_name=submission.first_name,
        email=submission.email,
        version=submission.version.value,
        responses=submission.responses,
    )

    return IntakeResponse(
        id=record["id"],
        first_name=record["first_name"],
        version=record["version"],
        status=ReportStatus.PENDING,
        created_at=record["created_at"],
        message="Survey submitted successfully. Your report will be generated shortly.",
    )


@app.get("/api/v1/intakes")
async def list_intakes():
    """List all submitted intakes (admin endpoint)."""
    intakes = await db.list_intakes()
    return {"intakes": intakes, "count": len(intakes)}


# ─── Reports ──────────────────────────────────────────────────
async def _generate_report_task(intake_id: str):
    """Background task: analyze responses + build DOCX."""
    try:
        await db.update_intake_status(intake_id, "analyzing")
        intake = await db.get_intake(intake_id)
        if not intake:
            return

        subject = intake["first_name"]
        responses = intake["responses"]

        # Step 1: AI Analysis
        report_data = await analyze_responses(subject, responses)

        # Step 2: Build DOCX
        await db.update_intake_status(intake_id, "generating")
        docx_path = OUTPUT_DIR / f"SAAQReport-{subject}-{intake_id[:8]}.docx"
        json_path = OUTPUT_DIR / f"_temp_{intake_id}.json"

        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        result = subprocess.run(
            ["node", str(PIPELINE_DIR / "build_report.js"), str(json_path), str(docx_path)],
            capture_output=True, text=True, timeout=30,
        )
        json_path.unlink(missing_ok=True)

        if result.returncode != 0:
            raise Exception(f"DOCX build failed: {result.stderr}")

        # Step 3: Save report
        await db.save_report(intake_id, subject, report_data, "complete")
        await db.update_intake_status(intake_id, "complete")

    except Exception as e:
        print(f"Report generation failed for {intake_id}: {e}")
        await db.update_intake_status(intake_id, "failed")
        await db.save_report(intake_id, intake.get("first_name", "Unknown"), {}, "failed")


@app.post("/api/v1/reports/generate")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """Kick off report generation for an intake. Runs in background."""
    intake = await db.get_intake(request.intake_id)
    if not intake:
        raise HTTPException(404, "Intake not found")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "API key not configured. Add ANTHROPIC_API_KEY to .env")

    # Check if report already exists
    existing = await db.get_report_by_intake(request.intake_id)
    if existing and existing.get("status") == "complete":
        return {"message": "Report already exists", "report_id": existing["id"], "status": "complete"}

    background_tasks.add_task(_generate_report_task, request.intake_id)
    return {"message": "Report generation started", "intake_id": request.intake_id, "status": "analyzing"}


@app.get("/api/v1/reports/{intake_id}")
async def get_report(intake_id: str):
    """Get report data (JSON) for an intake."""
    report = await db.get_report_by_intake(intake_id)
    if not report:
        # Check if intake exists and is still processing
        intake = await db.get_intake(intake_id)
        if intake:
            return {"status": intake.get("status", "pending"), "intake_id": intake_id}
        raise HTTPException(404, "Report not found")
    return report


@app.get("/api/v1/reports/{intake_id}/download")
async def download_report(intake_id: str):
    """Download the generated DOCX report."""
    intake = await db.get_intake(intake_id)
    if not intake:
        raise HTTPException(404, "Intake not found")

    subject = intake["first_name"]
    # Find the DOCX file
    for f in OUTPUT_DIR.iterdir():
        if f.name.startswith(f"SAAQReport-{subject}-{intake_id[:8]}") and f.suffix == ".docx":
            return FileResponse(
                str(f),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=f"SAAQReport-{subject}.docx",
            )

    raise HTTPException(404, "Report file not found. Generate the report first.")


@app.get("/api/v1/reports")
async def list_reports():
    """List all generated reports (admin endpoint)."""
    reports = await db.list_reports()
    return {"reports": reports, "count": len(reports)}


# ─── Batch ─────────────────────────────────────────────────────
@app.post("/api/v1/reports/batch")
async def batch_generate(request: BatchRequest, background_tasks: BackgroundTasks):
    """Generate reports for multiple intakes."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "API key not configured")

    started = []
    for intake_id in request.intake_ids:
        intake = await db.get_intake(intake_id)
        if intake:
            background_tasks.add_task(_generate_report_task, intake_id)
            started.append(intake_id)

    return {"message": f"Started {len(started)} report generations", "intake_ids": started}


# ─── Dashboard Stats ──────────────────────────────────────────
@app.get("/api/v1/dashboard", response_model=DashboardStats)
async def dashboard_stats():
    intakes = await db.list_intakes()
    reports = await db.list_reports()
    return DashboardStats(
        total_intakes=len(intakes),
        total_reports=len(reports),
        pending_reports=sum(1 for r in reports if r.get("status") == "pending"),
        completed_reports=sum(1 for r in reports if r.get("status") == "complete"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
