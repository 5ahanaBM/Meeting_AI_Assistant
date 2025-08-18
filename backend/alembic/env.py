from __future__ import annotations

import sys, pkgutil, importlib
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, text
from app.config import settings

# --- Load .env and make sure we can import app.* ---
from pathlib import Path
from dotenv import load_dotenv
BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# --- Alembic config ---
config = context.config

# --- Import settings and OVERRIDE the URL BEFORE engine_from_config ---
config.set_main_option("sqlalchemy.url", settings.alembic_database_url)

# Optional: log where Alembic thinks it will connect
print("ALEMBIC sqlalchemy.url =", config.get_main_option("sqlalchemy.url"))

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import Base and models so autogenerate can see them ---
from app.db import Base
try:
    import app.models as models_pkg  # noqa: F401
    pkg_path = BACKEND_ROOT / "app" / "models"
    if pkg_path.exists():
        for m in pkgutil.iter_modules([str(pkg_path)]):
            importlib.import_module(f"app.models.{m.name}")
except Exception:
    pass

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Force schema to public (belt & suspenders)
        connection.execute(text("SET search_path TO public"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table="alembic_version",
            version_table_schema="public",   # <<< important
            include_schemas=False,           # we only care about public here
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()