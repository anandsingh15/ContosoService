---
id: FEAT-01
slug: fleet-data-foundation
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-015
- INTK-0001-REQ-016
- INTK-0001-REQ-017
- INTK-0001-REQ-018
- INTK-0001-REQ-019
- INTK-0001-REQ-020
- INTK-0001-REQ-021
- INTK-0001-REQ-040
- INTK-0001-REQ-041
- INTK-0001-REQ-046
repository_context_hash: 60a495cc06b3571a703577b4100554c52d5d4745fd0a69587ab4f6209b98bc04
spec_hash: 4e1f11c4626c930faee5cee074b710856595a8b7d3878ba555732f0528d7924a
status: reviewed
---

# FEAT-01 — Fleet data foundation

<!-- FILL:intent -->
Establish the shared, trustworthy data backbone that every other fleet-maintenance
capability depends on. This feature makes sure that the people, places, and reference
values used across maintenance are consistent, that records relate to each other the way
the real world does, that removing one record never silently corrupts related history,
that everyday finding of records is predictable, and that the whole thing stays fast and
reporting-ready at the fleet's real operating scale. It reuses the depot and technician
records the business already keeps rather than re-inventing them, and it constrains
reportable fields to agreed value lists so that reports are meaningful.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- Reusing the organisation's existing depot and technician records as the reference data
  for maintenance (REQ-015).
- Constraining reportable fields to agreed, controlled value lists (REQ-016).
- Modelling real relationships between records, with the correct one-to-many and
  many-to-one multiplicity (REQ-017, REQ-018).
- Defining deletion behaviour: dependent maintenance history is removed with its parent
  where that is intended (REQ-019), while shared reference records such as depots and
  technicians are preserved and their history kept intact when they are retired (REQ-020).
- Predictable search and retrieval by the identifiers people already know (REQ-021).
- Sustaining fleet scale without everyday screens degrading, and keeping lists and
  searches lean (REQ-040, REQ-041).
- Keeping the underlying data reporting-ready (REQ-046).
- Retaining completed maintenance history live for a defined window and archiving older
  records while keeping them reachable for reporting (decision 2026-08-11; see Open
  decisions).

Out of scope:
- The vehicle register and its behaviour (FEAT-02), maintenance jobs and parts (FEAT-03),
  job completion rules (FEAT-04), automatic follow-up (FEAT-05), and roles and the
  application shell (FEAT-06).
- Any choice of storage technology, platform, or implementation mechanism; those are
  design-stage decisions.
<!-- /FILL -->

## Actors

- **Coordinator** — relies on consistent reference data and reliable search when working
  across the fleet.
- **Technician** — finds vehicles, jobs, and history by known identifiers.
- **Reporting consumer** — depends on agreed value lists and reporting-ready data for
  meaningful analysis.

## Functional behaviour

- Depots and technicians already recorded by the business are reused as-is rather than
  re-entered, so maintenance references a single version of those records.
- Fields that appear in reports draw their values from agreed lists, so the same concept
  is never recorded in several inconsistent ways.
- Records carry real relationships with correct multiplicity, so a vehicle can have many
  jobs and a job can carry many parts, and each dependent record knows its parent.
- When a parent record is deleted, its dependent maintenance history is removed with it
  where that history has no independent meaning; conversely, retiring a shared depot or
  technician preserves the record and the history that references it.
- People can find records predictably using the identifiers they already know.

## Non-functional behaviour

- Everyday screens stay responsive at roughly 5,000 vehicles and 40,000 maintenance jobs
  per year (REQ-040).
- Lists and searches return results without scanning the entire fleet (REQ-041).
- Completed maintenance jobs and their parts remain live for 24 months, after which older
  completed records are archived out of everyday lists while staying reachable for history
  and reporting (decision 2026-08-11).

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-015 | Reuse existing depot and technician records | data | Must |
| INTK-0001-REQ-016 | Reportable values from agreed lists | data | Must |
| INTK-0001-REQ-017 | Real record relationships | data | Must |
| INTK-0001-REQ-018 | Relationship multiplicity | data | Must |
| INTK-0001-REQ-019 | Cascade delete of dependent history | data | Should |
| INTK-0001-REQ-020 | Preserve records when depot or technician removed | data | Should |
| INTK-0001-REQ-021 | Predictable search by known identifiers | functional | Should |
| INTK-0001-REQ-040 | Sustain fleet scale without degradation | non-functional | Must |
| INTK-0001-REQ-041 | Lean lists and searches | non-functional | Should |
| INTK-0001-REQ-046 | Reporting-ready data | data | Must |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Associate a vehicle with an existing depot
  Given the organisation's existing customer and contact records
  When a depot or technician is associated with fleet records
  Then it uses the existing customer or contact record rather than a new register

Scenario: Select a reportable value from an agreed list
  Given a vehicle status, job stage, or job priority
  When a user sets the value
  Then it is chosen from an agreed list rather than entered as free text

Scenario: Navigate between linked records
  Given related fleet records
  When a user follows a relationship
  Then it is a real link that navigates to an existing record and never points at something that no longer exists

Scenario: Relate assets, jobs, and parts
  Given depots, vehicles, jobs, parts, and technicians
  When their relationships are established
  Then a depot owns many vehicles, a vehicle has many jobs, a job consumes many parts, and a technician is assigned many jobs

