---
name: doctor-openstudio-si
description: Report which OpenStudio SI plugins are ready, what each does, and how to resolve missing setup.
---

# Doctor OpenStudio SI

When asked which plugins are ready, run the setup skill's `scripts/doctor_runtime.py` with host Python. The helper supplies the installed core plugin's version and contract. If the current host exposes `hvac-modeler`, pass the root containing its `skills/` directory with `--plugin-dir`. Report each entry in `plugins`, including its description, status, and diagnostic message. A directory path checks package files and runtime compatibility; use this session's available skills to confirm that the host loaded the plugin. For local HVAC work when the runtime is unavailable, use `--core-metadata` and run the selected capability's local preflight.

Explain missing Python, missing runtime, missing OpenStudio, or path problems as setup items, not programming failures.

Bundled SDK commands share the installed plugin's `sdk/` library. Keep the complete plugin together, including `sdk/` and `skills/`; a skill folder alone is not an installable SDK bundle. Run the owning skill's `scripts/doctor.py` with host Python before local SDK modeling. A `plugin_incomplete` result requires restoring the complete plugin from its repository, not installing another Python library. This layout adds no setup dependency or runtime service. Export size evidence is in `sdk/PACKAGING.json`.
Unexpected execution failures route to `report-openstudio-failure`, which automatically submits allowlisted sanitized diagnostics to https://github.com/pnnl/openstudio-si-harness using existing GitHub CLI authentication. Issues are created under your own authenticated GitHub account. Models, companions and transcripts are excluded. Missing authentication/network retains local drafts. Run its independent `scripts/report_failure.py doctor` for optional reporting readiness and `policy disabled` to disable submission for this project. Reporting never gates modeling, and installation sends no incidents.
