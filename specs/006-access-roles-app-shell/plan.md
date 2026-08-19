---
id: DES-06
status: reviewed
implements_feature: FEAT-06
source_spec_hash: 42821d6f48143c9d2fc1854128f671df14e31e5be8c387dcfb8e2fb5e903069a
repository_context_hash: ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe
plan_hash: eb6ca3b9e606c34cec965b4730809be6b631396a82e7aee64c9d31353250e6cf
---

# Design - FEAT-06 access-roles-app-shell (DES-06)

FEAT-06 adds three least-privilege Dataverse roles, assigns those roles to
Dataverse owner teams in the existing root Business Unit, and publishes one
model-driven app with two task-oriented areas. The architect accepted manual
Dataverse team membership as a conscious deviation from REQ-038's automatic
identity-group joiner/leaver behavior.
Technician update isolation uses the FEAT-03 `ownerid` assignment boundary: one
single-member owner team per mapped technician owns that technician's jobs, and
the existing Maintenance Job-to-Job Part cascade carries ownership to parts.

## Architecture decisions

<!-- FILL:decisions -->
### Material decisions (architect-confirmed 2026-08-19)

- **Existing default Business Unit (selected by Anand Singh).** All FEAT-06 roles
  and teams use the existing active root Business Unit `org89912357`, immutable
  `businessunitid` `39b3aab1-defe-f011-8406-000d3a306f55`, in the registered
  `authoring-dataverse` environment. A read-only PAC FetchXML query against the
  exact configured URL returned this unique row where `parentbusinessunitid` is
  null. No `sec_business_unit` component is created.
