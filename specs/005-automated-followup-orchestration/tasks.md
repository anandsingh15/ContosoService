---
feature: FEAT-05
plan: DES-05
source_plan_hash: 831e1b92673653c3291cbcadda5a140b1f1c8f606735e727ae53b3677503b444
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
task_context_hash: c4d51e565c998aee024bcd7c6c8992703a2b5586dfa7a042a394c56fb203b2fd
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0045](development/DEV-0045.md) | DES-05-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0046](development/DEV-0046.md) | DES-05-CMP-002 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0047](development/DEV-0047.md) | DES-05-CMP-003 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | — | ready |
| [DEV-0048](development/DEV-0048.md) | DES-05-CMP-004 | schema_relationship | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0049](development/DEV-0049.md) | DES-05-CMP-005 | schema_key | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0047 | ready |
| [DEV-0050](development/DEV-0050.md) | DES-05-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api | agent | DEV-0047, DEV-0048 | ready |
| [DEV-0051](development/DEV-0051.md) | DES-05-CMP-007 | integ_connection_ref | repository_and_dataverse_solution | local_interactive | automation-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | ready |
| [DEV-0052](development/DEV-0052.md) | DES-05-CMP-008 | flow_cloud | repository_and_dataverse_solution | local_interactive | automation-solution-target | reuse_if_valid | microsoft-learn, power-automate-flowagent, dataverse-mcp | agent | DEV-0045, DEV-0046, DEV-0047, DEV-0048, DEV-0049, DEV-0051 | ready |
| [DEV-0053](development/DEV-0053.md) | DES-05-CMP-009 | flow_cloud | repository_and_dataverse_solution | local_interactive | automation-solution-target | reuse_if_valid | microsoft-learn, power-automate-flowagent, dataverse-mcp | agent | DEV-0046, DEV-0047, DEV-0048, DEV-0049, DEV-0051 | ready |
