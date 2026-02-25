"""
SAAQ Database Service
Supabase in production, in-memory dict for local dev.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional


# ─── In-memory store (dev fallback) ───────────────────────────
_intakes: dict[str, dict] = {}
_reports: dict[str, dict] = {}
_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        return None  # Fall back to in-memory

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception:
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Intake operations ────────────────────────────────────────
async def save_intake(first_name: str, email: Optional[str], version: str, responses: dict) -> dict:
    intake_id = str(uuid.uuid4())
    record = {
        "id": intake_id,
        "first_name": first_name,
        "email": email,
        "version": version,
        "responses": responses,
        "status": "pending",
        "created_at": _now(),
    }

    sb = _get_supabase()
    if sb:
        try:
            sb.table("intakes").insert(record).execute()
        except Exception as e:
            print(f"Supabase insert failed, using memory: {e}")
            _intakes[intake_id] = record
    else:
        _intakes[intake_id] = record

    return record


async def get_intake(intake_id: str) -> Optional[dict]:
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("intakes").select("*").eq("id", intake_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            pass
    return _intakes.get(intake_id)


async def list_intakes() -> list[dict]:
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("intakes").select("*").order("created_at", desc=True).execute()
            return result.data
        except Exception:
            pass
    return sorted(_intakes.values(), key=lambda x: x["created_at"], reverse=True)


async def update_intake_status(intake_id: str, status: str):
    sb = _get_supabase()
    if sb:
        try:
            sb.table("intakes").update({"status": status}).eq("id", intake_id).execute()
            return
        except Exception:
            pass
    if intake_id in _intakes:
        _intakes[intake_id]["status"] = status


# ─── Report operations ────────────────────────────────────────
async def save_report(intake_id: str, subject: str, report_data: dict, status: str = "complete") -> dict:
    report_id = str(uuid.uuid4())
    record = {
        "id": report_id,
        "intake_id": intake_id,
        "subject": subject,
        "report_data": report_data,
        "status": status,
        "created_at": _now(),
        "completed_at": _now() if status == "complete" else None,
    }

    sb = _get_supabase()
    if sb:
        try:
            sb.table("reports").insert(record).execute()
        except Exception as e:
            print(f"Supabase insert failed, using memory: {e}")
            _reports[report_id] = record
    else:
        _reports[report_id] = record

    return record


async def get_report(report_id: str) -> Optional[dict]:
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("reports").select("*").eq("id", report_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            pass
    return _reports.get(report_id)


async def get_report_by_intake(intake_id: str) -> Optional[dict]:
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("reports").select("*").eq("intake_id", intake_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            pass
    for r in _reports.values():
        if r["intake_id"] == intake_id:
            return r
    return None


async def list_reports() -> list[dict]:
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("reports").select("*").order("created_at", desc=True).execute()
            return result.data
        except Exception:
            pass
    return sorted(_reports.values(), key=lambda x: x["created_at"], reverse=True)
