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

In a Databricks App none of that is set by hand: the app's Lakebase resource gives it
``PGHOST``, ``PGDATABASE``, ``PGUSER`` (the app's service principal) and ``LAKEBASE_ENDPOINT``,
and the tables go in their own schema (``DRILL_DB_SCHEMA``, ``drill`` in the app), which the
service principal creates and owns. One app serves everyone, so each request reads and
writes as the signed-in person (:meth:`DocStore.for_owner`).

If Lakebase cannot be reached when the server starts on your own computer, it keeps going on the
local SQLite file and says so; ``drill store push`` sends that work up later. In a
Databricks App it keeps trying for a couple of minutes and then refuses to start: the
app's disk is wiped on every restart, so a local file there would quietly lose work.

Besides the documents there is an ``events`` table: one row per thing that happened
(a lesson step reached, a hint asked for, tests run), which is what a team dashboard
counts. See :mod:`drill.server.activity`.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import (
    Column,
    Float,
    Integer,
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
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from drill.config import PROJECT_ROOT

log = logging.getLogger("drill.server")

LOCAL_OWNER = "local"
TOKEN_LIFETIME = 45 * 60  # Lakebase passwords last an hour; get a new one well before that
CONNECT_TIMEOUT = 10  # seconds to wait for Postgres to answer before giving up on a connection
APP_WAIT = 120  # seconds a Databricks App keeps trying Lakebase before refusing to start

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
# The manager's view (drill.server.team): a dashboard reads these beside docs and events.
lessons = Table(
    "lessons",
    metadata,
    Column("id", String(120), primary_key=True),
    Column("no", String(12), nullable=False),  # "2.11": phase 2, its 11th lesson, as the page numbers it
    Column("position", Integer, nullable=False),  # 1 to N along the whole path
    Column("title", String(300), nullable=False),
    Column("phase", String(80), nullable=False),
    Column("module", String(160), nullable=False),
    Column("check_answer", Integer, nullable=False),  # the right option of the lesson's Check, from 0
)
summaries = Table(
    "summaries",
    metadata,
    Column("owner", String(320), primary_key=True),
    Column("week", String(10), primary_key=True),  # ISO week, "2026-W42"
    Column("made_at", Float, nullable=False),
    Column("summary", Text, nullable=False),  # a few plain sentences for the manager
    Column("facts", Text, nullable=False, default="{}"),  # the numbers it was written from, as JSON text
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
    """Where documents live: ``DRILL_DATABASE_URL`` if set, else the Lakebase a Databricks App
    was given (``PGHOST``), else the SQLite file in :func:`data_dir`."""
    url = os.getenv("DRILL_DATABASE_URL", "").strip()
    if url:
        return url
    host = os.getenv("PGHOST", "").strip()
    if host:
        port = os.getenv("PGPORT", "").strip() or "5432"
        database = os.getenv("PGDATABASE", "").strip() or "databricks_postgres"
        return f"postgresql+psycopg://{host}:{port}/{database}?sslmode={os.getenv('PGSSLMODE', '').strip() or 'require'}"
    return local_url()


def lakebase_endpoint() -> str:
    """The Lakebase endpoint to get passwords for: ours, or the one a Databricks App's resource names."""
    return os.getenv("DRILL_LAKEBASE_ENDPOINT", "").strip() or os.getenv("LAKEBASE_ENDPOINT", "").strip()


def _valid_schema(name: str) -> str:
    """``name`` when it is a safe Postgres identifier, else ``ValueError``.

    The schema name is pasted into ``CREATE SCHEMA`` and ``GRANT`` statements, so it is checked
    here, where it is used, whether it came from ``DRILL_DB_SCHEMA`` or a ``DocStore(schema=...)`` call.
    """
    if name and not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", name):
        raise ValueError(f"the schema (DRILL_DB_SCHEMA) must be lowercase letters, digits and underscores, not {name!r}")
    return name


def db_schema() -> str:
    """The Postgres schema for the tables (``DRILL_DB_SCHEMA``); empty means the database's default."""
    return _valid_schema(os.getenv("DRILL_DB_SCHEMA", "").strip())


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
        """The Lakebase role to sign in as: the person's Databricks user name (their work email)
        on a laptop, or ``PGUSER`` (the app's service principal) in a Databricks App. Only in an
        app: a laptop with PostgreSQL installed often sets ``PGUSER=postgres`` for its own server."""
        if not self._user:
            pguser = os.getenv("PGUSER", "").strip() if in_databricks_app() else ""
            self._user = pguser or self.client.current_user.me().user_name
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

    def __init__(self, url: str | None = None, owner: str | None = None, login: LakebaseLogin | None = None,
                 schema: str | None = None):
        self.url = url or database_url()
        self.schema = "" if self.url.startswith("sqlite") else _valid_schema(db_schema() if schema is None else schema)
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
            if "connect_timeout" not in self.url:
                kwargs["connect_args"] = {"connect_timeout": CONNECT_TIMEOUT}
        self.engine = create_engine(self.url, future=True, **kwargs)
        if login is not None:

            @event.listens_for(self.engine, "do_connect")
            def _sign_in(dialect, conn_rec, cargs, cparams):  # noqa: ARG001
                cparams["user"] = login.user
                cparams["password"] = login.password()

        if self.schema:
            # Every connection looks in our own schema first, so the tables are created and found there.
            @event.listens_for(self.engine, "do_connect")
            def _use_schema(dialect, conn_rec, cargs, cparams):  # noqa: ARG001
                cparams["options"] = f"-csearch_path={self.schema}"

            with self.engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))

        self.owner = owner or (login.user if login else os.getenv("DRILL_OWNER", "").strip() or LOCAL_OWNER)
        if self.url.startswith("sqlite"):
            _add_owner_column(self.engine)
        metadata.create_all(self.engine)
        # Read-change-write updates (update(), add()) hold this so two requests in this
        # process can't both read the old document and lose one of the changes.
        self._writing = threading.Lock()

    def for_owner(self, owner: str) -> "DocStore":
        """The same database, reading and writing ``owner``'s rows: one per signed-in person in an app."""
        if not owner or owner == self.owner:
            return self
        view = copy.copy(self)
        view.owner = owner
        return view

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
        """Replace the document at ``path`` (creating it if needed) and return it.

        One statement ("insert, or update if it's already there"), so two saves to the same
        path at the same moment can't trip over each other the way delete-then-insert did.
        """
        values = {"owner": self.owner, "path": path, "body": json.dumps(doc), "updated_at": updated_at or time.time()}
        upsert = (pg_insert if self.engine.dialect.name == "postgresql" else sqlite_insert)(docs).values(**values)
        upsert = upsert.on_conflict_do_update(
            index_elements=[docs.c.owner, docs.c.path],
            set_={"body": upsert.excluded.body, "updated_at": upsert.excluded.updated_at},
        )
        with self.engine.begin() as conn:
            conn.execute(upsert)
        return doc

    def update(self, path: str, patch: dict) -> dict:
        """Merge ``patch`` into the document (creating it if needed) and return the result."""
        with self._writing:
            merged = dict(self.get(path) or {})
            merged.update(patch)
            return self.set(path, merged)

    def add(self, path: str, key: str, amounts: dict[str, int]) -> dict:
        """Add ``amounts`` to the counters under ``key`` in the document at ``path``, e.g. a day's usage.

        Read and write happen under one lock, so two answers finishing together both count.
        """
        with self._writing:
            doc = self.get(path) or {}
            entry = doc.setdefault(key, {})
            for name, amount in amounts.items():
                entry[name] = int(entry.get(name, 0)) + int(amount)
            return self.set(path, doc)

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

    def prune(self, collection: str, older_than: float, keep: int | None = None) -> int:
        """Delete documents in ``collection`` last saved before ``older_than``, then all but the newest ``keep``.

        For the answer cache, so it ages out and stays a bounded size. Returns how many went.
        """
        prefix = collection.rstrip("/") + "/"
        inside = (self._mine(), docs.c.path.startswith(prefix, autoescape=True))
        with self.engine.begin() as conn:
            gone = conn.execute(delete(docs).where(*inside, docs.c.updated_at < older_than)).rowcount or 0
            if keep is not None:
                extra = conn.execute(
                    select(docs.c.path).where(*inside).order_by(docs.c.updated_at.desc()).offset(keep)
                ).scalars().all()
                for start in range(0, len(extra), 500):  # in batches, to keep each statement small
                    gone += conn.execute(delete(docs).where(self._mine(), docs.c.path.in_(extra[start:start + 500]))).rowcount or 0
        return gone

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
            # the kind can come from a request: line breaks out, so it can't forge a log line
            log.warning("Could not record %s event: %s", kind.replace("\r", " ").replace("\n", " "), exc)

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


def in_databricks_app() -> bool:
    """True when running as a Databricks App, which sets ``DATABRICKS_APP_NAME``."""
    return bool(os.getenv("DATABRICKS_APP_NAME", "").strip())


def open_store(make_login: Callable[[str], LakebaseLogin] = LakebaseLogin, wait: float | None = None) -> DocStore:
    """The store the settings ask for. Lakebase when ``DRILL_LAKEBASE_ENDPOINT`` is set.

    When Lakebase can't be reached: on your own computer, fall back to the local SQLite file (with
    ``fallback`` set) so practice goes on and ``drill store push`` sends it up later. In a
    Databricks App, keep trying for ``wait`` seconds (Lakebase may still be waking up) and
    then raise, because the app's local disk is wiped on restart and the work would be lost.
    """
    endpoint = lakebase_endpoint()
    if not endpoint:
        return DocStore()
    in_app = in_databricks_app()
    deadline = time.monotonic() + (APP_WAIT if wait is None else wait) if in_app else 0.0
    pause, login = 2.0, None
    while True:
        try:
            login = make_login(endpoint)
            store = DocStore(database_url(), login=login)
            with store.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return store
        except Exception as exc:  # noqa: BLE001
            if in_app and time.monotonic() + pause < deadline:
                log.warning("Lakebase is not answering yet (%s). Trying again in %.0fs.", exc, pause)
                time.sleep(pause)
                pause = min(pause * 2, 30.0)
                continue
            if in_app:
                raise RuntimeError(
                    "Lakebase could not be reached, so the app will not start: saving to this app's disk "
                    "would lose everyone's work at the next restart."
                ) from exc
            log.warning("Lakebase is out of reach (%s). Saving on this machine; run `drill store push` later.", exc)
            break
    try:
        owner = login.user if login is not None else ""
    except Exception:  # noqa: BLE001
        owner = ""
    store = DocStore(local_url(), owner=owner or os.getenv("DRILL_OWNER", "").strip() or LOCAL_OWNER)
    store.fallback = True
    return store
