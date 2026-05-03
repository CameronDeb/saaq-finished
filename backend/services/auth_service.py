"""
Auth Service — Supabase authentication helpers.
"""
from supabase import Client


def get_user_from_token(supabase: Client, token: str) -> dict | None:
    """Verify a JWT token and return the user profile."""
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            return None
        
        user = user_response.user
        # Get profile with role
        profile = supabase.table("profiles").select("*").eq("id", user.id).execute()
        if profile.data:
            return profile.data[0]
        return None
    except Exception:
        return None


def is_admin(profile: dict) -> bool:
    """Check if a user profile has admin role."""
    return profile.get("role") == "admin"


def signup_user(supabase: Client, email: str, password: str, full_name: str) -> dict:
    """Sign up a new user."""
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "role": "participant",
                }
            }
        })
        if result.user:
            return {
                "user_id": str(result.user.id),
                "email": result.user.email,
                "access_token": result.session.access_token if result.session else None,
            }
        raise ValueError("Signup failed")
    except Exception as e:
        raise ValueError(str(e))


def login_user(supabase: Client, email: str, password: str) -> dict:
    """Log in a user."""
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if result.user and result.session:
            # Get profile
            profile = supabase.table("profiles").select("*").eq("id", result.user.id).execute()
            role = profile.data[0]["role"] if profile.data else "participant"
            return {
                "user_id": str(result.user.id),
                "email": result.user.email,
                "role": role,
                "full_name": profile.data[0].get("full_name", "") if profile.data else "",
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
            }
        raise ValueError("Login failed")
    except Exception as e:
        raise ValueError(str(e))


def grant_admin(supabase: Client, user_email: str):
    """Grant admin role to a user by email."""
    supabase.table("profiles").update({"role": "admin"}).eq("email", user_email).execute()


def revoke_admin(supabase: Client, user_email: str):
    """Revoke admin role from a user."""
    supabase.table("profiles").update({"role": "participant"}).eq("email", user_email).execute()


def list_users(supabase: Client) -> list:
    """List all users (admin only)."""
    result = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
    return result.data
