"""
SAAQ Backend API — Full MVP v3
Supabase Storage for DOCX, grant flow fix, all endpoints.
"""
import json
import os
import subprocess
import base64
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional

from models.schemas import (
    IntakeSubmission, IntakeResponse, IntakeVersion,
    ReportRequest, ReportStatus, DashboardStats,
    BatchRequest, get_questions,
)
from services import database as db
from services.analyzer import analyze_responses

load_dotenv()

app = FastAPI(title="SAAQ API", version="3.0.0")

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
STORAGE_BUCKET = "reports"


def get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


# ─── Auth helpers ─────────────────────────────────────────────
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    sb = get_supabase()
    if not sb:
        return None
    try:
        user_resp = sb.auth.get_user(token)
        if not user_resp or not user_resp.user:
            return None
        profile = sb.table("profiles").select("*").eq("id", user_resp.user.id).execute()
        if profile.data:
            return profile.data[0]
        return None
    except Exception:
        return None


async def require_auth(authorization: Optional[str] = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


async def require_admin(authorization: Optional[str] = Header(None)):
    user = await require_auth(authorization)
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdatePriceRequest(BaseModel):
    key: str
    amount: int
    label: str

class GrantAdminRequest(BaseModel):
    email: str

class CheckoutRequest(BaseModel):
    product_type: str

class VerifyPaymentRequest(BaseModel):
    session_id: str


# ─── Health ───────────────────────────────────────────────────
@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "database_configured": bool(os.getenv("SUPABASE_URL")),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "pipeline_available": (PIPELINE_DIR / "build_report.js").exists(),
    }


# ─── Auth ─────────────────────────────────────────────────────
@app.post("/api/v1/auth/signup")
async def signup(req: SignupRequest):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    try:
        from supabase import create_client
        anon_url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_SERVICE_KEY"))
        anon_sb = create_client(anon_url, anon_key)
        result = anon_sb.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {"data": {"full_name": req.full_name, "role": "participant"}}
        })
        if result.user:
            return {
                "user_id": str(result.user.id),
                "email": result.user.email,
                "access_token": result.session.access_token if result.session else None,
                "refresh_token": result.session.refresh_token if result.session else None,
                "role": "participant",
                "full_name": req.full_name,
            }
        raise HTTPException(400, "Signup failed")
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    try:
        from supabase import create_client
        anon_url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_SERVICE_KEY"))
        anon_sb = create_client(anon_url, anon_key)
        result = anon_sb.auth.sign_in_with_password({"email": req.email, "password": req.password})
        if result.user and result.session:
            profile = sb.table("profiles").select("*").eq("id", result.user.id).execute()
            role = profile.data[0]["role"] if profile.data else "participant"
            name = profile.data[0].get("full_name", "") if profile.data else ""
            return {
                "user_id": str(result.user.id),
                "email": result.user.email,
                "role": role,
                "full_name": name,
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
            }
        raise HTTPException(401, "Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, str(e))


@app.get("/api/v1/auth/me")
async def get_me(user=Depends(require_auth)):
    return user


# ─── Stripe ───────────────────────────────────────────────────
@app.post("/api/v1/checkout")
async def create_checkout(req: CheckoutRequest, user=Depends(require_auth)):
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(503, "Stripe not configured")
    sb = get_supabase()
    price_row = sb.table("admin_settings").select("*").eq("key", f"price_{req.product_type}").execute()
    if not price_row.data:
        raise HTTPException(400, f"Unknown product: {req.product_type}")
    price_info = price_row.data[0]["value"]
    amount_cents = price_info["amount"] * 100
    frontend_url = os.getenv("FRONTEND_URL", "https://saaq-pi.vercel.app")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=user["email"],
        line_items=[{"price_data": {"currency": "usd", "product_data": {"name": f"SAAQ {price_info['label']}"}, "unit_amount": amount_cents}, "quantity": 1}],
        metadata={"user_id": user["id"], "product_type": req.product_type},
        success_url=f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_url}/pricing",
    )
    sb.table("payments").insert({"user_id": user["id"], "stripe_session_id": session.id, "product_type": req.product_type, "amount": price_info["amount"], "status": "pending"}).execute()
    return {"checkout_url": session.url, "session_id": session.id}


