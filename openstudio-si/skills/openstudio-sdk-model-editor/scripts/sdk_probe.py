"""Run this skill's entrypoint from the complete OpenStudio SI plugin."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

try:
    library = Path(__file__).resolve().parents[3] / "sdk"
    bundle = json.loads((library / "bundle.json").read_text(encoding="utf-8"))
    files = bundle["files"]
    identity = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if bundle.get("layout_version") != 1 or identity != 'a61b46b236bb99da3c40c7c5f8f1613d86d642502e948f6aa56425857e9f785b' or bundle.get("bundle_id") != identity:
        raise ValueError("SDK library does not match this skill launcher")
    for relative, expected in files.items():
        payload = library / relative
        if payload.is_symlink() or not payload.resolve().is_relative_to(library.resolve()) or hashlib.sha256(payload.read_bytes()).hexdigest() != expected:
            raise ValueError("SDK library file is missing or mismatched: " + relative)
except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
    print(json.dumps({"ok": False, "ready": False, "status": "plugin_incomplete", "error": str(exc)[:400], "next_action": "Restore or reinstall the complete OpenStudio SI core plugin, including sdk/; do not copy a skill alone."}))
    raise SystemExit(2)
sys.path.insert(0, str(library))
runpy.run_path(str(library / 'sdk_probe.py'), run_name="__main__")
