# Note: this is an LLM-generated file
from alembic import context
from sqlmodel import SQLModel

from quorra.classes import Device, OnboardingLink, User
from quorra.config import config
from quorra.database import engine

# Make sure every table gets registered on SQLModel.metadata before we use it
# below to diff against the live database.
target_metadata = SQLModel.metadata

# Always take the DB URL from Quorra's own config (config.yaml / QUORRA_CONFIG),
# rather than whatever might be hardcoded in alembic.ini, so migrations always
# target the same DB the running server actually uses.
context.config.set_main_option("sqlalchemy.url", config["database"]["sql"]["string"])


def run_migrations_online() -> None:
    """Run migrations against a live DB connection.

    Quorra always runs against a configured, reachable database, so we only
    need the "online" mode here (as opposed to "offline" mode, which just
    emits raw SQL without connecting to anything).
    """
    # Reuse the same engine the rest of the app uses, so we don't need to
    # duplicate connection/pooling setup here.
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite can't ALTER most things directly; batch mode has Alembic
            # recreate-and-copy the table under the hood instead. Postgres
            # doesn't need this, so only turn it on when it's actually SQLite.
            render_as_batch=(connection.dialect.name == "sqlite"),
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
