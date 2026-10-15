"""Content packs: optional lessons kept outside the public curriculum, written as YAML.

A pack is a folder (see content-packs/README.md and docs/CONTENT_PACKS.md)::

    my-pack/
      pack.yaml            # id, title, version, the phase or track it joins, its journeys and their lessons
      lessons/*.yaml       # one lesson per file: learn, check, practice, explain, evidence
      assets/              # screenshots and diagrams the lessons point at

A pack's lessons become ordinary modules and lessons in :func:`drill.content.build.build_data`,
with a ``practice`` block (an interactive exercise, see :data:`PRACTICE_KINDS`) in place of the
Python exercise. Nothing loads a pack unless asked: the server reads ``DRILL_CONTENT_PACKS``
(folders, separated by ``:``), and ``drill build-page`` only with ``--pack``. So the public page
never contains a pack. A folder named in ``DRILL_CONTENT_PACKS`` that is not there is skipped
with one log line, so a deployment can name a pack by default without every checkout carrying it;
a folder that is there but broken stops the server with a :class:`PackError` naming each problem.

Each lesson has a ``status``:

``slot``    a placeholder for content still to come. Never shown.
``draft``   being written. Shown only when previewing (``DRILL_SHOW_DRAFTS=1``), marked Draft.
``ready``   shown. Must be complete, with no ``_TODO`` placeholder left anywhere.

A journey whose lessons are all hidden is left out, so navigation never leads to an empty page.
Lesson ids are permanent: progress is saved under them. To rename one, keep the old id in
``aliases`` and the page carries the learner's progress over.
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from drill.config import PROJECT_ROOT
from drill.content.model import Module

log = logging.getLogger(__name__)

STATUSES = ("slot", "draft", "ready")
DIFFICULTIES = ("intro", "core", "advanced")
ID = re.compile(r"^[a-z][a-z0-9_]{2,62}$")
TODO = re.compile(r"[A-Z_]+_TODO\b")

# What a learner does in the Build step. Each kind has its own fields (check_practice says which).
# Several share one way of answering: pick one option after reading the artifacts.
PRACTICE_KINDS = {
    "multiple_choice": "choice",       # select the right explanation
    "identify_error": "choice",        # find the problem in a configuration or code snippet
    "troubleshooting": "choice",       # diagnose an error and choose the next action
    "review_decision": "choice",       # approve, request changes or escalate, with the reason
    "source_tracing": "choice",        # follow a value through implementation layers
    "difference_review": "choice",     # compare two configurations or planned changes
    "ordering": "ordering",            # put steps in the right order
    "relationship_mapping": "match",   # connect each reference to its target
    "configuration_repair": "repair",  # correct an invalid configuration; rules check the answer
    "reasoning": "reasoning",          # answer in your own words, then compare with the expected answer
}
ARTIFACT_KINDS = ("code", "config", "log", "plan", "text", "diff")
VIEW_KINDS = ("relationships", "trace", "walkthrough", "plan_review", "tour")
TRACE_STATES = ("same", "changed", "added", "unknown")
PLAN_ACTIONS = ("create", "update", "replace", "destroy", "read", "no_op")
RISKS = ("low", "medium", "high")
EVIDENCE_KINDS = ("doc", "code", "run", "screenshot", "other")
EVIDENCE_STATES = ("verified", "unverified", "outdated")


class PackError(ValueError):
    """Everything wrong with a pack, one line per problem, each naming the file and field."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


@dataclass
class Pack:
    id: str
    title: str
    version: str
    phase: str  # the phase name it joins, or the track id
    root: Path
    modules: list[Module] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)  # lesson ids not shown: slots, and drafts when not previewing
    assets: dict[str, str] = field(default_factory=dict)  # asset path in the pack -> file on disk


def pack_dirs(env: str | None = None) -> list[Path]:
    """The pack folders named in ``DRILL_CONTENT_PACKS`` (``:``-separated) that exist.

    A relative path counts from the project root. A folder that is not there is skipped with
    one log line, so an ``app.yaml`` can name a pack by default without every checkout carrying it.
    """
    value = os.getenv("DRILL_CONTENT_PACKS", "") if env is None else env
    dirs: list[Path] = []
    for p in value.split(os.pathsep):
        if not p.strip():
            continue
        path = Path(p.strip()).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.is_dir():
            log.info("content pack folder %s is not there; skipping it", path)
            continue
        dirs.append(path)
    return dirs


def show_drafts() -> bool:
    return os.getenv("DRILL_SHOW_DRAFTS", "").strip() == "1"


# -- reading -------------------------------------------------------------------------

