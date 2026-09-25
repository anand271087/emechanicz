"""Create the admin account in Supabase Auth (idempotent).

Run from backend/:  .venv/bin/python -m scripts.seed_admin
"""
from supabase import create_client

from app.config import settings


def main() -> None:
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    existing = next((u for u in sb.auth.admin.list_users() if u.email == settings.admin_email), None)
    if existing:
        if (existing.app_metadata or {}).get("role") != "admin":
            sb.auth.admin.update_user_by_id(existing.id, {"app_metadata": {"role": "admin"}})
            print(f"Promoted existing user {settings.admin_email} to admin")
        else:
            print(f"Admin {settings.admin_email} already exists")
        return
    sb.auth.admin.create_user({
        "email": settings.admin_email,
        "password": settings.admin_password,
        "email_confirm": True,
        "app_metadata": {"role": "admin"},
    })
    print(f"Created admin {settings.admin_email} — change the password after first login")


if __name__ == "__main__":
    main()
