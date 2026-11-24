---
name: openstudio-chiller-performance-editor
description: Edit explicit reference COP, cooling capacity (watts/Autosize) or part-load/unloading limits on one existing air- or water-cooled ChillerElectricEIR in place, preserving curves, unrequested sizing inputs, water circuits, controls and identities. Use for reference-rating changes; other chiller classes, heat recovery, thermosiphon and replacement need separate coverage.
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

Prefer configured, compatible NLR through `delegated-nlr-modeling`. After selecting
or transitioning to the local provider, run `scripts/doctor.py` with host Python
3.10+ and use its verified OpenStudio executable. Resolve resources beside this
SKILL.md (Claude: `${CLAUDE_SKILL_DIR}`). The complete plugin owns shared `sdk/`.

Read the [chiller contract](../../sdk/references/chiller_performance.md) and
[input schema](../../sdk/references/chiller_performance.schema.json). Inventory the model,
then select one Cooling plant's supply-side electric EIR chiller by name or handle.

```text
<verified-cli> execute_python_script <skill>/scripts/edit_chiller_performance.py --input <input.osm> --report <inventory.json>
```

On `requires_preparation`, run the bundled preparer, retain its lineage/state patch,
then re-inventory and preflight against the prepared copy. Never reuse a blocked
plan or write an ad hoc normalizer. See [preparation](../../sdk/references/model_preparation.md).

```text
<verified-cli> execute_python_script <skill>/scripts/prepare_model.py --input <original.osm> --output <prepared.osm> --report <preparation.json>
<verified-cli> execute_python_script <skill>/scripts/edit_chiller_performance.py --input <input.osm> --config <config.json> --report <plan.json>
```

The user supplies one or both reference ratings. `reference_cop` is a positive finite cooling W/electric W value at
the retained reference conditions. Do not substitute IPLV, seasonal or whole-plant
COP or infer a standards minimum. If the retained condenser fan power ratio is
positive, COP must exclude that separately modeled fan power. Resolve an unclear
rating basis before preflight. Missing choices stay unready for discussion;
existing authorization persists. Review before/after COP, reference temperatures,
curves, sizing, condenser type/plant, EMS and other chillers/dispatch. A curve and
retained controls can change actual efficiency. Unrequested capacity and all flow inputs/Autosize flags are preserved. A COP change alters condenser heat rejection: on the next
sizing run, autosized condenser flow, pumps and towers can acquire new sizes and
energy use. Review the plan's listed autosized condenser equipment and compare
plant energy separately from chiller electricity. Curve replacement, condenser
conversion and plant-readiness repairs require separate operations.

For capacity, require explicit `reference_capacity_w`: positive finite cooling
thermal watts or `"Autosize"`; never infer a capacity from COP or choose a sizing
factor. Review current/proposed capacity, retained PLRs, sizing factor and the bounded
other-chiller inventory. Review numeric dispatch limits (reference capacity × PLR,
excluding temperature-curve effects). A positive condenser fan ratio also scales
separate fan power with capacity × cycling fraction for every condenser type,
including water-cooled. Review before/after full-cycling fan watts and fan energy
separately from compressor and external tower-fan energy.
Capacity affects dispatch limits, part-load operation,
cycling/false loading and unmet cooling. With evaporator flow autosized, each chiller uses whole-plant design flow times
its sizing factor and plant design delta-T. With fixed evaporator flow, that flow
and plant design delta-T size capacity without applying the factor again. Units
do not automatically share capacity. Explicit Autosize also reports effective translated plant-sizing controls
and sizing-period count; a missing/unverified setup marks simulation unready while
allowing the reviewed input edit. Configure sizing separately. A capacity change
can resize autosized condenser equipment; retained flow inputs are not a promise
of unchanged sized flows or operating energy.

For part-load edits, require explicit minimum/maximum/optimum PLRs or
`minimum_unloading_ratio`: minimum ≤ optimum ≤ maximum and minimum ≤ unloading
≤ maximum; optimum/maximum > 0. Change companion limits only when requested.
Minimum PLR sets cycling; unloading sets the false-loading floor while on.
Review `impact.part_load_edit`, delivered cooling, cycling, false-load heat,
compressor/condenser-fan energy and unmet cooling. Optimum is a dispatch hint,
not an efficiency curve. Curves, flows and unrequested values stay unchanged.

COP below 2 or above 10 produces a non-blocking plausibility warning. Confirm units:
COP = 3.517 / (kW per ton), or COP = EER / 3.412. The script retains the explicit
COP without converting it or choosing a substitute. Source COP/capacity/curve translation
inconsistencies return unready plan errors for diagnosis, not unexpected failures.

Ready-to-edit and ready-to-simulate are separate. This operation explicitly combines
known operation and companion blockers in `simulation_ready`; it is not simulation
certification. Discuss missing pumps/setpoints or heat rejection without silently
repairing them. Apply only the reviewed plan, then hand simulation/results to the
selected provider. Other chiller classes, heat-recovery and thermosiphon operation
need their own contracts.

```text
<verified-cli> execute_python_script <skill>/scripts/edit_chiller_performance.py --plan <plan.json> --report <apply.json>
```

Use report files, keep the new OSM with its companion directory, and retain source,
plan, apply and output artifact lineage in workflow state when active. On unexpected
execution failures use `report-openstudio-failure` before recovery, honoring the
user's reporting preference; do not publish private models or plan warnings.