def _read(path: Path, problems: list[str]) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{path}: file not found")
        return {}
    except yaml.YAMLError as exc:
        problems.append(f"{path}: not valid YAML ({str(exc).splitlines()[0]})")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{path}: expected a mapping at the top, got {type(data).__name__}")
        return {}
    return json.loads(json.dumps(data, default=str))  # dates (reviewed: 2026-01-01) stay text


def _todo_paths(value: Any, path: str = "") -> list[str]:
    if isinstance(value, str):
        return [path or "(top)"] if TODO.search(value) else []
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in _todo_paths(v, f"{path}.{k}" if path else str(k))]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in _todo_paths(v, f"{path}[{i}]")]
    return []


def load_pack(root: Path, drafts: bool | None = None, taken: set[str] | None = None) -> Pack:
    """Read and check one pack. Raises :class:`PackError` listing every problem found."""
    drafts = show_drafts() if drafts is None else drafts
    root = Path(root)
    problems: list[str] = []
    manifest = _read(root / "pack.yaml", problems)
    if not manifest:
        raise PackError(problems or [f"{root / 'pack.yaml'}: empty"])
    where = root / "pack.yaml"
    for key in ("id", "title", "version", "journeys"):
        if key not in manifest:
            problems.append(f"{where}: missing '{key}'")
    from drill.content import modules as core

    # A pack joins one phase of the path (phase: Ship) or one track beside it (track: platform).
    phases = [name for name, _, _ in core.LIFECYCLE]
    tracks = [tid for tid, _, _, _ in core.TRACKS]
    if ("phase" in manifest) == ("track" in manifest):
        problems.append(f"{where}: give either 'phase' (one of {phases}) or 'track' (one of {tracks})")
    elif "phase" in manifest and manifest["phase"] not in phases:
        problems.append(f"{where}: phase '{manifest['phase']}' is not one of {phases}")
    elif "track" in manifest and manifest["track"] not in tracks:
        problems.append(f"{where}: track '{manifest['track']}' is not one of {tracks}")
    pack = Pack(str(manifest.get("id", "")), str(manifest.get("title", "")), str(manifest.get("version", "")),
                str(manifest.get("phase") or manifest.get("track") or ""), root)

    seen: dict[str, str] = {}
    taken = set(taken or ())
    module_ids = set(core.ORDER)
    lessons_read: list[tuple[dict, dict, Path]] = []
    for j, journey in enumerate(manifest.get("journeys") or []):
        jwhere = f"{where}: journeys[{j}]"
        for key in ("id", "title", "blurb", "lessons"):
            if key not in journey:
                problems.append(f"{jwhere}: missing '{key}'")
        jid = str(journey.get("id", ""))
        if jid in module_ids:
            problems.append(f"{jwhere}: id '{jid}' is already a module")
        module_ids.add(jid)
        for rel in journey.get("lessons") or []:
            path = root / rel
            data = _read(path, problems)
            if data:
                lessons_read.append((journey, data, path))
                lid = data.get("id")
                if lid in seen:
                    problems.append(f"{path}: id '{lid}' is already used by {seen[lid]}")
                elif lid in taken:
                    problems.append(f"{path}: id '{lid}' is already a lesson in the curriculum or another pack")
                seen[str(lid)] = str(path)

    for _, data, path in lessons_read:
        problems += check_lesson(data, path, root, set(seen))
    if problems:
        raise PackError(problems)

    by_journey: dict[str, Module] = {}
    for journey, data, path in lessons_read:
        status = data["status"]
        if status == "slot" or (status == "draft" and not drafts):
            pack.hidden.append(data["id"])
            continue
        jid = journey["id"]
        if jid not in by_journey:
            by_journey[jid] = Module(id=jid, title=journey["title"], blurb=journey["blurb"])
        by_journey[jid].lessons.append(to_lesson(data, pack))
        for asset in _asset_refs(data):
            pack.assets[asset] = str((root / asset).resolve())
    pack.modules = [by_journey[j["id"]] for j in manifest["journeys"] if j["id"] in by_journey]
    return pack


def load_packs(dirs: list[Path] | None = None, taken: set[str] | None = None, drafts: bool | None = None) -> list[Pack]:
    """Every pack in ``dirs`` (default: ``DRILL_CONTENT_PACKS``). An empty list when none is set."""
    packs, taken = [], set(taken or ())
    for root in (pack_dirs() if dirs is None else dirs):
        pack = load_pack(root, drafts=drafts, taken=taken)
        taken |= {lesson["id"] for m in pack.modules for lesson in m.lessons} | set(pack.hidden)
        packs.append(pack)
    return packs


