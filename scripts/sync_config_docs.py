#!/usr/bin/env python3
"""Sync each service's ``CONFIG.md`` into ``docs/config/<service>.md``.

The per-service ``CONFIG.md`` files live at the root of each service's own GitHub
repo. They are the source of truth; this script copies them into the
``arkitekt-server`` docs tree so they render on GitHub alongside the rest of the
docs, and (re)builds an index at ``docs/configuration.md``.

Two source modes:

* ``--from-mounts`` (default): read from a local checkout of the deployment, i.e.
  ``<MOUNTS_DIR>/<service>/CONFIG.md`` (``MOUNTS_DIR`` defaults to
  ``~/Code/deployments/next/mounts`` and is overridable via the ``MOUNTS_DIR``
  environment variable or ``--mounts-dir``).
* ``--from-github``: fetch each file from ``raw.githubusercontent.com``. Used by
  the ``sync-config-docs`` GitHub Action so the sync works without a local checkout.

Stdlib only — no third-party dependencies, so the Action needs no ``pip install``.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Single source of truth: which services exist and where their CONFIG.md lives.
# ``service`` is the local mount dir name (also used as the output file stem).
SERVICES = [
    {
        "service": "alpaka",
        "title": "Alpaka",
        "owner": "jhnnsrs",
        "repo": "alpaka-server",
        "branch": "next",
    },
    {
        "service": "dokuments",
        "title": "Dokuments",
        "owner": "jhnnsrs",
        "repo": "dokuments-server",
        "branch": "next",
    },
    {
        "service": "elektro",
        "title": "Elektro",
        "owner": "jhnnsrs",
        "repo": "elektro-server",
        "branch": "next",
    },
    {
        "service": "example",
        "title": "Example",
        "owner": "jhnnsrs",
        "repo": "example-server",
        "branch": "next",
    },
    {
        "service": "fluss",
        "title": "Fluss",
        "owner": "jhnnsrs",
        "repo": "fluss-server-next",
        "branch": "next",
    },
    {
        "service": "kabinet",
        "title": "Kabinet",
        "owner": "arkitektio",
        "repo": "kabinet-server",
        "branch": "next",
    },
    {
        "service": "kraph",
        "title": "Kraph",
        "owner": "jhnnsrs",
        "repo": "kraph-server",
        "branch": "next",
    },
    {
        "service": "lok",
        "title": "Lok",
        "owner": "arkitektio",
        "repo": "lok-server-next",
        "branch": "next",
    },
    {
        "service": "lovekit",
        "title": "Lovekit",
        "owner": "jhnnsrs",
        "repo": "lovekit-server",
        "branch": "next",
    },
    {
        "service": "mikro",
        "title": "Mikro",
        "owner": "arkitektio",
        "repo": "mikro-server-next",
        "branch": "next",
    },
    {
        "service": "omero-ark-server",
        "title": "Omero-Ark",
        "owner": "arkitektio",
        "repo": "omero-ark-server",
        "branch": "next",
    },
    {
        "service": "rekuest",
        "title": "Rekuest",
        "owner": "jhnnsrs",
        "repo": "rekuest-server-next",
        "branch": "next",
    },
]

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
CONFIG_DIR = DOCS_DIR / "config"
INDEX_FILE = DOCS_DIR / "configuration.md"

DEFAULT_MOUNTS_DIR = Path(os.path.expanduser("~/Code/deployments/next/mounts"))

# Matches inline markdown links ``[text](target)`` and image links ``![alt](target)``.
_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")


def github_blob_url(svc: dict, path: str) -> str:
    return (
        f"https://github.com/{svc['owner']}/{svc['repo']}/blob/{svc['branch']}/{path}"
    )


def github_raw_url(svc: dict) -> str:
    return f"https://raw.githubusercontent.com/{svc['owner']}/{svc['repo']}/{svc['branch']}/CONFIG.md"


def is_relative_link(target: str) -> bool:
    """True for repo-relative links that would break once the file is moved."""
    target = target.strip()
    if not target or target.startswith("#"):
        return False  # anchor-only links stay valid
    # Absolute URLs, protocol-relative, mailto, and root-absolute paths are left alone.
    if (
        re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target)
        or target.startswith("//")
        or target.startswith("/")
    ):
        return False
    return True


def rewrite_links(text: str, svc: dict) -> str:
    """Rewrite repo-relative links to absolute GitHub blob URLs."""

    def repl(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        target_stripped = target.strip()
        if not is_relative_link(target_stripped):
            return m.group(0)
        # Preserve any trailing #anchor on the relative path.
        path, _, anchor = target_stripped.partition("#")
        url = github_blob_url(svc, path)
        if anchor:
            url = f"{url}#{anchor}"
        return f"{label}({url})"

    return _LINK_RE.sub(repl, text)


def banner(svc: dict) -> str:
    return (
        f"<!-- AUTO-GENERATED — do not edit. Source: {github_blob_url(svc, 'CONFIG.md')}. "
        f"Run scripts/sync_config_docs.py to update. -->\n\n"
    )


def read_source(svc: dict, from_github: bool, mounts_dir: Path) -> str:
    if from_github:
        url = github_raw_url(svc)
        req = urllib.request.Request(url)
        # Private service repos (e.g. dokuments-server) 404 over anonymous raw.
        # Pass a token via GITHUB_TOKEN / CONFIG_SYNC_TOKEN with cross-repo read access.
        token = os.environ.get("CONFIG_SYNC_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted host)
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            hint = (
                " (private repo? set CONFIG_SYNC_TOKEN)" if e.code in (403, 404) else ""
            )
            raise RuntimeError(
                f"{svc['service']}: HTTP {e.code} fetching {url}{hint}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"{svc['service']}: failed to fetch {url}: {e.reason}"
            ) from e
    src = mounts_dir / svc["service"] / "CONFIG.md"
    if not src.is_file():
        raise RuntimeError(f"{svc['service']}: missing source file {src}")
    return src.read_text(encoding="utf-8")


def build_index() -> str:
    lines = [
        "# Configuration",
        "",
        "Every Arkitekt service is configured the same way: a typed",
        "[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)",
        "schema resolved from environment variables, config files and defaults.",
        "",
        "Each service publishes a full configuration reference (its `CONFIG.md`).",
        "These pages are **auto-synced** from the individual service repositories by",
        "`scripts/sync_config_docs.py` — edit them upstream, not here.",
        "",
        "| Service | Configuration reference | Source repo |",
        "| --- | --- | --- |",
    ]
    for svc in SERVICES:
        repo = f"{svc['owner']}/{svc['repo']}"
        repo_url = f"https://github.com/{repo}"
        lines.append(
            f"| {svc['title']} | [config/{svc['service']}.md](config/{svc['service']}.md) "
            f"| [{repo}]({repo_url}) |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--from-mounts",
        action="store_true",
        help="Read CONFIG.md from a local deployment checkout (default).",
    )
    group.add_argument(
        "--from-github",
        action="store_true",
        help="Fetch CONFIG.md from each service's GitHub repo.",
    )
    parser.add_argument(
        "--mounts-dir",
        type=Path,
        default=Path(os.environ.get("MOUNTS_DIR", DEFAULT_MOUNTS_DIR)),
        help=f"Mounts directory for --from-mounts (default: {DEFAULT_MOUNTS_DIR}).",
    )
    args = parser.parse_args()

    from_github = args.from_github  # --from-mounts is the default when neither is set

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    written = 0
    for svc in SERVICES:
        try:
            raw = read_source(svc, from_github, args.mounts_dir)
        except RuntimeError as e:
            errors.append(str(e))
            continue
        content = banner(svc) + rewrite_links(raw, svc)
        if not content.endswith("\n"):
            content += "\n"
        out = CONFIG_DIR / f"{svc['service']}.md"
        out.write_text(content, encoding="utf-8")
        written += 1
        print(f"  wrote {out.relative_to(REPO_ROOT)}")

    INDEX_FILE.write_text(build_index(), encoding="utf-8")
    print(f"  wrote {INDEX_FILE.relative_to(REPO_ROOT)}")

    print(
        f"\nSynced {written}/{len(SERVICES)} services "
        f"({'github' if from_github else 'mounts'})."
    )

    if errors:
        print("\nERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        raise Exception(errors)

    print("Ran successfully")


if __name__ == "__main__":
    main()
