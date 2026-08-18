---
feature: FEAT-04
plan: DES-04
source_plan_hash: 70bd78f891de2ce9bce64aaeb6665fba5685cf83b5ab88d8cf9154249f6f7553
repository_context_hash: a23ca2cd9841d7cb864ef8dd0dd5c4bd383089b94929bfb34e0db3339310e492
task_context_hash: 3939a3b8596170cd2714c7e0c8844c9d40aeda4785b296ff6c0de65ba69b8214
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | node-toolchain, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0043 | ready |
