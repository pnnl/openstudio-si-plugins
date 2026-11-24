---
name: hvac-modeler
description: Route HVAC design, sizing, topology, and system or equipment edits to the reviewed OpenStudio SI HVAC skills. Covers VAV reheat, packaged VAV, prototype CAV, plant loops, and air-side and plant components.
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

Apply this gate before selecting a capability for an HVAC request.

# HVAC Modeler

Use this skill for HVAC requests. Follow the core provider gate before selecting
a capability. Load `delegated-nlr-modeling` for configured NLR and record any
fallback before local SDK work. Use the selected capability's own runtime doctor
and validation. Preserve the core session, model lineage, and evidence on
multi-step work.

Review the requested system, served zones, existing topology, equipment choices,
and prerequisites. For changes, show the capability's plan and obtain any required
approval before applying it. Validate the saved model and report the resulting
model path, assumptions, and unresolved engineering checks.

For a plugin readiness question, use the active host's path to this skill.
Use the core `doctor-openstudio-si` skill and pass the parent of this plugin's
`skills/` directory with `--plugin-dir`.

## Capability routing

- Use `hvac-sizing-assistant` for sizing with OpenStudio simulations and SQL results.
- For the supported packaged VAV recipe, use `openstudio-vav-reheat-system-creator`
  with `prototype_pvav_v1`. Review gas heat, two-speed DX cooling, and electric
  terminal reheat with the user and follow the recipe's sizing validation.
- Use `openstudio-hvac-visualizer` to inspect HVAC components, directed ports and
  served zones as local JSON/Mermaid/Markdown before selection/removal or after
  an edit. Keep NLR priority and the recorded fallback boundary. Link the compact
  overview or selected diagrams; full topology and private labels stay local.
- Use `openstudio-vav-reheat-system-creator` for multi-zone VAV work through
  its exact-release doctor, bundled preflight/apply, and saved-model validator.
  Do not draft objects individually; the legacy child skills have been removed.
- Use `openstudio-cav-system-creator` for the prototype CAV arrangement with a
  constant-volume fan, water heating/reheat and VAV-reheat terminals. Clarify a
  different CAV arrangement before routing; generic prototype controls do not
  imply fixed airflow in every zone or template compliance. VAV/CAV parent scripts
  compose shared equipment functions inside one reviewed model transaction.
- Use `openstudio-district-capacity-editor` for an existing supply-side
  DistrictHeatingWater or DistrictCooling nominal thermal capacity: explicit watts
  or Autosize, preserving schedule, connections and identity. Review the retained
  capacity-fraction schedule; a capacity limit is not an efficiency saving. Steam,
  schedule changes and district production/loss modeling require separate coverage.
- Use `openstudio-tower-performance-editor` for one existing condenser supply-side
  CoolingTowerVariableSpeed design fan electrical power (watts/Autosize), minimum
  airflow ratio or free-convection fraction edits. Require explicit performance
  choices; retain design conditions, unrequested inputs, curves and identity.
  Low-load controls affect fan cycling/fan-off heat rejection and coupled energy;
  fan-off does not mean pumps off or guaranteed savings.
  Review autosized design airflow/airflow-based metrics coupled to fan power,
  evaporation/make-up water and tower electricity;
  other tower classes, user-defined thermal models and replacement need coverage.
- Use `openstudio-plant-equipment-replacer` for a selected hot-water boiler →
  district heating or air/water-cooled EIR chiller → district cooling conversion.
  Explicit capacity, fraction schedule and reference policy are required. Keep
  same-class settings in performance editors. Condenser branch removal is shown
  separately; the condenser plant remains.
- Use `openstudio-hvac-remover`'s `remove_unused_plants.py` for explicitly selected
  unused plant cleanup after fresh inventory. Zero coils alone is insufficient;
  active demand, shared cross-loop equipment or external references block cleanup.
  Never infer plant deletion from a coil migration or source conversion.
