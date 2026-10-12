"""A tiny document store: the local stand-in for the page's account storage.

On claude.ai the Daily Drill page keeps your study list and your progress in the
artifact's own database, addressed by path: ``study/<id>`` is one study item,
``data/users/<id>/progress`` is your progress. When the page is served from this Mac
instead, the same documents land here, under the same paths.

By default this is one SQLite file (``.drill/drill.db``): nothing to install, nothing to
run, and easy to back up. ``DRILL_HOME`` moves it (and the MLflow file) out of the repo.

Every row has an ``owner``: ``local`` on your own Mac, the person's work email when the
store is shared. A store only ever reads and writes its own owner's rows, so one
database can hold a whole team.

Lakebase (Postgres on Databricks) is the shared version. It needs two settings and a
Databricks login (``databricks auth login``), and no password: the app asks Databricks for
a fresh one-hour password whenever it opens a connection::

    DRILL_DATABASE_URL=postgresql+psycopg://<host>/databricks_postgres?sslmode=require
    DRILL_LAKEBASE_ENDPOINT=projects/<project>/branches/<branch>/endpoints/<endpoint>

If Lakebase cannot be reached when the server starts, it keeps going on the local SQLite
file and says so; ``drill store push`` sends that work up later.

Besides the documents there is an ``events`` table: one row per thing that happened
(a lesson step reached, a hint asked for, tests run), which is what a team dashboard
counts. See :mod:`drill.server.activity`.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import (
    Column,
    Float,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    event,
    inspect,
    insert,
    select,
    text,
)

from drill.config import PROJECT_ROOT

log = logging.getLogger("drill.server")

LOCAL_OWNER = "local"
TOKEN_LIFETIME = 45 * 60  # Lakebase passwords last an hour; get a new one well before that

metadata = MetaData()
docs = Table(
    "docs",
    metadata,
    Column("owner", String(320), primary_key=True),  # "local", or the person's work email
    Column("path", String(512), primary_key=True),
    Column("body", Text, nullable=False),  # the document itself, as JSON text
    Column("updated_at", Float, nullable=False),  # seconds since 1970, for "newest first"
)
events = Table(
    "events",
    metadata,
    Column("id", String(32), primary_key=True),  # random, so pushing the same event twice is harmless
    Column("owner", String(320), nullable=False, index=True),
    Column("at", Float, nullable=False),  # seconds since 1970
    Column("kind", String(40), nullable=False),  # step, checked, lesson_done, solved, asked, hint_used...
    Column("lesson_id", String(120), nullable=False, default=""),
    Column("detail", Text, nullable=False, default="{}"),  # anything else, as JSON text
)


def data_dir() -> Path:
    """Where this machine keeps its files: ``DRILL_HOME`` if set, else ``.drill/`` in the repo."""
    home = os.getenv("DRILL_HOME", "").strip()
    folder = Path(home).expanduser() if home else PROJECT_ROOT / ".drill"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def local_url() -> str:
    return f"sqlite:///{data_dir() / 'drill.db'}"


def database_url() -> str:
    """Where documents live: ``DRILL_DATABASE_URL`` if set, else the SQLite file in :func:`data_dir`."""
    return os.getenv("DRILL_DATABASE_URL", "").strip() or local_url()


def lakebase_endpoint() -> str:
    return os.getenv("DRILL_LAKEBASE_ENDPOINT", "").strip()


class LakebaseLogin:
    """The Databricks login behind a Lakebase connection: who you are, and a password that is never stale.

    ``client`` is a ``databricks.sdk.WorkspaceClient``; it uses whatever login is on this
    machine (``databricks auth login``, which goes through Entra on Azure, or ``az login``).
    """

    def __init__(self, endpoint: str, client: Any = None, lifetime: float = TOKEN_LIFETIME):
        if client is None:
            from databricks.sdk import WorkspaceClient

            client = WorkspaceClient()
        self.endpoint, self.client, self.lifetime = endpoint, client, lifetime
        self._token, self._until = "", 0.0
        self._user = ""

    @property
    def user(self) -> str:
        """The signed-in person's Databricks user name: their work email, and their Lakebase role."""
        if not self._user:
            self._user = self.client.current_user.me().user_name
        return self._user

    def password(self) -> str:
        if time.time() >= self._until:
            self._token = self.client.postgres.generate_database_credential(endpoint=self.endpoint).token
            self._until = time.time() + self.lifetime
        return self._token


