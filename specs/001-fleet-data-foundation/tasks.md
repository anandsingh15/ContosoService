---
feature: FEAT-01
plan: DES-01
source_plan_hash: ffe1fd50e90e56fcb1cd557b34fbce52bea8a9a5ba7d8893ef58d684745cf4eb
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
task_context_hash: 50140ab0b8594a7d7545858e92477d0b06d40d605d074eeea22130296ac17eec
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0001](development/DEV-0001.md) | DES-01-CMP-001 | schema_choice | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | completed |
| [DEV-0002](development/DEV-0002.md) | DES-01-CMP-002 | schema_choice | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | in_review |
| [DEV-0003](development/DEV-0003.md) | DES-01-CMP-003 | schema_choice | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | in_progress |
| [DEV-0004](development/DEV-0004.md) | DES-01-CMP-004 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | in_progress |
| [DEV-0005](development/DEV-0005.md) | DES-01-CMP-005 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | in_review |
| [DEV-0006](development/DEV-0006.md) | DES-01-CMP-006 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | in_review |
| [DEV-0007](development/DEV-0007.md) | DES-01-CMP-007 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0004 | in_review |
| [DEV-0008](development/DEV-0008.md) | DES-01-CMP-008 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0005 | in_review |
| [DEV-0009](development/DEV-0009.md) | DES-01-CMP-009 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0004, DEV-0005 | in_review |
| [DEV-0010](development/DEV-0010.md) | DES-01-CMP-010 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0005, DEV-0006 | in_review |
| [DEV-0011](development/DEV-0011.md) | DES-01-CMP-011 | schema_key | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0004 | in_review |
| [DEV-0012](development/DEV-0012.md) | DES-01-CMP-012 | schema_key | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0004 | in_review |
| [DEV-0013](development/DEV-0013.md) | DES-01-CMP-013 | schema_key | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0005 | in_review |
| [DEV-0014](development/DEV-0014.md) | DES-01-CMP-014 | schema_key | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0006 | in_review |
| [DEV-0015](development/DEV-0015.md) | DES-01-CMP-015 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0004, DEV-0005, DEV-0006 | ready |
