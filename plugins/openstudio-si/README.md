# OpenStudio SI

OpenStudio SI is a Codex plugin package for building-energy modeling workflows using OpenStudio, MCP tools, reusable skills, and reviewed knowledge.

## What It Includes

- `.mcp.json`: registers the `openstudio_si` MCP server.
- `skills/`: Codex-native workflows for orchestration, setup, model editing, simulation, results, and learning capture.
- `skills/*/references/`: reviewed SDK context packs, prompt contracts, blackboard schemas, and learning schemas used by the owning skills.
- `skills/setup-openstudio-si/scripts/`: marketplace runtime setup helpers.

## Skills

- `capture-session-lesson`
- `curate-learning`
- `delegated-nlr-modeling`
- `github-issue-submitter`
- `openstudio-modeling-orchestrator`
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

Bundled SDK commands share the installed plugin's `sdk/` library. Keep the complete plugin together, including `sdk/` and `skills/`; a skill folder alone is not an installable SDK bundle. Run the owning skill's `scripts/doctor.py` with host Python before local SDK modeling. A `plugin_incomplete` result requires restoring the complete plugin from its repository, not installing another Python library. This layout adds no setup dependency or runtime service. Export size evidence is in `sdk/PACKAGING.json`.
Unexpected execution failures route to `report-openstudio-failure`, which automatically submits allowlisted sanitized diagnostics to https://github.com/pnnl/openstudio-si-harness using existing GitHub CLI authentication. Issues are created under your own authenticated GitHub account. Models, companions and transcripts are excluded. Missing authentication/network retains local drafts. Run its independent `scripts/report_failure.py doctor` for optional reporting readiness and `policy disabled` to disable submission for this project. Reporting never gates modeling, and installation sends no incidents.
