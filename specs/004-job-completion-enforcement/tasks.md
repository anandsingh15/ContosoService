---
feature: FEAT-04
plan: DES-04
source_plan_hash: 26e19bc960e76e07c8a62e9dcb2d23ab895a01d0a6aaed905e3a621451adc5b6
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
task_context_hash: 5a7cb8ae1c420222fab33ac3e7b36dd2ff7df4d8efde54496cd4ddc46469afef
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, msal-python, dataverse-web-api, dataverse-mcp | agent | — | in_review |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | microsoft-learn, node-toolchain, dataverse-web-api, power-platform-cli | agent | — | in_review |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0043 | ready |
