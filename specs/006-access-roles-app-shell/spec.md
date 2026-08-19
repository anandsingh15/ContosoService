---
id: FEAT-06
slug: access-roles-app-shell
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-035
- INTK-0001-REQ-036
- INTK-0001-REQ-037
- INTK-0001-REQ-038
- INTK-0001-REQ-039
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
spec_hash: 623bdc57184981e3900d11cc32a9a724e34bd7b1b8abbaf3f5267a882a0c8052
status: reviewed
---

# FEAT-06 — Access, roles & app shell

<!-- FILL:intent -->
Make sure the right people can do the right things, and give them one place to do it.
Three roles frame what people can do: a Coordinator who manages fleet operations records
across the business unit, a Technician who can read across the fleet but change only the
jobs assigned to them and the parts on those jobs, and a Reader with read-only access to
vehicles, jobs, and parts. Access is granted through team membership tied to the
organisation's existing group structure, so joiners and leavers are handled by normal
identity administration rather than manual permission changes. All of this is presented as
a single application with two clear areas, so people work in one coherent place.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- The Coordinator role and its full management rights across the business unit (REQ-035).
- The Technician role: read across the fleet, change only assigned jobs and their parts
  (REQ-036).
- The Reader role: read-only access to vehicles, jobs, and parts (REQ-037).
- Granting access through team membership tied to the existing group structure (REQ-038).
- A single application organised into two areas (REQ-039).

Out of scope:
- The records and behaviours the roles govern (FEAT-01 through FEAT-05).
- The specific security, identity, and application technologies used to realise the roles
  and the shell, which are design-stage decisions.
<!-- /FILL -->

## Actors

- **Coordinator** — full create, read, change, delete, assign, and share across the
  business unit.
- **Technician** — reads across the fleet; changes only the jobs assigned to them and the
  parts on those jobs.
- **Reader** — read-only across vehicles, jobs, and parts.
- **Identity administrator** — manages group membership, which drives access.

## Functional behaviour

- Each role grants exactly the access described, and users outside a role are refused the
  actions that role reserves.
- A person's access follows their team membership: joining a group grants access and
  leaving it withdraws access, without any manual permission change.
- The whole capability is presented as one application with two areas, so people move
  between fleet records and maintenance work in a single coherent place.

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-035 | Coordinator role | security | Must |
| INTK-0001-REQ-036 | Technician role | security | Must |
| INTK-0001-REQ-037 | Reader role | security | Must |
| INTK-0001-REQ-038 | Team-based access provisioning | security | Should |
| INTK-0001-REQ-039 | Single application with two areas | functional | Must |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Coordinator manages fleet records
  Given a user in the Coordinator role
  When they work with fleet operations records across the business unit
  Then they can create, read, change, delete, assign, and share those records

Scenario: Negative - non-coordinator is refused management actions
  Given a user who is not in the Coordinator role
  When they attempt to create or delete a fleet operations record
  Then the action is refused and the record is left unchanged

Scenario: Technician edits only assigned work
  Given a user in the Technician role
  When they work with fleet records
  Then they can read all fleet records in the business unit but change only the jobs assigned to them and the parts on those jobs

Scenario: Negative - technician is refused edits to unassigned work
  Given a user in the Technician role
  When they attempt to change a job that is not assigned to them
  Then the change is refused and the job is left unchanged

Scenario: Reader has read-only access
  Given a user in the Reader role
  When they access vehicles, jobs, and parts across the business unit
  Then they can read the records but cannot change them

Scenario: Negative - reader is refused any modification
  Given a user in the Reader role
  When they attempt to create, change, or delete a vehicle, job, or part
  Then the action is refused and the record is left unchanged

Scenario: Grant access through group membership
  Given the organisation's existing group structure
  When a user joins or leaves a group
  Then their fleet access changes through team membership without manual permission changes

Scenario: Negative - removed group member loses access
  Given a user whose access was granted through group membership
  When they are removed from the group in the identity system
  Then their fleet access is withdrawn and they can no longer open fleet records

Scenario: Work within one application
  Given a user in any of the three roles
  When they use the solution
  Then they work in a single application with a fleet operations area (vehicles, jobs, parts) and a customer area (depots, technicians)
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
| INTK-0001-REQ-035 | INTK-0001-REQ-001, INTK-0001-REQ-007, INTK-0001-REQ-011 |
| INTK-0001-REQ-036 | INTK-0001-REQ-007, INTK-0001-REQ-011 |
| INTK-0001-REQ-037 | INTK-0001-REQ-001, INTK-0001-REQ-007, INTK-0001-REQ-011 |
| INTK-0001-REQ-038 | INTK-0001-REQ-035, INTK-0001-REQ-036, INTK-0001-REQ-037 |
| INTK-0001-REQ-039 | INTK-0001-REQ-001, INTK-0001-REQ-007, INTK-0001-REQ-011, INTK-0001-REQ-015 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-035 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `4164d9752de06b0297e20ec3bbd631cec82496410cb90f0460864c7f65273773` |
| INTK-0001-REQ-036 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `4e6dd6060436800828ac2f1c7a09ea8dd8e90567277a7811e1658faf3b1d7dbf` |
| INTK-0001-REQ-037 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `7c6fd8207398c25fa2e29e8246fc081cf8c4f274403053b88f5373eeafaa7b9b` |
| INTK-0001-REQ-038 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `e125edf2b61195b77f9b85ca9bcd5657c85c26f08c1da1bc89edf902da40cfee` |
| INTK-0001-REQ-039 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `fc22d5831b59f2145c625e9062ac3db3fc0911bf942fffe1cdfce309c9ada0e4` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §5 Users and Access Requirements (the Coordinator, Technician, and
Reader roles, team-based access provisioning, and the single application with two areas).
Member requirements: REQ-035, REQ-036, REQ-037, REQ-038, REQ-039. Depends on FEAT-01,
FEAT-02, and FEAT-03 because roles and the application shell are defined over the records
and areas those features establish.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
None recorded for this feature.
<!-- /FILL -->
