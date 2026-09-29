from fastapi import APIRouter
from core.debug_env import print_env_to_vercel_logs, get_env_dump

router = APIRouter()

@router.get("/debug-env", tags=["debug"])
def get_debug_env(show_all: bool = False):
    """
    Explicitly logs all environment variables (especially DATABASE_URL)
    to Vercel logs and returns the environment status.
    Pass ?show_all=true to include all system environment variables in the response.
    """
    print_env_to_vercel_logs(context="API_V1_DEBUG_ENDPOINT")
    dump = get_env_dump()
    res = {
        "status": "success",
        "message": "Environment variables successfully logged to Vercel runtime logs! Check your Vercel deployment logs dashboard.",
        "database_url": dump["database_url"] or "NOT_SET",
        "database_related": dump["database_related"],
        "app_variables": dump["app_variables"],
    }
    if show_all:
        res["all_variables"] = dump["all_variables"]
    return res
