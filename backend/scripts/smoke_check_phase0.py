"""
End-to-end smoke checks for Phase 0.

This script verifies:
1) Core imports succeed.
2) Database can connect and list expected tables.
3) HTTP health endpoint responds.

Run:
    python scripts/smoke_check.py
"""
# Ensure the backend root is on sys.path when running this script directly.
import sys, os
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from typing import List
import sys
from sqlalchemy import inspect
from app.db import engine
from app.main import app  # noqa: F401  # importing ensures metadata is created
import httpx

def _check_imports() -> List[str]:
    """
    Checks importability of core modules.

    Args:
        None

    Returns:
        List[str]: A list of error messages; empty if no errors.
    """
    errors: List[str] = []
    try:
        import app.config as _cfg  # noqa: F401
        import app.db as _db       # noqa: F401
        import app.models as _mdl  # noqa: F401
    except Exception as exc:
        errors.append(f"Import error: {exc!r}")
    return errors

def _check_db() -> List[str]:
    """
    Checks database connectivity and required tables.

    Args:
        None

    Returns:
        List[str]: A list of error messages; empty if no errors.
    """
    errors: List[str] = []
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        required = {"meetings", "utterances"}
        missing = required - tables
        if missing:
            errors.append(f"Missing tables: {sorted(missing)}")
    except Exception as exc:
        errors.append(f"DB error: {exc!r}")
    return errors

def _check_http() -> List[str]:
    """
    Checks that the HTTP health endpoint is responding.

    Args:
        None

    Returns:
        List[str]: A list of error messages; empty if no errors.
    """
    errors: List[str] = []
    try:
        resp = httpx.get("http://127.0.0.1:8000/health/ready", timeout=5.0)
        if resp.status_code != 200:
            errors.append(f"Health status code: {resp.status_code}")
        else:
            data = resp.json()
            if data.get("status") != "ok":
                errors.append(f"Unexpected health payload: {data}")
    except Exception as exc:
        errors.append(f"HTTP error: {exc!r}")
    return errors

def main() -> None:
    """
    Runs all smoke checks and prints a summary.

    Args:
        None

    Returns:
        None
    """
    overall_errors: List[str] = []
    overall_errors += _check_imports()
    overall_errors += _check_db()
    overall_errors += _check_http()

    if overall_errors:
        print("Smoke check FAILED")
        for e in overall_errors:
            print(" -", e)
        sys.exit(1)
    else:
        print("Smoke check PASSED")

if __name__ == "__main__":
    main()
