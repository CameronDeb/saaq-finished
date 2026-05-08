"""
SAAQ Database Service — Supabase-first.
All data goes to Supabase. In-memory fallback only if Supabase is not configured.
"""
import os
import uuid
from datetime import datetime

# ─── Supabase client ─────────────────────────────────────────
_supabase = None

def _get_sb():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if url and key:
            from supabase import create_client
            _supabase = create_client(url, key)
    return _supabase


# ─── In-memory fallback (only used if no Supabase) ───────────
_intakes = {}
_reports = {}


# ─── Intake operations ───────────────────────────────────────
async def save_intake(first_name: str, email: str, version: str, responses: dict, user_id: str = None, payment_id: str = None) -> dict:
    sb = _get_sb()
    record = {
        "id": str(uuid.uuid4()),
        "first_name": first_name,
        "email": email,
        "version": version,
        "responses": responses,
        "user_id": user_id,
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }
    if payment_id:
        record["payment_id"] = payment_id

    if sb:
        try:
            # Remove fields that might not exist in old schema
            insert_data = {k: v for k, v in record.items() if v is not None}
            result = sb.table("intakes").insert(insert_data).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            print(f"  Supabase insert failed: {e}, using in-memory fallback")

    _intakes[record["id"]] = record
    return record


async def get_intake(intake_id: str) -> dict | None:
    sb = _get_sb()
    if sb:
        try:
            result = sb.table("intakes").select("*").eq("id", intake_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            print(f"  Supabase get_intake failed: {e}")

    return _intakes.get(intake_id)


async def list_intakes() -> list:
    sb = _get_sb()
    if sb:
        try:
            result = sb.table("intakes").select("*").order("submitted_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"  Supabase list_intakes failed: {e}")

    return list(_intakes.values())


async def update_intake_status(intake_id: str, status: str):
    sb = _get_sb()
    if sb:
        try:
            sb.table("intakes").update({"status": status}).eq("id", intake_id).execute()
            return
        except Exception as e:
            print(f"  Supabase update_intake_status failed: {e}")

    if intake_id in _intakes:
        _intakes[intake_id]["status"] = status


# ─── Report operations ───────────────────────────────────────
async def save_report(intake_id: str, subject: str, report_data: dict, status: str = "complete") -> dict:
    sb = _get_sb()
    record = {
        "id": str(uuid.uuid4()),
        "intake_id": intake_id,
        "status": status,
        "report_data": report_data,
        "created_at": datetime.utcnow().isoformat(),
    }
    if status == "complete":
        record["completed_at"] = datetime.utcnow().isoformat()

    # Get user_id from intake
    intake = await get_intake(intake_id)
    if intake and intake.get("user_id"):
        record["user_id"] = intake["user_id"]

    if sb:
        try:
            # Check if report already exists for this intake
            existing = sb.table("reports").select("id").eq("intake_id", intake_id).execute()
            if existing.data:
                # Update existing
                update_data = {"status": status, "report_data": report_data}
                if status == "complete":
                    update_data["completed_at"] = datetime.utcnow().isoformat()
                sb.table("reports").update(update_data).eq("intake_id", intake_id).execute()
                return {**existing.data[0], **update_data}
            else:
                # Insert new
                insert_data = {k: v for k, v in record.items() if v is not None}
                result = sb.table("reports").insert(insert_data).execute()
                if result.data:
                    return result.data[0]
        except Exception as e:
            print(f"  Supabase save_report failed: {e}")

    _reports[record["id"]] = record
    return record


async def get_report_by_intake(intake_id: str) -> dict | None:
    sb = _get_sb()
    if sb:
        try:
            result = sb.table("reports").select("*").eq("intake_id", intake_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            print(f"  Supabase get_report failed: {e}")

    for r in _reports.values():
        if r.get("intake_id") == intake_id:
            return r
    return None


async def list_reports() -> list:
    sb = _get_sb()
    if sb:
        try:
            result = sb.table("reports").select("*").order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"  Supabase list_reports failed: {e}")

    return list(_reports.values())