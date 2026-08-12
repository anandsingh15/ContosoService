---
feature: FEAT-02
plan: DES-02
source_plan_hash: cd71e6435ee2c7cb201837053a75925167e3bc4885b94380eea60a4061e4e7d5
repository_context_hash: fc5d3500920545a6c95aafb7fc1ea428a257b8111265dbd41e6c8c5933e206d2
task_context_hash: b2ee64dafe4ecea16df3f5deffea30b418b98b65816a72ac3b3b87e6a00977b7
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0025](development/DEV-0025.md) | DES-02-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0026](development/DEV-0026.md) | DES-02-CMP-002 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0025 | ready |
| [DEV-0027](development/DEV-0027.md) | DES-02-CMP-003 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | — | ready |
| [DEV-0028](development/DEV-0028.md) | DES-02-CMP-004 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0025, DEV-0027 | ready |
| [DEV-0029](development/DEV-0029.md) | DES-02-CMP-005 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0025 | ready |
| [DEV-0030](development/DEV-0030.md) | DES-02-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0025 | ready |
| [DEV-0031](development/DEV-0031.md) | DES-02-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0025 | ready |
| [DEV-0032](development/DEV-0032.md) | DES-02-CMP-008 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center | hybrid | DEV-0025 | ready |
