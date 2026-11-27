# Contributing and publishing independent plugins

The central importer polls **registered public GitHub source releases**, verifies
both host packages against the exact source commit and opens a plugin-scoped PR.
Labs publish release assets in their own repositories; no lab PyPI project or
marketplace write token is required. A maintainer reviews/merges each PR, then
successful main-branch validation creates immutable plugin dependency tags.

The authoritative developer and deployment instructions ship with the harness:

- [One-skill OSM summary walkthrough](https://github.com/pnnl/openstudio-si-harness/blob/main/docs/PLUGIN_OSM_SUMMARY_TUTORIAL.md)
- [Publishing and enrollment guide](https://github.com/pnnl/openstudio-si-harness/blob/main/docs/PLUGIN_PUBLISHING.md)

Merge those harness guides before announcing this contribution path publicly.

## Enrollment

Submit a reviewed entry in `.openstudio-si/registry.json` with the plugin ID,
registered GitHub repository, manifest owner ID and relative `plugin_path`.
The registry is deliberately empty initially; no unowned demo repository is
trusted. `enabled: false` pauses future updates without deleting installed content.
Core `openstudio-si` and HVAC `openstudio-si-hvac` remain reserved.

## Maintainer deployment

1. Publish the harness tooling release containing `marketplace-poll`,
   `validate-marketplace` and `sync-core-marketplace` (prepared as 0.5.1).
2. Set repository variable `PLUGIN_TOOLING_VERSION` to that exact published version.
3. Set central-only secret `PLUGINS_PR_TOKEN` to a scoped automation token with
   contents/pull-request write access here. Its PRs must trigger normal CI.
4. Merge these workflows/helpers onto `main`, enable Actions/schedules and require
   **Validate marketplace** through the repository's branch rules.
5. Enroll a real source, publish its matching GitHub release, dispatch the importer
   and review its PR. Confirm both hosts install it after merge and tag creation.

Until these settings and a real end-to-end release are verified, this is an
implementation awaiting deployment, not an enabled production submission service.

## Workflows

- **Import registered plugin releases** runs every 15 minutes or on manual
  dispatch. A read-only job verifies source/assets/hosts/graph; a separate trusted
  stdlib-only writer opens or refreshes per-plugin release PRs. The write token is
  provided only to the publication step, never to native host readers or installers.
- **Validate marketplace** checks the full proposed graph, receipts and native host
  loading on every PR and main push. No agent or LLM judge runs in CI.
- **Tag validated plugin releases** handles successful main-push validation only.
  Tags use `<id>--v<version>`, point at the validated commit, and are never moved.

Do not edit an approved release version's package or receipt. Publish a new
version instead. Independent releases use separate branches and preserve other
plugins. A changed base is retried on the next poll rather than overwritten.
