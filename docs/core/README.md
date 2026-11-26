# OpenStudio SI Plugins

This repository is a generated marketplace distribution for the OpenStudio SI runtime. Do not edit generated plugin files here; change the harness source and re-export instead.

## Install

- [Claude Code installation](INSTALL.claude.md)
- [Codex installation](INSTALL.codex.md)

## HVAC upgrade from 0.4.2

Enable OpenStudio SI HVAC Modeler alongside the core to continue HVAC work. Claude Code retains the old names through 0.4.x hotfixes. Codex exposes the HVAC names from the specialist. Reload the host and recheck any saved plan before applying it.

## Contents

- Claude Code core plugin: `openstudio-si/`
- Codex core plugin: `plugins/openstudio-si/`
- HVAC Modeler: `openstudio-si-hvac/` for Claude Code and `plugins/openstudio-si-hvac/` for Codex.
- Runtime: install or update through the setup workflow after enabling a plugin.

## Provenance

- Package version: `0.5.1`
- MCP interface contract: `6.0`
- Runtime mode: `marketplace`
- Source revision: `3bfe2da72c2ea8a52a23c7a9c5109b34dddffac7`
- Complete machine-readable metadata: [`.generated.json`](../../.generated.json)
