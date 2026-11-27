"""Apply verified plugin-scoped proposals and open PRs from the central repository.

Standard library only. No contributor Python, dependency installation or shell
interpolation is used. Remote writes are allowed only in GitHub Actions.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

CATALOGS = {
    "claude": ".claude-plugin/marketplace.json",
    "codex": ".agents/plugins/marketplace.json",
}
RESERVED = {"openstudio-si", "openstudio-si-hvac"}


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def child(root, name):
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or path.as_posix() != name
        or "\\" in name
        or any(part in {"..", ".git"} for part in path.parts)
    ):
        raise ValueError("Unsafe proposal path.")
    target = Path(root)
    for part in path.parts:
        target /= part
        if target.is_symlink():
            raise ValueError("Symlink in proposal/marketplace path.")
    return target


def verify(root, bundle):
    root, bundle = Path(root), Path(bundle)
    plan = read(bundle / "plan.json")
    required = {
        "format",
        "id",
        "version",
        "base_sha",
        "record_sha256",
        "paths",
        "branch",
        "validation",
        "native_hosts_verified",
        "files",
        "executables",
    }
    if (
        set(plan) != required
        or plan["format"] != "openstudio-si-import-plan/0.1"
        or plan["native_hosts_verified"] is not True
    ):
        raise ValueError(
            "Proposal needs the verified plan format and native host checks."
        )
    identity, version = plan["id"], plan["version"]
    if (
        not isinstance(identity, str)
        or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", identity)
        or identity in RESERVED
    ):
        raise ValueError("Invalid or reserved plugin identity.")
    if (
        not isinstance(version, str)
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]+)?", version)
        or plan["branch"] != f"automated/plugin/{identity}-v{version}"
        or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", plan["base_sha"])
    ):
        raise ValueError("Invalid proposal version, branch or base SHA.")
    receipt_path = ".openstudio-si/releases/" + identity + ".json"
    allowed = [identity, "plugins/" + identity, *CATALOGS.values(), receipt_path]
    if (
        plan["paths"] != allowed
        or not isinstance(plan["files"], dict)
        or not isinstance(plan["executables"], list)
        or not set(plan["executables"]).issubset(plan["files"])
    ):
        raise ValueError(
            "Proposal may change only its plugin, host catalogs and receipt."
        )
    overlay = bundle / "overlay"
    observed = {}
    for file in overlay.rglob("*"):
        name = file.relative_to(overlay).as_posix()
        child(overlay, name)
        if file.is_file():
            if not any(
                name == prefix or name.startswith(prefix + "/") for prefix in allowed
            ):
                raise ValueError("Unexpected proposal file.")
            observed[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    if observed != plan["files"]:
        raise ValueError("Proposal artifact file hashes do not match its plan.")
    registry = read(child(root, ".openstudio-si/registry.json"))["plugins"]
    registration = registry[identity]
    receipt = read(child(overlay, receipt_path))
    record = receipt["record"]
    if (
        receipt["format"] != "openstudio-si-marketplace-release/0.1"
        or receipt["record_sha256"] != plan["record_sha256"]
        or digest(record) != plan["record_sha256"]
        or record["id"] != identity
        or record["version"] != version
        or record["repository"].lower() != registration["repository"].lower()
    ):
        raise ValueError("Proposal release receipt or registration does not match.")
    for host, location in CATALOGS.items():
        before, after = read(child(root, location)), read(child(overlay, location))
        old_entries, new_entries = before.pop("plugins"), after.pop("plugins")
        if before != after or [
            entry for entry in old_entries if entry["name"] != identity
        ] != [entry for entry in new_entries if entry["name"] != identity]:
            raise ValueError("Proposal would change unrelated catalog data.")
        entries = [entry for entry in new_entries if entry["name"] == identity]
        expected_source = (
            "./" + identity
            if host == "claude"
            else {"source": "local", "path": "./plugins/" + identity}
        )
        if (
            len(entries) != 1
            or entries[0]["source"] != expected_source
            or (host == "claude" and entries[0]["version"] != version)
        ):
            raise ValueError("Proposal catalog entry is invalid.")
        package = child(
            overlay, identity if host == "claude" else "plugins/" + identity
        )
        descriptor = package / "openstudio-si-export.json"
        data = read(descriptor)
        manifest = data["manifest"]
        if (
            hashlib.sha256(descriptor.read_bytes()).hexdigest()
            != record["packages"][host]["descriptor_sha256"]
            or manifest["id"] != identity
            or manifest["version"] != version
            or manifest["owner"]["id"] != registration["owner"]
        ):
            raise ValueError("Proposal package does not match its release or owner.")
        hashes = {
            file.relative_to(package)
            .as_posix(): hashlib.sha256(file.read_bytes())
            .hexdigest()
            for file in package.rglob("*")
            if file.is_file() and file != descriptor
        }
        if hashes != data["files"]:
            raise ValueError("Package content differs from its descriptor.")
    for name in allowed:
        child(root, name)
    return plan


def apply(root, bundle, plan):
    root, bundle = Path(root), Path(bundle)
    for name in plan["paths"]:
        source, target = child(bundle / "overlay", name), child(root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    # GitHub artifacts reset permissions; restore only the verified exec bits.
    for name in plan["files"]:
        child(root, name).chmod(0o755 if name in plan["executables"] else 0o644)


def run(command, root, *, allowed=(0,)):
    result = subprocess.run(
        command, cwd=root, check=False, text=True, capture_output=True
    )
    if result.returncode not in allowed:
        raise ValueError(
            "Trusted git/gh operation failed; inspect the central workflow."
        )
    return result.stdout.strip()


def publish(root, bundle, repository, *, dry_run=False):
    root, bundle = Path(root), Path(bundle)
    if not dry_run and (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_REPOSITORY") != repository
    ):
        raise ValueError(
            "Remote publication is restricted to the central Actions repository; use --dry-run locally."
        )
    if not dry_run:
        if run(["git", "status", "--porcelain"], root):
            raise ValueError("Publication needs a clean trusted checkout.")
        base = run(["git", "rev-parse", "origin/main"], root)
        # Each proposal was checked against main, never a previous candidate's
        # branch. Reset the checkout before verifying the next source's scope.
        run(["git", "switch", "--detach", base], root)
    plan = verify(root, bundle)
    if dry_run:
        return {"id": plan["id"], "status": "verified-dry-run"}
    if base != plan["base_sha"]:
        raise ValueError(
            "Marketplace main advanced; rerun polling against the new base."
        )
    branch = plan["branch"]
    run(["git", "check-ref-format", "refs/heads/" + branch], root)
    previous = run(
        ["git", "ls-remote", "--heads", "origin", "refs/heads/" + branch], root
    )
    previous_sha = previous.split()[0] if previous else ""
    if previous_sha:
        run(["git", "fetch", "--no-tags", "--depth=1", "origin", branch], root)
        existing = json.loads(
            run(
                [
                    "git",
                    "show",
                    "FETCH_HEAD:.openstudio-si/releases/" + plan["id"] + ".json",
                ],
                root,
            )
        )
        if existing["record_sha256"] != plan["record_sha256"]:
            raise ValueError(
                "This release branch already has different content; bump the version."
            )
    run(["git", "switch", "--detach", base], root)
    run(["git", "switch", "-C", branch], root)
    apply(root, bundle, plan)
    run(["git", "add", "--", *plan["paths"]], root)
    if not run(["git", "diff", "--cached", "--name-only"], root):
        return {"id": plan["id"], "status": "unchanged"}
    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            f"Release {plan['id']} v{plan['version']}",
        ],
        root,
    )
    run(
        [
            "git",
            "push",
            f"--force-with-lease=refs/heads/{branch}:{previous_sha}",
            "origin",
            f"HEAD:refs/heads/{branch}",
        ],
        root,
    )
    record = read(bundle / "overlay/.openstudio-si/releases" / (plan["id"] + ".json"))[
        "record"
    ]
    body = bundle / "pr-body.md"
    body.write_text(
        f"Verified release of **{plan['id']} {plan['version']}**.\n\nSource: https://github.com/{record['repository']}/commit/{record['source_sha']}\n\nBoth host packages match the immutable source export and pass native host checks. Full catalog dependencies were checked. No LLM score is a release gate.\n\nRecord fingerprint: `{plan['record_sha256']}`\n"
    )
    existing = json.loads(
        run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--head",
                branch,
                "--base",
                "main",
                "--state",
                "open",
                "--json",
                "number",
            ],
            root,
        )
    )
    title = f"Release {plan['id']} v{plan['version']}"
    if existing:
        run(
            [
                "gh",
                "pr",
                "edit",
                str(existing[0]["number"]),
                "--repo",
                repository,
                "--title",
                title,
                "--body-file",
                str(body),
            ],
            root,
        )
    else:
        run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repository,
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(body),
            ],
            root,
        )
    return {"id": plan["id"], "status": "pull-request"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marketplace", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    results = []
    for plan in sorted(args.candidates.glob("*/plan.json")):
        results.append(
            publish(
                args.marketplace, plan.parent, args.repository, dry_run=args.dry_run
            )
        )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
