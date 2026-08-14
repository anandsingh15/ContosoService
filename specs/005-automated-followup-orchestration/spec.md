---
id: FEAT-05
slug: automated-followup-orchestration
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-030
- INTK-0001-REQ-031
- INTK-0001-REQ-032
- INTK-0001-REQ-033
- INTK-0001-REQ-034
- INTK-0001-REQ-042
- INTK-0001-REQ-043
- INTK-0001-REQ-044
repository_context_hash: 4c861280702113294a79dcc91e61fc43a33cc6c78440edfbb17ba7ea5fe4063e
spec_hash: 10c7b4ba7330a935db67e1688070f01a7adb7bfce972cd952db9173a46547267
status: reviewed
---

# FEAT-05 — Automated follow-up & orchestration

<!-- FILL:intent -->
When a maintenance job completes, the right things should happen on their own, reliably.
Completing a job updates the vehicle's last service date, returns a vehicle that was in
maintenance back to service while leaving vehicles in other states untouched, and raises
the appropriate follow-up work — a confirmation task every time, and an alert task when
the job was high or critical priority. That follow-up stays inside the maintenance
workspace where people already work. The automation is dependable by design: running it
twice does not double up, it never overwrites the very completion that triggered it, and
if it fails the failure is visible rather than silent.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- Updating the vehicle's last service date on completion (REQ-030).
- Returning an in-maintenance vehicle to service on completion while leaving vehicles in
  other states unchanged (REQ-031).
- Raising a confirmation task on completion (REQ-032) and an alert task for high or
  critical priority jobs (REQ-033).
- Keeping follow-up within the maintenance workspace (REQ-034).
- Follow-up that is idempotent (REQ-042), that never overwrites its own trigger (REQ-043),
  and whose failures are visible (REQ-044).

Out of scope:
- The completion rules that fire this follow-up (FEAT-04).
- The job, parts, and vehicle records themselves (FEAT-02, FEAT-03).
- The technology used to run the automation, which is a design-stage decision.
<!-- /FILL -->

## Actors

- **Coordinator** — receives and acts on the confirmation and alert follow-up tasks.
- **Technician** — sees the vehicle return to service and the follow-up appear in the
  maintenance workspace.
- **System (automation)** — performs the follow-up reliably and reports its own failures.

## Functional behaviour

- Completing a job updates the vehicle's last service date and, only for a vehicle that
  was in maintenance, returns it to service; vehicles in any other state are left as they
  are.
- Completion raises a confirmation task every time and, for high or critical priority
  jobs, an additional alert task, both surfaced inside the maintenance workspace.
- The follow-up is safe to repeat without creating duplicates, never writes back over the
  completion that triggered it, and makes any failure visible so it can be dealt with.

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-030 | Update last service date on completion | functional | Must |
| INTK-0001-REQ-031 | Return in-maintenance vehicle to service, leave others unchanged | functional | Must |
| INTK-0001-REQ-032 | Raise a confirmation task on completion | functional | Should |
| INTK-0001-REQ-033 | Alert task for high or critical priority jobs | functional | Should |
| INTK-0001-REQ-034 | Keep follow-up within the maintenance workspace | functional | Should |
| INTK-0001-REQ-042 | Idempotent follow-up automation | non-functional | Should |
| INTK-0001-REQ-043 | Automation must not overwrite its trigger | non-functional | Should |
| INTK-0001-REQ-044 | Visible failure for failed automation | functional | Should |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Record the last service date on completion
  Given a maintenance job being completed
  When the completion is applied
  Then the related vehicle's last service date is updated

Scenario: Return a serviced vehicle to service
  Given a completed job whose vehicle was in maintenance
  When the completion is applied
  Then the vehicle is returned to service

Scenario: Do not override another status
  Given a completed job whose vehicle is in a status other than in maintenance
  When the completion is applied
  Then the vehicle's status is left unchanged

Scenario: Confirm closure with a task
  Given a maintenance job being completed
  When the completion is applied
  Then a confirmation task is raised so the closure is visible in the workload

