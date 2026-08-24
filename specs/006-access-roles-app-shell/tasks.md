---
feature: FEAT-06
plan: DES-06
source_plan_hash: 058093c7600c9ee9a7cfb4fd457519832f2f49d88e8bfa2d18b53d72d60cae5c
repository_context_hash: 55c31bfb5d694a25505e4088cec6aebb8b8fbd881bda092156778a6d28190c10
task_context_hash: 5e056278be47f2e19fee8bc6788f436dcca58f9be73d6ce0e9a74c7d6aad076f
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0054](development/DEV-0054.md) | DES-06-CMP-001 | sec_role | repository_and_dataverse_solution | local_interactive | security-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, power-platform-cli, dataverse-mcp | agent | — | in_review |
| [DEV-0055](development/DEV-0055.md) | DES-06-CMP-002 | sec_role | repository_and_dataverse_solution | local_interactive | security-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0056](development/DEV-0056.md) | DES-06-CMP-003 | sec_role | repository_and_dataverse_solution | local_interactive | security-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, power-platform-cli, dataverse-mcp | agent | — | ready |
| [DEV-0057](development/DEV-0057.md) | DES-06-CMP-004 | sec_team | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, dataverse-mcp | agent | DEV-0054 | ready |
| [DEV-0058](development/DEV-0058.md) | DES-06-CMP-005 | sec_team | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, dataverse-mcp | agent | DEV-0055 | ready |
| [DEV-0059](development/DEV-0059.md) | DES-06-CMP-006 | sec_team | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, dataverse-mcp | agent | DEV-0056 | ready |
| [DEV-0060](development/DEV-0060.md) | DES-06-CMP-007 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0061](development/DEV-0061.md) | DES-06-CMP-008 | code_plugin | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target | reuse_if_valid | microsoft-learn, dotnet-toolchain, dataverse-dotnet-sdk, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0060 | ready |
| [DEV-0062](development/DEV-0062.md) | DES-06-CMP-009 | uiux_app | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal, dataverse-mcp | agent | DEV-0054, DEV-0055, DEV-0056 | ready |
| [DEV-0063](development/DEV-0063.md) | DES-06-CMP-010 | uiux_sitemap | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal, dataverse-mcp | agent | DEV-0062 | ready |
