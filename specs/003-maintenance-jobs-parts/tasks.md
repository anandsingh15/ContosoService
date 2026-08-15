---
feature: FEAT-03
plan: DES-03
source_plan_hash: 61e6cdb4b1515c243c26efade5080133c4bb0949d1a351d4306edcce202c56a9
repository_context_hash: ced4735329e9b6e05b2e45ebdbabfadbe160bd2be1fb7a27f8364914c0cc4718
task_context_hash: 16a82a9c4768e9d84e9742a80c107e29a2a67efa6badf55f22732eb6ec8b76bf
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0016](development/DEV-0016.md) | DES-03-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0017](development/DEV-0017.md) | DES-03-CMP-002 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0018](development/DEV-0018.md) | DES-03-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | — | ready |
| [DEV-0019](development/DEV-0019.md) | DES-03-CMP-004 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0017 | ready |
| [DEV-0020](development/DEV-0020.md) | DES-03-CMP-005 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016, DEV-0017, DEV-0018, DEV-0019 | ready |
| [DEV-0021](development/DEV-0021.md) | DES-03-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0022](development/DEV-0022.md) | DES-03-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0023](development/DEV-0023.md) | DES-03-CMP-008 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0024](development/DEV-0024.md) | DES-03-CMP-009 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0016, DEV-0017 | ready |