- Use `openstudio-chiller-performance-editor` for one existing air- or water-cooled
  ChillerElectricEIR reference COP, cooling capacity (watts/Autosize) or explicit
  part-load/unloading edit on a
  Cooling plant. Preserve curves, unrequested sizing/flow inputs, condenser
  connections, controls and identities. Review effective plant-sizing readiness
  for explicit Autosize and its retained evaporator-flow/factor sizing basis;
  require minimum ≤ optimum ≤ maximum and minimum ≤ unloading ≤ maximum,
  with optimum/maximum > 0; cycling and false loading affect energy. Review autosized
  condenser pump/tower changes after sizing; chiller electricity is not plant
  savings. No inferred standards minimum,
  curve substitution or class conversion. Heat recovery, thermosiphon and other
  chiller classes need separate coverage.
- Use `openstudio-boiler-performance-editor` for explicit nominal thermal capacity
  or capacity Autosize, minimum/maximum/optimum PLRs, HHV efficiency and
  on-cycle electric/off-cycle fuel parasitics
  on a heating-plant BoilerHotWater. Retain identity, fuel, design-flow policy,
  curves, unrequested PLRs, sizing factor and controls. Explicit PLR choices must
  satisfy minimum ≤ optimum ≤ maximum, maximum > 0; minimum can force
  overproduction, and optimum is a dispatch hint. Capacity/PLR changes alter dispatch,
  PLR/curve/parasitic energy or unmet loads; no inferred matching flow or savings.
  Steam boilers, fuel conversion and replacement require separate coverage.
- Use `openstudio-terminal-replacer` for one connected single-duct VAV no-reheat
  ↔ constant-volume no-reheat terminal class change. Require explicit maximum-flow
  policy, VAV target minimum fraction and preservation/reheat/reference policies.
  Review new identity, changed airflow behavior, retained zone branch and sizing;
  this is not a whole-system VAV/CAV conversion. Reheat and unsupported terminal
  classes need separate coverage. Same-class VAV controls use the terminal editor.
  Do not draft substitute scripts for covered terminal replacements.
- Use `openstudio-terminal-editor` for one existing connected single-duct VAV
  reheat/no-reheat terminal's explicit Constant-method minimum fraction or applicable
  reheat controls, including terminals in prototype CAV systems. Preserve the
  terminal/coil, connections, references, schedules and unrequested sizing. Review
  supply-air versus OA, turndown/EMS overrides and flow/sizing warnings; honor
  simulation readiness. Reverse/reheat-flow-limit edits require supported water
  reheat controls. Terminal class/method changes, coil ratings and topology need
  separate coverage. Do not generate substitute scripts for covered terminal edits.
- Use `openstudio-economizer-editor` for explicit in-place economizer type,
  lockout and temperature/enthalpy cutoff edits on an existing direct OA controller.
  It preserves ventilation, DCV, schedules, sizing, topology and handles. Review
  retained additive limits, 100% OA floors and overriding controls; route minimum
  OA/DCV edits to `openstudio-ventilation-editor`. Use the OA connector for
  intake/recovery attachment. Do not draft a substitute script for covered economizer work.
- Use `openstudio-ventilation-editor` for explicit in-place minimum/maximum OA
  flow, OA schedule-reference and ZoneSum DCV edits on an existing direct OA system.
  It preserves zone OA/People, schedule contents, sizing, economizer and handles.
  DCV does not implicitly reset minimum flow or fraction floors: discuss masking
  floors and require explicit changes. Review occupancy, airflow caps, schedule
  ranges and sizing warnings; honor simulation readiness. Other MV-method DCV,
  CO2/IAQ and zone policy need separate coverage; route intake/recovery attachment
  to `openstudio-outdoor-air-connector`.
  Do not generate a substitute script for covered ventilation work.
- Use `openstudio-outdoor-air-connector` to attach a direct OA system at a served
  loop's main supply inlet, or sensible/latent heat recovery to empty OA/relief
  streams. Preview both-stream wiring and require explicit flow, effectiveness,
  power, frost, bypass and outlet-control choices. It does not infer template
  defaults or resize existing equipment. Shared/dedicated and embedded OA need
  separate coverage. Use `openstudio-heat-recovery-editor` for explicit in-place
  performance/control changes on an existing exchanger, preserving its handles,
  curves and references. Retained curves scale with 100% effectiveness edits.
  Verify translated outlet/reference setpoints and honor simulation readiness.
  Do not generate substitute scripts for covered intake or recovery work.
