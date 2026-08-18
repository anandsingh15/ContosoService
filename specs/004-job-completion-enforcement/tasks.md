---
feature: FEAT-04
plan: DES-04
source_plan_hash: f3576c7636637d30d5ae665dda1b6277c2ea498336db10bc86911d6885d4ec71
repository_context_hash: ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe
task_context_hash: 3a4800a07895989f1d58d10d2082e0faff97183af91954ac9770cd45323e6bee
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, msal-python, dataverse-web-api, dataverse-mcp | agent | — | in_review |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | microsoft-learn, node-toolchain, dataverse-web-api, power-platform-cli | agent | — | in_review |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0043 | ready |
