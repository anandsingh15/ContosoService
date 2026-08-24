---
id: DES-03
status: reviewed
implements_feature: FEAT-03
source_spec_hash: 5685339b5cf5c270ecd4e0caad82a5f0178a85e7531775ee9d4df111f7b3669b
repository_context_hash: 55c31bfb5d694a25505e4088cec6aebb8b8fbd881bda092156778a6d28190c10
plan_hash: e6f89e86ed4c3b8e282bb0d4b8a1cb419e61db7568a2466f3ebec010a51332f6
---

# Design — FEAT-03 maintenance-jobs-parts (DES-03)

FEAT-03 extends the Maintenance Job and Job Part skeleton tables created by
FEAT-01. It adds the job scheduling, priority, labour, and cost columns; the part
quantity, price, and calculated line value; a native model-driven job form with
vehicle context and inline part entry; and three shared operational job views.
The app shell and role-based access remain owned by FEAT-06.

## Architecture decisions

<!-- FILL:decisions -->
### Material decisions (architect-confirmed 2026-08-11)

- **Cost calculation — declarative Dataverse (Option A).** Job Part line value
  and Maintenance Job labour cost are Decimal Power Fx formula columns. Total
  parts cost is a Decimal rollup over related Job Parts, and total cost is a
  Decimal Power Fx formula column using the latest total-parts rollup plus
  labour cost. Anand Singh selected this configuration-first option on
  2026-08-11 and confirmed migration from legacy calculated columns to formula
  columns on 2026-08-16. Currency operands are converted with `Decimal(...)`
  because Dataverse formula columns do not expose Currency as an output type.
  A cloud flow (Option B) was rejected because it adds run latency, operations,
  and connection dependencies; a synchronous plug-in (Option C) was rejected
  because the requirements do not justify pro-code deployment and test scope.
  The accepted implication is that total parts and total cost follow Dataverse
  rollup refresh timing rather than updating transactionally with each line.
  Dataverse rollups run asynchronously, with a default minimum recurrence of one
  hour, and users with write access can request an online recalculation.
  *Grounding:* [Define rollup columns that aggregate values](https://learn.microsoft.com/power-apps/maker/data-platform/define-rollup-fields#rollup-calculations)
  and [Create and edit Dataverse columns](https://learn.microsoft.com/power-apps/maker/data-platform/create-edit-field-solution-explorer#column-type).
- **Job UX — native model-driven controls (Option A).** The Maintenance Job main
  form presents job number, stage, and priority in its header; embeds a Vehicle
  quick-view form; and uses an editable Power Apps grid subgrid for Job Parts.
  Anand Singh selected this option on 2026-08-11. A Quick Create dialog per part
  (Option B) was rejected because REQ-014 requires line-by-line entry without a
  separate record form. A custom PCF grid (Option C) was rejected because the
  native grid already supports editable views and subgrids, so pro-code would
  add accessibility, packaging, and test scope without a capability gap.
  *Grounding:* [Power Apps grid control](https://learn.microsoft.com/power-apps/maker/model-driven-apps/the-power-apps-grid-control),
  [Types of model-driven forms](https://learn.microsoft.com/power-apps/maker/model-driven-apps/types-forms),
  and [Quick view components](https://learn.microsoft.com/power-apps/maker/model-driven-apps/form-designer-add-configure-quickview).
- **Operational assignment — record ownership (Option A).** The Maintenance Job
  `ownerid` is the operational assignment used by the shared "Jobs Assigned to
  Me" view and by FEAT-06 security. The existing `aks_technicianid` Contact
  lookup remains the business technician reference required by FEAT-01. Anand
  Singh selected this option on 2026-08-11. A custom System User-to-Contact
  mapping and synchronization design (Option B) was rejected as additional data
  and automation outside FEAT-03. Assignment operations must keep owner and the
  technician reference consistent; FEAT-06 owns enforcement of update access.
  *Grounding:* FEAT-01 defines Maintenance Job as user/team-owned and reuses
  Contact for the technician relationship; FEAT-06 defines technicians' write
  access over assigned jobs. Dataverse owner columns reference users or teams:
  [Owner references](https://learn.microsoft.com/power-apps/maker/canvas-apps/working-with-references#show-the-columns-of-a-record-owner).

### Decision axes

1. **logic_tier — Configuration only.** Formula and rollup columns, forms,
   the Power Apps grid control, and public views satisfy the feature. No flow,
   plug-in, JavaScript, PCF, or Azure component is introduced.
2. **data_residency — Dataverse-native.** Maintenance Job and Job Part remain in
   the existing authoring Dataverse environment. No data is copied externally.
3. **alm_boundary — Segmented custom solutions.** Table extensions, forms, and
  views route to `ContosoServiceCore`; only app definitions and site maps route
  to `ContosoServiceApps`; the audit extension remains environment-bound. Publisher `AnandPOC` and prefix
   `aks` come from `.d365/authoring-targets.yml`; export and promotion remain
   external-pipeline concerns.
4. **security — Existing user/team ownership, roles deferred to FEAT-06.** The
   feature adds no roles or field-security profiles. Maintenance Job ownership
   is the operational assignment boundary. Server-side privileges, team access,
   and technician edit restrictions are designed in FEAT-06, not hidden in form
   logic.
5. **integration — None external.** No connector, API integration, or external
   system is required.
6. **environment — Registered authoring environment only.** Dataverse-bound
   components use `authoring-dataverse` with interactive-user authentication and
   compiler-resolved targets. No service principal or inferred environment is
   permitted.
7. **ux_surface — Model-driven app forms and views.** FEAT-03 supplies table
   forms and views for the single app that FEAT-06 owns. A Vehicle Quick View
   projects registration, VIN, status, roadworthiness, and depot through the
   existing vehicle lookup; the job form hosts that projection and the editable
   Job Parts subgrid.
8. **observability — Dataverse auditing and rollup health.** Status, scheduling,
   labour, price, quantity, and cost columns extend FEAT-01's core-table audit
   policy. Rollup date/state and system-job outcomes expose total-cost freshness
   and failures. Details are in the Observability section.
9. **batch_processing — Dataverse rollup system job only.** The platform's
   asynchronous rollup job calculates total parts cost. There is no custom
   scheduled flow or batch process.
10. **reporting — Operational views and reportable columns.** Public views cover
    active, assigned, and high/critical work. Currency and choice columns remain
    queryable for later reporting, but no dashboard or Power BI artifact is in
    FEAT-03.

### Additional strategies

- **AI:** None. The feature has no AI requirement or grounded capability need.
- **Testing:** Validate each calculation at zero, one-line, multi-line, and
  decimal/currency boundaries; verify rollup freshness and manual recalculation;
  verify each shared view's FetchXML criteria; and test the main form, vehicle
  quick view, editable part grid, keyboard navigation, and role-visible behavior
  in the published model-driven app.
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-03-CMP-001
    component_type: schema_table
    name: Maintenance Job feature extension
    schema_name: aks_maintenancejob
    table: aks_maintenancejob
    operation: extend
    ownership: UserOwned
    primary_name: aks_name
    columns:
      - name: aks_stage
        data_type: Choice
        choice: aks_maintenancejobstage
        required_level: ApplicationRequired
      - name: aks_priority
        data_type: Choice
        choice: aks_maintenancejobpriority
        required_level: ApplicationRequired
      - name: aks_scheduleddate
        data_type: DateTime
        behavior: UserLocal
        required_level: Recommended
      - name: aks_completeddate
        data_type: DateTime
        behavior: UserLocal
        required_level: None
      - name: aks_labourhours
        data_type: Decimal
        precision: 2
        minimum: 0
        required_level: None
      - name: aks_hourlyrate
        data_type: Currency
        minimum: 0
        required_level: None
    satisfies: [INTK-0001-REQ-007, INTK-0001-REQ-013]
  - id: DES-03-CMP-002
    component_type: schema_table
    name: Job Part feature extension
    schema_name: aks_jobpart
    table: aks_jobpart
    operation: extend
    ownership: UserOwned
    primary_name: aks_name
    columns:
      - name: aks_quantity
        data_type: Decimal
        precision: 2
        minimum: 0.01
        required_level: ApplicationRequired
      - name: aks_unitprice
        data_type: Currency
        minimum: 0
        required_level: ApplicationRequired
    satisfies: [INTK-0001-REQ-011, INTK-0001-REQ-012]
  - id: DES-03-CMP-003
    component_type: uiux_form
    name: Vehicle — Job Context
    schema_name: aks_vehicle_jobcontext_quickview
    table: aks_vehicle
    form_type: Quick View
    sections:
      - name: Key vehicle details
        columns: [aks_registrationnumber, aks_vin, aks_status, aks_roadworthy, aks_depotid]
    satisfies: [INTK-0001-REQ-009]
  - id: DES-03-CMP-004
    component_type: uiux_view
    name: Job Parts — Inline Entry
    schema_name: aks_jobparts_inlineentry
    table: aks_jobpart
    filter: Associated Job Parts through aks_maintenancejob_jobpart
    columns:
      - aks_partnumber (sort ascending)
      - aks_quantity
      - aks_unitprice
      - aks_linevalue
    depends_on: [DES-03-CMP-002, DES-03-CMP-010]
    satisfies: [INTK-0001-REQ-011, INTK-0001-REQ-012, INTK-0001-REQ-014]
  - id: DES-03-CMP-005
    component_type: uiux_form
    name: Maintenance Job — Main
    schema_name: aks_maintenancejob_main
    table: aks_maintenancejob
    form_type: Main
    sections:
      - name: Header
        columns: [aks_jobnumber, aks_stage, aks_priority]
      - name: Job details
        columns: [aks_vehicleid, ownerid, aks_technicianid, aks_scheduleddate, aks_completeddate]
      - name: Vehicle context
        quick_view: aks_vehicle_jobcontext_quickview via aks_vehicleid
      - name: Labour and totals
        columns: [aks_labourhours, aks_hourlyrate, aks_labourcost, aks_totalpartscost, aks_totalcost]
      - name: Parts used
        subgrid: aks_jobparts_inlineentry
        relationship: aks_maintenancejob_jobpart
        control: Power Apps grid
        editable: true
    depends_on: [DES-03-CMP-001, DES-03-CMP-002, DES-03-CMP-003, DES-03-CMP-004, DES-03-CMP-010, DES-03-CMP-011, DES-03-CMP-012, DES-03-CMP-013]
    satisfies: [INTK-0001-REQ-007, INTK-0001-REQ-008, INTK-0001-REQ-009, INTK-0001-REQ-011, INTK-0001-REQ-012, INTK-0001-REQ-013, INTK-0001-REQ-014]
  - id: DES-03-CMP-006
    component_type: uiux_view
    name: Active Jobs
    schema_name: aks_activejobs
    table: aks_maintenancejob
    filter: aks_stage not-in [74880 (Completed), 74881 (Cancelled)]
    columns:
      - aks_jobnumber (sort ascending)
      - aks_stage
      - aks_priority
      - aks_vehicleid
      - ownerid
      - aks_scheduleddate
    depends_on: [DES-03-CMP-001]
    satisfies: [INTK-0001-REQ-010]
  - id: DES-03-CMP-007
    component_type: uiux_view
    name: Jobs Assigned to Me
    schema_name: aks_jobsassignedtome
    table: aks_maintenancejob
    filter: ownerid equals current user
    columns:
      - aks_jobnumber (sort ascending)
      - aks_stage
      - aks_priority
      - aks_vehicleid
      - aks_scheduleddate
    depends_on: [DES-03-CMP-001]
    satisfies: [INTK-0001-REQ-010]
  - id: DES-03-CMP-008
    component_type: uiux_view
    name: High and Critical Priority Jobs
    schema_name: aks_highcriticaljobs
    table: aks_maintenancejob
    filter: aks_priority in [74884 (High), 74885 (Critical)]
    columns:
      - aks_jobnumber (sort ascending)
      - aks_priority
      - aks_stage
      - aks_vehicleid
      - ownerid
      - aks_scheduleddate
    depends_on: [DES-03-CMP-001]
    satisfies: [INTK-0001-REQ-010]
  - id: DES-03-CMP-009
    component_type: config_audit
    name: Maintenance job and part feature auditing
    record_name: Contoso Service core-table auditing
    scope:
      - aks_maintenancejob: [aks_stage, aks_priority, aks_scheduleddate, aks_completeddate, aks_labourhours, aks_hourlyrate, aks_labourcost, aks_totalpartscost, aks_totalcost]
      - aks_jobpart: [aks_quantity, aks_unitprice, aks_linevalue]
    depends_on: [DES-03-CMP-001, DES-03-CMP-002, DES-03-CMP-010, DES-03-CMP-011, DES-03-CMP-012, DES-03-CMP-013]
    satisfies: [INTK-0001-REQ-007, INTK-0001-REQ-011, INTK-0001-REQ-013]
  - id: DES-03-CMP-010
    component_type: schema_derived_column
    name: Job Part line value formula
    schema_name: aks_linevalue
    table: aks_jobpart
    base_data_type: decimal
    derived_type: formula
    formula: aks_quantity * Decimal(aks_unitprice)
    required_level: None
    depends_on: [DES-03-CMP-002]
    satisfies: [INTK-0001-REQ-011, INTK-0001-REQ-012]
  - id: DES-03-CMP-011
    component_type: schema_derived_column
    name: Maintenance Job labour cost formula
    schema_name: aks_labourcost
    table: aks_maintenancejob
    base_data_type: decimal
    derived_type: formula
    formula: aks_labourhours * Decimal(aks_hourlyrate)
    required_level: None
    depends_on: [DES-03-CMP-001]
    satisfies: [INTK-0001-REQ-007, INTK-0001-REQ-013]
  - id: DES-03-CMP-012
    component_type: schema_derived_column
    name: Maintenance Job total parts cost rollup
    schema_name: aks_totalpartscost
    table: aks_maintenancejob
    base_data_type: decimal
    derived_type: rollup
    formula: null
    rollup_spec:
      related_entity: aks_jobpart
      aggregate_function: SUM
      aggregate_attribute: aks_linevalue
    required_level: None
    depends_on: [DES-03-CMP-010]
    satisfies: [INTK-0001-REQ-013]
  - id: DES-03-CMP-013
    component_type: schema_derived_column
    name: Maintenance Job total cost formula
    schema_name: aks_totalcost
    table: aks_maintenancejob
    base_data_type: decimal
    derived_type: formula
    formula: aks_totalpartscost + aks_labourcost
    required_level: None
    depends_on: [DES-03-CMP-011, DES-03-CMP-012]
    satisfies: [INTK-0001-REQ-013]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-03 adds no custom compute, so it uses Dataverse audit and rollup operational
signals rather than Application Insights.

- **Events.** Auditing records job stage, priority, schedule, completion, labour,
  price, quantity, and cost changes. Job Part create/update/delete events provide
  the business trail behind each parts-total change.
- **Metrics.** Monitor rollup state (`Calculated`, error states), rollup last-
  calculated age, failed rollup system jobs, and editable-grid save failures.
  Functional verification measures line value against quantity × unit price,
  total parts against the sum of related lines, and total cost against parts plus
  labour after rollup recalculation. FEAT-03 carries no numeric NFR target.
- **Traces.** No cross-service trace exists. Correlation is the Maintenance Job
  row ID plus the Dataverse audit history and rollup date/state columns.
- **Alerts.** Operations reviews any rollup error state immediately and any
  active-job total whose last-calculated age exceeds two incremental job windows
  (two hours under the accepted default cadence). Repeated editable-grid save
  failures are escalated to the application owner with the affected form/view
  identity, never customer values.
- **Audit.** Component DES-03-CMP-009 extends the existing FEAT-01 core-table
  audit record to all new status, scheduling, labour, quantity, price, and cost
  columns. Telemetry and issue evidence must not include customer content,
  prices, personal data, tokens, or secrets.

*Grounding:* Dataverse exposes rollup date/state and calculates rollups through
asynchronous system jobs: [Specialized columns — rollup columns](https://learn.microsoft.com/power-apps/developer/data-platform/specialized-columns#rollup-columns)
and [Rollup calculations](https://learn.microsoft.com/power-apps/maker/data-platform/define-rollup-fields#rollup-calculations).
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
None. The cost, UX, and assignment choices were explicitly decided by Anand
Singh on 2026-08-11 and are recorded above. FEAT-02 must provide the Vehicle
columns referenced by the quick-view form; FEAT-01 already provides the backing
Vehicle lookup and table relationships. Anand Singh confirmed on 2026-08-16 that
table-level forms and views ship with Core while Apps contains only app-shell
components such as model-driven app definitions and site maps.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-007 | DES-03-CMP-001, DES-03-CMP-005, DES-03-CMP-009, DES-03-CMP-011 |
| INTK-0001-REQ-008 | DES-03-CMP-005 |
| INTK-0001-REQ-009 | DES-03-CMP-003, DES-03-CMP-005 |
| INTK-0001-REQ-010 | DES-03-CMP-006, DES-03-CMP-007, DES-03-CMP-008 |
| INTK-0001-REQ-011 | DES-03-CMP-002, DES-03-CMP-004, DES-03-CMP-005, DES-03-CMP-009, DES-03-CMP-010 |
| INTK-0001-REQ-012 | DES-03-CMP-002, DES-03-CMP-004, DES-03-CMP-005, DES-03-CMP-010 |
| INTK-0001-REQ-013 | DES-03-CMP-001, DES-03-CMP-005, DES-03-CMP-009, DES-03-CMP-011, DES-03-CMP-012, DES-03-CMP-013 |
| INTK-0001-REQ-014 | DES-03-CMP-004, DES-03-CMP-005 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-03-CMP-001 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-002 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-003 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-004 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-005 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-006 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-007 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-008 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-009 | config_audit | dataverse-security | repository_and_dataverse_environment | local_interactive | dataverse-environment-authoring |
| DES-03-CMP-010 | schema_derived_column | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-011 | schema_derived_column | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-012 | schema_derived_column | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-03-CMP-013 | schema_derived_column | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-03 | FEAT-03 | `5685339b5cf5c270ecd4e0caad82a5f0178a85e7531775ee9d4df111f7b3669b` | `55c31bfb5d694a25505e4088cec6aebb8b8fbd881bda092156778a6d28190c10` |
<!-- COMPILER:END provenance -->
