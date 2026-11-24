---
name: add-vav-reheat
description: Add a multi-zone VAV system using the parent skill's bundled scripts.
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

Prioritize configured, compatible NLR OpenStudio MCP through
`delegated-nlr-modeling`. After selecting the local fallback, use
`openstudio-vav-reheat-system-creator`. Its doctor, preflight,
reviewed-plan apply and saved-topology validation run through host tools.
Read the skill and input contract; execute the scripts without loading their
implementation or drafting per-object code. Follow its missing-input and failure
handling. Use workflow-state tools only when the active task needs them;
simulation/results are a separate handoff after the saved model is ready.
