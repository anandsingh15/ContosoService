---
id: FEAT-03
slug: maintenance-jobs-parts
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-007
- INTK-0001-REQ-008
- INTK-0001-REQ-009
- INTK-0001-REQ-010
- INTK-0001-REQ-011
- INTK-0001-REQ-012
- INTK-0001-REQ-013
- INTK-0001-REQ-014
repository_context_hash: c95e3a189999b2566c41aab8ee206e51e15c1308a2c36a4fb4aa0aa21bfce66f
spec_hash: 92d98edd5fb2946eb27fb4bca4fe0acdf9c261aac5452734d98605bc1f1f49fb
status: reviewed
---

# FEAT-03 — Maintenance jobs & parts

<!-- FILL:intent -->
Let Contoso Service raise and progress the maintenance work done on a vehicle, and record
the parts that work consumes. A maintenance job is a first-class record tied to its
vehicle, whose status is clear at a glance and whose header carries the vehicle details a
technician needs without leaving the job. Parts are recorded against the job, each part
line values itself, and the job rolls those lines up into a total parts cost; per the
2026-08-11 decision the job also carries labour (hours worked at an hourly rate), and the
job's total cost is parts plus labour. Everyday users can keep saved job lists so the work
they own is easy to return to.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- The maintenance job record and its relationship to the vehicle (REQ-007).
- A job header that shows status at a glance (REQ-008) and the vehicle details in context
  (REQ-009).
- Saved, reusable job lists (REQ-010).
- The job part record (REQ-011), the calculated value of each part line (REQ-012), the
  job's total parts cost (REQ-013), and entering parts directly on the job (REQ-014).
- Recording labour on the job as hours worked at an hourly rate, and composing the job's
  total cost as parts plus labour (decision 2026-08-11; see Open decisions).

Out of scope:
- The rules that govern completing a job and the guards around it (FEAT-04).
- Anything triggered automatically when a job completes (FEAT-05).
- Role-based access to jobs and parts (FEAT-06), and storage/platform choices.
<!-- /FILL -->

## Actors

- **Coordinator** — raises jobs, oversees progress across the fleet, and curates saved
  job lists.
- **Technician** — works the jobs assigned to them and records the parts they use.
- **Reader** — reviews jobs and their parts without changing them.

## Functional behaviour

- A maintenance job is raised against a specific vehicle and always knows which vehicle it
  belongs to.
- The job header communicates status at a glance and surfaces the vehicle details needed
  to work, without navigating away.
- Parts are entered directly on the job; each part line computes its own value, and the
  job totals its part lines into a parts cost. Per the 2026-08-11 decision the job also
  records labour as hours worked at an hourly rate, and the job's total cost is the sum of
  its parts cost and its labour cost.
- People can define and reuse saved lists of jobs that match how they work.

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-007 | Maintenance job record | data | Must |
| INTK-0001-REQ-008 | Job header shows status at a glance | functional | Should |
| INTK-0001-REQ-009 | Vehicle details on the job | functional | Should |
| INTK-0001-REQ-010 | Saved job lists | functional | Should |
| INTK-0001-REQ-011 | Job part record | data | Must |
| INTK-0001-REQ-012 | Calculated part line value | functional | Must |
| INTK-0001-REQ-013 | Job total parts cost | functional | Must |
| INTK-0001-REQ-014 | Enter parts on the job | functional | Should |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Record a maintenance job against a vehicle
  Given a vehicle that needs service work
  When a coordinator raises a maintenance job for it
  Then the job records the vehicle, its stage, its priority, and its scheduled and completed dates

Scenario: Understand a job's status at a glance
  Given an open maintenance job
  When a user views the record
  Then the job number, stage, and priority are shown at the top

Scenario: See vehicle details without leaving the job
  Given a maintenance job linked to a vehicle
  When a user views the job
  Then key details of the related vehicle are visible on the job itself