def _core_ids() -> set[str]:
    global _CORE
    if _CORE is None:
        from drill.content import modules as core

        _CORE = {lesson["id"] for m in core.load() for lesson in m.lessons}
    return _CORE


_CORE: set[str] | None = None


# -- checking --------------------------------------------------------------------------

def _need(d: dict, keys: tuple, where: str, problems: list[str]) -> None:
    for key in keys:
        if d.get(key) in (None, "", [], {}):
            problems.append(f"{where}: missing '{key}'")


def _asset_refs(lesson: dict) -> list[str]:
    """Every pack file a lesson shows: screenshots, its diagram, and each guided tour's image."""
    learn = lesson.get("learn") or {}
    refs = [s.get("file") for s in learn.get("screenshots") or [] if isinstance(s, dict)]
    if learn.get("diagram"):
        refs.append(learn["diagram"])
    shown = list(learn.get("views") or []) + list((lesson.get("practice") or {}).get("artifacts") or [])
    refs += [v.get("image") for v in shown if isinstance(v, dict) and v.get("kind") == "tour"]
    return [r for r in refs if r]


def check_lesson(data: dict, path: Path, root: Path, ids: set[str]) -> list[str]:
    """Problems with one lesson file. A slot only needs its id, title and what it will cover."""
    problems: list[str] = []
    w = str(path)
    lid, status = data.get("id"), data.get("status")
    if not isinstance(lid, str) or not ID.match(lid):
        problems.append(f"{w}: id '{lid}' must be lowercase letters, digits and underscores (3 to 63), starting with a letter")
    if status not in STATUSES:
        problems.append(f"{w}: status '{status}' must be one of {STATUSES}")
        return problems
    _need(data, ("title", "summary"), w, problems)
    if status == "slot":
        return problems

    _need(data, ("objective", "difficulty", "learn", "check", "practice", "explain"), w, problems)
    if data.get("difficulty") and data["difficulty"] not in DIFFICULTIES:
        problems.append(f"{w}: difficulty '{data['difficulty']}' must be one of {DIFFICULTIES}")
    for pre in data.get("prerequisites") or []:
        if pre not in ids:
            if pre not in _core_ids():
                problems.append(f"{w}: prerequisite '{pre}' is not a lesson in this pack or the curriculum")
    for alias in data.get("aliases") or []:
        if not isinstance(alias, str) or not ID.match(alias):
            problems.append(f"{w}: alias '{alias}' is not a valid id")

    evidence = {e.get("id"): e for e in data.get("evidence") or [] if isinstance(e, dict)}
    for i, e in enumerate(data.get("evidence") or []):
        ew = f"{w}: evidence[{i}]"
        _need(e, ("id", "kind", "title", "ref", "status"), ew, problems)
        if e.get("kind") and e["kind"] not in EVIDENCE_KINDS:
            problems.append(f"{ew}: kind '{e['kind']}' must be one of {EVIDENCE_KINDS}")
        if e.get("status") and e["status"] not in EVIDENCE_STATES:
            problems.append(f"{ew}: status '{e['status']}' must be one of {EVIDENCE_STATES}")
        if e.get("status") == "verified" and not e.get("reviewed"):
            problems.append(f"{ew}: verified evidence needs 'reviewed' (the date someone checked it)")

    learn = data.get("learn") or {}
    if learn:
        _need(learn, ("text",), f"{w}: learn", problems)
        for i, ex in enumerate(learn.get("examples") or []):
            _need(ex, ("caption", "code"), f"{w}: learn.examples[{i}]", problems)
        for i, v in enumerate(learn.get("views") or []):
            problems += check_view(v, f"{w}: learn.views[{i}]")
        for ref in _asset_refs(data):
            # Confined to the pack folder: the server serves and the static build inlines
            # whatever a lesson names. resolve() also catches a symlink that leads outside.
            full = (root / ref).resolve()
            if not full.is_relative_to(root.resolve()):
                problems.append(f"{w}: '{ref}' points outside the pack folder; keep files under assets/")
            elif not full.is_file():
                problems.append(f"{w}: learn refers to '{ref}', which is not in the pack")
        for ref in learn.get("sources") or []:
            if ref not in evidence:
                problems.append(f"{w}: learn.sources names '{ref}', which is not in evidence")

    check = data.get("check") or {}
    if check:
        _need(check, ("question", "options", "why"), f"{w}: check", problems)
        opts = check.get("options") or []
        if not isinstance(check.get("answer"), int) or not 0 <= check["answer"] < len(opts):
            problems.append(f"{w}: check.answer must be the index of one of the {len(opts)} options (from 0)")

    if data.get("practice"):
        problems += check_practice(data["practice"], f"{w}: practice")

    explain = data.get("explain") or {}
    if explain:
        _need(explain, ("reasoning", "say"), f"{w}: explain", problems)
        for ref in explain.get("evidence") or []:
            if ref not in evidence:
                problems.append(f"{w}: explain.evidence names '{ref}', which is not in evidence")

    if status == "ready":
        for p in _todo_paths(data):
            problems.append(f"{w}: {p} still has a _TODO placeholder; a ready lesson must be complete")
    return problems