class DocStore:
    """JSON documents at paths, such as ``study/abc123`` or ``data/users/local/progress``, for one owner.

    A path with an even number of parts is a document; the part before the last is its
    collection. That mirrors the artifact database the page already uses, so the page's
    code does not care which one it is talking to.
    """

    def __init__(self, url: str | None = None, owner: str | None = None, login: LakebaseLogin | None = None):
        self.url = url or database_url()
        self.login = login
        self.fallback = False  # set by open_store when Lakebase was wanted but could not be reached
        kwargs: dict[str, Any] = {}
        if self.url.startswith("sqlite"):
            # SQLite ties a connection to the thread that opened it, which a web
            # server's worker threads would trip over. The busy timeout lets the web
            # server and the stdio MCP process share the one file politely.
            kwargs["connect_args"] = {"check_same_thread": False, "timeout": 5}
        else:
            kwargs["pool_pre_ping"] = True  # Lakebase sleeps when idle; check a connection before using it
        self.engine = create_engine(self.url, future=True, **kwargs)
        if login is not None:

            @event.listens_for(self.engine, "do_connect")
            def _sign_in(dialect, conn_rec, cargs, cparams):  # noqa: ARG001
                cparams["user"] = login.user
                cparams["password"] = login.password()

        self.owner = owner or (login.user if login else os.getenv("DRILL_OWNER", "").strip() or LOCAL_OWNER)
        if self.url.startswith("sqlite"):
            _add_owner_column(self.engine)
        metadata.create_all(self.engine)

    @property
    def kind(self) -> str:
        """``sqlite``, ``postgresql`` or ``lakebase``: shown in the health check, never the full URL."""
        if self.login is not None:
            return "lakebase"
        return self.url.split(":", 1)[0].split("+", 1)[0]

    def _mine(self):
        return docs.c.owner == self.owner

    def get(self, path: str) -> dict | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(docs.c.body).where(self._mine(), docs.c.path == path)).first()
        return json.loads(row[0]) if row else None

    def set(self, path: str, doc: dict, updated_at: float | None = None) -> dict:
        """Replace the document at ``path`` (creating it if needed) and return it."""
        with self.engine.begin() as conn:
            conn.execute(delete(docs).where(self._mine(), docs.c.path == path))
            conn.execute(
                insert(docs).values(
                    owner=self.owner, path=path, body=json.dumps(doc), updated_at=updated_at or time.time()
                )
            )
        return doc

    def update(self, path: str, patch: dict) -> dict:
        """Merge ``patch`` into the document (creating it if needed) and return the result."""
        merged = dict(self.get(path) or {})
        merged.update(patch)
        return self.set(path, merged)

    def delete(self, path: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(docs).where(self._mine(), docs.c.path == path))

    def list(self, collection: str) -> list[tuple[str, dict]]:
        """The documents directly inside ``collection``, as ``(id, document)`` pairs, newest first."""
        prefix = collection.rstrip("/") + "/"
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(docs.c.path, docs.c.body)
                .where(self._mine(), docs.c.path.startswith(prefix, autoescape=True))
                .order_by(docs.c.updated_at.desc())
            ).all()
        out: list[tuple[str, dict]] = []
        for path, body in rows:
            rest = path[len(prefix) :]
            if rest and "/" not in rest:  # a direct child, not something nested deeper
                out.append((rest, json.loads(body)))
        return out

    # -- the activity log ----------------------------------------------------

    def log(self, kind: str, lesson_id: str = "", **detail: Any) -> None:
        """Record one thing that happened. Never raises: losing a log line must not lose a lesson."""
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    insert(events).values(
                        id=uuid.uuid4().hex, owner=self.owner, at=time.time(), kind=kind,
                        lesson_id=lesson_id or "", detail=json.dumps(detail),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not record %s event: %s", kind, exc)

    def events(self, since: float = 0.0) -> list[dict]:
        """This owner's events, oldest first."""
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(events).where(events.c.owner == self.owner, events.c.at >= since).order_by(events.c.at)
            ).mappings().all()
        return [{**row, "detail": json.loads(row["detail"])} for row in rows]

    # -- moving work between stores -------------------------------------------

    def push_to(self, other: DocStore) -> dict:
        """Copy this store's documents and events into ``other``, under ``other``'s owner.

        For when the server ran on the local file because Lakebase was out of reach, or to
        bring your own history to work. A document already in ``other`` keeps whichever
        copy changed last; an event already there is skipped.
        """
        with self.engine.begin() as conn:
            mine = conn.execute(select(docs.c.path, docs.c.body, docs.c.updated_at).where(self._mine())).all()
            my_events = conn.execute(select(events).where(events.c.owner == self.owner)).mappings().all()
        with other.engine.begin() as conn:
            theirs = dict(conn.execute(select(docs.c.path, docs.c.updated_at).where(other._mine())).all())
            seen = set(conn.execute(select(events.c.id).where(events.c.owner == other.owner)).scalars())
        counts = {"docs": 0, "skipped": 0, "events": 0}
        for path, body, updated_at in mine:
            if path in theirs and theirs[path] >= updated_at:
                counts["skipped"] += 1
                continue
            other.set(path, json.loads(body), updated_at=updated_at)
            counts["docs"] += 1
        new = [{**row, "owner": other.owner} for row in my_events if row["id"] not in seen]
        if new:
            with other.engine.begin() as conn:
                conn.execute(insert(events), new)
        counts["events"] = len(new)
        return counts


def _add_owner_column(engine) -> None:
    """Bring a SQLite file from before owners existed up to date; its rows become ``local``'s."""
    names = inspect(engine).get_table_names()
    if "docs" not in names:
        return
    if "owner" in {c["name"] for c in inspect(engine).get_columns("docs")}:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE docs RENAME TO docs_before_owner"))
        docs.create(conn)
        conn.execute(
            text(
                "INSERT INTO docs (owner, path, body, updated_at) "
                "SELECT :owner, path, body, updated_at FROM docs_before_owner"
            ),
            {"owner": LOCAL_OWNER},
        )
        conn.execute(text("DROP TABLE docs_before_owner"))


def open_store(make_login: Callable[[str], LakebaseLogin] = LakebaseLogin) -> DocStore:
    """The store the settings ask for. Lakebase when ``DRILL_LAKEBASE_ENDPOINT`` is set, falling
    back to the local SQLite file (with ``fallback`` set) when it cannot be reached."""
    endpoint = lakebase_endpoint()
    if not endpoint:
        return DocStore()
    try:
        login = make_login(endpoint)
        store = DocStore(database_url(), login=login)
        with store.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return store
    except Exception as exc:  # noqa: BLE001
        log.warning("Lakebase is out of reach (%s). Saving on this machine; run `drill store push` later.", exc)
        try:
            owner = login.user  # type: ignore[possibly-undefined]
        except Exception:  # noqa: BLE001
            owner = os.getenv("DRILL_OWNER", "").strip() or LOCAL_OWNER
        store = DocStore(local_url(), owner=owner)
        store.fallback = True
        return store
