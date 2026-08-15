---
feature: FEAT-02
plan: DES-02
source_plan_hash: 898efdc9bbe3751738ee1ae7236ef467879b2e8208e7abc7fecf09ec2f00f045
repository_context_hash: cdddee4fea2d4971b55efed9a706edffb5baec4591010e1903afd382b48ddd35
task_context_hash: e72f59f09f1a70182c7240822dd67c31a17b9e42163b71e2c31ce2a9c38386d4
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0025](development/DEV-0025.md) | DES-02-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0026](development/DEV-0026.md) | DES-02-CMP-002 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | ready |
| [DEV-0027](development/DEV-0027.md) | DES-02-CMP-003 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | — | ready |
| [DEV-0028](development/DEV-0028.md) | DES-02-CMP-004 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025, DEV-0027 | ready |
| [DEV-0029](development/DEV-0029.md) | DES-02-CMP-005 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | ready |
| [DEV-0030](development/DEV-0030.md) | DES-02-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | ready |
| [DEV-0031](development/DEV-0031.md) | DES-02-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | hybrid | DEV-0025 | ready |
| [DEV-0032](development/DEV-0032.md) | DES-02-CMP-008 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0025 | ready |
