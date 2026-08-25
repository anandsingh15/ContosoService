---
feature: FEAT-04
plan: DES-04
source_plan_hash: 7d18db37f47fe34da005c94115a20a188ad305c62fa58616b2ca96ba268fda03
repository_context_hash: ce1596580d3b332f571bd9adaac8a24f20e7a871a02dc9e28dc26223ee927417
task_context_hash: 6c924c74e2984a89bb14da6097e13c71523b55ccf518a881323bb519728bb68c
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0042](development/DEV-0042.md) | DES-04-CMP-001 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, msal-python, dataverse-web-api, power-platform-cli, dataverse-mcp | agent | — | in_review |
| [DEV-0043](development/DEV-0043.md) | DES-04-CMP-002 | code_webres_js | repository_and_dataverse_solution | local_interactive | webresource-solution-target | reuse_if_valid | node-toolchain, dataverse-web-api, dataverse-mcp | agent | — | in_review |
| [DEV-0044](development/DEV-0044.md) | DES-04-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0043 | ready |
