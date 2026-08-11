# INTK-0001 requirements

Generated index. Individual requirement files are authoritative.

Requirement groups are non-governing navigation. They do not replace atomic REQ provenance or determine epic/feature boundaries.

## Requirement group summary

| Order | Group | Capability or process | Atomic REQs |
| ---: | --- | --- | ---: |
| 1 | `INTK-0001-GRP-01` | Vehicle Asset Records | 6 |
| 2 | `INTK-0001-GRP-02` | Maintenance Job Management | 4 |
| 3 | `INTK-0001-GRP-03` | Parts Consumption and Costing | 4 |
| 4 | `INTK-0001-GRP-04` | Data Model Integrity and Relationships | 7 |
| 5 | `INTK-0001-GRP-05` | Job Completion Enforcement | 8 |
| 6 | `INTK-0001-GRP-06` | Automated Follow-up and Orchestration | 5 |
| 7 | `INTK-0001-GRP-07` | Users and Access | 5 |
| 8 | `INTK-0001-GRP-08` | Non-Functional Expectations | 7 |

## 1. Vehicle Asset Records (`INTK-0001-GRP-01`)

Capturing and maintaining fleet vehicle records — their identity, current condition, and service history — and the saved lists used to manage the fleet day to day.

**Atomic requirements:** 6

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.1 Recording and maintaining a vehicle

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-001](requirements/INTK-0001-REQ-001.md) | Vehicle asset record | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-002](requirements/INTK-0001-REQ-002.md) | Unique vehicle identity | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-003](requirements/INTK-0001-REQ-003.md) | Quick vehicle capture | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.1 Recording and maintaining a vehicle |
| [INTK-0001-REQ-004](requirements/INTK-0001-REQ-004.md) | Key vehicle facts visible on open | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.1 Recording and maintaining a vehicle |
| [INTK-0001-REQ-005](requirements/INTK-0001-REQ-005.md) | Maintenance history in context | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.1 Recording and maintaining a vehicle |
| [INTK-0001-REQ-006](requirements/INTK-0001-REQ-006.md) | Saved vehicle lists | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.1 Recording and maintaining a vehicle |

## 2. Maintenance Job Management (`INTK-0001-GRP-02`)

Raising, viewing, and progressing maintenance jobs against vehicles, and the saved lists that support daily job work.

**Atomic requirements:** 4

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-007](requirements/INTK-0001-REQ-007.md) | Maintenance job record | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-008](requirements/INTK-0001-REQ-008.md) | Job header shows status at a glance | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |
| [INTK-0001-REQ-009](requirements/INTK-0001-REQ-009.md) | Vehicle details on the job | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |
| [INTK-0001-REQ-010](requirements/INTK-0001-REQ-010.md) | Saved job lists | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |

## 3. Parts Consumption and Costing (`INTK-0001-GRP-03`)

Recording the parts consumed on a maintenance job and deriving the line value and job cost of those parts.

**Atomic requirements:** 4

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-011](requirements/INTK-0001-REQ-011.md) | Job part record | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-012](requirements/INTK-0001-REQ-012.md) | Calculated part line value | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |
| [INTK-0001-REQ-013](requirements/INTK-0001-REQ-013.md) | Job total parts cost | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |
| [INTK-0001-REQ-014](requirements/INTK-0001-REQ-014.md) | Enter parts on the job | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.2 Raising and progressing a maintenance job |

## 4. Data Model Integrity and Relationships (`INTK-0001-GRP-04`)

The value lists, real record links, relationship multiplicities, removal rules, and search that keep fleet information trustworthy and navigable.

**Atomic requirements:** 7

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-015](requirements/INTK-0001-REQ-015.md) | Reuse existing depot and technician records | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-016](requirements/INTK-0001-REQ-016.md) | Reportable values from agreed lists | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-017](requirements/INTK-0001-REQ-017.md) | Real record relationships | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-018](requirements/INTK-0001-REQ-018.md) | Relationship multiplicity | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-019](requirements/INTK-0001-REQ-019.md) | Cascade delete of dependent history | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-020](requirements/INTK-0001-REQ-020.md) | Preserve records when depot or technician removed | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |
| [INTK-0001-REQ-021](requirements/INTK-0001-REQ-021.md) | Predictable search by known identifiers | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §3 Business Information Requirements |

