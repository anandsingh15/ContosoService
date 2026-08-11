---
id: DES-01
implements_feature: FEAT-01
source_spec_hash: 2642c68742d36cfa4bf09d81275b299cf771ed945a35cde64877f0391e5a5304
repository_context_hash: fc5d3500920545a6c95aafb7fc1ea428a257b8111265dbd41e6c8c5933e206d2
plan_hash: 2b574056d8d55618b736a7bd0e9dcc526f430fa7030df23e0923e1396f030e84
status: reviewed
---

# Design — FEAT-01 fleet-data-foundation (DES-01)

FEAT-01 is the shared data foundation on which FEAT-02–06 build. It establishes
the three core custom tables (Vehicle, Maintenance Job, Job Part) as minimal
skeletons, the real relationships between them and the existing Account (depot)
and Contact (technician) records, the controlled global choices used for
reportable values, the alternate keys that make record search predictable and
lean at fleet scale, and auditing on the core tables. All behaviour is
declarative Dataverse metadata — no code, flows, or external integration ship in
this feature.

Sibling features extend these skeletons: FEAT-02 adds the Vehicle asset record's
descriptive columns, forms, views and saved lists; FEAT-03 adds the Maintenance
Job / Job Part descriptive columns, calculations, forms, views and saved lists.

## Architecture decisions

<!-- FILL:decisions -->
### Material decisions (architect-confirmed 2026-08-11)

- **Foundation boundary — Strategy A.** FEAT-01 creates the three core custom
  tables as *minimal skeletons* (primary name plus the identity columns needed
  for keys) and owns **all** relationships, global choices, and alternate keys.
  FEAT-02 (Vehicle) and FEAT-03 (Maintenance Job / Job Part) then *extend* those
  tables with descriptive columns, forms, views, business rules and saved lists.
  This keeps the feature dependency graph acyclic (FEAT-02–06 depend on FEAT-01,
  never the reverse) and gives FEAT-01 concrete component ownership of the
  relationship, multiplicity, delete and search requirements it must satisfy
  (REQ-017/018/019/020/021). Alternatives B (choices-only, deferring
  relationships/keys) and C (cross-feature dependency inverting build order) were
  rejected — B leaves REQ-017–021 without an owning component here and C creates
  a feature-graph cycle.
- **Depot = existing Account, Technician = existing Contact (REQ-015).** Vehicle
  carries a lookup to Account and Maintenance Job carries a lookup to Contact.
  Both are **Referential with Remove-Link** delete behaviour so retiring a depot
  or technician preserves the vehicle/job and clears only the association
  (REQ-020). No new Depot or Technician tables are created.
- **Dependent-history delete = Parental cascade (REQ-019).** Vehicle → Maintenance
  Job and Maintenance Job → Job Part are **Parental (Cascade All)**, so deleting a
  vehicle removes its maintenance jobs and their part lines.
- **Archival mechanism deferred (see OQ-01).** The Gate-2 decision (24-month live
  window then archive completed jobs/parts while keeping them reachable for
  history and reporting) is retained as a business decision, but its technical
  realisation is deferred from FEAT-01 pending the flagged change-request intake.
  FEAT-01 ships the data foundation a later archival design will build on.

### Decision axes

1. **logic_tier — Declarative (configuration-first).** Every FEAT-01 component is
   Dataverse metadata: tables, 1:N relationships, global choices, alternate keys,
   and auditing. Delete semantics (cascade / remove-link) are configured on the
   relationship, not coded. No plug-ins, flows, or client code.
   *Grounding:* relationship cascade behaviour is a platform metadata setting
   (Microsoft Learn — Create and edit 1:N relationships).
2. **data_residency — Dataverse-native, single environment.** All data resides in
   the authoring Dataverse environment (org89912357). Depot and technician reuse
   the existing Account and Contact tables; there is no external store and no data
   duplication. *Grounding:* lookup columns may reference Account/Contact
   (Microsoft Learn — Create and edit relationships).
3. **alm_boundary — Segmented solutions, one publisher.** Schema components ship
   in the ContosoServiceCore solution; auditing is an environment-scoped record
   with no solution membership. Publisher AnandPOC / prefix `aks`. Solution
   routing is compiler-owned per `.d365/authoring-targets.yml`. Keeping the data
   model in a dedicated core solution lets FEAT-02–06 layer app, config and
   automation solutions on top without cross-layer coupling.
4. **security — Least-privilege; no roles in FEAT-01.** The three tables are
   **UserOwned** so the FEAT-06 security model can later grant row-level access by
   business unit and team. FEAT-01 introduces no security roles or field-security
   profiles — role design belongs to FEAT-06; the foundation only sets ownership
   so those roles have records to bind to.
5. **integration — None external.** No connectors, APIs, or external systems.
   Internal reuse of Account and Contact only.
