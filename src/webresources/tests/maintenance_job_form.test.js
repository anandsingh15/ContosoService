"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const script = fs.readFileSync(
    path.join(__dirname, "..", "scripts", "maintenance_job_form.js"),
    "utf8"
);

function createHarness(options = {}) {
    const values = {
        aks_vehicleid: null,
        aks_stage: null,
        aks_completeddate: null,
        aks_scheduleddate: null,
        ...options.values
    };
    const notifications = new Map(options.notifications || []);
    const clearedNotifications = [];
    const retrieveCalls = [];
    let saveModeInspected = false;
    let savePrevented = false;

    const formContext = {
        getAttribute: (name) => Object.hasOwn(values, name) ? {
            getValue: () => values[name]
        } : null,
        ui: {
            getFormType: () => options.formType ?? 1,
            setFormNotification: (message, level, id) => {
                notifications.set(id, { message, level });
            },
            clearFormNotification: (id) => {
                clearedNotifications.push(id);
                notifications.delete(id);
                return true;
            }
        }
    };
    const eventArgs = {
        getSaveMode: () => {
            saveModeInspected = true;
            return options.saveMode ?? 1;
        },
        preventDefault: () => {
            savePrevented = true;
        }
    };
    const executionContext = {
        getFormContext: () => formContext,
        getEventArgs: () => eventArgs
    };
    const retrieveRecord = options.retrieveRecord || (async () => ({
        aks_status: 74875,
        aks_roadworthy: true
    }));
    const context = vm.createContext({
        Date,
        Number,
        window: {
            Xrm: {
                WebApi: {
                    retrieveRecord: async (...args) => {
                        retrieveCalls.push(args);
                        return retrieveRecord(...args);
                    }
                }
            }
        }
    });
    vm.runInContext(script, context);

    return {
        api: context.window.Contoso.MaintenanceJobForm,
        clearedNotifications,
        executionContext,
        notifications,
        retrieveCalls,
        values,
        wasSaveModeInspected: () => saveModeInspected,
        wasSavePrevented: () => savePrevented
    };
}

test("exports every declared form handler", () => {
    const { api } = createHarness();

    assert.deepEqual(
        Object.keys(api).sort(),
        ["onLoad", "onSave", "onScheduledDateChange", "onStageChange", "onVehicleChange"]
    );
});

test("warns immediately when the selected vehicle is not roadworthy", async () => {
    const harness = createHarness({
        values: { aks_vehicleid: [{ id: "{01234567-89AB-CDEF-0123-456789ABCDEF}" }] },
        retrieveRecord: async () => ({ aks_status: 74875, aks_roadworthy: false })
    });

    await harness.api.onVehicleChange(harness.executionContext);

    assert.deepEqual(harness.retrieveCalls[0], [
        "aks_vehicle",
        "01234567-89AB-CDEF-0123-456789ABCDEF",
        "?$select=aks_status,aks_roadworthy"
    ]);
    assert.match(
        harness.notifications.get("maintenance_job_vehicle_warning").message,
        /not roadworthy/
    );
});

test("warns immediately when the selected vehicle is retired", async () => {
    const harness = createHarness({
        values: { aks_vehicleid: [{ id: "vehicle-id" }] },
        retrieveRecord: async () => ({ aks_status: 74876, aks_roadworthy: true })
    });

    await harness.api.onVehicleChange(harness.executionContext);

    assert.match(
        harness.notifications.get("maintenance_job_vehicle_warning").message,
        /retired/
    );
});

test("clears stale vehicle warnings when the vehicle is valid", async () => {
    const harness = createHarness({
        values: { aks_vehicleid: [{ id: "vehicle-id" }] },
        notifications: [["maintenance_job_vehicle_warning", { message: "stale" }]]
    });

    await harness.api.onVehicleChange(harness.executionContext);

    assert.equal(harness.notifications.has("maintenance_job_vehicle_warning"), false);
    assert.ok(harness.clearedNotifications.includes("maintenance_job_vehicle_warning"));
});

test("shows a stable warning when the vehicle lookup fails", async () => {
    const harness = createHarness({
        values: { aks_vehicleid: [{ id: "vehicle-id" }] },
        retrieveRecord: async () => {
            throw new Error("network unavailable");
        }
    });

    await harness.api.onVehicleChange(harness.executionContext);

    assert.match(
        harness.notifications.get("maintenance_job_vehicle_lookup_error").message,
        /could not be checked/
    );
});

test("prompts immediately for a missing completion date and clears the prompt", () => {
    const harness = createHarness({ values: { aks_stage: 74880 } });

    harness.api.onStageChange(harness.executionContext);
    assert.match(
        harness.notifications.get("maintenance_job_completion_date_required").message,
        /completion date/
    );

    harness.values.aks_completeddate = new Date("2026-08-19T12:00:00Z");
    harness.api.onStageChange(harness.executionContext);
    assert.equal(harness.notifications.has("maintenance_job_completion_date_required"), false);
});

test("flags and clears a past scheduled date on a new job", () => {
    const harness = createHarness({
        values: { aks_scheduleddate: new Date("2000-01-01T12:00:00Z") }
    });

    harness.api.onScheduledDateChange(harness.executionContext);
    assert.match(
        harness.notifications.get("maintenance_job_scheduled_date_past").message,
        /cannot be earlier than today/
    );

    harness.values.aks_scheduleddate = new Date("2999-01-01T12:00:00Z");
    harness.api.onScheduledDateChange(harness.executionContext);
    assert.equal(harness.notifications.has("maintenance_job_scheduled_date_past"), false);
});

test("prevents save synchronously for a past date on a new job", () => {
    const harness = createHarness({
        values: { aks_scheduleddate: new Date("2000-01-01T12:00:00Z") }
    });

    harness.api.onSave(harness.executionContext);

    assert.equal(harness.wasSaveModeInspected(), true);
    assert.equal(harness.wasSavePrevented(), true);
});

test("allows a valid date and does not block past dates on existing jobs", () => {
    const newJob = createHarness({
        values: { aks_scheduleddate: new Date("2999-01-01T12:00:00Z") }
    });
    const existingJob = createHarness({
        formType: 2,
        values: { aks_scheduleddate: new Date("2000-01-01T12:00:00Z") }
    });

    newJob.api.onSave(newJob.executionContext);
    existingJob.api.onSave(existingJob.executionContext);

    assert.equal(newJob.wasSavePrevented(), false);
    assert.equal(existingJob.wasSavePrevented(), false);
});

test("onLoad evaluates all advisory checks without runtime handler registration", async () => {
    const harness = createHarness({
        values: {
            aks_vehicleid: [{ id: "vehicle-id" }],
            aks_stage: 74880,
            aks_scheduleddate: new Date("2000-01-01T12:00:00Z")
        }
    });

    await harness.api.onLoad(harness.executionContext);

    assert.equal(harness.retrieveCalls.length, 1);
    assert.equal(harness.notifications.has("maintenance_job_completion_date_required"), true);
    assert.equal(harness.notifications.has("maintenance_job_scheduled_date_past"), true);
});