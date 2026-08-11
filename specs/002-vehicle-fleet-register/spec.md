---
id: FEAT-02
slug: vehicle-fleet-register
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-001
- INTK-0001-REQ-002
- INTK-0001-REQ-003
- INTK-0001-REQ-004
- INTK-0001-REQ-005
- INTK-0001-REQ-006
repository_context_hash: cf6012d358a3661b2cb5ebf82a8c61cb007ce45361da9d33f0e9ed9c780950bb
spec_hash: bce31c2b91c596d52ac059baa4cd69d8402400680cc0a82ec753ad84100c272d
status: reviewed
---

# FEAT-02 — Vehicle & fleet register

<!-- FILL:intent -->
Give Contoso Service a single, reliable register of the vehicles it maintains. Each
vehicle is a first-class record with a unique identity, quick to capture when a new
vehicle enters the fleet, and immediately informative when opened — its key facts and its
maintenance history are visible in context. People who work with the fleet every day can
keep their own saved lists so the vehicles that matter to them are one click away. This
register is the anchor that maintenance jobs, completion, follow-up, and access all hang
from.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- The vehicle asset record and the facts it holds (REQ-001).
- A unique, unambiguous identity for every vehicle so the same vehicle is never recorded
  twice (REQ-002).
- Fast capture of a new vehicle with the minimum needed to get started (REQ-003).
- Showing the key vehicle facts as soon as a vehicle is opened (REQ-004).
- Seeing a vehicle's maintenance history in context from the vehicle itself (REQ-005).
- Saved, reusable vehicle lists for everyday work (REQ-006).

Out of scope:
- The shared reference data and relationship rules that vehicles rely on (FEAT-01).
- Maintenance jobs and parts (FEAT-03) and everything downstream of them.
- Storage, platform, and implementation choices, which are design-stage decisions.
<!-- /FILL -->

## Actors

- **Coordinator** — registers vehicles, curates saved lists, and works across the whole
  fleet.
- **Technician** — opens a vehicle to see its key facts and history before or during work.
- **Reader** — browses the register and saved lists without changing anything.

## Functional behaviour

- A vehicle is captured quickly with the essential facts, and can be enriched later.
- Every vehicle carries a unique identity, so duplicates are prevented and each vehicle is
  addressable without ambiguity.
- Opening a vehicle immediately shows its key facts, so a person does not have to hunt for
  them.
- A vehicle's maintenance history is visible in context from the vehicle record, so its
  service story is understood at a glance.
- People can define and reuse saved lists of vehicles that match how they work.

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-001 | Vehicle asset record | data | Must |
| INTK-0001-REQ-002 | Unique vehicle identity | data | Must |
| INTK-0001-REQ-003 | Quick vehicle capture | functional | Should |
| INTK-0001-REQ-004 | Key vehicle facts visible on open | functional | Should |
| INTK-0001-REQ-005 | Maintenance history in context | functional | Should |
| INTK-0001-REQ-006 | Saved vehicle lists | functional | Should |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Register a vehicle with its core attributes
  Given a fleet asset that needs to be tracked
  When a coordinator creates its vehicle record
  Then the record stores the VIN, registration, current status, roadworthiness, and service history

Scenario: Prevent duplicate asset records
  Given a vehicle already recorded with a given VIN and registration
  When a user attempts to create another vehicle with the same VIN and registration
  Then the solution treats it as the same asset and does not create a duplicate record

Scenario: Quick-create a vehicle with minimal detail
  Given a coordinator capturing a new vehicle
  When they enter only the key identifiers
  Then the vehicle is created and the remaining details can be completed later

Scenario: See decisive vehicle facts at a glance
  Given an existing vehicle record
  When a user opens it
  Then its status, roadworthiness, and depot are visible without scrolling

Scenario: Review a vehicle's maintenance history
  Given a vehicle with prior maintenance jobs
  When a supervisor opens the vehicle record
  Then its maintenance history is shown in context on the record

Scenario: Use saved vehicle lists
  Given the fleet of vehicle records
  When a user opens the saved vehicle lists
  Then they can view all active vehicles, vehicles currently in maintenance, and vehicles grouped by depot
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
| INTK-0001-REQ-001 | INTK-0001-REQ-016 |
| INTK-0001-REQ-002 | INTK-0001-REQ-001 |
| INTK-0001-REQ-003 | INTK-0001-REQ-001 |
| INTK-0001-REQ-004 | INTK-0001-REQ-001 |
| INTK-0001-REQ-005 | INTK-0001-REQ-001 |
| INTK-0001-REQ-006 | INTK-0001-REQ-001, INTK-0001-REQ-016 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-001 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `7e19e0a4c0f7536c2484828c26e1f95124cb700e1c7c1213cc39f51f2aa1b297` |
| INTK-0001-REQ-002 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `b23c9a7125545346046a5611b391ffc88efa34f554265b8576920afc5555b9e5` |
| INTK-0001-REQ-003 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `c68edd3027ae1f3b712abec185e414febb08b1ee4a490ff07d3cec527d168e08` |
| INTK-0001-REQ-004 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `fbb11a6d491b431ab97441900cdb08119a2d1d1a7d5e1d9b0889b196133f11fe` |
| INTK-0001-REQ-005 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `8e593c99b284ccb0d2b9a97ac16311039d34652b90522458ac08a8dad8e69a15` |
| INTK-0001-REQ-006 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `861c96850bee6b22df7d3a075d13cacec647bc576f6010fbde8841cb79bf3ebb` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §3 Business Information Requirements (the vehicle asset record and
its unique identity) and §4.1 Recording and maintaining a vehicle (quick capture, key
facts on open, maintenance history in context, and saved vehicle lists). Member
requirements: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006. Depends on FEAT-01
for the shared reference data, relationships, and value lists the vehicle record uses.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
None recorded for this feature.
<!-- /FILL -->
