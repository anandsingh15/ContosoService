---
id: DES-05
status: reviewed
implements_feature: FEAT-05
source_spec_hash: f440eb5f381f844a006ed36a40758ea6a18d775f4c81a49a6b9c6c7e2a78c47a
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
plan_hash: 0fea55af3d489b30b0a79b420f106bd1bb9824654a20ec02719992afb2b3f5fe
---

# Design - FEAT-05 automated-followup-orchestration (DES-05)

FEAT-05 uses two solution-aware Dataverse cloud flows because completion follow-up
and urgent-job alerting are separate business events. Both flows remain inside the
current Dataverse environment, create standard Task rows assigned to the Maintenance
Job owner, and use durable markers, a unique follow-up key, atomic changesets, retries,
and visible failure Tasks. FEAT-02 owns Vehicle status, FEAT-03 owns Maintenance Job
data, FEAT-04 owns the authoritative completion transition, and FEAT-06 owns the final
application shell and security roles.

## Architecture decisions

<!-- FILL:decisions -->
### Material decisions (architect-confirmed 2026-08-19)

- **Two Dataverse cloud flows (selected by anand).** One Update-triggered flow
  handles the transition to Maintenance Job stage 74880 (Completed); one Create-
  triggered flow handles priority 74884 (High) or 74885 (Critical). This is the
  declarative-first choice for asynchronous orchestration. A synchronous plug-in was
  rejected because FEAT-04 already owns transactional completion enforcement and
  follow-up failures must not roll back that approved completion. Asynchronous plug-ins
  were rejected because they add code and registration without improving the required
  retry, failure-task, or task-orchestration behavior. Dataverse triggers support
  filtering columns and OData filter expressions, while Power Automate scopes, run-
  after paths, retries, and Terminate support explicit error handling:
  [Dataverse row trigger](https://learn.microsoft.com/power-automate/dataverse/create-update-delete-trigger)
  and [Power Automate error handling](https://learn.microsoft.com/power-automate/guidance/coding-guidelines/error-handling).
- **Standard Task with a custom Maintenance Job lookup (selected by anand).** The
  standard `task` table is reused and extended with `aks_maintenancejobid`, follow-up
  kind, and follow-up key metadata. Enabling native activities/Regarding on the current
  Maintenance Job table was rejected because that capability is irreversible and the
  registered table-update executor supports scoped column extension, not the table-
  capability mutation. A custom follow-up table was rejected because it would duplicate
  Task ownership, status, priority, and activity behavior. The standard Task table is a
  user-owned Dataverse activity with writable owner, priority, subject, description, and
  scheduling fields:
  [Task table reference](https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/task).
- **Durable idempotency (selected by anand).** Each Maintenance Job carries one marker
  for completion follow-up and one for urgent alert creation. Every generated Task has
  an immutable `aks_followupkey`, enforced by alternate key. Trigger concurrency is one;
  each flow checks its marker and key before acting. Successful business writes and the
  marker update execute in one Dataverse changeset, so a failed member rolls back the
  group. Duplicate-key recovery re-reads the existing Task and marker and exits as an
  idempotent success rather than creating another Task. Query-before-create alone was
  rejected because it cannot prevent a duplicate-trigger race. Microsoft documents
  changesets as atomic and documents trigger concurrency controls:
  [Dataverse changesets](https://learn.microsoft.com/power-automate/dataverse/change-set)
  and [Optimize Power Automate triggers](https://learn.microsoft.com/power-automate/guidance/coding-guidelines/optimize-power-automate-triggers#use-trigger-concurrency-control).
- **Maintenance Job owner assignment (selected by anand).** Confirmation, urgent-alert,
  and failure Tasks use the triggering job's `ownerid`. This directly implements the
  job-owner wording of REQ-033 and avoids inventing a Coordinator team before FEAT-06
  defines exact security identities. FEAT-06 roles and app shell may broaden visibility,
  but they do not change the canonical Task owner selected here.
- **Date-only service history (selected by anand).** Vehicle
  `aks_lastservicedate` is a Date Only column populated from the completed job's
  `aks_completeddate` calendar date. A user-local timestamp was rejected because the
  requirement names a service date rather than a service instant.

### Decision axes

1. **logic_tier - Low-code orchestration.** Two solution-aware cloud flows perform the
   asynchronous cross-row updates and Task creation. FEAT-04 remains the synchronous
   pro-code integrity boundary. Declarative table metadata, alternate key, relationship,
   view, and connection reference support the flows.
2. **data_residency - Dataverse-native.** Vehicle, Maintenance Job, standard Task,
   markers, and flow state remain in the registered Dataverse environment. No business
   or telemetry data is copied to another store.
3. **alm_boundary - Segmented custom solutions.** Table extensions, relationship, key,
   and Task view route through the compiler to `ContosoServiceCore`; the two flows and
   one Dataverse connection reference route to `ContosoServiceAutomation`. Publisher
   and target metadata come only from `.d365/authoring-targets.yml`; export and
   promotion remain external-pipeline concerns.
4. **security - Existing owner and least privilege.** Flows bind to an embedded
   Dataverse connection reference, operate only on the triggering job, its related
   Vehicle, and generated Tasks, and assign every Task to the job owner. No elevated
   custom API or external credential is introduced. FEAT-06 must grant its roles the
   least privileges needed for these existing tables and the new columns.
5. **integration - Current-environment Dataverse connector only.** No external API or
   custom connector is introduced. Both flows reuse one solution-aware connection
   reference for `shared_commondataserviceforapps`.
6. **environment - Registered authoring environment only.** Every component uses the
   compiler-resolved implementation scope, resource route, and authoring target.
   Concrete connections remain environment-bound deployment configuration and are not
   stored in this plan.
7. **ux_surface - Shared maintenance follow-up Task view.** A public Task view exposes
   open automated follow-up work by subject, kind, job, owner, priority, due date, and
   status. FEAT-06 owns placement of that view in the final model-driven app shell;
   FEAT-05 owns the Task data and reusable view, not app navigation.
8. **observability - Flow run history, durable failure Tasks, and Dataverse audit.**
   Run history provides action outcomes and correlation; catch scopes upsert a visible
   failure Task and terminate the run as Failed. Existing core-table auditing is reused,
   with new business and orchestration columns audit-enabled. Details are in
   Observability.
9. **batch_processing - Event driven, no batch.** Both flows respond to precise row
   events. There is no schedule, polling loop, or reconciliation batch. Sequential
   trigger execution is selected for idempotency, not batch processing.
10. **reporting - Operational view only.** The Task view supports day-to-day follow-up;
    no dashboard, chart, semantic model, or Power BI report is required.

### Additional strategies

- **AI:** None. No requirement needs generation, classification, prediction, or an AI
  service.
- **Testing:** Validate metadata and alternate-key activation first. For the completion
  flow, test Vehicle last-service date, conditional In maintenance to Active transition,
  preservation of every other Vehicle status, one confirmation Task, duplicate delivery,
  partial-action rollback, duplicate-key recovery, and visible failure Task. For the
  urgent flow, test High, Critical, non-urgent, duplicate delivery, owner assignment,
  vehicle/schedule context, and failure handling. Verify trigger filters prevent marker
  updates from retriggering completion, both flows use the embedded connection reference,
  and the public view returns only open follow-up Tasks.
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-05-CMP-001
    component_type: schema_table
    name: Vehicle service-date extension
    schema_name: aks_vehicle
    table: aks_vehicle
    operation: extend
    ownership: user_team
    primary_name: aks_name
    columns:
      - name: aks_lastservicedate
        data_type: DateTime
        date_time_behavior: DateOnly
        required_level: optional
        auditing: enabled
    satisfies: [INTK-0001-REQ-030]
  - id: DES-05-CMP-002
    component_type: schema_table
    name: Maintenance Job follow-up state extension
    schema_name: aks_maintenancejob
    table: aks_maintenancejob
    operation: extend
    ownership: user_team
    primary_name: aks_name
    columns:
      - name: aks_completionfollowupcompleted
        data_type: Boolean
        required_level: optional
        default: false
        auditing: enabled
      - name: aks_urgentalertcreated
        data_type: Boolean
        required_level: optional
        default: false
        auditing: enabled
    satisfies: [INTK-0001-REQ-042, INTK-0001-REQ-043]
  - id: DES-05-CMP-003
    component_type: schema_table
    name: Task follow-up metadata extension
    schema_name: task
    table: task
    operation: extend
    ownership: user_team
    primary_name: subject
    columns:
      - name: aks_followupkey
        data_type: Text
        max_length: 200
        required_level: optional
        auditing: enabled
      - name: aks_followupkind
        data_type: Text
        max_length: 32
        required_level: optional
        allowed_values: [confirmation, urgent_alert, automation_failure]
        auditing: enabled
    satisfies: [INTK-0001-REQ-032, INTK-0001-REQ-033, INTK-0001-REQ-034, INTK-0001-REQ-042, INTK-0001-REQ-044]
  - id: DES-05-CMP-004
    component_type: schema_relationship
    name: aks_maintenancejob_task
    schema_name: aks_maintenancejob_task
    table: aks_maintenancejob
    relationship_type: one_to_many
    related_table: task
    lookup_column: aks_maintenancejobid
    referenced_attribute: aks_maintenancejobid
    required_level: optional
    cascade_configuration:
      Assign: Cascade
      Delete: Restrict
      Merge: NoCascade
      Reparent: Cascade
      Share: Cascade
      Unshare: Cascade
    satisfies: [INTK-0001-REQ-032, INTK-0001-REQ-033, INTK-0001-REQ-034, INTK-0001-REQ-044]
  - id: DES-05-CMP-005
    component_type: schema_key
    name: aks_task_followup_key
    schema_name: aks_task_followup_key
    table: task
    key_columns: [aks_followupkey]
    depends_on: [DES-05-CMP-003]
    satisfies: [INTK-0001-REQ-042]
  - id: DES-05-CMP-006
    component_type: uiux_view
    name: Open Maintenance Follow-up Tasks
    schema_name: aks_openmaintenancefollowuptasks
    table: task
    view_type: public
    columns: [subject, aks_followupkind, aks_maintenancejobid, ownerid, prioritycode, scheduledend, statuscode]
    filters:
      - {column: aks_followupkey, operator: not-null}
      - {column: statecode, operator: eq, value: 0}
    sorts:
      - {column: prioritycode, descending: true}
      - {column: createdon, descending: false}
    depends_on: [DES-05-CMP-003, DES-05-CMP-004]
    satisfies: [INTK-0001-REQ-032, INTK-0001-REQ-033, INTK-0001-REQ-034, INTK-0001-REQ-044]
  - id: DES-05-CMP-007
    component_type: integ_connection_ref
    name: Dataverse - Automated follow-up
    schema_name: aks_DataverseAutomatedFollowUp
    connector: shared_commondataserviceforapps
    satisfies: [INTK-0001-REQ-030, INTK-0001-REQ-031, INTK-0001-REQ-032, INTK-0001-REQ-033, INTK-0001-REQ-042, INTK-0001-REQ-043, INTK-0001-REQ-044]
  - id: DES-05-CMP-008
    component_type: flow_cloud
    name: Process Maintenance Job Completion Follow-up
    schema_name: aks_ProcessMaintenanceJobCompletionFollowUp
    trigger:
      connector: shared_commondataserviceforapps
      connection_reference: aks_DataverseAutomatedFollowUp
      event: row_updated
      table: aks_maintenancejob
      scope: organization
      select_columns: [aks_stage]
      filter_rows: aks_stage eq 74880
      concurrency: 1
    actions:
      - exit succeeded when aks_completionfollowupcompleted is true
      - derive immutable follow-up keys from aks_maintenancejobid and event kind
      - read the related aks_vehicle and any existing task by aks_followupkey
      - reconcile an existing confirmation task and marker as idempotent success
      - when vehicle aks_status is 74874, perform one changeset that updates aks_lastservicedate and aks_status to 74873, creates the owner-assigned confirmation task, and sets aks_completionfollowupcompleted true
      - when vehicle aks_status is not 74874, perform one changeset that updates only aks_lastservicedate, creates the owner-assigned confirmation task, and sets aks_completionfollowupcompleted true
      - retry transient Dataverse actions with exponential backoff
      - on failure or timeout, upsert one owner-assigned automation_failure task by failure key with sanitized flow-run correlation and terminate Failed
    depends_on: [DES-05-CMP-001, DES-05-CMP-002, DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-005, DES-05-CMP-007]
    satisfies: [INTK-0001-REQ-030, INTK-0001-REQ-031, INTK-0001-REQ-032, INTK-0001-REQ-034, INTK-0001-REQ-042, INTK-0001-REQ-043, INTK-0001-REQ-044]
  - id: DES-05-CMP-009
    component_type: flow_cloud
    name: Create Urgent Maintenance Job Alert
    schema_name: aks_CreateUrgentMaintenanceJobAlert
    trigger:
      connector: shared_commondataserviceforapps
      connection_reference: aks_DataverseAutomatedFollowUp
      event: row_added
      table: aks_maintenancejob
      scope: organization
      filter_rows: aks_priority eq 74884 or aks_priority eq 74885
      concurrency: 1
    actions:
      - exit succeeded when aks_urgentalertcreated is true
      - derive immutable urgent-alert and failure keys from aks_maintenancejobid
      - read any existing task by aks_followupkey and reconcile its marker as idempotent success
      - perform one changeset that creates a High-priority owner-assigned urgent_alert task carrying vehicle and scheduled-date context and sets aks_urgentalertcreated true
      - retry transient Dataverse actions with exponential backoff
      - on failure or timeout, upsert one owner-assigned automation_failure task by failure key with sanitized flow-run correlation and terminate Failed
    depends_on: [DES-05-CMP-002, DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-005, DES-05-CMP-007]
    satisfies: [INTK-0001-REQ-033, INTK-0001-REQ-034, INTK-0001-REQ-042, INTK-0001-REQ-044]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-05 uses Power Automate run history, durable Dataverse Tasks, and existing
Dataverse audit. It adds no Azure telemetry sink.

- **Events.** Each flow records trigger accepted, marker skip, existing-key
  reconciliation, changeset success, retry, catch entry, failure-Task upsert, and final
  outcome through normal run history. Events include the flow/run correlation and stable
  rule code but exclude Vehicle registration, job number, free text, and user content.
- **Metrics.** Operations derives completion-follow-up successes, urgent-alert successes,
  idempotent skips, retries, failed runs, and open automation-failure Tasks from flow run
  history and the shared Task view. The requirements set no numeric latency, throughput,
  or availability target, so the design does not invent one.
- **Traces.** `workflow().run.name` correlates a failed run with its failure Task. The
  Task stores only sanitized correlation and category; authorized operators use the
  `aks_maintenancejobid` lookup to inspect business context in Dataverse.
- **Alerts.** An unhandled action failure or timeout upserts a single open
  `automation_failure` Task assigned to the job owner and then terminates the run as
  Failed. Native Power Automate owner notifications remain a secondary signal for
  broken connections or suspended flows. Repeated open failure Tasks require operator
  investigation; no ungrounded paging threshold is introduced.
- **Audit.** Reuse `Contoso Service core-table auditing` from DES-01 for Vehicle and
  Maintenance Job changes. New `aks_lastservicedate`, marker, Task key, Task kind, and
  Job lookup metadata are audit-enabled. Keys, marker values, flow correlation, and
  status are operational metadata; no secrets or copied customer content are logged.
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
None. On 2026-08-19, anand selected two Dataverse cloud flows, a custom Maintenance
Job lookup on standard Task, marker-plus-key idempotency with atomic changesets,
Maintenance Job owner assignment for all generated Tasks, and Date Only storage for
Vehicle last service date. FEAT-06 remains responsible for security-role privileges and
placing the reusable Task view in the final app shell; it does not reopen these FEAT-05
component identities or behaviors.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-030 | DES-05-CMP-001, DES-05-CMP-007, DES-05-CMP-008 |
| INTK-0001-REQ-031 | DES-05-CMP-007, DES-05-CMP-008 |
| INTK-0001-REQ-032 | DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-006, DES-05-CMP-007, DES-05-CMP-008 |
| INTK-0001-REQ-033 | DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-006, DES-05-CMP-007, DES-05-CMP-009 |
| INTK-0001-REQ-034 | DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-006, DES-05-CMP-008, DES-05-CMP-009 |
| INTK-0001-REQ-042 | DES-05-CMP-002, DES-05-CMP-003, DES-05-CMP-005, DES-05-CMP-007, DES-05-CMP-008, DES-05-CMP-009 |
| INTK-0001-REQ-043 | DES-05-CMP-002, DES-05-CMP-007, DES-05-CMP-008 |
| INTK-0001-REQ-044 | DES-05-CMP-003, DES-05-CMP-004, DES-05-CMP-006, DES-05-CMP-007, DES-05-CMP-008, DES-05-CMP-009 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-05-CMP-001 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-002 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-003 | schema_table | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-004 | schema_relationship | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-005 | schema_key | dataverse-table | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-006 | uiux_view | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
| DES-05-CMP-007 | integ_connection_ref | integration-wiring | repository_and_dataverse_solution | local_interactive | automation-solution-target |
| DES-05-CMP-008 | flow_cloud | power-automate-flow | repository_and_dataverse_solution | local_interactive | automation-solution-target |
| DES-05-CMP-009 | flow_cloud | power-automate-flow | repository_and_dataverse_solution | local_interactive | automation-solution-target |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-05 | FEAT-05 | `f440eb5f381f844a006ed36a40758ea6a18d775f4c81a49a6b9c6c7e2a78c47a` | `60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04` |
<!-- COMPILER:END provenance -->
