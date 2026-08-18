---
feature: FEAT-04
plan: DES-04
source_plan_hash: b58c608d5dc64317a068b36a98cd443356352f9ece3a566e8484c1af7aa8da08
repository_context_hash: c95e3a189999b2566c41aab8ee206e51e15c1308a2c36a4fb4aa0aa21bfce66f
task_context_hash: fe302bcdb1b2670b04cbef461c935ac266c1af707491a6be96eaa33fe8d236ad
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | node-toolchain, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0043 | ready |