def check_view(v: dict, where: str) -> list[str]:
    """An investigation view: what each kind needs."""
    problems: list[str] = []
    kind = v.get("kind")
    if kind not in VIEW_KINDS:
        return [f"{where}: kind '{kind}' must be one of {VIEW_KINDS}"]
    if kind == "relationships":
        _need(v, ("links",), where, problems)
        for i, link in enumerate(v.get("links") or []):
            _need(link, ("from", "ref", "to"), f"{where}.links[{i}]", problems)
    elif kind == "trace":
        _need(v, ("field", "layers"), where, problems)
        for i, layer in enumerate(v.get("layers") or []):
            _need(layer, ("layer", "value", "state"), f"{where}.layers[{i}]", problems)
            if layer.get("state") and layer["state"] not in TRACE_STATES:
                problems.append(f"{where}.layers[{i}]: state '{layer['state']}' must be one of {TRACE_STATES}")
    elif kind == "walkthrough":
        _need(v, ("symptom", "steps", "root_cause", "resolution"), where, problems)
        for i, step in enumerate(v.get("steps") or []):
            _need(step, ("look", "found"), f"{where}.steps[{i}]", problems)
    elif kind == "tour":
        _need(v, ("image", "stops"), where, problems)
        for i, stop in enumerate(v.get("stops") or []):
            sw = f"{where}.stops[{i}]"
            _need(stop, ("title", "text"), sw, problems)
            for key in ("x", "y", "w", "h"):
                value = stop.get(key)
                if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                    problems.append(f"{sw}: {key} must be a number from 0 to 100 (a percentage of the image)")
    elif kind == "plan_review":
        _need(v, ("changes",), where, problems)
        for i, c in enumerate(v.get("changes") or []):
            _need(c, ("action", "address", "risk"), f"{where}.changes[{i}]", problems)
            if c.get("action") and c["action"] not in PLAN_ACTIONS:
                problems.append(f"{where}.changes[{i}]: action '{c['action']}' must be one of {PLAN_ACTIONS}")
            if c.get("risk") and c["risk"] not in RISKS:
                problems.append(f"{where}.changes[{i}]: risk '{c['risk']}' must be one of {RISKS}")
    return problems


def check_practice(p: dict, where: str) -> list[str]:
    """The exercise contract: every kind needs a prompt and a why; then its own fields."""
    problems: list[str] = []
    kind = p.get("kind")
    if kind not in PRACTICE_KINDS:
        return [f"{where}: kind '{kind}' must be one of {sorted(PRACTICE_KINDS)}"]
    _need(p, ("prompt",), where, problems)
    shape = PRACTICE_KINDS[kind]
    for i, a in enumerate(p.get("artifacts") or []):
        aw = f"{where}.artifacts[{i}]"
        _need(a, ("label", "kind"), aw, problems)
        if a.get("kind") not in ARTIFACT_KINDS + VIEW_KINDS:
            problems.append(f"{aw}: kind '{a.get('kind')}' must be one of {ARTIFACT_KINDS + VIEW_KINDS}")
        elif a["kind"] == "diff":
            _need(a, ("before", "after"), aw, problems)
        elif a["kind"] in VIEW_KINDS:
            problems += check_view(a, aw)
        else:
            _need(a, ("content",), aw, problems)
    if shape == "choice":
        if kind == "review_decision" and not p.get("options"):
            p["options"] = ["Approve", "Request changes", "Escalate"]
        _need(p, ("options", "why"), where, problems)
        opts = p.get("options") or []
        if not isinstance(p.get("answer"), int) or not 0 <= p["answer"] < len(opts):
            problems.append(f"{where}: answer must be the index of one of the {len(opts)} options (from 0)")
        if kind in ("troubleshooting", "review_decision"):
            _need(p, ("next_check",), where, problems)
        if kind == "difference_review" and not any((a or {}).get("kind") == "diff" for a in p.get("artifacts") or []):
            problems.append(f"{where}: a difference review needs a 'diff' artifact (before and after)")
    elif shape == "ordering":
        _need(p, ("steps", "why"), where, problems)
        if len(p.get("steps") or []) < 3:
            problems.append(f"{where}: ordering needs at least 3 steps, listed in the right order")
    elif shape == "match":
        _need(p, ("pairs", "why"), where, problems)
        for i, pair in enumerate(p.get("pairs") or []):
            _need(pair, ("from", "to"), f"{where}.pairs[{i}]", problems)
    elif shape == "repair":
        _need(p, ("broken", "fixed", "rules"), where, problems)
        for i, rule in enumerate(p.get("rules") or []):
            if sum(k in rule for k in ("must_contain", "must_not_contain")) != 1:
                problems.append(f"{where}.rules[{i}]: give exactly one of must_contain or must_not_contain")
            _need(rule, ("why",), f"{where}.rules[{i}]", problems)
        fixed = str(p.get("fixed", ""))
        for i, rule in enumerate(p.get("rules") or []):
            if "must_contain" in rule and rule["must_contain"] not in fixed:
                problems.append(f"{where}.rules[{i}]: the fixed version does not contain '{rule['must_contain']}'")
            if "must_not_contain" in rule and rule["must_not_contain"] in fixed:
                problems.append(f"{where}.rules[{i}]: the fixed version still contains '{rule['must_not_contain']}'")
    elif shape == "reasoning":
        _need(p, ("questions",), where, problems)
        for i, q in enumerate(p.get("questions") or []):
            _need(q, ("ask", "expected", "why"), f"{where}.questions[{i}]", problems)
    return problems


