---
feature: FEAT-03
plan: DES-03
source_plan_hash: cde729989711cc95d5a7a4128dd66377f79273b4e1c3c5164e94b4506740fd0c
repository_context_hash: 57f0a4f5dbc626d20911615aa95895c2f044a1ed7a421d64fb99ea2c40e931a8
task_context_hash: 6e59367d518ee1e27f02179de750a95fdc32ce2cd2600fd316d56e2ea411958b
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0016](development/DEV-0016.md) | DES-03-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | completed |
| [DEV-0017](development/DEV-0017.md) | DES-03-CMP-002 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | completed |
| [DEV-0018](development/DEV-0018.md) | DES-03-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | — | completed |
| [DEV-0019](development/DEV-0019.md) | DES-03-CMP-004 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0017, DEV-0038 | completed |
| [DEV-0020](development/DEV-0020.md) | DES-03-CMP-005 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0016, DEV-0017, DEV-0018, DEV-0019, DEV-0038, DEV-0039, DEV-0040, DEV-0041 | ready |
| [DEV-0021](development/DEV-0021.md) | DES-03-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0016 | ready |
| [DEV-0022](development/DEV-0022.md) | DES-03-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0016 | ready |
| [DEV-0023](development/DEV-0023.md) | DES-03-CMP-008 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0016 | ready |
| [DEV-0024](development/DEV-0024.md) | DES-03-CMP-009 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0016, DEV-0017, DEV-0038, DEV-0039, DEV-0040, DEV-0041 | ready |
| [DEV-0038](development/DEV-0038.md) | DES-03-CMP-010 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0017 | completed |
| [DEV-0039](development/DEV-0039.md) | DES-03-CMP-011 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0016 | ready |
| [DEV-0040](development/DEV-0040.md) | DES-03-CMP-012 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0038 | ready |
| [DEV-0041](development/DEV-0041.md) | DES-03-CMP-013 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0039, DEV-0040 | draft |
