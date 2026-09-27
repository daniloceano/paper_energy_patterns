#!/usr/bin/env python3
"""Audit and safely mirror the canonical Overleaf manuscript into the repository.

The Overleaf project and the GitHub repository have unrelated Git histories.  This
tool deliberately compares file trees and blob hashes instead of merging branches.
It is read-only by default.  Updating the repository copy requires the explicit
``pull --apply`` command and is refused when the manuscript directory has local
changes or files that are absent from Overleaf.

The tool never pushes to Overleaf.  Incorporating repository results into the
canonical manuscript remains a reviewed, manual operation performed from an
Overleaf-based checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = PROJECT_ROOT / "docs" / "energy_patterns_clim_dyn"
STATE_FILE = PROJECT_ROOT / "docs" / "overleaf_sync_state.json"
DEFAULT_REMOTE = "overleaf"
DEFAULT_BRANCH = "main"


class SyncError(RuntimeError):
    """Raised when a synchronization safety condition is not satisfied."""


@dataclass(frozen=True)
class AuditResult:
    checked_at_utc: str
    github_head: str
    overleaf_ref: str
    overleaf_head: str
    common_ancestor: str | None
    identical_files: list[str]
    different_files: list[str]
    missing_locally: list[str]
    extra_locally: list[str]

    @property
    def synchronized(self) -> bool:
        return not (self.different_files or self.missing_locally or self.extra_locally)


def run_git(*args: str, check: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=check,
        capture_output=True,
        text=text,
    )


def fetch_overleaf(remote: str, branch: str) -> None:
    print(f"Fetching {remote}/{branch}...")
    run_git("fetch", remote, branch)


def require_ref(ref: str) -> None:
    probe = run_git("rev-parse", "--verify", ref, check=False)
    if probe.returncode != 0:
        raise SyncError(f"Git ref {ref!r} is unavailable. Fetch the Overleaf remote first.")


def tree_files(ref: str) -> list[str]:
    result = run_git("ls-tree", "-r", "--name-only", "-z", ref, text=False)
    return sorted(item.decode() for item in result.stdout.split(b"\0") if item)


def local_files() -> list[str]:
    if not MANUSCRIPT_DIR.is_dir():
        return []
    return sorted(
        str(item.relative_to(MANUSCRIPT_DIR))
        for item in MANUSCRIPT_DIR.rglob("*")
        if item.is_file()
    )


def remote_blob_hash(ref: str, relative_path: str) -> str:
    return run_git("rev-parse", f"{ref}:{relative_path}").stdout.strip()


def local_blob_hash(relative_path: str) -> str:
    local_path = MANUSCRIPT_DIR / relative_path
    return run_git("hash-object", str(local_path)).stdout.strip()


def sha256_file(local_path: Path) -> str:
    digest = hashlib.sha256()
    with local_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(ref: str) -> AuditResult:
    require_ref(ref)
    remote_paths = set(tree_files(ref))
    repository_paths = set(local_files())

    missing = sorted(remote_paths - repository_paths)
    extra = sorted(repository_paths - remote_paths)
    identical: list[str] = []
    different: list[str] = []

    for relative_path in sorted(remote_paths & repository_paths):
        if remote_blob_hash(ref, relative_path) == local_blob_hash(relative_path):
            identical.append(relative_path)
        else:
            different.append(relative_path)

    merge_base = run_git("merge-base", "HEAD", ref, check=False)
    common_ancestor = merge_base.stdout.strip() if merge_base.returncode == 0 else None

    return AuditResult(
        checked_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        github_head=run_git("rev-parse", "HEAD").stdout.strip(),
        overleaf_ref=ref,
        overleaf_head=run_git("rev-parse", ref).stdout.strip(),
        common_ancestor=common_ancestor,
        identical_files=identical,
        different_files=different,
        missing_locally=missing,
        extra_locally=extra,
    )


def print_audit(result: AuditResult) -> None:
    print("\nOverleaf manuscript audit")
    print(f"  GitHub HEAD:       {result.github_head}")
    print(f"  Overleaf ref:      {result.overleaf_ref}")
    print(f"  Overleaf HEAD:     {result.overleaf_head}")
    print(f"  Common ancestor:   {result.common_ancestor or 'none (independent histories)'}")
    print(f"  Identical files:   {len(result.identical_files)}")
    print(f"  Different files:   {len(result.different_files)}")
    print(f"  Missing locally:   {len(result.missing_locally)}")
    print(f"  Extra locally:     {len(result.extra_locally)}")
    print(f"  Status:            {'SYNCHRONIZED' if result.synchronized else 'DIVERGED'}")

    for label, paths in (
        ("Different", result.different_files),
        ("Missing locally", result.missing_locally),
        ("Extra locally", result.extra_locally),
    ):
        if paths:
            print(f"\n{label}:")
            for relative_path in paths:
                print(f"  - {relative_path}")


def manuscript_is_dirty() -> bool:
    status = run_git(
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        str(MANUSCRIPT_DIR.relative_to(PROJECT_ROOT)),
    )
    return bool(status.stdout.strip())


def copy_blob_atomically(ref: str, relative_path: str) -> None:
    destination = MANUSCRIPT_DIR / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    blob = run_git("show", f"{ref}:{relative_path}", text=False).stdout

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".overleaf-sync",
        dir=destination.parent,
    )
    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(blob)
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def apply_pull(ref: str, before: AuditResult) -> AuditResult:
    if manuscript_is_dirty():
        raise SyncError(
            "The manuscript directory has uncommitted or untracked changes; refusing to overwrite it."
        )
    if before.extra_locally:
        raise SyncError(
            "The repository manuscript contains files absent from Overleaf; review them manually before pulling."
        )

    update_paths = sorted(set(before.different_files + before.missing_locally))
    if not update_paths:
        print("No manuscript files need to be updated.")
        return before

    print("Applying canonical Overleaf files:")
    for relative_path in update_paths:
        print(f"  - {relative_path}")
        copy_blob_atomically(ref, relative_path)

    after = audit(ref)
    if not after.synchronized:
        raise SyncError("Post-pull verification failed; the manuscript trees still differ.")
    return after


def write_state(result: AuditResult) -> None:
    if not result.synchronized:
        raise SyncError("A synchronization state can only be recorded for identical trees.")

    payload = asdict(result)
    payload["synchronized"] = True
    payload["files"] = {
        relative_path: sha256_file(MANUSCRIPT_DIR / relative_path)
        for relative_path in result.identical_files
    }
    temporary_state = STATE_FILE.with_suffix(".json.tmp")
    temporary_state.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary_state, STATE_FILE)
    print(f"Recorded synchronized state in {STATE_FILE.relative_to(PROJECT_ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="Overleaf Git remote name")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Overleaf branch name")
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Audit the existing remote-tracking ref without fetching first",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit", help="Compare without modifying files")
    audit_parser.add_argument(
        "--write-state",
        action="store_true",
        help="Record the verified commit and hashes when both trees are identical",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help="Mirror canonical Overleaf files into the repository manuscript directory",
    )
    pull_parser.add_argument(
        "--apply",
        action="store_true",
        required=True,
        help="Required acknowledgement that manuscript files may be updated",
    )
    pull_parser.add_argument(
        "--write-state",
        action="store_true",
        help="Record the verified commit and hashes after a successful pull",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ref = f"{args.remote}/{args.branch}"

    try:
        if not args.no_fetch:
            fetch_overleaf(args.remote, args.branch)

        result = audit(ref)
        print_audit(result)

        if args.command == "pull":
            result = apply_pull(ref, result)
            print_audit(result)

        if args.write_state:
            write_state(result)
        return 0 if result.synchronized else 1
    except (SyncError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