- Use `openstudio-pump-performance-editor` for explicit in-place head, motor,
  electric-power sizing, operating-mode or variable-speed power-curve edits on
  a selected single plant supply/demand pump. Preserve its handles and plumbing;
  inspect fixed-power/inactive-sizing warnings before promising energy savings.
  Use `openstudio-pump-replacer` for genuine single constant ↔ variable-speed
  class changes with explicit curve/minimum flow and flow/power policies. It
  retains plant boundaries/controls and rejects references requiring migration.
  Banks and pressure-reset/plant-flow redesign need separate coverage.
  Do not generate an ad hoc script for a covered pump edit.
- Use `openstudio-supply-fan-performance-editor` for explicit efficiency/pressure changes
  to an existing air loop's sole direct constant- or variable-volume supply fan.
  It edits the existing fan in place and preserves its handle, connections,
  metadata, incoming references, flow controls and unselected model state.
  Use `openstudio-supply-fan-replacer` for a genuine constant-volume ↔ variable-
  volume class change, with explicit performance/curve, Autosize and terminal/
  system-sizing preservation choices. It preserves air boundaries and translated
  controls, reports new identities, and rejects references requiring migration.
  Whole-system VAV/CAV conversion needs separate coverage.
  Embedded fans need separate coverage. Whole-system VAV/CAV construction uses
  the shared fan functions inside its parent transaction.
- Use `openstudio-water-coil-editor` for existing main-supply water-coil ratings,
  name, availability, Autosize resets and controller settings. These are in-place
  setters preserving coil, controller, connection, metadata and reference handles,
  including EMS/LifeCycleCost. Use `openstudio-water-coil-connector` to attach
  a new water coil at the selected air loop's supply outlet and compatible existing
  plant demand branch, or to migrate an existing main-supply coil to another ready
  water plant with explicit Autosize resets. Migration preserves coil/controller/
  air identities; it requires a dedicated single-coil demand branch and may rebuild
  water nodes/connections. Present both plants and sizing/identity effects. New
  attachment requires explicit design, schedule, sizing and controller choices;
  interior/inlet attachment is unsupported. Same-class replacement is not exported.
  Use the connector's `relocate_air` operation for a main-supply water coil moved
  immediately upstream of a selected supply outlet on the same or another unsplit
  air loop, with explicit Autosize. It preserves equipment/controller and plant
  branch identities, updates the sensor, and reports the removed interior air node
  and all affected zones. No zone reassignment or system resizing is implicit.
  Use `openstudio-coil-replacer` for genuine main-supply heating-water to electric
  conversion, with explicit efficiency, preserved temperature control, Autosize and reference
  policy. It preserves schedule/air boundaries/coil metadata, creates a new coil
  and removes the owned water controller/branch; external references block its
  initial Reject policy. Show fuel, remaining-plant-load and identity effects.
  Other class conversions and OA/unitary/terminal coils need separate coverage.
  Whole VAV/CAV creation shares these setters within its parent transaction.
- Use `openstudio-plant-loop-creator` as an independent plant-building module for
  hot-water, chilled-water and associated condenser systems. Route direct plant
  requests and plant stages of broader HVAC workflows here; it is not restricted
  to missing plants or VAV preparation. It creates plant supply equipment,
  pumping and controls, including chiller-to-condenser connections. Pass its
  output model and plant names/handles to the appropriate air-side skill, which
  connects its water coils to plant demand branches. The current VAV skill supports
  that connection; check coverage for other air-side systems before choosing a route.
- Use `openstudio-hvac-remover` independently for explicitly selected existing
  HVAC removal. Include removal in a replacement workflow only when requested;
  plant creation alone does not require removal or subsequent VAV creation.
  Carry each reviewed output into the next selected operation. Expose all zones
  affected by shared-system removal and preserve unselected systems and plants.
  Do not generate ad hoc scripts for covered plant/removal work.
- Use `query-energy-standards` when a task has a code basis (a named standard, "code minimum" or compliance) to resolve equipment efficiency, fan power, economizer, energy recovery, pump, ventilation, envelope or lighting values before the owning skill's configuration is prepared. The owning skill applies the values; the standards skill only looks them up.
- Use bespoke SDK programming only when no specific energy-modeling skill covers
  the request. A failed covered workflow requires diagnosis, not a generated-code
  bypass.
