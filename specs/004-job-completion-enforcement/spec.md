---
id: FEAT-04
slug: job-completion-enforcement
epic: EPIC-01
member_reqs:
- INTK-0001-REQ-022
- INTK-0001-REQ-023
- INTK-0001-REQ-024
- INTK-0001-REQ-025
- INTK-0001-REQ-026
- INTK-0001-REQ-027
- INTK-0001-REQ-028
- INTK-0001-REQ-029
- INTK-0001-REQ-045
repository_context_hash: ae33ece0c20d793460f5f5f9817c5cec233d4800e78ecb012c6fe7a7d9f813fe
spec_hash: 2ee45ddbb5398807ec196752f757303dab82f3f3cc0700131ac2d0949febdb44
status: reviewed
---

# FEAT-04 — Job completion enforcement

<!-- FILL:intent -->
Make completing a maintenance job a disciplined, trustworthy moment. A job can only be
completed when its preconditions are genuinely met, and those rules hold no matter how the
completion is attempted. When a job is completed the completion date is recorded
automatically, and the whole completion either succeeds as one atomic step or is rejected
with a clear, specific reason. People are warned early — before they hit a wall — when a
vehicle is not roadworthy, when a stage still needs a completion date, or when a date
would fall in the past, and any rule that blocks a save says so immediately. The result is
that a "completed" job always means the same thing.
<!-- /FILL -->

## Scope

<!-- FILL:scope -->
In scope:
- The preconditions that must hold before a job can be completed (REQ-022).
- Recording the completion date automatically on completion (REQ-023).
- Enforcing the completion rules on every route that could complete a job (REQ-024).
- Rejecting an invalid completion with a clear reason (REQ-025) and surfacing any
  save-blocking rule immediately (REQ-045).
- Completing atomically, so completion never leaves a job half-done (REQ-026).
- Early warnings for a non-roadworthy vehicle (REQ-027), for a stage that still needs a
  completion date (REQ-028), and against scheduling in the past (REQ-029).

Out of scope:
- What happens automatically after a job completes (FEAT-05).
- The job and parts records themselves (FEAT-03) and role-based access (FEAT-06).
- Implementation mechanisms for enforcing the rules, which are design-stage decisions.
<!-- /FILL -->

## Actors

- **Coordinator** — completes jobs and depends on completion meaning exactly one thing.
- **Technician** — is guided by early warnings and clear rejection reasons while working a
  job toward completion.

## Functional behaviour

- A job completes only when its preconditions are met; the rules apply identically however
  completion is triggered.
- On successful completion the completion date is set automatically, and the change is
  applied atomically — all of it, or none of it.
- An invalid completion is rejected with a clear, specific reason rather than failing
  silently, and any rule that blocks a save reports itself immediately.
- The person is warned early when a vehicle is not roadworthy, when a stage needs a
  completion date, and when a date would fall in the past — before the block becomes a
  dead end.
- A completed job is final: it cannot be reopened or reverted, and a correction is made by
  raising a new maintenance job (decision 2026-08-11).

## Requirements traceability

<!-- COMPILER:BEGIN traceability -->
| REQ | Title | Type | Priority |
| --- | --- | --- | --- |
| INTK-0001-REQ-022 | Completion preconditions | functional | Must |
| INTK-0001-REQ-023 | Auto-record completion date | functional | Must |
| INTK-0001-REQ-024 | Enforce completion rules on every route | functional | Must |
| INTK-0001-REQ-025 | Reject invalid completion with a clear reason | functional | Must |
| INTK-0001-REQ-026 | Atomic completion | functional | Must |
| INTK-0001-REQ-027 | Early warning for non-roadworthy vehicle | functional | Should |
| INTK-0001-REQ-028 | Early warning when a stage needs a completion date | functional | Should |
| INTK-0001-REQ-029 | Prevent scheduling in the past | functional | Should |
| INTK-0001-REQ-045 | Immediate message when a rule blocks a save | functional | Should |
<!-- COMPILER:END traceability -->

## Acceptance scenarios

