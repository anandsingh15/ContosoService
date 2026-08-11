<!-- d365-intake-evidence: derived Markdown. The body below the rule is a verbatim
     MarkItDown conversion of the commit-pinned source document. Do not edit the
     converted body; it is the only sanctioned basis for drafting requirements. -->

# Converted evidence — Contoso Service Fleet Maintenance Business Requirements

> **Derived evidence for intake batch `INTK-0001`.** Produced by converting the
> commit-pinned source document with the MarkItDown MCP (`convert_to_markdown`).
> Fact locations are the document's numbered sections (§1–§9) and the role table
> in §5, preserved as headings/table in the converted body below.

| Provenance | Value |
|------------|-------|
| Intake batch | `INTK-0001` |
| Intake issue | [#5](https://github.com/anandsingh15/ContosoService/issues/5) |
| Repository | `anandsingh15/ContosoService` |
| Commit (immutable) | `7c9bb92027bfed1fef000141f7ff9ea192174c98` |
| Source path | `intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx` |
| Permanent link | <https://github.com/anandsingh15/ContosoService/blob/7c9bb92027bfed1fef000141f7ff9ea192174c98/intake/contoso/2026-08-11/Contoso-Service-Fleet-Maintenance-Business-Requirements.docx> |
| Source SHA-256 | `75cbcb31d2c3d17107e43309edf10a11612a5f20139e6c9b1265b7c34f4e3f0d` |
| Source bytes | 42380 |
| Converter | MarkItDown MCP `convert_to_markdown` |
| Converted (UTC) | 2026-08-11 |

---

Contoso Service Fleet Maintenance

Business Requirements Document

*Prepared for fleet operations leadership. Version 1.0, 10 August 2026.*

**Contents**

# 1. Purpose and Scope

Contoso Service maintains a fleet of vehicles that must stay roadworthy, and today the work of recording assets, scheduling repairs, tracking the parts consumed, and reporting on cost is spread across disconnected records. This document states, in business terms, what the new fleet maintenance solution must do. It is written for the operations managers, depot supervisors, and service leads who will own the process, and it deliberately avoids implementation detail so that the business intent can be agreed before any configuration is finalised.

The scope covers a single maintenance workspace that brings together fleet assets, service work, the parts consumed on each job, and the depot and technician context around them. The solution must support a fleet of approximately 5,000 vehicles and an annual workload of about 40,000 maintenance jobs. Depots and technicians are represented using the organisation's existing customer and contact records rather than new registers, so that the maintenance process inherits information the business already maintains.

Out of scope for this release are procurement and purchasing of parts, financial posting to the general ledger, driver or route management, and any customer-facing portal. These may be considered in later phases but must not delay the maintenance workspace.

# 2. Business Objectives

The solution exists to give Contoso Service a single, trustworthy record of what has been done to every vehicle, by whom, at what cost, and with what outcome. Four objectives frame every requirement in this document.

* Record: every vehicle must carry a reliable identity so that no two records can describe the same asset and no service history is lost.
* Orchestrate: routine follow-up work, such as updating a vehicle after service or alerting an owner to urgent work, must happen automatically rather than depending on someone remembering.
* Enforce: the rules that protect data quality, particularly around closing a job, must hold no matter how the change is made.
* Experience: the people doing the work must be able to complete a normal day's tasks without hunting across screens or re-entering information.

# 3. Business Information Requirements

The business needs three new categories of information, held alongside the existing depot and technician records. A vehicle record identifies the asset by its vehicle identification number and registration, and carries its current status and service history. A maintenance job records a piece of service work against a vehicle, including the stage it has reached, its priority, its scheduled and completed dates, and its cost. A job part records each part consumed on a job, with the quantity used, the unit price, and the resulting line value that contributes to the job total.

The information must be linked so that the business can move naturally between an asset, its service history, and the parts consumed. A depot may own many vehicles, a vehicle may have many maintenance jobs, a job may consume many parts, and a technician may be assigned many jobs.

Two rules govern the quality of this information. First, values that the business reports on, such as vehicle status, job stage, and priority, must be selected from an agreed list rather than typed as free text, so that reporting and search are dependable. Second, the relationships must be real links between records rather than typed references, so that a user can always navigate from one to the other and so that no record points at something that no longer exists.

The business also requires a defined position on what happens when a record is removed. Removing a vehicle must remove its maintenance history and the parts recorded against it, because that history has no meaning without the asset; the same applies to a job and its parts. Removing a depot or a technician must never destroy vehicle or job records; it must only clear the association, so that operational history survives organisational change.

Search must be predictable. Users expect to find records by the identifiers they actually quote to each other: vehicle name, registration, vehicle identification number, job number, and part number.

# 4. Business Process Requirements

## 4.1 Recording and maintaining a vehicle

A coordinator must be able to add a vehicle quickly, entering only the identifiers that matter at the point of capture, and complete the remaining detail later. When a vehicle is opened, its status, roadworthiness, and depot must be visible immediately without scrolling, because these three facts determine whether work can proceed. The vehicle record must present its maintenance history in context, so that a supervisor can judge whether a new fault is a recurrence.

The business needs saved lists that match how the fleet is actually managed: all active vehicles, vehicles currently in maintenance, and vehicles grouped by depot.

## 4.2 Raising and progressing a maintenance job

A maintenance job must show its job number, stage, and priority at the top of the record, so that anyone opening it understands its status at a glance. Because most questions asked during a job concern the vehicle, key vehicle details must be visible on the job itself rather than requiring the user to navigate away.

Technicians must be able to enter the parts they have used directly on the job, line by line, without opening a separate record for each one. Each line captures the quantity and unit price and the system calculates the line value; the job must then reflect the total cost of parts consumed.

Daily work must be supported by saved lists of active jobs, jobs assigned to the signed-in technician, and jobs of high or critical priority.

## 4.3 Completing a job

Completion is the point at which the maintenance record becomes the business's official account of the work, so it carries the strictest rules. A job may only be marked completed when the vehicle it relates to is roadworthy and has not been retired, and when at least one part line has been recorded against it. When a job is completed, the date of completion must be recorded automatically if the user has not supplied it.

These rules must apply to every route into the system, including the application screens, bulk data imports, integrations, and automated processes. If a completion attempt breaks a rule it must be rejected outright, with a clear explanation such as a job cannot be completed on a non-roadworthy or retired vehicle. A partially applied completion is not acceptable.

The user interface should warn people before they reach that point. When a technician selects a vehicle that is not roadworthy, or sets a stage that requires a completion date, the form should prompt them immediately rather than waiting for a save to fail. The system must also prevent a newly raised job from being scheduled in the past.

## 4.4 Automatic follow-up

Two follow-up activities must happen without human intervention. When a job is completed, the vehicle's last service date must be updated, a vehicle that was in maintenance must be returned to service, and a confirmation task must be raised so the closure is visible in the operational workload. Vehicles in any other status must be left alone, because the business does not want automation overriding a deliberate decision such as retirement.

When a job is raised at high or critical priority, a task must be created for the job owner carrying the vehicle and scheduling context, so that urgent work is noticed the moment it is logged rather than at the next review.

All follow-up work and its resulting tasks must remain inside the maintenance workspace, so that the operational picture is complete without users checking a second system.

# 5. Users and Access Requirements

Three roles cover the fleet operation, and each is granted only the access its work requires.

| **Role** | **What they may do** | **Typical daily work** |
| --- | --- | --- |
| Coordinator | Create, read, change, delete, assign and share fleet operations records across the business unit. | Maintains the vehicle register, raises jobs, assigns technicians, resolves exceptions. |
| Technician | Read fleet records across the business unit; change only the jobs assigned to them and the parts on those jobs. | Works assigned jobs, records parts used, completes jobs. |
| Reader | Read-only access to vehicles, jobs and parts across the business unit. | Oversight, reporting and cost review. |

Access is granted through team membership tied to the organisation's existing group structure, so that joiners and leavers are handled by normal identity administration rather than by manual permission changes. All three roles work in the same application, which is organised into a fleet operations area covering vehicles, jobs, and parts, and a customer area covering depots and technicians.

# 6. Non-Functional Expectations

The solution must sustain a fleet of 5,000 vehicles and around 40,000 maintenance jobs a year without degradation in day-to-day screens, which means lists and searches must stay lean and must not be built on filters that force the system to scan the whole fleet.

Automated follow-up must be reliable and must not duplicate work. If the same event is processed more than once, the business outcome must be unchanged, and automation must never overwrite the change that triggered it. Where an automated step fails, the failure must be recorded as a visible task rather than disappearing silently, so that operations can intervene.

Because completion rules are enforced as the record is saved, users must receive an immediate and understandable message when a rule blocks them. Consistent use of agreed value lists and reliable relationships is also what makes the data usable for future reporting and analytics, which the business regards as a requirement rather than a by-product.

# 7. Delivery Status and Outstanding Work

As at the build record dated 29 July 2026, the core of the solution is in place: the information model, the forms and lists that support daily work, the three access roles and the application itself, the enforcement of completion rules, and the early on-screen warnings on the maintenance job form.

The following items remain before the solution can be released to the business.

* Build the two automatic follow-up processes for job completion and high-priority alerting.
* Activate the on-screen prompts that respond when the job stage or the selected vehicle changes.
* Configure the calculated part line value and the roll-up of parts cost to the job.
* Consolidate all components into a single deployable package.
* Complete end-to-end acceptance testing with operations before release.

Status must be re-confirmed against the target environment before any release decision is taken.

# 8. Assumptions and Open Points

This document assumes that depot and technician information is already maintained to an acceptable standard in the existing customer and contact records, and that no separate register is required. It assumes that part pricing is captured on the job line at the time of use and is not sourced from a live price list. It also assumes that the volumes quoted, 5,000 vehicles and 40,000 jobs a year, represent steady-state operation rather than a peak.

Three points remain open for the business to confirm: whether any role beyond the coordinator should be able to reopen a completed job, whether parts cost alone is a sufficient measure of job cost or labour must also be captured, and how long completed maintenance history must be retained before archiving.

# 9. Sign-Off

Approval of this document confirms that the objectives, information requirements, process rules, and access model described here reflect the intended operation of Contoso Service fleet maintenance, and authorises completion of the outstanding work listed in section 7.