@app.post("/api/v1/checkout/verify")
async def verify_payment(req: VerifyPaymentRequest, user=Depends(require_auth)):
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    try:
        session = stripe.checkout.Session.retrieve(req.session_id)
        sb = get_supabase()
        if session.payment_status == "paid":
            sb.table("payments").update({"status": "completed", "stripe_payment_intent": session.payment_intent}).eq("stripe_session_id", req.session_id).execute()
            payment = sb.table("payments").select("*").eq("stripe_session_id", req.session_id).execute()
            return {"status": "completed", "product_type": payment.data[0]["product_type"] if payment.data else None, "payment_id": payment.data[0]["id"] if payment.data else None}
        return {"status": "pending"}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret) if webhook_secret and sig else json.loads(payload)
    except Exception:
        raise HTTPException(400, "Invalid webhook")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        sb = get_supabase()
        if sb:
            sb.table("payments").update({"status": "completed", "stripe_payment_intent": session.get("payment_intent")}).eq("stripe_session_id", session["id"]).execute()
    return {"received": True}


# ─── Pricing (public) ────────────────────────────────────────
@app.get("/api/v1/pricing")
async def get_pricing():
    sb = get_supabase()
    defaults = {
        "15q_report": {"amount": 400, "label": "15-Question Report Only"},
        "15q_bundle": {"amount": 1000, "label": "15-Question Report + Sessions"},
        "30q_report": {"amount": 500, "label": "30-Question Report Only"},
        "30q_bundle": {"amount": 1000, "label": "30-Question Report + Sessions"},
    }
    if not sb:
        return {"prices": defaults}
    result = sb.table("admin_settings").select("*").like("key", "price_%").execute()
    prices = {}
    for row in result.data:
        prices[row["key"].replace("price_", "")] = row["value"]
    return {"prices": {**defaults, **prices}}


# ─── Grants ───────────────────────────────────────────────────
@app.post("/api/v1/admin/grant-free")
async def grant_free_report(request: Request, user=Depends(require_admin)):
    body = await request.json()
    email = body.get("email", "").strip().lower()
    product_type = body.get("product_type", "30q_report")
    if not email:
        raise HTTPException(400, "Email required")
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    sb.table("grants").insert({"email": email, "product_type": product_type, "granted_by": user["id"]}).execute()
    return {"message": f"Free report granted to {email}"}


@app.get("/api/v1/check-grant")
async def check_grant(user=Depends(require_auth)):
    sb = get_supabase()
    if not sb:
        return {"has_grant": False}
    result = sb.table("grants").select("*").eq("email", user["email"].lower()).eq("used", False).execute()
    if result.data:
        return {"has_grant": True, "grant_id": result.data[0]["id"], "product_type": result.data[0]["product_type"]}
    return {"has_grant": False}


@app.post("/api/v1/redeem-grant")
async def redeem_grant(request: Request, user=Depends(require_auth)):
    body = await request.json()
    grant_id = body.get("grant_id")
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    sb.table("grants").update({"used": True}).eq("id", grant_id).eq("email", user["email"].lower()).execute()
    return {"message": "Grant redeemed"}


# ─── Questions ────────────────────────────────────────────────
@app.get("/api/v1/questions/{version}")
async def get_survey_questions(version: IntakeVersion):
    questions = get_questions(version)
    return {"version": version.value, "count": len(questions), "questions": [{"id": i, "text": q} for i, q in enumerate(questions)]}


# ─── Intake ───────────────────────────────────────────────────
@app.post("/api/v1/intake/submit", response_model=IntakeResponse)
async def submit_intake(submission: IntakeSubmission, authorization: Optional[str] = Header(None)):
    if not submission.responses:
        raise HTTPException(400, "No responses provided")
    user = await get_current_user(authorization)
    record = await db.save_intake(
        first_name=submission.first_name, email=submission.email,
        version=submission.version.value, responses=submission.responses,
        user_id=user["id"] if user else None,
    )
    return IntakeResponse(id=record["id"], first_name=record["first_name"], version=record["version"], status=ReportStatus.PENDING, created_at=record.get("created_at", record.get("submitted_at", "")), message="Survey submitted successfully.")


@app.get("/api/v1/intakes")
async def list_intakes():
    intakes = await db.list_intakes()
    return {"intakes": intakes, "count": len(intakes)}


@app.get("/api/v1/my/intakes")
async def my_intakes(user=Depends(require_auth)):
    sb = get_supabase()
    if sb:
        result = sb.table("intakes").select("*").eq("user_id", user["id"]).order("submitted_at", desc=True).execute()
        return {"intakes": result.data, "count": len(result.data)}
    return {"intakes": [], "count": 0}


