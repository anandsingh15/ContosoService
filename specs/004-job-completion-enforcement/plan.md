---
id: DES-04
status: reviewed
implements_feature: FEAT-04
source_spec_hash: 06b93f1af140e588ddcec9956cd29b8bd17fa2495529d45ada3d9714d680a60c
repository_context_hash: c95e3a189999b2566c41aab8ee206e51e15c1308a2c36a4fb4aa0aa21bfce66f
plan_hash: b58c608d5dc64317a068b36a98cd443356352f9ece3a566e8484c1af7aa8da08
---

# Design - FEAT-04 job-completion-enforcement (DES-04)

FEAT-04 makes Maintenance Job completion a server-enforced state transition and
adds immediate model-driven form guidance. The server remains authoritative for
every caller; the client script improves feedback but is never a security or
integrity boundary. FEAT-03 owns the Maintenance Job form and job/part schema,
FEAT-02 owns vehicle status and roadworthiness, and FEAT-01 owns the global
stage and vehicle-status choices.

## Architecture decisions

<!-- FILL:decisions -->
### Material decision (architect-confirmed 2026-08-18)

- **Completion enforcement - synchronous plug-in plus form script (Option A).**
  Anand Singh selected a synchronous Dataverse plug-in for all-route, atomic
  enforcement and a JavaScript form library for early guidance on 2026-08-18.
  One stateless plug-in type uses PreOperation steps so it can reject invalid
  requests and default `aks_completeddate` within the same database transaction.
  The form library uses supported Client API events to warn as soon as relevant
  values change and to block an invalid new-job scheduled date before save.
  A plug-in-only option was rejected because it would not warn before save as
  required by REQ-027 and REQ-028. Declarative business rules and form logic
  alone were rejected because they cannot authoritatively query the related
  Vehicle and Job Part rows or govern imports, integrations, and automation.
  A custom completion API was rejected because direct table updates must still
  be guarded, so it would add another entry point without removing the plug-in.
  *Grounding:* synchronous plug-in exceptions cancel and roll back an operation,
  `InvalidPluginExecutionException` controls the user-facing rejection message,
  and PreOperation runs within the transaction and can change input values:
  [Handle exceptions in plug-ins](https://learn.microsoft.com/power-apps/developer/data-platform/handle-exceptions)
  and [Event framework](https://learn.microsoft.com/power-apps/developer/data-platform/event-framework#event-execution-pipeline).
  Model-driven forms support OnLoad, OnSave, and column OnChange handlers, and
  OnSave can cancel a save with `preventDefault`:
  [Form OnSave event](https://learn.microsoft.com/power-apps/developer/model-driven-apps/clientapi/reference/events/form-onsave)
  and [Configure form event handlers](https://learn.microsoft.com/power-apps/maker/model-driven-apps/configure-event-handlers-legacy).

### Decision axes

1. **logic_tier - Pro-code with a declarative form registration.** A synchronous
   .NET plug-in is required for related-row validation, transactionality, and
   enforcement across every Dataverse route. A JavaScript web resource is
   required for the related-Vehicle warning before save. The existing form owns
   declarative event registration. Business rules are not authoritative because
   the rules depend on related Vehicle and Job Part rows and must apply outside
   model-driven forms.
2. **data_residency - Dataverse-native.** The plug-in reads only the current
   Maintenance Job, its related Vehicle, and whether at least one related Job
   Part exists. It mutates only the in-flight Maintenance Job target. No data is
   copied outside Dataverse, and the form queries only the selected Vehicle.
3. **alm_boundary - Segmented custom solutions.** The plug-in assembly, type,
   steps, and image route to `ContosoServicePluginAndCustomApi`; the JavaScript
   resource routes to `ContosoServiceWebResource`; and the existing Maintenance
   Job main-form update routes to `ContosoServiceCore`. Publisher `AnandPOC` and
   prefix `aks` come from `.d365/authoring-targets.yml`. Export and promotion
   remain external-pipeline concerns.
4. **security - Calling-user context and existing privileges.** Both plug-in
   steps run as the calling user and use no elevation. Existing FEAT-06 roles
   govern Maintenance Job writes and related Vehicle/Job Part reads. The client
   script is guidance only; server-side enforcement cannot be bypassed by hiding
   fields, disabling JavaScript, importing data, or calling the API directly.
5. **integration - No external integration.** No connector, custom API, outbound
   call, or external system is introduced. Existing integrations and automated
   processes receive the same Dataverse validation error as every other caller.
6. **environment - Registered authoring environment only.** Dataverse-bound
   components use compiler-resolved targets and interactive-user authentication.
   Development must pin the currently unconfigured .NET SDK and Dataverse SDK
   tool versions before execution; Design does not invent those versions.
7. **ux_surface - Existing model-driven Maintenance Job main form.** The script
   warns immediately when a selected Vehicle is not roadworthy or is retired,
   prompts when Completed requires a completion date, and flags a past scheduled
   date on a new job. The OnSave handler synchronously blocks the same-row past-
   date violation with an understandable form notification. Server rejection
   remains the final message for related-record and non-form violations.
8. **observability - Plug-in tracing plus existing Dataverse audit.** The plug-in
   traces the operation, stage, correlation ID, evaluated rule names, and outcome
   without customer values. DES-02 and DES-03 already audit Vehicle status and
   roadworthiness plus Maintenance Job stage, schedule, and completion date, so
   no duplicate audit component is created. Details are in Observability.
9. **batch_processing - None.** Validation is synchronous per Create or Update;
   there is no scheduled reconciliation, flow, or batch process.
10. **reporting - No new reporting component.** Existing audited columns and
    operational views remain queryable. This feature adds enforcement behavior,
    not a dashboard, chart, dataset, or report.

### Additional strategies

- **AI:** None. The feature has no AI requirement or grounded capability need.
- **Testing:** Unit-test the plug-in offline with a Dataverse fake execution
  context for valid completion, each failed precondition, automatic completion
  date, supplied date preservation, initial completion, past scheduling, final
  state/reopen rejection, irrelevant updates, and atomic failure. Unit-test the
  JavaScript with mocked model-driven Client API contexts for vehicle, stage,
  date, notifications, and save cancellation. In Dataverse, verify the registered
  steps, image, form library, handlers, clear messages, audit entries, and equal
  behavior through the form, import, Web API, and automation routes.
<!-- /FILL -->

## Components

<!-- FILL:components -->
```yaml
components:
  - id: DES-04-CMP-001
    component_type: code_plugin
    name: Maintenance Job completion enforcement
    schema_name: ContosoService.Plugins.MaintenanceJobCompletionPlugin
    assembly: ContosoService.Plugins
    class_name: ContosoService.Plugins.MaintenanceJobCompletionPlugin
    steps:
      - name: Maintenance Job Create completion and schedule guard
        message: Create
        table: aks_maintenancejob
        stage: PreOperation
        mode: Synchronous
        rank: 10
        run_as: Calling User
        behavior:
          - reject aks_scheduleddate earlier than the current date
          - reject initial aks_stage 74880 (Completed) because a new job cannot yet have a related aks_jobpart
      - name: Maintenance Job Update completion and final-state guard
        message: Update
        table: aks_maintenancejob
        stage: PreOperation
        mode: Synchronous
        rank: 10
        filtering_attributes: [aks_stage]
        run_as: Calling User
        pre_image:
          alias: PreImage
          columns: [aks_stage, aks_completeddate, aks_scheduleddate, aks_vehicleid]
        behavior:
          - merge Target with PreImage to evaluate the effective row
          - reject transition to 74880 (Completed) unless the related aks_vehicle is roadworthy, not 74876 (Retired), and at least one related aks_jobpart exists
          - when entering Completed without aks_completeddate, set aks_completeddate from an injected UTC clock
          - reject any transition from 74880 (Completed) to another stage
    satisfies: [INTK-0001-REQ-022, INTK-0001-REQ-023, INTK-0001-REQ-024, INTK-0001-REQ-025, INTK-0001-REQ-026, INTK-0001-REQ-029, INTK-0001-REQ-045]
  - id: DES-04-CMP-002
    component_type: code_webres_js
    name: aks_/scripts/maintenance_job_form.js
    schema_name: aks_/scripts/maintenance_job_form.js
    source_path: scripts/maintenance_job_form.js
    namespace: Contoso.MaintenanceJobForm
    handlers:
      - event: OnLoad
        function: Contoso.MaintenanceJobForm.onLoad
        pass_execution_context: true
      - event: aks_vehicleid.OnChange
        function: Contoso.MaintenanceJobForm.onVehicleChange
        pass_execution_context: true
      - event: aks_stage.OnChange
        function: Contoso.MaintenanceJobForm.onStageChange
        pass_execution_context: true
      - event: aks_scheduleddate.OnChange
        function: Contoso.MaintenanceJobForm.onScheduledDateChange
        pass_execution_context: true
      - event: OnSave
        function: Contoso.MaintenanceJobForm.onSave
        pass_execution_context: true
    behavior:
      - use the supported Xrm WebApi to read aks_status and aks_roadworthy for the selected vehicle
      - show and clear stable form notifications for non-roadworthy or retired vehicles
      - prompt immediately when stage 74880 (Completed) has no completion date
      - flag a past scheduled date on a new job and synchronously cancel save until corrected
    satisfies: [INTK-0001-REQ-027, INTK-0001-REQ-028, INTK-0001-REQ-029, INTK-0001-REQ-045]
  - id: DES-04-CMP-003
    component_type: uiux_form
    name: Maintenance Job - Main completion handlers
    schema_name: aks_maintenancejob_main
    table: aks_maintenancejob
    form_type: main
    sections:
      - name: existing_feat03_layout
        fields: [aks_jobnumber, aks_stage, aks_priority, aks_vehicleid, ownerid, aks_technicianid, aks_scheduleddate, aks_completeddate, aks_labourhours, aks_hourlyrate, aks_labourcost, aks_totalpartscost, aks_totalcost]
        change: preserve all existing header, job details, vehicle context, labour and totals, and parts-used controls
        library: aks_/scripts/maintenance_job_form.js
        handlers:
          - OnLoad: Contoso.MaintenanceJobForm.onLoad
          - aks_vehicleid.OnChange: Contoso.MaintenanceJobForm.onVehicleChange
          - aks_stage.OnChange: Contoso.MaintenanceJobForm.onStageChange
          - aks_scheduleddate.OnChange: Contoso.MaintenanceJobForm.onScheduledDateChange
          - OnSave: Contoso.MaintenanceJobForm.onSave
        pass_execution_context: true
    depends_on: [DES-04-CMP-002]
    satisfies: [INTK-0001-REQ-027, INTK-0001-REQ-028, INTK-0001-REQ-029, INTK-0001-REQ-045]
```
<!-- /FILL -->

## Observability

<!-- FILL:observability -->
FEAT-04 uses Dataverse-native tracing and audit; it adds no Azure telemetry sink.

- **Events.** Each plug-in invocation emits sanitized trace events for start,
  short-circuit, rule rejection, completion-date default, and success. Traces
  identify the component, message, pipeline stage, rule code, and outcome, but
  never Vehicle, Job, Part, date, or user values.
- **Metrics.** Operational review derives counts of successful completions,
  rejected completions by rule code, reopen attempts, past-date rejections, and
  plug-in failures from Plugin Trace Log during support windows. No numeric NFR
  target is specified, so no synthetic SLA is introduced.
- **Traces.** The Dataverse correlation ID joins the plug-in trace to the
  originating platform operation. Maintenance Job ID and customer content are
  omitted from trace text; authorized support staff correlate row history using
  Dataverse audit and the platform operation context.
- **Alerts.** Operations investigates any unexpected plug-in exception and a
  repeated rejection pattern that indicates an integration is submitting invalid
  transitions. Expected business-rule rejections remain user feedback, not
  paging alerts. Alert thresholds are an operations-policy concern because the
  source requirements define no volume or latency target.
- **Audit.** Reuse `Contoso Service core-table auditing`: DES-02 covers
  `aks_vehicle.aks_status` and `aks_vehicle.aks_roadworthy`; DES-03 covers
  `aks_maintenancejob.aks_stage`, `aks_scheduleddate`, and
  `aks_completeddate`. Audit proves the before/after business state while trace
  proves which enforcement path ran. Neither surface records secrets or copied
  customer content.
<!-- /FILL -->

## Open questions

<!-- FILL:open-questions -->
None. Anand Singh selected the synchronous plug-in plus form-script architecture
on 2026-08-18. Jane Smith's reviewed FEAT-04 decision that completed jobs are
final and corrections require a new job remains authoritative. The server uses
one cohesive plug-in type with two PreOperation registrations: Create covers new-
job scheduling and attempted initial completion, while Update covers completion
transitions and prevents reopening. Before Development execution, the registered
resource contract must supply the pinned .NET and Dataverse SDK tool versions;
this is an execution prerequisite, not an unresolved architecture decision.
<!-- /FILL -->

## Requirement coverage

<!-- COMPILER:BEGIN coverage -->
| REQ | Components |
| --- | --- |
| INTK-0001-REQ-022 | DES-04-CMP-001 |
| INTK-0001-REQ-023 | DES-04-CMP-001 |
| INTK-0001-REQ-024 | DES-04-CMP-001 |
| INTK-0001-REQ-025 | DES-04-CMP-001 |
| INTK-0001-REQ-026 | DES-04-CMP-001 |
| INTK-0001-REQ-027 | DES-04-CMP-002, DES-04-CMP-003 |
| INTK-0001-REQ-028 | DES-04-CMP-002, DES-04-CMP-003 |
| INTK-0001-REQ-029 | DES-04-CMP-001, DES-04-CMP-002, DES-04-CMP-003 |
| INTK-0001-REQ-045 | DES-04-CMP-001, DES-04-CMP-002, DES-04-CMP-003 |
<!-- COMPILER:END coverage -->

## Build skills and routing

<!-- COMPILER:BEGIN skills -->
| Component | Type | Build skill | Implementation scope | Execution host | Authoring target |
| --- | --- | --- | --- | --- | --- |
| DES-04-CMP-001 | code_plugin | dataverse-procode | repository_and_dataverse_solution | local_interactive | plugin-customapi-solution-target |
| DES-04-CMP-002 | code_webres_js | dataverse-procode | repository_and_dataverse_solution | local_interactive | webresource-solution-target |
| DES-04-CMP-003 | uiux_form | model-driven-ui | repository_and_dataverse_solution | local_interactive | core-solution-target |
<!-- COMPILER:END skills -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| Plan | Feature | Source spec SHA-256 | Repository context |
| --- | --- | --- | --- |
| DES-04 | FEAT-04 | `06b93f1af140e588ddcec9956cd29b8bd17fa2495529d45ada3d9714d680a60c` | `c95e3a189999b2566c41aab8ee206e51e15c1308a2c36a4fb4aa0aa21bfce66f` |
<!-- COMPILER:END provenance -->