Scenario: Remove a vehicle and its dependent history
  Given a vehicle with maintenance jobs and job parts
  When the vehicle is removed
  Then its maintenance jobs and their parts are removed with it

Scenario: Remove a depot without losing vehicles
  Given a depot associated with vehicles, or a technician associated with jobs
  When the depot or technician is removed
  Then the vehicle and job records survive and only the association is cleared

Scenario: Find records by quoted identifiers
  Given fleet vehicles, jobs, and parts
  When a user searches by vehicle name, registration, VIN, job number, or part number
  Then the matching records are found

Scenario: Hold performance at fleet scale
  Given a fleet of roughly five thousand vehicles and about forty thousand jobs a year
  When users work with the everyday screens
  Then the screens do not become slow at that scale

Scenario: Return results without scanning the whole fleet
  Given the full set of fleet records
  When a user runs a list or a search
  Then the result is returned without scanning the whole fleet

Scenario: Trust the data for reporting
  Given fleet records with consistent value lists and reliable relationships
  When reporting and analytics consume the data
  Then they can trust the values and relationships without additional cleansing
```
<!-- COMPILER:END scenarios -->

## Non-functional requirements

<!-- COMPILER:BEGIN nfr -->
| REQ | NFR |
| --- | --- |
| INTK-0001-REQ-040 | [{'metric': 'throughput', 'target': 'Sustain approximately 5,000 vehicles and 40,000 maintenance jobs per year without everyday screens becoming slow'}] |
| INTK-0001-REQ-041 | [{'metric': 'page_load', 'target': 'Lists and searches return results without scanning the whole fleet'}] |
<!-- COMPILER:END nfr -->

## Dependencies

<!-- COMPILER:BEGIN deps -->
| REQ | Depends on |
| --- | --- |
| INTK-0001-REQ-015 | — |
| INTK-0001-REQ-016 | — |
| INTK-0001-REQ-017 | — |
| INTK-0001-REQ-018 | INTK-0001-REQ-017 |
| INTK-0001-REQ-019 | INTK-0001-REQ-018 |
| INTK-0001-REQ-020 | INTK-0001-REQ-018 |
| INTK-0001-REQ-021 | — |
| INTK-0001-REQ-040 | — |
| INTK-0001-REQ-041 | — |
| INTK-0001-REQ-046 | INTK-0001-REQ-016, INTK-0001-REQ-017 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-015 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `33017e1e62686a66077e8f0fab417f3433c25ca60cd52b72e68f915046aad5a2` |
| INTK-0001-REQ-016 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `0085dd8d5ac92d9aa4c51e7eca327f432eb0817c799529029e66a2329b5365da` |
| INTK-0001-REQ-017 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `a6f6e8618e97f0c47094ddd8fb4b61daa5a8b5ef94e26e2f94500085edc8ca07` |
| INTK-0001-REQ-018 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `483ad4a8b51c1874013f7674b069ccef0419c3f0f2735ab0f59b73fcf8f0f5ef` |
| INTK-0001-REQ-019 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `186243a39d4409411a8d66b1e2867095183ae604760ea51863a16f156eed80ac` |
| INTK-0001-REQ-020 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `0f43a28d6109edc862e37eb3588b9cdf0857403d5cb6f6fb39aa2af18f7f808f` |
| INTK-0001-REQ-021 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `7cc61046de8da18dcbb613c95fbe32c7097d29790a1cbb7eac44f64a324224a2` |
| INTK-0001-REQ-040 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `3141c67072f6fbabf3146bbdce3faf2dc2d961e24a40f3da89e25879210e8518` |
| INTK-0001-REQ-041 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `e43501c6291707049c8ea157ff5f6d4057b99cc53077d12357b56829fd30d72d` |
| INTK-0001-REQ-046 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `066eb00282723aa6f85a0fcf6b40863dab45ac85765ef8d2a9e698cbe5640baf` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §3 Business Information Requirements (record shape, reference-data
reuse, value lists, relationships, multiplicity, deletion behaviour, and search) and
§6 Non-Functional Expectations (fleet-scale performance, lean lists, reporting-ready
data). Member requirements: REQ-015, REQ-016, REQ-017, REQ-018, REQ-019, REQ-020,
REQ-021, REQ-040, REQ-041, REQ-046. This feature is the foundation on which FEAT-02
through FEAT-06 build and has no upstream feature dependency.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
- [x] **Retention and archival of completed maintenance history.** Decided: Option B —
  completed maintenance jobs and their parts remain live for 24 months, after which older
  completed records are archived out of everyday working lists while remaining reachable
  for history-in-context (REQ-005) and reporting (REQ-046). This protects everyday
  performance at fleet scale (REQ-040, REQ-041). — decided by Jane Smith, Contoso Service
  Product Owner, 2026-08-11.
  - Note: the original INTK-0001 evidence is silent on retention, so this recorded Gate-2
    decision extends scope. It should be formalised as a requirement (with its own
    acceptance scenario) through a change-request intake, and Design (Stage 3) must
    implement the 24-month live window, the archival behaviour, and the route to reach
    archived history for reporting.
<!-- /FILL -->