# ─── Reports ──────────────────────────────────────────────────
def _upload_docx_to_storage(sb, file_path: Path, storage_name: str) -> str | None:
    """Upload DOCX to Supabase Storage and return the path."""
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        sb.storage.from_(STORAGE_BUCKET).upload(
            storage_name,
            file_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        return storage_name
    except Exception as e:
        print(f"  Storage upload failed: {e}")
        # Try to update if already exists
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            sb.storage.from_(STORAGE_BUCKET).update(
                storage_name,
                file_bytes,
                {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
            )
            return storage_name
        except Exception as e2:
            print(f"  Storage update also failed: {e2}")
            return None


def _download_docx_from_storage(sb, storage_name: str) -> bytes | None:
    """Download DOCX from Supabase Storage."""
    try:
        data = sb.storage.from_(STORAGE_BUCKET).download(storage_name)
        return data
    except Exception as e:
        print(f"  Storage download failed: {e}")
        return None


async def _generate_report_task(intake_id: str):
    try:
        await db.update_intake_status(intake_id, "analyzing")
        intake = await db.get_intake(intake_id)
        if not intake:
            return
        subject = intake["first_name"]
        responses = intake["responses"]

        # step 1: AI analysis
        report_data = await analyze_responses(subject, responses)

        # step 2: build DOCX
        await db.update_intake_status(intake_id, "generating")
        docx_filename = f"SAAQReport-{subject}-{intake_id[:8]}.docx"
        docx_path = OUTPUT_DIR / docx_filename
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

        # step 3: upload to Supabase Storage
        sb = get_supabase()
        storage_path = None
        if sb:
            storage_name = f"{intake_id}/{docx_filename}"
            storage_path = _upload_docx_to_storage(sb, docx_path, storage_name)

        # step 4: save report record
        await db.save_report(intake_id, subject, report_data, "complete")

        # update docx_path in report
        if sb and storage_path:
            sb.table("reports").update({"docx_path": storage_path}).eq("intake_id", intake_id).execute()

        await db.update_intake_status(intake_id, "complete")

        # step 5: email report
        email = intake.get("email")
        if email and os.getenv("RESEND_API_KEY"):
            try:
                from services.email_service import send_report_email
                with open(docx_path, "rb") as f:
                    docx_bytes = f.read()
                send_report_email(email, subject, docx_bytes, f"SAAQReport-{subject}.docx")
                if sb:
                    sb.table("reports").update({"emailed_at": datetime.utcnow().isoformat()}).eq("intake_id", intake_id).execute()
            except Exception as e:
                print(f"  Email failed: {e}")

        # cleanup local file (it's in storage now)
        docx_path.unlink(missing_ok=True)

    except Exception as e:
        print(f"Report generation failed for {intake_id}: {e}")
        await db.update_intake_status(intake_id, "failed")
        try:
            await db.save_report(intake_id, "Unknown", {}, "failed")
        except Exception:
            pass


@app.post("/api/v1/reports/generate")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    intake = await db.get_intake(request.intake_id)
    if not intake:
        raise HTTPException(404, "Intake not found")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "API key not configured")
    existing = await db.get_report_by_intake(request.intake_id)
    if existing and existing.get("status") == "complete":
        return {"message": "Report already exists", "report_id": existing["id"], "status": "complete"}
    background_tasks.add_task(_generate_report_task, request.intake_id)
    return {"message": "Report generation started", "intake_id": request.intake_id, "status": "analyzing"}


@app.get("/api/v1/reports/{intake_id}")
async def get_report(intake_id: str):
    report = await db.get_report_by_intake(intake_id)
    if not report:
        intake = await db.get_intake(intake_id)
        if intake:
            return {"status": intake.get("status", "pending"), "intake_id": intake_id}
        raise HTTPException(404, "Report not found")
    return report


@app.get("/api/v1/reports/{intake_id}/download")
async def download_report(intake_id: str):
    intake = await db.get_intake(intake_id)
    if not intake:
        raise HTTPException(404, "Intake not found")
    subject = intake["first_name"]
    filename = f"SAAQReport-{subject}.docx"

    # try Supabase Storage first
    sb = get_supabase()
    if sb:
        report = await db.get_report_by_intake(intake_id)
        storage_path = report.get("docx_path") if report else None
        if storage_path:
            docx_bytes = _download_docx_from_storage(sb, storage_path)
            if docx_bytes:
                return Response(
                    content=docx_bytes,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )

    # fallback: check local filesystem
    for f in OUTPUT_DIR.iterdir():
        if f.name.startswith(f"SAAQReport-{subject}-{intake_id[:8]}") and f.suffix == ".docx":
            return FileResponse(str(f), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=filename)

    raise HTTPException(404, "Report file not found. Try regenerating the report.")


@app.get("/api/v1/reports")
async def list_reports():
    reports = await db.list_reports()
    return {"reports": reports, "count": len(reports)}


@app.get("/api/v1/my/reports")
async def my_reports(user=Depends(require_auth)):
    sb = get_supabase()
    if sb:
        result = sb.table("reports").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        return {"reports": result.data, "count": len(result.data)}
    return {"reports": [], "count": 0}


@app.post("/api/v1/reports/batch")
async def batch_generate(request: BatchRequest, background_tasks: BackgroundTasks):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "API key not configured")
    started = []
    for intake_id in request.intake_ids:
        intake = await db.get_intake(intake_id)
        if intake:
            background_tasks.add_task(_generate_report_task, intake_id)
            started.append(intake_id)
    return {"message": f"Started {len(started)} reports", "intake_ids": started}