Scenario: Use saved job lists
  Given the set of maintenance jobs
  When a technician opens the saved job lists
  Then they can view active jobs, jobs assigned to them, and jobs of high or critical priority

Scenario: Record a part consumed on a job
  Given a maintenance job in progress
  When a technician records a part used on the job
  Then a job part captures the quantity used and the unit price

Scenario: Calculate a part line value
  Given a job part with a quantity and a unit price
  When the job part is saved
  Then the solution calculates its line value from the quantity and unit price

Scenario: Roll up parts cost to the job
  Given a maintenance job with one or more job parts
  When the job parts are recorded
  Then the job reflects the total cost of the parts consumed

Scenario: Add parts line by line on the job
  Given a technician working a maintenance job
  When they enter the parts used
  Then each part is added line by line on the job without opening a separate record
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
| INTK-0001-REQ-007 | INTK-0001-REQ-001, INTK-0001-REQ-016 |
| INTK-0001-REQ-008 | INTK-0001-REQ-007 |
| INTK-0001-REQ-009 | INTK-0001-REQ-007, INTK-0001-REQ-001 |
| INTK-0001-REQ-010 | INTK-0001-REQ-007, INTK-0001-REQ-016 |
| INTK-0001-REQ-011 | INTK-0001-REQ-007 |
| INTK-0001-REQ-012 | INTK-0001-REQ-011 |
| INTK-0001-REQ-013 | INTK-0001-REQ-012, INTK-0001-REQ-007 |
| INTK-0001-REQ-014 | INTK-0001-REQ-011, INTK-0001-REQ-007 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-007 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `91d744281964d3625cd381500edba4e8b5dd13638e1caa70bbf3f6a1cdee20b0` |
| INTK-0001-REQ-008 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `cb00565b48559eaf4b7173422acaafeb38e57ebd7e25594a1a7fcac34466bf68` |
| INTK-0001-REQ-009 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `841ccb8f2b287bf317a63d25f7a8bb01ee7f97c6dec2cd7a9cba57594e058dfe` |
| INTK-0001-REQ-010 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `cf872fca33088a24b3aac83de47898950568a7c3a3f8d2a58a8be229e2c2894a` |
| INTK-0001-REQ-011 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `34acac89fd20e6d99e905e65e61a29a665b9c775acd35674e1b12adebbfa3934` |
| INTK-0001-REQ-012 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `24c58a205b224455d65dc867f113c35bc1134755ff9127800e9573ce5eb2942a` |
| INTK-0001-REQ-013 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `d63ae99795e71005f6fb9087749814e3b15aa7d4b478fb52ca247691a119793b` |
| INTK-0001-REQ-014 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `7e4fcf73fa6176f075ec882fa95b4ac674180b30457da55130080907e9ca90d7` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §3 Business Information Requirements (the maintenance job record and
the job part record) and §4.2 Raising and progressing a maintenance job (status at a
glance, vehicle details on the job, saved job lists, calculated part line value, job total
parts cost, and entering parts on the job). Member requirements: REQ-007, REQ-008,
REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014. Depends on FEAT-01 for shared data
and relationships, and on FEAT-02 for the vehicle a job is raised against.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
- [x] **Does a job's cost include labour, or parts only?** Decided: Option B — the job's
  total cost includes labour in addition to parts. Labour is recorded on the job as hours
  worked at an hourly rate (labour cost = hours × hourly rate), and the job total = total
  parts cost (REQ-013) + labour cost. — decided by Jane Smith, Contoso Service Product
  Owner, 2026-08-11.
  - Note: the original INTK-0001 evidence describes a parts-only total (REQ-011–REQ-013),
    so this recorded Gate-2 decision extends scope. It should be formalised as a
    requirement (with its own acceptance scenario) through a change-request intake, and
    Design (Stage 3) must implement labour capture (hours, hourly rate) and the
    parts-plus-labour job total.
<!-- /FILL -->