- **Three Dataverse owner teams with manual membership (selected by Anand
  Singh).** Coordinator, Technician, and Reader roles are assigned to separate
  owner teams in the root BU. Dataverse administrators add and remove users from
  those teams; no Microsoft Entra group binding is used. This keeps role grants
  team-based but intentionally does not automate joiner/leaver changes from the
  organisation's identity groups. The architect accepted that REQ-038 deviation
  on 2026-08-19. Microsoft documents that owner teams can have security roles and
  that their members are managed in Dataverse:
  [Manage teams](https://learn.microsoft.com/power-platform/admin/manage-teams).
- **One single-member owner team per technician (selected by Anand Singh).** A
  Contact-to-System User lookup maps each technician business record to one
  Dataverse user. A synchronous plug-in deterministically provisions one owner
  team in `org89912357`, keeps only the mapped user as its member, and sets a
  Maintenance Job's `ownerid` to that team whenever `aks_technicianid` is set or
  changed. The owner team receives no security role; the user's Technician role
  comes only from the Technician role team, so an administrator can withdraw
  custom-table and app privileges independently of historical ownership membership.
  A shared Technician owner team was rejected because every member could change
  every team-owned job. Direct user ownership was rejected because the selected
  architecture requires an explicit per-technician ownership principal.
- **Owner-based technician enforcement.** Technician Read is Business Unit depth
  for Vehicle, Maintenance Job, and Job Part; Write is User depth only for
  Maintenance Job and Job Part. Dataverse User/Basic access includes records the
  user owns or records owned by a team to which the user belongs. FEAT-01 already
  configures Assign cascade from Maintenance Job to Job Part, so no relationship
  change is required:
  [Security roles and privileges](https://learn.microsoft.com/power-platform/admin/security-roles-privileges)
  and DES-01 `aks_maintenancejob_jobpart`.
- **One role-shared model-driven app.** `Contoso Service` is associated with the
  Coordinator, Technician, and Reader roles and contains Vehicle, Maintenance
  Job, Job Part, Account, and Contact. Its site map has Fleet Operations and
  Customers areas. Dataverse privileges trim actions and records per persona;
  the app does not use client-side hiding as security. Microsoft documents
  sharing model-driven apps with security roles and teams:
  [Share a model-driven app](https://learn.microsoft.com/power-apps/maker/model-driven-apps/share-model-driven-app).

### Decision axes

1. **logic_tier - Configuration plus narrowly scoped pro-code.** Roles, group
   teams, app, and site map are declarative. A synchronous plug-in is justified
   only for atomic Contact-to-user ownership alignment and deterministic owner-
   team provisioning on assignment; an asynchronous flow would leave a window in
   which the wrong principal could retain or lack Write access.
2. **data_residency - Dataverse-native.** Roles, teams, Contact mapping, app
   metadata, and ownership remain in the registered Dataverse environment. No
   identity or business data is copied to an external store.
3. **alm_boundary - Segmented custom solutions and environment records.** Roles
   route to `ContosoServiceSecurity`; Contact mapping routes to
   `ContosoServiceCore`; plug-in assembly and steps route to
   `ContosoServicePluginAndCustomApi`; app and site map route to
   `ContosoServiceApps`. Group and runtime owner teams are environment records in
   `authoring-dataverse`. The existing BU is referenced, never created.
4. **security - Least privilege at Business Unit and User depth.** Coordinator
   receives the required create/read/write/delete/assign/share operations at BU
   depth for fleet tables. Technician receives BU Read and owner-scoped Write for
   jobs and parts. Reader receives BU Read only. Account and Contact are readable
   for the customer area and lookup context; no persona receives broader
   organisation-level fleet privileges. Role grants are cumulative, so acceptance
   testing must use personas without unrelated broad roles.
5. **integration - None.** Team membership is administered directly in Dataverse.
  There is no Microsoft Entra group binding, custom connector, Graph
  synchronization, or external API.
6. **environment - Registered authoring environment and existing root BU.** All
   writes use compiler-routed targets with interactive-user authentication. The
   root BU binding is `org89912357` / `39b3aab1-defe-f011-8406-000d3a306f55`.
7. **ux_surface - One model-driven application.** The Fleet Operations area
   exposes Vehicles, Maintenance Jobs, and Job Parts. The Customers area exposes
   Depots through Account and Technicians through Contact. Existing forms and
   views from FEAT-02, FEAT-03, and FEAT-05 are reused and privilege trimmed.
8. **observability - Plug-in traces, Dataverse audit, and access verification.**
   Ownership alignment emits sanitized Dataverse plug-in traces. Existing audit
   covers owner changes; the new Contact mapping is audit-enabled. Role, team,
   app-role association, and negative persona tests provide access evidence.
9. **batch_processing - None.** Assignment enforcement is synchronous per row,
  and persona-team membership is changed manually by a Dataverse administrator.
  No schedule, polling, or reconciliation batch is introduced.
10. **reporting - No new reporting component.** Existing operational views remain
    available through the app. FEAT-06 adds access and navigation, not a dashboard,
    semantic model, or report.

### Additional strategies

- **AI:** None. No requirement needs generation, prediction, or an AI service.
- **Testing:** Use dedicated Coordinator, Technician A, Technician B, Reader, and
  no-role personas in the root BU with no unrelated broad roles. Verify every
  positive and negative privilege, manual team add/remove behavior, app visibility,
  area navigation, deterministic owner-team provisioning, owner alignment on job
  create and reassignment, Job Part assignment cascade, cross-technician denial,
  unmapped/disabled user rejection, and transactional rollback on provisioning
  failure. Verify all components by immutable identity and publish the app.
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-06-CMP-001
    component_type: sec_role
    name: Contoso Service Coordinator
    schema_name: aks_ContosoServiceCoordinator
    base_role: Basic User
    business_unit:
      record_name: org89912357
      businessunitid: 39b3aab1-defe-f011-8406-000d3a306f55
    privileges:
      - {privilege: prvCreateaks_vehicle, depth: local}
      - {privilege: prvReadaks_vehicle, depth: local}
      - {privilege: prvWriteaks_vehicle, depth: local}
      - {privilege: prvDeleteaks_vehicle, depth: local}
      - {privilege: prvAppendaks_vehicle, depth: local}
      - {privilege: prvAppendToaks_vehicle, depth: local}
      - {privilege: prvAssignaks_vehicle, depth: local}
      - {privilege: prvShareaks_vehicle, depth: local}
      - {privilege: prvCreateaks_maintenancejob, depth: local}
      - {privilege: prvReadaks_maintenancejob, depth: local}
      - {privilege: prvWriteaks_maintenancejob, depth: local}
      - {privilege: prvDeleteaks_maintenancejob, depth: local}
      - {privilege: prvAppendaks_maintenancejob, depth: local}
      - {privilege: prvAppendToaks_maintenancejob, depth: local}
      - {privilege: prvAssignaks_maintenancejob, depth: local}
      - {privilege: prvShareaks_maintenancejob, depth: local}
      - {privilege: prvCreateaks_jobpart, depth: local}
      - {privilege: prvReadaks_jobpart, depth: local}
      - {privilege: prvWriteaks_jobpart, depth: local}
      - {privilege: prvDeleteaks_jobpart, depth: local}
      - {privilege: prvAppendaks_jobpart, depth: local}
      - {privilege: prvAppendToaks_jobpart, depth: local}
      - {privilege: prvAssignaks_jobpart, depth: local}
      - {privilege: prvShareaks_jobpart, depth: local}
      - {privilege: prvReadAccount, depth: local}
      - {privilege: prvAppendToAccount, depth: local}
      - {privilege: prvReadContact, depth: local}
      - {privilege: prvAppendToContact, depth: local}
    satisfies: [INTK-0001-REQ-035, INTK-0001-REQ-039]
  - id: DES-06-CMP-002
    component_type: sec_role
    name: Contoso Service Technician
    schema_name: aks_ContosoServiceTechnician
    base_role: Basic User
    business_unit:
      record_name: org89912357
      businessunitid: 39b3aab1-defe-f011-8406-000d3a306f55
    privileges:
      - {privilege: prvReadaks_vehicle, depth: local}
      - {privilege: prvAppendToaks_vehicle, depth: local}
      - {privilege: prvReadaks_maintenancejob, depth: local}
      - {privilege: prvWriteaks_maintenancejob, depth: basic}
      - {privilege: prvAppendaks_maintenancejob, depth: basic}
      - {privilege: prvAppendToaks_maintenancejob, depth: basic}
      - {privilege: prvReadaks_jobpart, depth: local}
      - {privilege: prvWriteaks_jobpart, depth: basic}
      - {privilege: prvAppendaks_jobpart, depth: basic}
      - {privilege: prvAppendToaks_jobpart, depth: basic}
      - {privilege: prvReadAccount, depth: local}
      - {privilege: prvAppendToAccount, depth: local}
      - {privilege: prvReadContact, depth: local}
      - {privilege: prvAppendToContact, depth: local}
    satisfies: [INTK-0001-REQ-036, INTK-0001-REQ-039]
  - id: DES-06-CMP-003
    component_type: sec_role
    name: Contoso Service Reader
    schema_name: aks_ContosoServiceReader
    base_role: Basic User
    business_unit:
      record_name: org89912357
      businessunitid: 39b3aab1-defe-f011-8406-000d3a306f55
    privileges:
      - {privilege: prvReadaks_vehicle, depth: local}
      - {privilege: prvReadaks_maintenancejob, depth: local}
      - {privilege: prvReadaks_jobpart, depth: local}
      - {privilege: prvReadAccount, depth: local}
      - {privilege: prvReadContact, depth: local}
    satisfies: [INTK-0001-REQ-037, INTK-0001-REQ-039]
  - id: DES-06-CMP-004
    component_type: sec_team
    name: Contoso Service Coordinators - org89912357
    record_name: Contoso Service Coordinators - org89912357
    team_type: owner
    membership_management: manual_dataverse_administrator
    business_unit: org89912357
    business_unit_id: 39b3aab1-defe-f011-8406-000d3a306f55
    roles: [aks_ContosoServiceCoordinator]
    depends_on: [DES-06-CMP-001]
    satisfies: [INTK-0001-REQ-035, INTK-0001-REQ-038]
  - id: DES-06-CMP-005
    component_type: sec_team
    name: Contoso Service Technicians - org89912357
    record_name: Contoso Service Technicians - org89912357
    team_type: owner
    membership_management: manual_dataverse_administrator
    business_unit: org89912357
    business_unit_id: 39b3aab1-defe-f011-8406-000d3a306f55
    roles: [aks_ContosoServiceTechnician]
    depends_on: [DES-06-CMP-002]
    satisfies: [INTK-0001-REQ-036, INTK-0001-REQ-038]
  - id: DES-06-CMP-006
    component_type: sec_team
    name: Contoso Service Readers - org89912357
    record_name: Contoso Service Readers - org89912357
    team_type: owner
    membership_management: manual_dataverse_administrator
    business_unit: org89912357
    business_unit_id: 39b3aab1-defe-f011-8406-000d3a306f55
    roles: [aks_ContosoServiceReader]
    depends_on: [DES-06-CMP-003]
    satisfies: [INTK-0001-REQ-037, INTK-0001-REQ-038]
  - id: DES-06-CMP-007
    component_type: schema_relationship
    name: Technician Contact to Dataverse System User
    schema_name: aks_contact_systemuser_technician
    table: contact
    relationship_type: many_to_one
    related_table: systemuser
    lookup_column: aks_systemuserid
    referenced_attribute: systemuserid
    required_level: optional
    auditing: enabled
    cascade_configuration:
      Assign: NoCascade
      Delete: Restrict
      Merge: NoCascade
      Reparent: NoCascade
      Share: NoCascade
      Unshare: NoCascade
    satisfies: [INTK-0001-REQ-036, INTK-0001-REQ-038]
  - id: DES-06-CMP-008
    component_type: code_plugin
    name: Technician ownership alignment
    schema_name: ContosoService.Plugins.TechnicianOwnershipAlignmentPlugin
    assembly: ContosoService.Plugins
    class_name: ContosoService.Plugins.TechnicianOwnershipAlignmentPlugin
    owner_team:
      record_name_prefix: aks_technician_
      record_name_suffix_source: contactid_lowercase_d_guid
      business_unit: org89912357
      business_unit_id: 39b3aab1-defe-f011-8406-000d3a306f55
      membership: exactly the active systemuser referenced by contact.aks_systemuserid
      roles: []
    steps:
      - name: Maintenance Job Create technician ownership alignment
        message: Create
        table: aks_maintenancejob
        stage: PreOperation
        mode: Synchronous
        rank: 20
        run_as: Step Owner
        behavior:
          - when aks_technicianid is present, require one active systemuser in contact.aks_systemuserid
          - upsert the deterministic single-member owner team in the resolved root Business Unit
          - set ownerid on the in-flight job to that owner team
          - reject the operation with a clear message when mapping or provisioning is invalid
      - name: Maintenance Job Update technician ownership alignment
        message: Update
        table: aks_maintenancejob
        stage: PreOperation
        mode: Synchronous
        rank: 20
        filtering_attributes: [aks_technicianid]
        run_as: Step Owner
        pre_image:
          alias: PreImage
          columns: [aks_technicianid, ownerid]
        behavior:
          - when aks_technicianid changes, require one active mapped systemuser
          - upsert and normalize the deterministic single-member owner team
          - set ownerid on the in-flight job to the selected technician owner team
          - rely on aks_maintenancejob_jobpart Assign Cascade for related part ownership
          - reject and roll back the operation when mapping or provisioning fails
    depends_on: [DES-06-CMP-007]
    satisfies: [INTK-0001-REQ-036, INTK-0001-REQ-038]
  - id: DES-06-CMP-009
    component_type: uiux_app
    name: Contoso Service
    schema_name: aks_ContosoService
    app_type: model_driven
    tables: [aks_vehicle, aks_maintenancejob, aks_jobpart, account, contact]
    roles: [aks_ContosoServiceCoordinator, aks_ContosoServiceTechnician, aks_ContosoServiceReader]
    reuse_components:
      - FEAT-02 Vehicle forms and views
      - FEAT-03 Maintenance Job and Job Part forms and views
      - FEAT-05 Open Maintenance Follow-up Tasks view where role privileges permit
    depends_on: [DES-06-CMP-001, DES-06-CMP-002, DES-06-CMP-003]
    satisfies: [INTK-0001-REQ-039]
  - id: DES-06-CMP-010
    component_type: uiux_sitemap
    name: Contoso Service navigation
    schema_name: aks_ContosoServiceSiteMap
    app: aks_ContosoService
    areas:
      - name: Fleet Operations
        groups:
          - name: Fleet
            subareas:
              - {name: Vehicles, table: aks_vehicle}
              - {name: Maintenance Jobs, table: aks_maintenancejob}
              - {name: Job Parts, table: aks_jobpart}
      - name: Customers
        groups:
          - name: Service Network
            subareas:
              - {name: Depots, table: account}
              - {name: Technicians, table: contact}
    depends_on: [DES-06-CMP-009]
    satisfies: [INTK-0001-REQ-039]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-06 uses Dataverse-native tracing, audit, and access-verification evidence; it
adds no Azure telemetry sink.

- **Events.** Each ownership-alignment invocation emits sanitized start, mapping
  resolved, team found/created, membership normalized, owner set, rejection, and
  success events. Events include message, stage, correlation ID, stable rule code,
  and outcome, but omit names, email addresses, team IDs, row values, and secrets.
- **Metrics.** Operations derives counts of ownership alignments, owner-team
  creations, mapping rejections, disabled-user rejections, membership corrections,
  and unexpected plug-in failures from Plugin Trace Log during support windows.
  The source requirements define no numeric latency or availability target, so the
  design does not invent one.
- **Traces.** Dataverse correlation ID joins the plug-in trace to the originating
  create/update operation. Authorized support staff use audit history to inspect
  row identity and before/after ownership; trace text contains no customer or
  identity values.
- **Alerts.** Any unexpected plug-in exception or repeated mapping/provisioning
  rejection requires administrator investigation because assignment was rolled
  back. Expected cross-technician authorization denials remain security-test and
  user-feedback outcomes, not paging alerts. No ungrounded threshold is added.
- **Audit.** Reuse core-table audit for Maintenance Job `ownerid` and related Job
  Part ownership. Audit-enable `contact.aks_systemuserid`. Preserve environment
  evidence for group-team role assignments and app-role associations, and execute
  positive/negative persona tests after every security change. Never record team
  membership lists, tokens, email addresses, or customer values in telemetry.
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
- [x] Use the environment's default Business Unit for FEAT-06 teams - decided by
  Anand Singh 2026-08-19. Live read-only evidence resolved `org89912357`,
  `businessunitid` `39b3aab1-defe-f011-8406-000d3a306f55`, active, with no parent.
- [x] Use one single-member owner team per mapped technician, a Contact-to-System
  User mapping, and synchronous ownership alignment - decided by Anand Singh
  2026-08-19.
- [x] Create Coordinator, Technician, and Reader as Dataverse owner teams with
  manual Dataverse administrator membership and no Microsoft Entra group binding;
  accept the resulting deviation from REQ-038 automatic identity-group
  joiner/leaver handling - decided by Anand Singh 2026-08-19.
- [x] Encode the per-technician owner-team name as literal prefix
  `aks_technician_` plus the Contact ID in lowercase D GUID format, without a
  brace placeholder in the compiler payload - decided by Anand Singh 2026-08-19.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-035 | DES-06-CMP-001, DES-06-CMP-004 |
| INTK-0001-REQ-036 | DES-06-CMP-002, DES-06-CMP-005, DES-06-CMP-007, DES-06-CMP-008 |
| INTK-0001-REQ-037 | DES-06-CMP-003, DES-06-CMP-006 |
| INTK-0001-REQ-038 | DES-06-CMP-004, DES-06-CMP-005, DES-06-CMP-006, DES-06-CMP-007, DES-06-CMP-008 |
| INTK-0001-REQ-039 | DES-06-CMP-001, DES-06-CMP-002, DES-06-CMP-003, DES-06-CMP-009, DES-06-CMP-010 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-06-CMP-001 | sec_role | dataverse-security | repository_and_dataverse_solution | local_interactive | security-solution-target |
| DES-06-CMP-002 | sec_role | dataverse-security | repository_and_dataverse_solution | local_interactive | security-solution-target |
| DES-06-CMP-003 | sec_role | dataverse-security | repository_and_dataverse_solution | local_interactive | security-solution-target |
| DES-06-CMP-004 | sec_team | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
| DES-06-CMP-005 | sec_team | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
| DES-06-CMP-006 | sec_team | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
| DES-06-CMP-007 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-06-CMP-008 | code_plugin | dataverse-procode | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target |
| DES-06-CMP-009 | uiux_app | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
| DES-06-CMP-010 | uiux_sitemap | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-06 | FEAT-06 | `42821d6f48143c9d2fc1854128f671df14e31e5be8c387dcfb8e2fb5e903069a` | `ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe` |
<!-- COMPILER:END provenance -->
