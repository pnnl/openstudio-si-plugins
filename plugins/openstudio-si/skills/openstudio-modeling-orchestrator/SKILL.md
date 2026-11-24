---
name: openstudio-modeling-orchestrator
description: Route broad OpenStudio modeling requests to the appropriate skills, MCP tools, and workflow-state support.
---

# OpenStudio Modeling Orchestrator

Use this skill for broad OpenStudio modeling requests that span model lifecycle,
SDK editing, simulation, results, or long-running workflow state. Load the
task-specific skill before acting; do not recreate its procedure from memory.

## Routing

- If NLR is configured as `openstudio-mcp`, load `delegated-nlr-modeling` first. It
  performs preflight and selects NLR as the preferred exclusive provider for
  model, measure, simulation, and result work when compatible. It also owns
  the explicit NLR-to-SDK fallback boundary. If NLR is unavailable or
  unsuitable, continue with the OpenStudio SI routes below. This priority applies
  to VAV and requests mentioning local bundled scripts. If NLR cannot cover the
  operation, record the evidence and provider transition before local SDK work.
- For HVAC creation, sizing, topology, or equipment edits, load `hvac-modeler`
  from the OpenStudio SI HVAC Modeler plugin. If the skill is unavailable, tell
  the user and identify the plugin needed for the local bundled workflow.
- When resuming workflow state or lessons, resolve old `openstudio-si:` HVAC
  skill names to their equivalents in `openstudio-si-hvac`. Preserve existing
  state and lineage. If the capability or its core dependency is unavailable,
  stop the covered HVAC workflow. Do not draft a replacement SDK script.
- For plugin readiness, load `doctor-openstudio-si`. Pass the active
  `hvac-modeler` plugin root to the doctor with `--plugin-dir` if that skill
  is available. Report each known plugin's description and status.
- Use `openstudio-sdk-model-editor` for other direct `.osm` inspection or scoped
  edits. It checks for a bundled operation before its bespoke-edit guidance.
- Use `view-openstudio-geometry` to generate a read-only, self-contained HTML
  geometry viewer from an `.osm` model.
- Use `query-energy-standards` when a task has a code basis (a named standard, "code minimum" or compliance) to resolve equipment efficiency, fan power, economizer, energy recovery, pump, ventilation, envelope or lighting values before the owning skill's configuration is prepared. The owning skill applies the values; the standards skill only looks them up.
- Use `simulate` for simulation and `query-results` for SQL-backed results.
- For uncovered operations, follow the general SDK editor after confirming there
  is no owning capability. Diagnose a failed covered workflow using its evidence.
- Use `openstudio-workflow-state` for active long-running workflows that span
  simulations or multiple modeling tasks; standalone bundled operations keep
  their configuration, plans and reports locally.

## Runtime Boundaries

- When `delegated-nlr-modeling` is active, do not call OpenStudio SI
  `model_*`, `sim_*`, `results_*`, measure, or SDK tools until it records a
  provider transition. Do not call an NLR critical mutation before the skill's
  required blackboard checkpoint.
- Use `model_*` MCP tools for model lifecycle, validation, weather, and approved
  measures.
- Use `sim_*` MCP tools for simulation execution, polling, and artifacts.
- Use `results_*` MCP tools for SQL-backed results.
- Use `sdk_docs_*` only as directed by SDK-editing skills.
- Use MCP blackboard tools for an active long-running workflow. Standalone
  bundled HVAC execution persists its configuration, plan, logs and report
  locally and does not require MCP state or modeling-runtime readiness.
- When the active workflow has learning tools, before a non-trivial modeling
  action call `learning_search_lessons` with the
  task type and relevant tags. Use only returned personal lessons that fit the
  current model/version scope, and still validate the model independently.
- At the end of meaningful work, offer to save a concise observation. Capture
  or review learning only after the user explicitly agrees.
- Personal lessons are local guidance. Never promote them directly into trusted
  skills, knowledge, measures, or MCP tools.

For a local bundle returning `requires_preparation`, run that owning skill's
`scripts/prepare_model.py` through its verified CLI with a new copied output and
JSON report. Store original → prepared lineage/state patch, then re-inventory
and re-preflight the prepared path. Do not write ad hoc normalization scripts
or bypass exact plan checks. This applies after the existing NLR-first provider
transition; preparation does not change provider priority.

Bundled SDK skill commands are fixed launchers into the installed plugin's
shared `sdk/` library. A `plugin_incomplete` report requires restoring that whole
plugin; do not search a different checkout or substitute generated scripts.


## Unexpected failures and resume

On an unexpected execution failure, invoke `report-openstudio-failure` before
recovery, abandoning the step or continuing to another modeling step. Reuse a
bundled `failure_receipt`; if absent (MCP error, crash, doctor/probe failure or
broken plugin), use that skill's independent host-Python collector to capture
minimal configuration, versions, expected/actual behavior, publication state and
reproduction evidence. The selected policy automatically submits allowlisted,
sanitized diagnostics to `pnnl/openstudio-si-harness`; no per-incident approval is
required. Issues are created under the user's own authenticated GitHub account.
Do not upload models, companions, transcripts or credentials. Security-
sensitive incidents remain local for private reporting. Explicit user bug reports
qualify; ordinary missing inputs, scope refusals, cancellation, version readiness
and `requires_preparation` do not automatically create issues.

Use the project root as CWD, or set the same absolute `OPENSTUDIO_SI_FAILURE_DIR`
and reporter `--state-dir`. On resume, run its `pending` command and process
pending receipts before new modeling work. Preserve the original incident across
successful workarounds and repeated retries. Store receipt/issue under
`failure_incidents[fingerprint]` in an active blackboard. If reporting is offline,
disabled, locked or uncertain, retain the draft and state the reason, then continue
otherwise safe recovery. Never repeat a mutation to get evidence or issue a second
POST for an uncertain submission. Reporting does not change NLR-first routing or
any preparation/transaction checks.

Do not recursively report reporter/auth/network failures; retain their reason in
the original receipt and continue safe modeling work.
