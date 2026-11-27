---
name: openstudio-coil-replacer
description: Replace a directly connected main-supply water heating coil with an electric heating coil in a reviewed model copy. Use the water-coil editor for same-class settings changes.
metadata:
  version: 0.2.0
---

## Core preflight

Before using this capability, locate the active OpenStudio SI core plugin via
its `delegated-nlr-modeling` skill in this session. Use host Python to run
`<core-plugin-root>/skills/setup-openstudio-si/scripts/doctor_runtime.py --core-metadata`.
Require `ok: true`, `plugin_version` >=0.5.0 <0.6.0, and
`plugin_contract_version` 6.0. If the core plugin is missing
or incompatible, stop the covered HVAC workflow and ask the user to enable
or update it. Do not draft a replacement SDK script.

Local topology inspection and bundled SDK edits use this disk check and the owning
skill's local OpenStudio preflight. A live OpenStudio SI MCP connection is required
for simulation and results. For those steps, use `runtime_plugin_compatibility`
to verify the connected core plugin and runtime are both >=0.5.0 <0.6.0 and
declare the compatible contract. Keep the existing provider-selection rules.

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

Prefer configured, compatible NLR through `delegated-nlr-modeling`. For selected
local SDK work, run `scripts/doctor.py` with host Python 3.10+ and use its verified
pinned-release OpenStudio executable. Resolve scripts beside this SKILL.md
(Claude: `${CLAUDE_SKILL_DIR}`).

Read [the conversion contract](../../sdk/references/coil_conversion.md) and inventory
the input before selecting a coil. Initial coverage is `CoilHeatingWater` to
`CoilHeatingElectric` on an unsplit main supply path. Require explicit electric
efficiency, `temperature_control: Preserve`, Autosize and reference-policy choices.
Collect missing choices; do not supply an unrequested default or treat a refusal
as permission to change the heating fuel. Show the plan's impact and warnings.

Conversion adds no setpoint manager or temperature schedule. Retain existing
outlet controls, or OpenStudio's generated supply-air tracking with fan compensation
when the OSM outlet is unmanaged. Review before/after translated control fields.
Fixed-temperature/preheat changes need a separate contract; do not convert a
heating design/rating temperature into a control setpoint. Reject older
`outlet_temperature_c` configurations and regenerate their plans.

This is a real class replacement: the coil gets a new handle and loses its water
controller/branch. Availability, air boundary nodes and coil metadata are retained.
EMS/LifeCycleCost or other references to removed equipment/nodes block this initial
contract; they are never silently discarded or retargeted. Controller metadata is
removed with its owner and disclosed in impact. The source plant stays in place;
review remaining loads and retention rather than automatically deleting it.

```text
<verified-cli> execute_python_script <skill>/scripts/replace_coil.py --input <input.osm> --report <inventory.json>
<verified-cli> execute_python_script <skill>/scripts/replace_coil.py --input <input.osm> --config <config.json> --report <plan.json>
<verified-cli> execute_python_script <skill>/scripts/replace_coil.py --plan <plan.json> --report <apply.json>
```

Apply an unchanged ready plan to publish a new model and companion directory.
Saved checks cover performance, controls, identity mappings, the whole connection
graph, protected objects and EnergyPlus translation. Request sizing separately;
fuel conversion does not establish energy savings or ventilation adequacy.
Same-class changes use `openstudio-water-coil-editor`; plant/air migration uses
`openstudio-water-coil-connector`. Other conversion classes and embedded coils
need separate coverage. Diagnose a covered failure without an ad hoc script bypass.