# ─── Admin ────────────────────────────────────────────────────
@app.get("/api/v1/admin/settings")
async def get_admin_settings(user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    result = sb.table("admin_settings").select("*").execute()
    return {"settings": result.data}


@app.post("/api/v1/admin/settings/price")
async def update_price(req: UpdatePriceRequest, user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    sb.table("admin_settings").upsert({"key": req.key, "value": {"amount": req.amount, "label": req.label}, "updated_at": datetime.utcnow().isoformat()}).execute()
    return {"message": "Price updated", "key": req.key, "amount": req.amount}


@app.get("/api/v1/admin/users")
async def admin_list_users(user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    profiles = sb.table("profiles").select("*").order("created_at", desc=True).execute()
    payments = sb.table("payments").select("*").eq("status", "completed").execute()
    totals = {}
    for p in payments.data:
        uid = p.get("user_id")
        if uid:
            totals[uid] = totals.get(uid, 0) + p.get("amount", 0)
    users = [{**prof, "total_spent": totals.get(prof["id"], 0)} for prof in profiles.data]
    return {"users": users, "count": len(users)}


@app.post("/api/v1/admin/grant-admin")
async def grant_admin(req: GrantAdminRequest, user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    result = sb.table("profiles").update({"role": "admin"}).eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(404, f"User {req.email} not found")
    return {"message": f"Admin granted to {req.email}"}


@app.post("/api/v1/admin/revoke-admin")
async def revoke_admin(req: GrantAdminRequest, user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    sb.table("profiles").update({"role": "participant"}).eq("email", req.email).execute()
    return {"message": f"Admin revoked from {req.email}"}


@app.get("/api/v1/admin/payments")
async def admin_payments(user=Depends(require_admin)):
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Database not configured")
    result = sb.table("payments").select("*").order("created_at", desc=True).execute()
    return {"payments": result.data, "count": len(result.data)}


@app.get("/api/v1/admin/dashboard")
async def admin_dashboard_stats(user=Depends(require_admin)):
    sb = get_supabase()
    intakes = await db.list_intakes()
    reports = await db.list_reports()
    revenue = 0
    num_payments = 0
    num_users = 0
    if sb:
        pay_result = sb.table("payments").select("*").eq("status", "completed").execute()
        revenue = sum(p.get("amount", 0) for p in pay_result.data)
        num_payments = len(pay_result.data)
        prof_result = sb.table("profiles").select("id").execute()
        num_users = len(prof_result.data)
    return {
        "total_submissions": len(intakes),
        "reports_complete": sum(1 for r in reports if r.get("status") == "complete"),
        "reports_pending": sum(1 for r in reports if r.get("status") in ("pending", "analyzing", "generating")),
        "reports_failed": sum(1 for r in reports if r.get("status") == "failed"),
        "total_revenue": revenue,
        "total_payments": num_payments,
        "total_users": num_users,
    }


@app.get("/api/v1/dashboard", response_model=DashboardStats)
async def dashboard_stats():
    intakes = await db.list_intakes()
    reports = await db.list_reports()
    return DashboardStats(
        total_intakes=len(intakes), total_reports=len(reports),
        pending_reports=sum(1 for r in reports if r.get("status") == "pending"),
        completed_reports=sum(1 for r in reports if r.get("status") == "complete"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)