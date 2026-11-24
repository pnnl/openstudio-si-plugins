"""Check whether the OpenStudio SI runtime can be used by this plugin."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility for exported helpers
    tomllib = None

PLUGIN_VERSION = "0.5.0"
PLUGIN_CONTRACT_VERSION = "6.0"


def command_status(command: str) -> dict[str, object]:
    if sys.prefix != sys.base_prefix:
        scripts_dir = Path(sys.prefix) / ("Scripts" if os.name == "nt" else "bin")
        names = [command, f"{command}.exe"] if os.name == "nt" else [command]
        path = next(
            (str(scripts_dir / name) for name in names if (scripts_dir / name).is_file()),
            None,
        )
    else:
        path = shutil.which(command)
    return {"command": command, "available": path is not None, "path": path}


def nlr_mcp_status() -> dict[str, object]:
    """Report whether the optional NLR MCP server is configured locally."""
    checked_paths = []
    codex_config = Path.home() / ".codex" / "config.toml"
    checked_paths.append(str(codex_config))
    if tomllib is not None and codex_config.is_file():
        try:
            config = tomllib.loads(codex_config.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            config = {}
        servers = config.get("mcp_servers") if isinstance(config, dict) else None
        if isinstance(servers, dict) and "openstudio-mcp" in servers:
            return {"configured": True, "name": "openstudio-mcp", "source": str(codex_config)}

    for directory in (Path.cwd(), *Path.cwd().parents):
        mcp_config = directory / ".mcp.json"
        checked_paths.append(str(mcp_config))
        if not mcp_config.is_file():
            continue
        try:
            config = json.loads(mcp_config.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        servers = config.get("mcpServers") if isinstance(config, dict) else None
        if isinstance(servers, dict) and "openstudio-mcp" in servers:
            return {"configured": True, "name": "openstudio-mcp", "source": str(mcp_config)}

    return {"configured": False, "name": "nlr_openstudio", "checked_paths": checked_paths}


def core_metadata() -> dict[str, object]:
    """Read the colocated host manifest and MCP declaration without starting a service."""
    core = Path(__file__).resolve().parents[3]
    try:
        manifest_path = next(
            core / f".{host}-plugin" / "plugin.json"
            for host in ("claude", "codex")
            if (core / f".{host}-plugin" / "plugin.json").is_file()
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config = json.loads((core / ".mcp.json").read_text(encoding="utf-8"))
        metadata = config["mcpServers"]["openstudio_si"]["env"]
        version = metadata["OPENSTUDIO_SI_PLUGIN_VERSION"]
        contract = metadata["OPENSTUDIO_SI_PLUGIN_CONTRACT_VERSION"]
        if (
            manifest["name"] != "openstudio-si"
            or version != manifest["version"]
            or version != PLUGIN_VERSION
            or contract != PLUGIN_CONTRACT_VERSION
        ):
            raise ValueError("Core plugin manifest, MCP declaration, and doctor disagree.")
    except StopIteration:
        return {"ok": False, "error": "Core host plugin manifest is missing."}
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "plugin_version": version, "plugin_contract_version": contract}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenStudio SI plugin readiness.")
    parser.add_argument("--plugin-dir", type=Path, help="Active HVAC Modeler plugin root.")
    parser.add_argument("--core-metadata", action="store_true", help="Read core plugin metadata from disk.")
    args = parser.parse_args()
    if args.core_metadata:
        payload = core_metadata()
        print(json.dumps(payload, indent=2))
        return 0 if payload["ok"] else 2
    specialist_args = ["--plugin-dir", str(args.plugin_dir)] if args.plugin_dir else []
    reporting_script = Path(__file__).resolve().parents[3] / "skills" / "report-openstudio-failure" / "scripts" / "report_failure.py"
    reporting = {"optional": True, "submission_ready": False, "affects_modeling_readiness": False}
    if reporting_script.is_file():
        try:
            status = subprocess.run([sys.executable, "-I", "-S", str(reporting_script), "doctor"], capture_output=True, text=True, timeout=8)
            if status.returncode == 0:
                reporting = json.loads(status.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    report = {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "openstudio_si_mcp": command_status("openstudio-si-mcp"),
        "openstudio_si": command_status("openstudio-si"),
        "nlr_openstudio": nlr_mcp_status(),
        "failure_reporting": reporting,
        # Optional: install the `standards` extra for building-code lookups.
        "besd_mcp_optional": command_status("besd-mcp"),
    }
    print(json.dumps(report, indent=2))

    if not report["openstudio_si_mcp"]["available"] or not report["openstudio_si"]["available"]:
        print(
            "\nOpenStudio SI runtime commands are not fully available. "
            "Ask the user before running install_runtime.py."
        )
        return 2

    doctor = subprocess.run(
        [
            report["openstudio_si"]["path"],
            "doctor",
            "--json",
            "--plugin-version",
            PLUGIN_VERSION,
            "--plugin-contract-version",
            PLUGIN_CONTRACT_VERSION,
            *specialist_args,
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if doctor.stdout:
        print(doctor.stdout.strip())

    try:
        payload = json.loads(doctor.stdout)
    except json.JSONDecodeError:
        print("\nThe runtime doctor returned an unreadable report. Run `openstudio-si doctor` directly.")
        if doctor.stderr.strip():
            print(doctor.stderr.strip())
        return 2

    if payload.get("plugin_ready") is False:
        print(
            "\nThe plugin requires a newer OpenStudio SI MCP interface than the "
            "running runtime provides. Ask the user before running "
            "install_runtime.py, then restart or reconnect the host before retrying."
        )
        if doctor.stderr.strip():
            print(doctor.stderr.strip())
        return doctor.returncode or 1

    if doctor.returncode != 0 or payload.get("core_ready") is not True:
        print("\nOpenStudio SI is not ready for energy modeling. Resolve the blocking diagnostics, reconnect the host, and rerun setup.")
        if doctor.stderr.strip():
            print(doctor.stderr.strip())
        return doctor.returncode or 1

    print("\nOpenStudio SI is ready for energy modeling.")
    nlr = payload.get("optional_capabilities", {}).get("nlr_openstudio", {})
    if nlr:
        print(f"NLR OpenStudio-MCP: {nlr.get('status', 'unknown')} — {nlr.get('message', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
