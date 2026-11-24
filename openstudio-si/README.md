# OpenStudio SI

OpenStudio SI is a Claude plugin package for building-energy modeling workflows using OpenStudio, MCP tools, reusable skills, and a reviewed SDK knowledge base.

## What It Includes

- `.mcp.json`: registers the `openstudio_si` MCP server.
- `agents/openstudio-modeler.md`: the OpenStudio modeler agent prompt.
- `settings.json`: sets `agent` to `openstudio-modeler`, activating it as the main Claude Code thread while the plugin is enabled.
- `skills/`: Claude-native workflow and model-editing skills.
- `skills/*/references/`: reviewed SDK context packs, schemas, and workflow contracts.
- `monitors/`: passive learning-event notifications for candidate learning workflows.
- `bin/`: monitor helper executables.

## User-Facing Skills

- `/openstudio-si:simulate`: run or prepare an OpenStudio simulation workflow.
- `/openstudio-si:query-results`: retrieve SQL-backed simulation results.

## Runtime Skills

- `capture-session-lesson`
- `curate-learning`
- `delegated-nlr-modeling`
- `github-issue-submitter`
- `openstudio-sdk-model-editor`
- `openstudio-workflow-state`
- `propose-measure`
- `query-energy-standards`
- `query-results`
- `report-openstudio-failure`
- `simulate`
- `view-openstudio-geometry`

## Runtime Note

Runtime mode: `marketplace`.

In `local` mode, this plugin references a source checkout. In `installed` and `marketplace` mode, it expects the `openstudio-si-mcp` command to be available on the user's machine.

## Claude Code Activation

Claude Code does not automatically read arbitrary plugin instruction files. This package uses the supported `settings.json` `agent` key to activate `agents/openstudio-modeler.md` as the main thread. If a host or managed policy ignores plugin settings, the skills and MCP server still load, but natural-language orchestration will depend on the user invoking the OpenStudio skills explicitly.

Bundled SDK commands share the installed plugin's `sdk/` library. Keep the complete plugin together, including `sdk/` and `skills/`; a skill folder alone is not an installable SDK bundle. Run the owning skill's `scripts/doctor.py` with host Python before local SDK modeling. A `plugin_incomplete` result requires restoring the complete plugin from its repository, not installing another Python library. This layout adds no setup dependency or runtime service. Export size evidence is in `sdk/PACKAGING.json`.
Unexpected execution failures route to `report-openstudio-failure`, which automatically submits allowlisted sanitized diagnostics to https://github.com/pnnl/openstudio-si-harness using existing GitHub CLI authentication. Issues are created under your own authenticated GitHub account. Models, companions and transcripts are excluded. Missing authentication/network retains local drafts. Run its independent `scripts/report_failure.py doctor` for optional reporting readiness and `policy disabled` to disable submission for this project. Reporting never gates modeling, and installation sends no incidents.
