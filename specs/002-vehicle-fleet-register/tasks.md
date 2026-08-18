---
feature: FEAT-02
plan: DES-02
source_plan_hash: cee05c840b9a4c8e992fb64483707bbf02801ae5323678d9a67cb8d377e8e354
repository_context_hash: 57f0a4f5dbc626d20911615aa95895c2f044a1ed7a421d64fb99ea2c40e931a8
task_context_hash: 41067c45f3869b43948e5882138e6a98dd890d63e3b1532f639c9c8c19962a47
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0025](development/DEV-0025.md) | DES-02-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | in_review |
| [DEV-0026](development/DEV-0026.md) | DES-02-CMP-002 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | in_review |
| [DEV-0027](development/DEV-0027.md) | DES-02-CMP-003 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | — | in_review |
| [DEV-0029](development/DEV-0029.md) | DES-02-CMP-005 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | in_progress |
| [DEV-0030](development/DEV-0030.md) | DES-02-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | in_review |
| [DEV-0031](development/DEV-0031.md) | DES-02-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | in_review |
| [DEV-0032](development/DEV-0032.md) | DES-02-CMP-008 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0025 | ready |
| [DEV-0033](development/DEV-0033.md) | DES-02-CMP-009 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0025, DEV-0027 | draft |
| [DEV-0034](development/DEV-0034.md) | DES-02-CMP-010 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0026 | draft |
| [DEV-0035](development/DEV-0035.md) | DES-02-CMP-011 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0027 | draft |
| [DEV-0036](development/DEV-0036.md) | DES-02-CMP-012 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0033 | draft |
| [DEV-0037](development/DEV-0037.md) | DES-02-CMP-013 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0029 | draft |
