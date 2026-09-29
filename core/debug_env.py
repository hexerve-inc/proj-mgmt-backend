import os
import sys
from datetime import datetime

def get_env_dump():
    """
    Gathers environment variables with special focus on DATABASE_URL
    and database-related configurations.
    """
    database_url = os.getenv("DATABASE_URL", "")
    
    # Check alternate database environment variables commonly set by Vercel or cloud providers
    db_related_keys = [
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_PRISMA_URL",
        "POSTGRES_URL_NON_POOLING",
        "POSTGRES_USER",
        "POSTGRES_HOST",
        "POSTGRES_PASSWORD",
        "POSTGRES_DATABASE",
        "NEON_DATABASE_URL",
        "SUPABASE_URL",
        "DATABASE_PRIVATE_URL",
    ]
    db_vars = {k: os.getenv(k) for k in db_related_keys if os.getenv(k) is not None}
    
    # Key application variables
    app_keys = [
        "PROJECT_NAME",
        "EXTERNAL_API_KEY",
        "FRONTEND_URL",
        "EMAIL_ENABLED",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_USE_TLS",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
        "VERCEL",
        "VERCEL_ENV",
        "VERCEL_URL",
        "VERCEL_REGION",
    ]
    app_vars = {k: os.getenv(k) for k in app_keys if os.getenv(k) is not None}
    
    # All system environment variables sorted by key
    all_vars = dict(sorted(os.environ.items()))
    
    return {
        "database_url": database_url,
        "database_related": db_vars,
        "app_variables": app_vars,
        "all_variables": all_vars,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

def print_env_to_vercel_logs(context: str = "GENERAL"):
    """
    Explicitly prints all environment variables (especially DATABASE_URL)
    to stdout/stderr with flush=True so they immediately appear in Vercel Function logs.
    """
    data = get_env_dump()
    border = "=" * 80
    
    print(f"\n{border}", flush=True)
    print(f"[VERCEL LOGS] ENVIRONMENT DUMP ({context}) - {data['timestamp']}", flush=True)
    print(border, flush=True)
    
    print("\n--- DATABASE URL ---", flush=True)
    if data["database_url"]:
        print(f"DATABASE_URL = {data['database_url']}", flush=True)
    else:
        print("DATABASE_URL is NOT SET or is empty in os.environ!", flush=True)
        
    print("\n--- DATABASE-RELATED VARIABLES ---", flush=True)
    if data["database_related"]:
        for k, v in data["database_related"].items():
            print(f"  {k} = {v}", flush=True)
    else:
        print("  None detected.", flush=True)
        
    print("\n--- APPLICATION CONFIGURATION ---", flush=True)
    for k, v in data["app_variables"].items():
        print(f"  {k} = {v}", flush=True)
        
    print("\n--- ALL ENVIRONMENT VARIABLES (os.environ) ---", flush=True)
    for k, v in data["all_variables"].items():
        print(f"  {k} = {v}", flush=True)
        
    print(f"\n{border}\n", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
