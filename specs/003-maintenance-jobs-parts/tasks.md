---
feature: FEAT-03
plan: DES-03
source_plan_hash: 8ef6848475a71e124f736aeb229c4ba13e63adb4be154b9536239d26f10b26e1
repository_context_hash: fc5d3500920545a6c95aafb7fc1ea428a257b8111265dbd41e6c8c5933e206d2
task_context_hash: cf876827b400207b215e52febb2527c6f110ce58004a6451683111036c9af2b8
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0016](development/DEV-0016.md) | DES-03-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0017](development/DEV-0017.md) | DES-03-CMP-002 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0018](development/DEV-0018.md) | DES-03-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | — | ready |
| [DEV-0019](development/DEV-0019.md) | DES-03-CMP-004 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0017 | ready |
| [DEV-0020](development/DEV-0020.md) | DES-03-CMP-005 | uiux_form | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0016, DEV-0017, DEV-0018, DEV-0019 | ready |
| [DEV-0021](development/DEV-0021.md) | DES-03-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0016 | ready |
| [DEV-0022](development/DEV-0022.md) | DES-03-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0016 | ready |
| [DEV-0023](development/DEV-0023.md) | DES-03-CMP-008 | uiux_view | repository_and_dataverse_solution | local_interactive | apps-solution-target | reuse_if_valid | microsoft-learn, maker-portal | hybrid | DEV-0016 | ready |
| [DEV-0024](development/DEV-0024.md) | DES-03-CMP-009 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center | hybrid | DEV-0016, DEV-0017 | ready |
