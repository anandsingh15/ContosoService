---
id: DES-02
status: reviewed
implements_feature: FEAT-02
source_spec_hash: bbfa968b7baa98c1cc1ebefe271ff6a87e3ac23a823b4dc31162b198ede82c1c
repository_context_hash: ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe
plan_hash: dd7097b7aaa6422277d2ecb89d5041c9a795ec0b26d17c3f6ab7c65c51321a21
---

# Design — FEAT-02 vehicle-fleet-register (DES-02)

FEAT-02 extends the Vehicle skeleton created by FEAT-01 with current status and
roadworthiness, then supplies the model-driven forms and views used to capture,
open, and browse fleet assets. FEAT-01 continues to own VIN and registration
alternate keys, the Depot relationship, the Vehicle-to-Maintenance Job
relationship, and the global Vehicle Status choice. FEAT-06 owns the app shell,
security roles, and privileges for personal saved views.

## Architecture decisions

<!-- FILL:decisions -->
### Material decisions (architect-confirmed 2026-08-11)

- **Vehicle boundary — extend the FEAT-01 skeleton (Option A).** The existing
  `aks_vehicle` table gains only `aks_status` and `aks_roadworthy`. VIN,
  registration, Depot, relationships, alternate keys, and the Vehicle Status
  global choice remain owned by FEAT-01 and are reused rather than duplicated.
  Anand Singh selected this option on 2026-08-11. Creating a second Vehicle
  table (Option B) was rejected because it would duplicate identity and break
  the approved relationship model. Recreating keys or relationships in DES-02
  (Option C) was rejected because one logical Dataverse component must have one
  owner. Dataverse alternate keys enforce uniqueness after their backing index
  becomes active.
  *Grounding:* [Define alternate keys to reference rows](https://learn.microsoft.com/power-apps/maker/data-platform/define-alternate-keys-reference-records)
  and the approved DES-01 component model.
- **Vehicle UX — native model-driven forms and views (Option A).** A Quick
  Create form captures registration and VIN; a Main form keeps status,
  roadworthiness, and Depot above the fold and embeds related Maintenance Jobs;
  public views provide the required shared lists. Anand Singh selected this
  configuration-first option on 2026-08-11. A single Main form for both rapid
  capture and full work (Option B) was rejected because it adds navigation and
  fields to the point-of-capture flow. Custom JavaScript or PCF (Option C) was
  rejected because native forms, subgrids, and views cover the behavior without
  pro-code accessibility and packaging scope.
  *Grounding:* [Types of model-driven app forms](https://learn.microsoft.com/power-apps/maker/model-driven-apps/types-forms),
  [Create or edit quick create forms](https://learn.microsoft.com/power-apps/maker/model-driven-apps/create-edit-quick-create-forms),
  and [Design productive main forms](https://learn.microsoft.com/power-apps/maker/model-driven-apps/design-productive-forms).
- **Depot list — public view sorted by Depot (Option A).** The shared Vehicles
  by Depot view places Depot first and sorts by Depot then registration. Anand
  Singh selected this behavior on 2026-08-11, accepting that the rows do not
  have collapsible group headers. A denormalized Depot Name text column plus
  synchronization automation (Option B) was rejected because it duplicates
  Account data and introduces failure handling. A Depot-form-only related
  subgrid (Option C) was rejected because it is not one cross-depot saved list.
  The Power Apps grid supports grouping but not on lookup columns, and grouping
  criteria are not saved to a view; Depot is the approved Account lookup.
  *Grounding:* [Power Apps grid control](https://learn.microsoft.com/power-apps/maker/model-driven-apps/the-power-apps-grid-control)
  and [Explore data on a grid page](https://learn.microsoft.com/power-apps/user/grid-filters#column-header-actions).

### Decision axes

1. **logic_tier — Configuration only.** Dataverse columns, existing alternate
   keys, model-driven forms, subgrids, public views, and auditing satisfy the
   feature. No flow, plug-in, JavaScript, PCF, or Azure component is introduced.
2. **data_residency — Dataverse-native.** Vehicle data and related Maintenance
   Jobs remain in the registered Dataverse environment. No copy or external
   store is introduced.
3. **alm_boundary — Segmented custom solutions.** The Vehicle table extension,
  forms, and views route to `ContosoServiceCore`; only app definitions and site
  maps route to `ContosoServiceApps`; the audit extension remains environment-bound.
   Publisher `AnandPOC` and prefix `aks` come from the authoring-target manifest;
  export and promotion remain external-pipeline concerns. For the one-time
  correction approved by Anand Singh on 2026-08-16, the existing Core-routed
  form/view work orders add or verify membership first; four dependent delta
  components then remove only the exact unmanaged membership from
  `ContosoServiceApps`. This exceptional split preserves the underlying rows,
  immutable IDs, source files, and historical DEV evidence. HTTP `DELETE` is
  prohibited.
4. **security — Existing ownership; roles remain in FEAT-06.** Vehicle remains
   user/team-owned. DES-02 adds no security role or field-security profile.
   FEAT-06 owns coordinator/technician/reader privileges and the Saved View
   privileges required for users to create and reuse personal views. Form
   visibility is never treated as access control.
5. **integration — None external.** No connector, API integration, or external
   system is required.
6. **environment — Registered authoring environment only.** Dataverse-bound
   components use `authoring-dataverse` with interactive-user authentication
   and compiler-resolved targets. No service principal or inferred target is
   permitted.
7. **ux_surface — Model-driven forms and views.** Quick Create handles minimum
   capture, Main presents decisive facts without scrolling and related history
   in context, and public views provide stable organizational baselines. Users
   may derive personal views when FEAT-06 grants Saved View privileges.
8. **observability — Dataverse auditing and form/view verification.** The audit
   record established by FEAT-01 extends to status and roadworthiness. Alternate
   key state, duplicate-save outcomes, form saves, and view results provide the
   operational signals detailed below.
9. **batch_processing — None.** FEAT-02 introduces no scheduled or asynchronous
   custom process. Alternate-key index creation remains platform-managed and is
   owned by FEAT-01 implementation.
10. **reporting — Operational views only.** Active, in-maintenance, and
    Depot-sorted vehicle views support day-to-day browsing. No dashboard,
    semantic model, or Power BI report is introduced.

### Additional strategies

- **AI:** None. The feature has no AI requirement or grounded capability need.
- **Testing:** Verify duplicate rejection for each FEAT-01 alternate key after
  key activation; Quick Create with registration and VIN; Main-form above-fold
  placement at supported desktop and mobile widths; related-history filtering;
  each public view's server-side criteria and sort; personal-view availability
  under FEAT-06 privileges; keyboard and screen-reader behavior; and audit
  capture for status and roadworthiness without exposing customer content.
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-02-CMP-001
    component_type: schema_table
    name: Vehicle feature extension
    schema_name: aks_vehicle
    table: aks_vehicle
    operation: extend
    ownership: UserOwned
    primary_name: aks_name
    settings:
      enable_quick_create: true
    columns:
      - name: aks_status
        data_type: Choice
        choice: aks_vehiclestatus
        required_level: ApplicationRequired
      - name: aks_roadworthy
        data_type: Boolean
        required_level: ApplicationRequired
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-002, INTK-0001-REQ-003, INTK-0001-REQ-004]
  - id: DES-02-CMP-002
    component_type: uiux_form
    name: Vehicle — Quick Create
    schema_name: aks_vehicle_quickcreate
    table: aks_vehicle
    form_type: Quick Create
    sections:
      - name: Vehicle identifiers
        columns: [aks_registrationnumber, aks_vin]
    depends_on: [DES-02-CMP-001]
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-002, INTK-0001-REQ-003]
  - id: DES-02-CMP-003
    component_type: uiux_view
    name: Vehicle — Maintenance History
    schema_name: aks_vehicle_maintenancehistory
    table: aks_maintenancejob
    filter: Related Maintenance Jobs through aks_vehicle_maintenancejob for the current Vehicle
    columns:
      - aks_jobnumber (sort descending)
      - aks_technicianid
      - createdon
      - modifiedon
    satisfies: [INTK-0001-REQ-005]
  - id: DES-02-CMP-005
    component_type: uiux_view
    name: Active Vehicles
    schema_name: aks_activevehicles
    table: aks_vehicle
    filter: aks_status equals 74873 (Active)
    columns:
      - aks_registrationnumber (sort ascending)
      - aks_vin
      - aks_status
      - aks_roadworthy
      - aks_depotid
    depends_on: [DES-02-CMP-001]
    satisfies: [INTK-0001-REQ-006]
  - id: DES-02-CMP-006
    component_type: uiux_view
    name: Vehicles in Maintenance
    schema_name: aks_vehiclesinmaintenance
    table: aks_vehicle
    filter: aks_status equals 74874 (In maintenance)
    columns:
      - aks_registrationnumber (sort ascending)
      - aks_vin
      - aks_status
      - aks_roadworthy
      - aks_depotid
    depends_on: [DES-02-CMP-001]
    satisfies: [INTK-0001-REQ-006]
  - id: DES-02-CMP-007
    component_type: uiux_view
    name: Vehicles by Depot
    schema_name: aks_vehiclesbydepot
    table: aks_vehicle
    filter: All vehicle records; no additional row filter
    columns:
      - aks_depotid (sort ascending)
      - aks_registrationnumber (sort ascending)
      - aks_vin
      - aks_status
      - aks_roadworthy
    depends_on: [DES-02-CMP-001]
    satisfies: [INTK-0001-REQ-006]
  - id: DES-02-CMP-008
    component_type: config_audit
    name: Vehicle feature auditing
    record_name: Contoso Service core-table auditing
    scope:
      - aks_vehicle: [aks_status, aks_roadworthy]
    depends_on: [DES-02-CMP-001]
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-004]
  - id: DES-02-CMP-009
    component_type: uiux_form
    name: Vehicle — Main
    schema_name: aks_vehicle_main
    table: aks_vehicle
    form_type: Main
    sections:
      - name: Header
        columns: [aks_status, aks_roadworthy, aks_depotid]
      - name: Vehicle identity
        columns: [aks_name, aks_registrationnumber, aks_vin]
      - name: Maintenance history
        subgrid: aks_vehicle_maintenancehistory
        relationship: aks_vehicle_maintenancejob
        records: Only Related Records
        read_only: true
    depends_on: [DES-02-CMP-001, DES-02-CMP-003]
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-004, INTK-0001-REQ-005]
  - id: DES-02-CMP-010
    component_type: uiux_form
    name: Vehicle — Quick Create membership removal
    schema_name: aks_vehicle_quickcreate
    table: aks_vehicle
    form_type: quick_create
    sections:
      - name: Vehicle identifiers
        columns: [aks_registrationnumber, aks_vin]
    operation: remove_solution_component
    immutable_id: 600a01e0-3499-f111-b8db-6045bd01db1c
    membership_only: true
    depends_on: [DES-02-CMP-002]
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-002, INTK-0001-REQ-003]
  - id: DES-02-CMP-011
    component_type: uiux_view
    name: Vehicle — Maintenance History membership removal
    schema_name: aks_vehicle_maintenancehistory
    table: aks_maintenancejob
    view_type: public
    columns:
      - aks_jobnumber (sort descending)
      - aks_technicianid
      - createdon
      - modifiedon
    operation: remove_solution_component
    immutable_id: ad45c3e1-3c99-f111-b8db-6045bd01db70
    membership_only: true
    depends_on: [DES-02-CMP-003]
    satisfies: [INTK-0001-REQ-005]
  - id: DES-02-CMP-012
    component_type: uiux_form
    name: Vehicle — Main membership removal
    schema_name: aks_vehicle_main
    table: aks_vehicle
    form_type: main
    sections:
      - name: Header
        columns: [aks_status, aks_roadworthy, aks_depotid]
      - name: Vehicle identity
        columns: [aks_name, aks_registrationnumber, aks_vin]
      - name: Maintenance history
        subgrid: aks_vehicle_maintenancehistory
        relationship: aks_vehicle_maintenancejob
        records: Only Related Records
        read_only: true
    operation: remove_solution_component
    immutable_id: d0031527-4399-f111-b8db-6045bd01d8e8
    membership_only: true
    depends_on: [DES-02-CMP-009]
    satisfies: [INTK-0001-REQ-001, INTK-0001-REQ-004, INTK-0001-REQ-005]
  - id: DES-02-CMP-013
    component_type: uiux_view
    name: Active Vehicles membership removal
    schema_name: aks_activevehicles
    table: aks_vehicle
    view_type: public
    columns:
      - aks_registrationnumber (sort ascending)
      - aks_vin
      - aks_status
      - aks_roadworthy
      - aks_depotid
    operation: remove_solution_component
    immutable_id: 314cef73-4d99-f111-b8db-6045bd01db70
    membership_only: true
    depends_on: [DES-02-CMP-005]
    satisfies: [INTK-0001-REQ-006]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-02 adds no custom compute, so observability uses Dataverse audit, metadata
state, and published-form/view verification rather than Application Insights.

- **Events.** Dataverse auditing records Vehicle status and roadworthiness
  changes. Vehicle create/update outcomes and Maintenance Job relationship
  changes provide the business trail for register and history behavior. Each
  one-time relocation records destination membership verification, source
  membership removal, and final exclusive-Core verification in its Development
  issue without copying customer content.
- **Metrics.** Track duplicate-create rejection by VIN and registration,
  alternate-key state, failed Vehicle saves, published-form load/save failures,
  and view-result conformance for the three required lists. FEAT-02 carries no
  numeric NFR target.
- **Traces.** No cross-service trace exists. Correlation uses the Vehicle row ID,
  Dataverse audit history, form identity, and view identity; customer field
  values are excluded from telemetry and issue evidence.
- **Alerts.** Operations escalates a failed or inactive VIN/registration key,
  repeated Vehicle save failures, a published form that does not render its
  required controls, or a required public view whose filter/sort no longer
  conforms to the plan.
- **Audit.** Component DES-02-CMP-008 extends the FEAT-01 core-table audit record
  to `aks_status` and `aks_roadworthy`. Tokens, secrets, VINs, registration
  values, and other customer content must not be copied into telemetry or issue
  evidence.

*Grounding:* alternate-key creation exposes Pending, In Progress, Active, and
Failed states in [Define alternate keys to reference rows](https://learn.microsoft.com/power-apps/maker/data-platform/define-alternate-keys-reference-records#track-the-status-of-the-creation-of-the-alternate-key).
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
None. Anand Singh confirmed the table/UX boundary and configuration-first
architecture on 2026-08-11. Anand Singh selected the Depot-sorted public view
without collapsible grouping on 2026-08-11 after the native lookup-grouping
constraint and alternatives were presented. Anand Singh confirmed on 2026-08-16
that table-level forms and views ship with Core while Apps contains only app-shell
components such as model-driven app definitions and site maps. Anand Singh also
approved the one-time eight-work-order exception on 2026-08-16: the four existing
Core work orders precede four exact Apps membership removals, with no upstream
Craft change and no deletion of the underlying Dataverse rows.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-001 | DES-02-CMP-001, DES-02-CMP-002, DES-02-CMP-008, DES-02-CMP-009, DES-02-CMP-010, DES-02-CMP-012 |
| INTK-0001-REQ-002 | DES-02-CMP-001, DES-02-CMP-002, DES-02-CMP-010 |
| INTK-0001-REQ-003 | DES-02-CMP-001, DES-02-CMP-002, DES-02-CMP-010 |
| INTK-0001-REQ-004 | DES-02-CMP-001, DES-02-CMP-008, DES-02-CMP-009, DES-02-CMP-012 |
| INTK-0001-REQ-005 | DES-02-CMP-003, DES-02-CMP-009, DES-02-CMP-011, DES-02-CMP-012 |
| INTK-0001-REQ-006 | DES-02-CMP-005, DES-02-CMP-006, DES-02-CMP-007, DES-02-CMP-013 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-02-CMP-001 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-002 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-003 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-005 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-006 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-007 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-008 | config_audit | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
| DES-02-CMP-009 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-02-CMP-010 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
| DES-02-CMP-011 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
| DES-02-CMP-012 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
| DES-02-CMP-013 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | apps-solution-target |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-02 | FEAT-02 | `bbfa968b7baa98c1cc1ebefe271ff6a87e3ac23a823b4dc31162b198ede82c1c` | `ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe` |
<!-- COMPILER:END provenance -->
