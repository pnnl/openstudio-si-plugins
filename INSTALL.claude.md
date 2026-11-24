# Install OpenStudio SI In Claude Code

This export is a Claude Code marketplace containing the OpenStudio SI plugin. Use this exported marketplace folder.

## 1. Validate The Export

From the OpenStudio SI harness repository:

```bash
claude plugin validate <path-to-this-marketplace-folder>
```

## 2. Add The Local Marketplace

Open Claude Code in the target project and run:

```text
/plugin marketplace add <path-to-this-marketplace-folder>
```

## 3. Install The Plugin

Still inside Claude Code, run:

```text
/plugin install openstudio-si@openstudio-si-local
```

If Claude Code asks for scope, choose local or project scope for testing.

## 4. Reload Plugins

```text
/reload-plugins
```

## 5. Try The Plugin

Use one of the namespaced skills:

```text
/openstudio-si:simulate
/openstudio-si:query-results
```

The plugin also contributes the OpenStudio modeler agent and an `openstudio_si` MCP server.

## Runtime Setup

After installation, run the setup skill:

```text
/openstudio-si:setup-openstudio-si
```

The setup skill checks Python, checks `openstudio-si-mcp`, and explains any missing installation steps in energy-modeler language.

Bundled SDK commands share the installed plugin's `sdk/` library. Keep the complete plugin together, including `sdk/` and `skills/`; a skill folder alone is not an installable SDK bundle. Run the owning skill's `scripts/doctor.py` with host Python before local SDK modeling. A `plugin_incomplete` result requires restoring the complete plugin from its repository, not installing another Python library. This layout adds no setup dependency or runtime service. Export size evidence is in `sdk/PACKAGING.json`.
Unexpected execution failures route to `report-openstudio-failure`, which automatically submits allowlisted sanitized diagnostics to https://github.com/pnnl/openstudio-si-harness using existing GitHub CLI authentication. Issues are created under your own authenticated GitHub account. Models, companions and transcripts are excluded. Missing authentication/network retains local drafts. Run its independent `scripts/report_failure.py doctor` for optional reporting readiness and `policy disabled` to disable submission for this project. Reporting never gates modeling, and installation sends no incidents.

## HVAC Modeler

For VAV, packaged VAV, CAV, and equipment workflows, install the `openstudio-si-hvac` plugin alongside OpenStudio SI. Install it with `/plugin install openstudio-si-hvac@openstudio-si-local` and reload.
Start with `/openstudio-si-hvac:hvac-modeler`. To check availability, ask which OpenStudio SI plugins are ready in your current session.
When upgrading from 0.4.2, enable HVAC Modeler explicitly. Route older HVAC skill names to the specialist. Resume saved work with the specialist skill and verify the model, plan, and approval before applying.