Scenario: Alert the owner of an urgent job
  Given a maintenance job being raised at high or critical priority
  When the job is created
  Then a task is created for the job owner carrying the vehicle and scheduling context

Scenario: Keep follow-up in one workspace
  Given automatic follow-up work and its tasks
  When they are created
  Then they remain inside the maintenance workspace

Scenario: Reprocess a completion event safely
  Given a completion event that has already been processed
  When the same event is processed again
  Then the outcome is unchanged and nothing is duplicated

Scenario: Preserve the triggering change
  Given a change that triggers follow-up automation
  When the automation runs
  Then it does not overwrite the change that triggered it

Scenario: Surface a failed follow-up action
  Given a follow-up action that fails
  When the failure occurs
  Then it is recorded as a visible task rather than failing silently
```
<!-- COMPILER:END scenarios -->

## Non-functional requirements

<!-- COMPILER:BEGIN nfr -->
| REQ | NFR |
| --- | --- |
<!-- COMPILER:END nfr -->

## Dependencies

<!-- COMPILER:BEGIN deps -->
| REQ | Depends on |
| --- | --- |
| INTK-0001-REQ-030 | INTK-0001-REQ-022, INTK-0001-REQ-001 |
| INTK-0001-REQ-031 | INTK-0001-REQ-022, INTK-0001-REQ-001 |
| INTK-0001-REQ-032 | INTK-0001-REQ-022 |
| INTK-0001-REQ-033 | INTK-0001-REQ-007, INTK-0001-REQ-016 |
| INTK-0001-REQ-034 | INTK-0001-REQ-032, INTK-0001-REQ-033 |
| INTK-0001-REQ-042 | INTK-0001-REQ-030, INTK-0001-REQ-031, INTK-0001-REQ-032 |
| INTK-0001-REQ-043 | INTK-0001-REQ-030, INTK-0001-REQ-031 |
| INTK-0001-REQ-044 | INTK-0001-REQ-030, INTK-0001-REQ-031, INTK-0001-REQ-032 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-030 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `a7ea563ce63dc4536ee60b47581b0c92c922b21b8f18ef6f88381879ec9c1ecf` |
| INTK-0001-REQ-031 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `ec1697f3ffb82516c66020b99540e878213c3342ea828dedfcd52bc7ea85a271` |
| INTK-0001-REQ-032 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `b7f26ab13177d495def55e76b2fdbb22b260a4bcd28b45b32902b895b7a9bef3` |
| INTK-0001-REQ-033 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `96edae2cb3130ad3911240203ee5cf04f8194d38c222c01b491a637dd6ecd700` |
| INTK-0001-REQ-034 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `6c41e67de6defc29af4661be1eb001428f4829b9483c5424b2695f5b5cf146e9` |
| INTK-0001-REQ-042 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `03c02440c427dc0c99ecd91800ceb23791d519272e51896a94a857687359e0c1` |
| INTK-0001-REQ-043 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `9c02a4ed93f3c3e5ae7935f995556dd39ddf3a84f9aa417231308e7757975fd0` |
| INTK-0001-REQ-044 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `020a11003a3231ccab1dc7a54b2d00a8da759e42851a4cf00c22ee07d5a723d3` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §4.4 Automatic follow-up (last service date, returning an
in-maintenance vehicle to service, the confirmation and alert tasks, and keeping follow-up
in the maintenance workspace) and §6 Non-Functional Expectations (idempotent automation,
not overwriting its trigger, and visible failure). Member requirements: REQ-030, REQ-031,
REQ-032, REQ-033, REQ-034, REQ-042, REQ-043, REQ-044. Depends on FEAT-04 for the
completion that triggers follow-up, and on FEAT-02 and FEAT-03 for the vehicle and job it
updates.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
None recorded for this feature. The FEAT-04 decision of 2026-08-11 that job completion is
final removes the earlier contingency about withdrawing follow-up when a job is reopened;
follow-up raised on completion therefore always stands.
<!-- /FILL -->