<!-- COMPILER:BEGIN scenarios -->
```gherkin
Scenario: Block completion when preconditions are not met
  Given a maintenance job whose vehicle is not roadworthy, or is retired, or that has no part lines
  When a user attempts to mark the job completed
  Then completion is not allowed

Scenario: Allow completion when preconditions are met
  Given a maintenance job whose vehicle is roadworthy and not retired and that has at least one part line
  When a user marks the job completed
  Then completion is allowed

Scenario: Default the completion date
  Given a job being completed without a completion date
  When the completion is applied
  Then the solution records the completion date automatically

Scenario: Enforce completion rules regardless of route
  Given a completion attempt that breaks a completion rule
  When it arrives through application screens, a bulk import, an integration, or an automated process
  Then the same completion rules are enforced on every route

Scenario: Explain a rejected completion
  Given a completion attempt that breaks a completion rule
  When the attempt is processed
  Then it is rejected outright with a clear explanation of the rule that was broken

Scenario: Never partially apply a completion
  Given a completion attempt that breaks a rule partway through
  When the attempt is rejected
  Then no part of the completion is applied

Scenario: Warn on selecting a non-roadworthy vehicle
  Given a maintenance job form
  When a technician selects a vehicle that is not roadworthy
  Then the form warns them immediately, before saving

Scenario: Prompt for a required completion date
  Given a maintenance job form
  When a technician sets a stage that requires a completion date
  Then the form prompts them immediately, before saving

Scenario: Reject a past scheduled date on a new job
  Given a newly raised maintenance job
  When a user sets its scheduled date in the past
  Then the solution prevents the job from being scheduled in the past

Scenario: Explain a blocked save at once
  Given a save that a rule blocks
  When the user attempts it
  Then they see an immediate, understandable message explaining why the save was blocked
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
| INTK-0001-REQ-022 | INTK-0001-REQ-007, INTK-0001-REQ-011, INTK-0001-REQ-001 |
| INTK-0001-REQ-023 | INTK-0001-REQ-022 |
| INTK-0001-REQ-024 | INTK-0001-REQ-022 |
| INTK-0001-REQ-025 | INTK-0001-REQ-022 |
| INTK-0001-REQ-026 | INTK-0001-REQ-022 |
| INTK-0001-REQ-027 | INTK-0001-REQ-022, INTK-0001-REQ-001 |
| INTK-0001-REQ-028 | INTK-0001-REQ-023, INTK-0001-REQ-007 |
| INTK-0001-REQ-029 | INTK-0001-REQ-007 |
| INTK-0001-REQ-045 | INTK-0001-REQ-025 |
<!-- COMPILER:END deps -->

## Provenance

<!-- COMPILER:BEGIN provenance -->
| REQ | Intake | Source | Requirement SHA-256 |
| --- | --- | --- | --- |
| INTK-0001-REQ-022 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `88a00c166c2be706b6997d67c567489ed67c7be8ebeae14e37b9b9f153a7e330` |
| INTK-0001-REQ-023 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `fcb1e3a3557bb7a9dff6ae4702b4ff93581682a21f00a649372cc90e12b7db5e` |
| INTK-0001-REQ-024 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `fd1a58590c186e7ad44679865d1343af0d960ae98a3587cbd85770525b2ad916` |
| INTK-0001-REQ-025 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `7f2ec6dc73eadbec05b5d3377e75873702473934a780d0d27b115ebc866b15d4` |
| INTK-0001-REQ-026 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `70609073bb1678f09d88783e8a2673d2a56015a74bbc6af949d34c233f81488d` |
| INTK-0001-REQ-027 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `ae92e734b62fc71aeb886962d2989396c375c5eeacccabb0510b45b94b424027` |
| INTK-0001-REQ-028 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `8206471d24f3422e89a9b121abb0632b1b06a6d61bf0f3b8fcdf28db4c154ab6` |
| INTK-0001-REQ-029 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `aadadff7972c7b36cd900e6aa93e4884a037870e4bfccc23654f221153af5f5b` |
| INTK-0001-REQ-045 | INTK-0001 | intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx | `d36dadaf89d05c424ddebad4a89af91b27cb2ba76d0d24b466c400ab977043fb` |
<!-- COMPILER:END provenance -->

## Grounding

<!-- FILL:grounding -->
Grounded in the reviewed requirements drawn from the Contoso Service Fleet Maintenance
Business Requirements, §4.3 Completing a job (completion preconditions, automatic
completion date, enforcement on every route, clear rejection, atomic completion, and the
early warnings) and §6 Non-Functional Expectations (an immediate message when a rule
blocks a save). Member requirements: REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027,
REQ-028, REQ-029, REQ-045. Depends on FEAT-03 for the job and parts it governs.
<!-- /FILL -->

## Open decisions

<!-- FILL:open-decisions -->
- [x] **Can a completed job be reopened or reverted, and by whom?** Decided: completion is
  final. A completed job cannot be reopened or reverted; a correction is handled by raising
  a new maintenance job. This is the as-specified reading of REQ-022–REQ-026, so it adds no
  scope. — decided by Jane Smith, Contoso Service Product Owner, 2026-08-11.
<!-- /FILL -->
