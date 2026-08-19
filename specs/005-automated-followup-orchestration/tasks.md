---
feature: FEAT-05
plan: DES-05
source_plan_hash: 3f94f74d4e476ae7495fbd98350367c97975fdc8a167e849ddd65b130d77f98c
repository_context_hash: ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe
task_context_hash: 05612cf0e652fcc746a934a7c50f1e6c3879f3ea40d2bae29c876ed9ccd1a480
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
