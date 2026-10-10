"""A tiny document store: the local stand-in for the page's account storage.

On claude.ai the Daily Drill page keeps your study list and your progress in the
artifact's own database, addressed by path: ``study/<id>`` is one study item,
``data/users/<id>/progress`` is your progress. When the page is served from this Mac
instead, the same documents land here, under the same paths.

By default this is one SQLite file (``.drill/drill.db``): nothing to install, nothing to
run, and easy to back up. It goes through SQLAlchemy, so pointing it at Postgres later -
Neon on Azure, Lakebase on Databricks - is a connection string, not a rewrite::

    DRILL_DATABASE_URL=postgresql+psycopg://user:password@host/dbname
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from sqlalchemy import Column, Float, MetaData, String, Table, Text, create_engine, delete, insert, select

from drill.config import PROJECT_ROOT

DEFAULT_DB_PATH = PROJECT_ROOT / ".drill" / "drill.db"

metadata = MetaData()
docs = Table(
    "docs",
    metadata,
    Column("path", String(512), primary_key=True),
    Column("body", Text, nullable=False),  # the document itself, as JSON text
    Column("updated_at", Float, nullable=False),  # seconds since 1970, for "newest first"
)


def database_url() -> str:
    """Where documents live: ``DRILL_DATABASE_URL`` if set, else the SQLite file under .drill/."""
    url = os.getenv("DRILL_DATABASE_URL", "").strip()
    if url:
        return url
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_DB_PATH}"


class DocStore:
    """JSON documents at paths, such as ``study/abc123`` or ``data/users/local/progress``.

    A path with an even number of parts is a document; the part before the last is its
    collection. That mirrors the artifact database the page already uses, so the page's
    code does not care which one it is talking to.
    """

    def __init__(self, url: str | None = None):
        self.url = url or database_url()
        kwargs: dict[str, Any] = {}
        if self.url.startswith("sqlite"):
            # SQLite ties a connection to the thread that opened it, which a web
            # server's worker threads would trip over. The busy timeout lets the web
            # server and the stdio MCP process share the one file politely.
            kwargs["connect_args"] = {"check_same_thread": False, "timeout": 5}
        self.engine = create_engine(self.url, future=True, **kwargs)
        metadata.create_all(self.engine)

    @property
    def kind(self) -> str:
        """``sqlite`` or ``postgresql``: shown in the health check, never the full URL."""
        return self.url.split(":", 1)[0].split("+", 1)[0]

    def get(self, path: str) -> dict | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(docs.c.body).where(docs.c.path == path)).first()
        return json.loads(row[0]) if row else None

    def set(self, path: str, doc: dict) -> dict:
        """Replace the document at ``path`` (creating it if needed) and return it."""
        with self.engine.begin() as conn:
            conn.execute(delete(docs).where(docs.c.path == path))
            conn.execute(insert(docs).values(path=path, body=json.dumps(doc), updated_at=time.time()))
        return doc

    def update(self, path: str, patch: dict) -> dict:
        """Merge ``patch`` into the document (creating it if needed) and return the result."""
        merged = dict(self.get(path) or {})
        merged.update(patch)
        return self.set(path, merged)

    def delete(self, path: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(docs).where(docs.c.path == path))

    def list(self, collection: str) -> list[tuple[str, dict]]:
        """The documents directly inside ``collection``, as ``(id, document)`` pairs, newest first."""
        prefix = collection.rstrip("/") + "/"
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(docs.c.path, docs.c.body)
                .where(docs.c.path.startswith(prefix, autoescape=True))
                .order_by(docs.c.updated_at.desc())
            ).all()
        out: list[tuple[str, dict]] = []
        for path, body in rows:
            rest = path[len(prefix) :]
            if rest and "/" not in rest:  # a direct child, not something nested deeper
                out.append((rest, json.loads(body)))
        return out
