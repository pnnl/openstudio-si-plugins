"""Trusted writer/tag helpers are checked without GitHub tokens or remote writes."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import publish_candidates as writer
import tag_plugin_releases as tags


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixture(folder):
    root, bundle = folder / "market", folder / "candidate"
    identity, version = "demo", "0.1.0"
    write(
        root / ".openstudio-si/registry.json",
        {
            "schema_version": "0.1",
            "plugins": {
                identity: {
                    "repository": "lab/demo",
                    "owner": "lab",
                    "plugin_path": "plugin",
                }
            },
        },
    )
    record = {
        "id": identity,
        "version": version,
        "repository": "lab/demo",
        "source_sha": "a" * 40,
        "packages": {},
    }
    for host, location in writer.CATALOGS.items():
        original = {"name": "test", "plugins": [{"name": "neighbor", "source": "keep"}]}
        write(root / location, original)
        package = (
            bundle
            / "overlay"
            / (identity if host == "claude" else "plugins/" + identity)
        )
        resource = package / "bin/read-model"
        resource.parent.mkdir(parents=True)
        resource.write_text("read-only fixture")
        descriptor = {
            "manifest": {"id": identity, "version": version, "owner": {"id": "lab"}},
            "files": {
                "bin/read-model": hashlib.sha256(resource.read_bytes()).hexdigest()
            },
        }
        write(package / "openstudio-si-export.json", descriptor)
        record["packages"][host] = {
            "descriptor_sha256": hashlib.sha256(
                (package / "openstudio-si-export.json").read_bytes()
            ).hexdigest()
        }
        entry = {
            "name": identity,
            "source": (
                "./demo"
                if host == "claude"
                else {"source": "local", "path": "./plugins/demo"}
            ),
        }
        if host == "claude":
            entry["version"] = version
        write(
            bundle / "overlay" / location,
            {"name": "test", "plugins": [*original["plugins"], entry]},
        )
    fingerprint = writer.digest(record)
    write(
        bundle / "overlay/.openstudio-si/releases/demo.json",
        {
            "format": "openstudio-si-marketplace-release/0.1",
            "record_sha256": fingerprint,
            "record": record,
        },
    )
    plan = {
        "format": "openstudio-si-import-plan/0.1",
        "id": identity,
        "version": version,
        "base_sha": "b" * 40,
        "record_sha256": fingerprint,
        "paths": [
            identity,
            "plugins/" + identity,
            *writer.CATALOGS.values(),
            ".openstudio-si/releases/demo.json",
        ],
        "branch": "automated/plugin/demo-v0.1.0",
        "validation": {},
        "native_hosts_verified": True,
        "files": {},
        "executables": ["demo/bin/read-model", "plugins/demo/bin/read-model"],
    }
    write(bundle / "plan.json", plan)
    refresh(bundle)
    return root, bundle


def refresh(bundle):
    plan = writer.read(bundle / "plan.json")
    plan["files"] = {
        file.relative_to(bundle / "overlay")
        .as_posix(): hashlib.sha256(file.read_bytes())
        .hexdigest()
        for file in (bundle / "overlay").rglob("*")
        if file.is_file()
    }
    write(bundle / "plan.json", plan)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root, self.bundle = fixture(Path(self.temporary.name))

    def test_dry_run_never_mutates_the_marketplace(self):
        before = {
            file.relative_to(self.root).as_posix(): file.read_bytes()
            for file in self.root.rglob("*")
            if file.is_file()
        }
        result = writer.publish(
            self.root, self.bundle, "pnnl/openstudio-si-plugins", dry_run=True
        )
        self.assertEqual(result["status"], "verified-dry-run")
        self.assertEqual(
            before,
            {
                file.relative_to(self.root).as_posix(): file.read_bytes()
                for file in self.root.rglob("*")
                if file.is_file()
            },
        )

    def test_writer_restores_exec_bits_and_preserves_neighbors(self):
        plan = writer.verify(self.root, self.bundle)
        writer.apply(self.root, self.bundle, plan)
        self.assertTrue((self.root / "demo/bin/read-model").stat().st_mode & 0o111)
        self.assertEqual(
            writer.read(self.root / ".claude-plugin/marketplace.json")["plugins"][0],
            {"name": "neighbor", "source": "keep"},
        )

    def test_payload_tampering_is_rejected(self):
        (self.bundle / "overlay/demo/bin/read-model").write_text("changed")
        with self.assertRaisesRegex(ValueError, "hash"):
            writer.verify(self.root, self.bundle)

    def test_missing_native_validation_is_rejected(self):
        plan = writer.read(self.bundle / "plan.json")
        plan["native_hosts_verified"] = False
        write(self.bundle / "plan.json", plan)
        with self.assertRaises(ValueError):
            writer.verify(self.root, self.bundle)

    def test_even_rehashed_artifact_cannot_remove_a_neighbor(self):
        catalog = self.bundle / "overlay/.claude-plugin/marketplace.json"
        data = writer.read(catalog)
        data["plugins"].pop(0)
        write(catalog, data)
        refresh(self.bundle)
        with self.assertRaisesRegex(ValueError, "unrelated"):
            writer.verify(self.root, self.bundle)

    def test_publication_is_forbidden_outside_actions(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaisesRegex(
            ValueError, "Actions"
        ):
            writer.publish(self.root, self.bundle, "pnnl/openstudio-si-plugins")

    def test_main_advancement_prevents_publication(self):
        with patch.dict(
            "os.environ",
            {
                "GITHUB_ACTIONS": "true",
                "GITHUB_REPOSITORY": "pnnl/openstudio-si-plugins",
            },
            clear=True,
        ), patch.object(
            writer, "run", side_effect=["", "c" * 40, ""]
        ), self.assertRaisesRegex(
            ValueError, "advanced"
        ):
            writer.publish(self.root, self.bundle, "pnnl/openstudio-si-plugins")

    def test_each_remote_candidate_is_verified_from_main(self):
        calls = []

        def operation(command, root, **kwargs):
            calls.append(command)
            return "b" * 40 if command[1:3] == ["rev-parse", "origin/main"] else ""

        def verify(root, bundle):
            self.assertEqual(calls[-1], ["git", "switch", "--detach", "b" * 40])
            raise ValueError("verified against main")

        with patch.dict(
            "os.environ",
            {
                "GITHUB_ACTIONS": "true",
                "GITHUB_REPOSITORY": "pnnl/openstudio-si-plugins",
            },
            clear=True,
        ), patch.object(writer, "run", side_effect=operation), patch.object(
            writer, "verify", side_effect=verify
        ), self.assertRaisesRegex(
            ValueError, "verified against main"
        ):
            writer.publish(self.root, self.bundle, "pnnl/openstudio-si-plugins")

    def test_paths_cannot_escape_or_target_core(self):
        with self.assertRaises(ValueError):
            writer.child(self.root, "../escape")
        plan = writer.read(self.bundle / "plan.json")
        plan["id"] = "openstudio-si"
        write(self.bundle / "plan.json", plan)
        with self.assertRaisesRegex(ValueError, "reserved"):
            writer.verify(self.root, self.bundle)


class TagTests(unittest.TestCase):
    def test_changed_content_cannot_reuse_an_existing_tag(self):
        with patch.object(
            tags, "run", side_effect=["old-tree", "new-tree"]
        ), self.assertRaisesRegex(ValueError, "different content"):
            tags.verify_existing(Path("."), "demo", "a" * 40, "b" * 40)

    def test_same_content_is_idempotent(self):
        with patch.object(tags, "run", side_effect=["same", "same", "same", "same"]):
            tags.verify_existing(Path("."), "demo", "a" * 40, "b" * 40)

    def test_tag_target_must_equal_validated_head(self):
        with patch.object(tags, "run", return_value="b" * 40), self.assertRaisesRegex(
            ValueError, "exact validated"
        ):
            tags.tag(Path("."), "a" * 40, dry_run=True)


if __name__ == "__main__":
    unittest.main()