# -- turning a pack lesson into the curriculum's shape ------------------------------------

def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def to_lesson(data: dict, pack: Pack) -> dict:
    """A pack lesson as a curriculum lesson dict, plus the fields only pack lessons have."""
    learn, check, explain = data["learn"], data["check"], data["explain"]
    examples = learn.get("examples") or []
    first = examples[0] if examples else {"caption": "", "code": ""}
    return {
        "id": data["id"], "title": data["title"], "learn": list(learn["text"]),
        "example": {"caption": first["caption"], "code": first["code"]},
        "check": {"question": check["question"], "options": list(check["options"]), "answer": check["answer"], "why": check["why"]},
        "angle": {"pattern": explain.get("pattern") or data["title"], "text": explain["reasoning"],
                  "say": explain["say"], "classic": None},
        "stack": None, "exercise": None,
        "pack": {
            "pack": pack.id, "version": pack.version, "status": data["status"], "summary": data["summary"],
            "objective": data["objective"], "difficulty": data["difficulty"],
            "prerequisites": list(data.get("prerequisites") or []), "aliases": list(data.get("aliases") or []),
            "concepts": list(learn.get("concepts") or []), "examples": examples[1:],
            "views": list(learn.get("views") or []), "diagram": learn.get("diagram"),
            "screenshots": list(learn.get("screenshots") or []), "sources": list(learn.get("sources") or []),
            "practice": data["practice"], "mistakes": list(explain.get("mistakes") or []),
            "steps": list(explain.get("steps") or []), "explain_evidence": list(explain.get("evidence") or []),
            "evidence": list(data.get("evidence") or []),
        },
    }


def asset_slots(extra: dict) -> list[tuple[dict, str]]:
    """Every place a built pack lesson names a file, as (holder, key), so it can be repointed."""
    slots = [(extra, "diagram")] if extra.get("diagram") else []
    slots += [(shot, "file") for shot in extra.get("screenshots") or []]
    shown = list(extra.get("views") or []) + list((extra.get("practice") or {}).get("artifacts") or [])
    slots += [(v, "image") for v in shown if isinstance(v, dict) and v.get("kind") == "tour" and v.get("image")]
    return slots


def inline_assets(data: dict, packs: list[Pack]) -> None:
    """Swap each asset path in the built data for the file itself (a data: URL), for a static page."""
    files = {k: v for p in packs for k, v in p.assets.items()}
    for lesson in data["lessons"].values():
        for holder, key in asset_slots(lesson.get("pack") or {}):
            if holder[key] in files:
                holder[key] = _data_uri(Path(files[holder[key]]))


def report(dirs: list[Path]) -> list[str]:
    """Plain lines for ``drill content check``: per pack, what is ready, draft and still a slot."""
    lines = []
    for root in dirs:
        pack = load_pack(root, drafts=True)
        counts = {"ready": 0, "draft": 0}
        for m in pack.modules:
            for lesson in m.lessons:
                counts[lesson["pack"]["status"]] += 1
        lines.append(f"{pack.id} {pack.version} ({root}): {counts['ready']} ready, {counts['draft']} draft, "
                     f"{len(pack.hidden)} slots; joins {pack.phase}")
    return lines
