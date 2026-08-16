---
feature: FEAT-01
plan: DES-01
source_plan_hash: b39b133c285cfb6437c7a9bf641fe16020a94067b139d1c9b12d881725589f4c
repository_context_hash: c95e3a189999b2566c41aab8ee206e51e15c1308a2c36a4fb4aa0aa21bfce66f
task_context_hash: e0f28994d5b067141de1c7ee74b145ac5096a0b68f97b2995a91c7fffbcc26ad
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
