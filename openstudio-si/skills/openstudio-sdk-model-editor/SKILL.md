---
name: openstudio-sdk-model-editor
description: Route local OSM inspection and edits to bundled SDK skills, or guide bespoke SDK scripts when no bundled operation applies.
metadata:
  version: 0.5.1
  output_format: markdown_with_json_summary
---

If inventory or preflight returns `status: requires_preparation`, run this bundled
operation through the verified CLI before any modeling plan:

```text
<verified-cli> execute_python_script <skill>/scripts/prepare_model.py --input <original.osm> --output <new-prepared.osm> --report <new-preparation.json>
```

Store its `state_patch` and original → prepared `lineage` in workflow state. Use
`output_model_path` for a fresh inventory and preflight; never reuse the blocked
plan or write an ad hoc normalizer. `already_current` reuses the input and writes
no model. Invalid current-version references require diagnosis rather than
manufactured repair. See [model preparation](../../sdk/references/model_preparation.md).

These script paths are fixed launchers into the installed plugin's shared `sdk/`
library. Keep the complete plugin together when copying or distributing it. A
`plugin_incomplete` result requires restoring the complete plugin; do not search
for another SDK library or generate a replacement script. Setup remains the
usual plugin installation plus this skill's doctor.

Unexpected execution failures route to `report-openstudio-failure` before
recovery; pass any `failure_receipt`. Expected readiness/input questions,
including `requires_preparation`, do not submit.

## Scope

Use this skill only for OpenStudio model inspection and model editing. Do not use
it to run simulations or retrieve simulation results. Simulation execution,
polling, artifacts, and SQL-backed result retrieval belong to the OpenStudio MCP
tools.

Use host execution for bundled SDK scripts and scoped generated scripts against
a local `.osm` file. Bundled SDK scripts run directly through the host, without
the OpenStudio SI MCP runtime or measure registry. Host execution means the mechanism
available in the current agent host: AUTOMA-AI may expose `run_python`, Codex
may use its shell/Python execution environment, Claude Code may use its
approved command or script execution path, and some hosts may require asking the
user to run the displayed script manually. Simulation and results use MCP
`sim_*` and `results_*` tools. Bundled model-edit operations use their skill scripts.

When NLR is configured and compatible, prioritize `delegated-nlr-modeling` before
local SDK work. Requests mentioning scripts do not bypass that provider gate.
When NLR is selected as the modeling provider, this skill is available only
after `delegated-nlr-modeling` records a supported provider transition. It must
use the host-visible staged model path recorded in the blackboard, never an NLR
container path such as `/runs/...`.

Allowed uses:

- inspect spaces, thermal zones, surfaces, constructions, schedules, loads, and
  other model objects;
- compute model-level summaries from `.osm` content;
- copy a model and apply scoped edits requested by the user;
- report object counts, names, before/after values, assumptions, warnings, and
  the output model path.

Disallowed uses:

- simulation execution;
- simulation polling;
- SQL result retrieval;
- artifact retrieval;
- network calls;
- shell commands or subprocesses inside model-edit scripts (the bundled doctor
  may launch read-only CLI and embedded SDK probes);
- overwriting the original model unless explicitly requested.

## Choose the operation first

- Use `hvac-modeler` for scoped HVAC workflows, including topology inspection,
  system creation, and equipment edits. If it is missing, unavailable, or fails
  core preflight, stop the covered workflow and tell the user to enable or
  update OpenStudio SI HVAC Modeler. Do not use the bespoke SDK route for a
  covered HVAC operation, including when resuming an older workflow.
- For other local inspection/edits, read
  [bespoke SDK guidance](references/openstudio_sdk_generated_edits.md) only
  after confirming that no specific energy-modeling skill provides the requested
  operation. Bespoke SDK programming is the fallback for uncovered requests.
- A failed or unsupported bundled operation is not permission to draft a
  substitute; report the cause and scope any extension/repair separately.

## Exact SDK Release Gate

This package requires the exact OpenStudio release recorded in
the plugin-root `sdk/compatibility.json`. Build metadata is allowed; prereleases and other
patch releases are rejected. Do not change the contract to accommodate an installed version.

Before SDK model execution, run `scripts/doctor.py` beside this skill with a host
Python 3.10+ interpreter. Prefer the current project's `./.venv/bin/python`, or
its nearest project root's `.venv/bin/python` when working in a subdirectory;
then try a project-configured interpreter, followed by host `python3` or `python`.
Check the Python version without modifying the environment and use the first
usable interpreter to launch doctor. `OPENSTUDIO_PATH` selects the native
OpenStudio executable, not this host Python interpreter.

Doctor uses only the standard library; the host Python does not need OpenStudio
or OpenStudio SI installed. For Claude Code resolve the
script through `${CLAUDE_SKILL_DIR}`; for Codex resolve it relative to this
`SKILL.md`'s actual directory, not the user's current working directory.

Doctor can discover the required executable or accept `--openstudio /absolute/path`
(also accepts `OPENSTUDIO_PATH`). Explicit paths are authoritative: incompatibility
blocks execution rather than triggering fallback. Read its JSON report and exit
code. Continue only when `ok` is true, using the returned absolute
`openstudio_executable` to launch SDK scripts:

```text
<verified-executable> execute_python_script <absolute-script-path> <arguments>
```

Every executable SDK script must independently call the bundled
`common.version_guard.require_sdk()` before loading or editing a user's model.
The embedded launcher needs the script's folder added to `sys.path` to import
its local helpers; follow `scripts/sdk_probe.py` when developing entrypoints.
Doctor verifies CLI identity and the embedded SDK/model binding, but a prior
successful doctor report never replaces the entrypoint's version check.

On failure, report the required and detected versions and the installation link
from doctor. Request installation of the exact release or its executable path.
Do not install automatically, use a different release, or fall back to a host
virtualenv. CLI/SDK mismatch must be resolved before any model operation.

Compatibility checks and supported bundled execution need no SDK wiki packs
or API documentation lookup. Bespoke scripts follow the linked reference,
including its API verification, required-input, result, and review rules.
Execute them through the doctor-selected CLI with the shared guard; project
Python environments are not an incompatible-version fallback.

## Claude Code Supporting Files

Load these files only when needed for the current SDK task:

- `references/openstudio_sdk_recipes.md`: SDK context-pack routing and non-negotiable scripting rules.
- `references/sdk_wiki/`: detailed OpenStudio SDK context packs for geometry, constructions, schedules, spaces/zones/loads, daylighting, HVAC, and simulation-result idioms.

