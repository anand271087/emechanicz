import pytest
from supabase import create_client

from app.config import settings


@pytest.mark.integration
def test_tables_exist():
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    for table in ["customers", "quotes", "quote_items", "app_settings"]:
        sb.table(table).select("*").limit(1).execute()


@pytest.mark.integration
def test_settings_seeded():
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    keys = {r["key"] for r in sb.table("app_settings").select("key").execute().data}
    assert {"company", "quote_seq", "default_terms", "default_intro"} <= keys
