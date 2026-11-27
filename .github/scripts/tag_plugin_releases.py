"""Create immutable plugin-scoped tags after successful main-branch validation."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def run(command, root):
    result = subprocess.run(
        command, cwd=root, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise ValueError(
            "Tag verification or push failed; tags are never force-updated."
        )
    return result.stdout.strip()


def releases(root):
    root = Path(root)
    catalogs = [
        json.loads((root / path).read_text())
        for path in [
            ".claude-plugin/marketplace.json",
            ".agents/plugins/marketplace.json",
        ]
    ]
    identities = [
        {entry["name"] for entry in catalog["plugins"]} for catalog in catalogs
    ]
    if identities[0] != identities[1]:
        raise ValueError("Host catalog identities differ.")
    result = {}
    for identity in sorted(identities[0]):
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", identity):
            raise ValueError("Invalid plugin identity.")
        paths = [
            root / identity / ".claude-plugin/plugin.json",
            root / "plugins" / identity / ".codex-plugin/plugin.json",
        ]
        records = [json.loads(path.read_text()) for path in paths]
        if (
            any(record["name"] != identity for record in records)
            or records[0]["version"] != records[1]["version"]
        ):
            raise ValueError("Host package identities or versions differ.")
        version = records[0]["version"]
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]+)?", version):
            raise ValueError("Invalid plugin release version.")
        result[identity] = version
    return result


def verify_existing(root, identity, old_sha, target_sha):
    for path in [identity, "plugins/" + identity]:
        previous = run(["git", "rev-parse", old_sha + ":" + path], root)
        current = run(["git", "rev-parse", target_sha + ":" + path], root)
        if previous != current:
            raise ValueError(
                "A plugin release tag already identifies different content; bump its version."
            )


def tag(root, target_sha, *, dry_run=False):
    root = Path(root)
    if not dry_run and os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Use --dry-run outside the validated Actions workflow.")
    if (
        not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", target_sha)
        or run(["git", "rev-parse", "HEAD"], root) != target_sha
    ):
        raise ValueError("Tag target must be the exact validated checkout commit.")
    results = []
    for identity, version in releases(root).items():
        name = identity + "--v" + version
        run(["git", "check-ref-format", "refs/tags/" + name], root)
        existing = run(
            [
                "git",
                "ls-remote",
                "--tags",
                "origin",
                "refs/tags/" + name,
                "refs/tags/" + name + "^{}",
            ],
            root,
        )
        if existing:
            run(
                [
                    "git",
                    "fetch",
                    "--no-tags",
                    "--depth=1",
                    "origin",
                    "refs/tags/" + name,
                ],
                root,
            )
            old_sha = run(["git", "rev-parse", "FETCH_HEAD^{commit}"], root)
            verify_existing(root, identity, old_sha, target_sha)
            status = "unchanged"
        elif dry_run:
            status = "would-create"
        else:
            run(["git", "tag", name, target_sha], root)
            run(["git", "push", "origin", "refs/tags/" + name], root)
            status = "created"
        results.append({"tag": name, "status": status})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marketplace", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            tag(args.marketplace, args.source_sha, dry_run=args.dry_run), indent=2
        )
    )


if __name__ == "__main__":
    main()