## 5. Job Completion Enforcement (`INTK-0001-GRP-05`)

The rules that govern when and how a maintenance job may be completed, enforced on every route into the system with clear feedback.

**Atomic requirements:** 8

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-022](requirements/INTK-0001-REQ-022.md) | Completion preconditions | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-023](requirements/INTK-0001-REQ-023.md) | Auto-record completion date | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-024](requirements/INTK-0001-REQ-024.md) | Enforce completion rules on every route | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-025](requirements/INTK-0001-REQ-025.md) | Reject invalid completion with a clear reason | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-026](requirements/INTK-0001-REQ-026.md) | Atomic completion | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-027](requirements/INTK-0001-REQ-027.md) | Early warning for non-roadworthy vehicle | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-028](requirements/INTK-0001-REQ-028.md) | Early warning when a stage needs a completion date | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |
| [INTK-0001-REQ-029](requirements/INTK-0001-REQ-029.md) | Prevent scheduling in the past | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.3 Completing a job |

## 6. Automated Follow-up and Orchestration (`INTK-0001-GRP-06`)

The automatic updates and tasks raised when a job is completed or raised at high priority, kept within the maintenance workspace.

**Atomic requirements:** 5

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-030](requirements/INTK-0001-REQ-030.md) | Update last service date on completion | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up |
| [INTK-0001-REQ-031](requirements/INTK-0001-REQ-031.md) | Return in-maintenance vehicle to service, leave others unchanged | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up |
| [INTK-0001-REQ-032](requirements/INTK-0001-REQ-032.md) | Raise a confirmation task on completion | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up |
| [INTK-0001-REQ-033](requirements/INTK-0001-REQ-033.md) | Alert task for high or critical priority jobs | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up |
| [INTK-0001-REQ-034](requirements/INTK-0001-REQ-034.md) | Keep follow-up within the maintenance workspace | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §4.4 Automatic follow-up |

## 7. Users and Access (`INTK-0001-GRP-07`)

The roles, business-unit access model, team-based access provisioning, and single application structure for fleet operations.

**Atomic requirements:** 5

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-035](requirements/INTK-0001-REQ-035.md) | Coordinator role | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements |
| [INTK-0001-REQ-036](requirements/INTK-0001-REQ-036.md) | Technician role | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements |
| [INTK-0001-REQ-037](requirements/INTK-0001-REQ-037.md) | Reader role | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements |
| [INTK-0001-REQ-038](requirements/INTK-0001-REQ-038.md) | Team-based access provisioning | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements |
| [INTK-0001-REQ-039](requirements/INTK-0001-REQ-039.md) | Single application with two areas | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §5 Users and Access Requirements |

## 8. Non-Functional Expectations (`INTK-0001-GRP-08`)

Performance and scale, reliable and idempotent automation, visible failures, immediate rule feedback, and reporting-ready data.

**Atomic requirements:** 7

**Group evidence:**
- `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations

| Requirement | Title | Status | Evidence provenance |
| --- | --- | --- | --- |
| [INTK-0001-REQ-040](requirements/INTK-0001-REQ-040.md) | Sustain fleet scale without degradation | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-041](requirements/INTK-0001-REQ-041.md) | Lean lists and searches | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-042](requirements/INTK-0001-REQ-042.md) | Idempotent follow-up automation | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-043](requirements/INTK-0001-REQ-043.md) | Automation must not overwrite its trigger | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-044](requirements/INTK-0001-REQ-044.md) | Visible failure for failed automation | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-045](requirements/INTK-0001-REQ-045.md) | Immediate message when a rule blocks a save | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
| [INTK-0001-REQ-046](requirements/INTK-0001-REQ-046.md) | Reporting-ready data | reviewed | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` — §6 Non-Functional Expectations |
