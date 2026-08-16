---
feature: FEAT-02
plan: DES-02
source_plan_hash: 1f74e11793e931564cb56f6f8f7d6c8399ecc45a0fcb3ca2b2eed172ce1edb34
repository_context_hash: 98bdc05931b95ea9aa8fc8c9bb85a0b826a9e79e1d56d9fae1890a9e503f39bb
task_context_hash: d72786ab974f19749be5d9a44cda9082dc4a2418a015c506361302eac050a08d
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
