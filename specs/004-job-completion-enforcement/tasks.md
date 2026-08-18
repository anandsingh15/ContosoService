---
feature: FEAT-04
plan: DES-04
source_plan_hash: 99321645dc69dd66e4f31285d51b47893ede1cf789526b2f1d22d64d4d336078
repository_context_hash: 57f0a4f5dbc626d20911615aa95895c2f044a1ed7a421d64fb99ea2c40e931a8
task_context_hash: fde86b48d9c7ffa9c5da7aeb0fedb72e377d14fb42340117c149fa972feb2be9
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | node-toolchain, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0043 | ready |
