---
feature: FEAT-03
plan: DES-03
source_plan_hash: 71e740fd217ec3011c6ada5aaaec056cc3745394062a3006ad04c50da95b02dc
repository_context_hash: ce1596580d3b332f571bd9adaac8a24f20e7a871a02dc9e28dc26223ee927417
task_context_hash: bba63172da0fb99bc123dcd5ca6c17bfbbf7afc4cd714b74467086601a2a9b3e
status: draft
---
# Development work index

Generated from the current plan.md. Historical DEV artifacts are retained but omitted.

| DEV | Component | Type | Scope | Execution host | Authoring target | Authentication policy | Required resources | Executor | Depends on | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [DEV-0016](development/DEV-0016.md) | DES-03-CMP-001 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | completed |
| [DEV-0017](development/DEV-0017.md) | DES-03-CMP-002 | schema_table | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | — | completed |
| [DEV-0018](development/DEV-0018.md) | DES-03-CMP-003 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | — | completed |
| [DEV-0019](development/DEV-0019.md) | DES-03-CMP-004 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0017, DEV-0038 | completed |
| [DEV-0020](development/DEV-0020.md) | DES-03-CMP-005 | uiux_form | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016, DEV-0017, DEV-0018, DEV-0019, DEV-0038, DEV-0039, DEV-0040, DEV-0041 | ready |
| [DEV-0021](development/DEV-0021.md) | DES-03-CMP-006 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0022](development/DEV-0022.md) | DES-03-CMP-007 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0023](development/DEV-0023.md) | DES-03-CMP-008 | uiux_view | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | hybrid | DEV-0016 | ready |
| [DEV-0024](development/DEV-0024.md) | DES-03-CMP-009 | config_audit | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring | reuse_if_valid | microsoft-learn, power-platform-admin-center, dataverse-mcp | hybrid | DEV-0016, DEV-0017, DEV-0038, DEV-0039, DEV-0040, DEV-0041 | ready |
| [DEV-0038](development/DEV-0038.md) | DES-03-CMP-010 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0017 | completed |
| [DEV-0039](development/DEV-0039.md) | DES-03-CMP-011 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0016 | in_review |
| [DEV-0040](development/DEV-0040.md) | DES-03-CMP-012 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0038 | ready |
| [DEV-0041](development/DEV-0041.md) | DES-03-CMP-013 | schema_derived_column | repository_and_dataverse_solution | local_interactive | core-solution-target | reuse_if_valid | microsoft-learn, msal-python, dataverse-web-api, dataverse-mcp | agent | DEV-0039, DEV-0040 | draft |