6. **environment — authoring-dataverse, interactive user.** Single environment
   (https://org89912357.crm.dynamics.com), `interactive_user` authentication per
   the authoring-targets manifest. No service principal or unattended auth.
7. **ux_surface — Model-driven; owned by FEAT-02/03.** FEAT-01 ships no forms,
   views, or apps. It provides the *search substrate* — indexed alternate keys —
   that FEAT-02/03 quick-find, lookups and views consume. Rich UI is owned by the
   vehicle and job features per the Gate-2 boundaries, so the foundation stays
   UI-agnostic. *Grounding:* alternate keys are indexed for faster, predictable
   lookups (Microsoft Learn — Define alternate keys).
8. **observability — Dataverse auditing on the core tables.** Auditing is enabled
   on Vehicle, Maintenance Job and Job Part to capture record change history for
   reporting integrity (REQ-046) and to make relationship link/unlink and cascade
   events traceable. Detailed in the Observability section below.
9. **batch_processing — None in FEAT-01.** The 24-month archival batch is deferred
   (OQ-01). No scheduled flows or jobs ship in this feature, because the retention
   mechanism extends beyond INTK-0001 evidence and awaits a change-request intake.
10. **reporting — Reporting-ready at the data-model level.** Controlled global
    choices (REQ-016) and reliable, real relationships (REQ-017/018) make the data
    queryable and aggregatable without free-text clean-up (REQ-046). Downstream
    analytics surfaces (Synapse Link / Power BI) are out of FEAT-01 build scope.
    *Grounding:* global choices centralise reusable values maintained in one place
    (Microsoft Learn — Create and edit global choices).
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-01-CMP-001
    component_type: schema_choice
    name: Vehicle Status global choice
    schema_name: aks_vehiclestatus
    options:
      - Active
      - In maintenance
      - Out of service
      - Retired
    satisfies: [INTK-0001-REQ-016, INTK-0001-REQ-046]
  - id: DES-01-CMP-002
    component_type: schema_choice
    name: Maintenance Job Stage global choice
    schema_name: aks_maintenancejobstage
    options:
      - Scheduled
      - In progress
      - On hold
      - Completed
      - Cancelled
    satisfies: [INTK-0001-REQ-016, INTK-0001-REQ-046]
  - id: DES-01-CMP-003
    component_type: schema_choice
    name: Maintenance Job Priority global choice
    schema_name: aks_maintenancejobpriority
    options:
      - Low
      - Medium
      - High
      - Critical
    satisfies: [INTK-0001-REQ-016, INTK-0001-REQ-046]
  - id: DES-01-CMP-004
    component_type: schema_table
    name: Vehicle core table (skeleton)
    schema_name: aks_vehicle
    table: aks_vehicle
    operation: create
    ownership: UserOwned
    primary_name: aks_name
    columns:
      - name: aks_name
        data_type: Text
        required_level: ApplicationRequired
        description: Primary name / fleet identifier.
      - name: aks_registrationnumber
        data_type: Text
        required_level: ApplicationRequired
        description: Registration plate — alternate-key source.
      - name: aks_vin
        data_type: Text
        required_level: Recommended
        description: Vehicle identification number — alternate-key source.
    satisfies: [INTK-0001-REQ-017]
  - id: DES-01-CMP-005
    component_type: schema_table
    name: Maintenance Job core table (skeleton)
    schema_name: aks_maintenancejob
    table: aks_maintenancejob
    operation: create
    ownership: UserOwned
    primary_name: aks_name
    columns:
      - name: aks_name
        data_type: Text
        required_level: ApplicationRequired
        description: Primary name / job title.
      - name: aks_jobnumber
        data_type: Text
        required_level: ApplicationRequired
        description: Business job number — alternate-key source.
    satisfies: [INTK-0001-REQ-017]
  - id: DES-01-CMP-006
    component_type: schema_table
    name: Job Part core table (skeleton)
    schema_name: aks_jobpart
    table: aks_jobpart
    operation: create
    ownership: UserOwned
    primary_name: aks_name
    columns:
      - name: aks_name
        data_type: Text
        required_level: ApplicationRequired
        description: Primary name / part-line label.
      - name: aks_partnumber
        data_type: Text
        required_level: ApplicationRequired
        description: Part number — alternate-key source.
    satisfies: [INTK-0001-REQ-017]
  - id: DES-01-CMP-007
    component_type: schema_relationship
    name: Depot (Account) to Vehicle
    schema_name: aks_account_vehicle_depot
    table: aks_vehicle
    relationship_type: OneToMany
    related_table: account
    lookup_column: aks_depotid
    referenced_attribute: accountid
    required_level: None
    cascade_configuration: "Referential — Remove Link on delete (link cleared, both rows preserved)"
    depends_on: [DES-01-CMP-004]
    satisfies: [INTK-0001-REQ-015, INTK-0001-REQ-017, INTK-0001-REQ-018, INTK-0001-REQ-020]
  - id: DES-01-CMP-008
    component_type: schema_relationship
    name: Technician (Contact) to Maintenance Job
    schema_name: aks_contact_maintenancejob_technician
    table: aks_maintenancejob
    relationship_type: OneToMany
    related_table: contact
    lookup_column: aks_technicianid
    referenced_attribute: contactid
    required_level: None
    cascade_configuration: "Referential — Remove Link on delete (link cleared, both rows preserved)"
    depends_on: [DES-01-CMP-005]
    satisfies: [INTK-0001-REQ-015, INTK-0001-REQ-017, INTK-0001-REQ-018, INTK-0001-REQ-020]
  - id: DES-01-CMP-009
    component_type: schema_relationship
    name: Vehicle to Maintenance Job
    schema_name: aks_vehicle_maintenancejob
    table: aks_maintenancejob
    relationship_type: OneToMany
    related_table: aks_vehicle
    lookup_column: aks_vehicleid
    referenced_attribute: aks_vehicleid
    required_level: ApplicationRequired
    cascade_configuration: "Parental — Cascade All on delete (dependent jobs removed with the vehicle)"
    depends_on: [DES-01-CMP-004, DES-01-CMP-005]
    satisfies: [INTK-0001-REQ-017, INTK-0001-REQ-018, INTK-0001-REQ-019]
  - id: DES-01-CMP-010
    component_type: schema_relationship
    name: Maintenance Job to Job Part
    schema_name: aks_maintenancejob_jobpart
    table: aks_jobpart
    relationship_type: OneToMany
    related_table: aks_maintenancejob
    lookup_column: aks_maintenancejobid
    referenced_attribute: aks_maintenancejobid
    required_level: ApplicationRequired
    cascade_configuration: "Parental — Cascade All on delete (dependent part lines removed with the job)"
    depends_on: [DES-01-CMP-005, DES-01-CMP-006]
    satisfies: [INTK-0001-REQ-017, INTK-0001-REQ-018, INTK-0001-REQ-019]
  - id: DES-01-CMP-011
    component_type: schema_key
    name: Vehicle registration alternate key
    schema_name: aks_vehicle_registration_key
    table: aks_vehicle
    key_columns: [aks_registrationnumber]
    depends_on: [DES-01-CMP-004]
    satisfies: [INTK-0001-REQ-021, INTK-0001-REQ-040, INTK-0001-REQ-041]
  - id: DES-01-CMP-012
    component_type: schema_key
    name: Vehicle VIN alternate key
    schema_name: aks_vehicle_vin_key
    table: aks_vehicle
    key_columns: [aks_vin]
    depends_on: [DES-01-CMP-004]
    satisfies: [INTK-0001-REQ-021, INTK-0001-REQ-040, INTK-0001-REQ-041]
  - id: DES-01-CMP-013
    component_type: schema_key
    name: Maintenance Job number alternate key
    schema_name: aks_maintenancejob_number_key
    table: aks_maintenancejob
    key_columns: [aks_jobnumber]
    depends_on: [DES-01-CMP-005]
    satisfies: [INTK-0001-REQ-021, INTK-0001-REQ-040, INTK-0001-REQ-041]
  - id: DES-01-CMP-014
    component_type: schema_key
    name: Job Part number alternate key
    schema_name: aks_jobpart_number_key
    table: aks_jobpart
    key_columns: [aks_partnumber]
    depends_on: [DES-01-CMP-006]
    satisfies: [INTK-0001-REQ-021, INTK-0001-REQ-040, INTK-0001-REQ-041]
  - id: DES-01-CMP-015
    component_type: config_audit
    name: Core fleet tables auditing
    record_name: Contoso Service core-table auditing
    scope:
      - aks_vehicle
      - aks_maintenancejob
      - aks_jobpart
    depends_on: [DES-01-CMP-004, DES-01-CMP-005, DES-01-CMP-006]
    satisfies: [INTK-0001-REQ-046]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-01 is a metadata-only feature, so observability rests on platform auditing
and Dataverse analytics rather than custom telemetry.

- **Audit (component DES-01-CMP-015).** Dataverse auditing is enabled on
  `aks_vehicle`, `aks_maintenancejob`, and `aks_jobpart` for create, update, and
  delete, including the identity and relationship columns (registration, VIN, job
  number, part number, depot lookup, technician lookup). This gives a change
  history that underpins reporting integrity (REQ-046) and makes remove-link
  (REQ-020) and cascade-delete (REQ-019) events traceable.
- **Metrics tied to NFRs.**
  - *Volume vs REQ-040:* track row counts against the planned fleet scale
    (~5,000 vehicles steady-state; ~40,000 maintenance jobs per year) to confirm
    the model sustains scale. Sustained growth beyond plan is the trigger to
    activate the deferred archival mechanism (OQ-01).
  - *Search latency vs REQ-041:* alternate-key lookups (registration, VIN, job
    number, part number) and quick-find must resolve against indexes rather than
    full-table scans. The alternate-key indexes are the control; watch
    platform slow-query / performance signals.
- **Events.** Relationship link/unlink and cascade-delete operations are captured
  by auditing, providing the evidence needed to verify REQ-019 and REQ-020
  behaviour.
- **Traces.** Not applicable — FEAT-01 introduces no custom code paths.
- **Alerts.** Environment storage/capacity growth against the REQ-040 volumes;
  raise a review when Maintenance Job growth approaches the threshold at which the
  24-month retention window (OQ-01) should be implemented.
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
### OQ-01 — Archival mechanism and retained-history reporting route (24-month retention)

- **Context.** Gate-2 (spec.md, decided by Jane Smith, Contoso Service Product
  Owner, 2026-08-11) set completed maintenance jobs and parts to remain live for
  24 months, then be archived out of everyday lists while remaining reachable for
  history-in-context (REQ-005 / FEAT-04) and reporting (REQ-046). The spec flags
  this as extending beyond INTK-0001 evidence, to be formalised via a
  change-request intake.
- **Options considered.**
  - **A — Declarative custom:** an `Archived` status column on Maintenance Job
    (and Job Part), a scheduled cloud flow that flags completed records older than
    24 months, and filtered views (everyday views exclude archived; an "Archived
    history" view keeps them reachable). No Managed Environment prerequisite; fits
    the ~5,000 / ~40,000 scale.
  - **B — Native Dataverse Long-term data retention:** a retention policy with
    scheduled runs moving rows to a managed data lake. Retained data is read-only
    and queried via FetchXml `datasource="retained"` / Fabric; **requires a
    Managed Environment plus capacity** (an environment-governance decision).
  - **C — Defer:** design the mechanism only once the change-request intake
    formalises the requirement.
- **Decision (decided by Anand Singh, 2026-08-11): Deferred from FEAT-01 (Option C).**
  FEAT-01 ships the data foundation — tables, relationships, controlled choices,
  alternate keys, and auditing — on which a later archival design will build. The
  mechanism choice (A vs B) is made when the change-request intake is raised.
- **Status: Closed — decided by Anand Singh, 2026-08-11.** Resolved by deferring
  the archival mechanism out of FEAT-01; no FEAT-01 requirement depends on the
  mechanism choice, so the data foundation ships unblocked. **Follow-up (outside
  FEAT-01):** raise the flagged change-request intake for the 24-month retention
  requirement, including the Managed Environment governance decision if Option B
  is later chosen.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-015 | DES-01-CMP-007, DES-01-CMP-008 |
| INTK-0001-REQ-016 | DES-01-CMP-001, DES-01-CMP-002, DES-01-CMP-003 |
| INTK-0001-REQ-017 | DES-01-CMP-004, DES-01-CMP-005, DES-01-CMP-006, DES-01-CMP-007, DES-01-CMP-008, DES-01-CMP-009, DES-01-CMP-010 |
| INTK-0001-REQ-018 | DES-01-CMP-007, DES-01-CMP-008, DES-01-CMP-009, DES-01-CMP-010 |
| INTK-0001-REQ-019 | DES-01-CMP-009, DES-01-CMP-010 |
| INTK-0001-REQ-020 | DES-01-CMP-007, DES-01-CMP-008 |
| INTK-0001-REQ-021 | DES-01-CMP-011, DES-01-CMP-012, DES-01-CMP-013, DES-01-CMP-014 |
| INTK-0001-REQ-040 | DES-01-CMP-011, DES-01-CMP-012, DES-01-CMP-013, DES-01-CMP-014 |
| INTK-0001-REQ-041 | DES-01-CMP-011, DES-01-CMP-012, DES-01-CMP-013, DES-01-CMP-014 |
| INTK-0001-REQ-046 | DES-01-CMP-001, DES-01-CMP-002, DES-01-CMP-003, DES-01-CMP-015 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-01-CMP-001 | schema_choice | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-002 | schema_choice | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-003 | schema_choice | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-004 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-005 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-006 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-007 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-008 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-009 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-010 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-011 | schema_key | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-012 | schema_key | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-013 | schema_key | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-014 | schema_key | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-01-CMP-015 | config_audit | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-01 | FEAT-01 | `2642c68742d36cfa4bf09d81275b299cf771ed945a35cde64877f0391e5a5304` | `fc5d3500920545a6c95aafb7fc1ea428a257b8111265dbd41e6c8c5933e206d2` |
<!-- COMPILER:END provenance -->
