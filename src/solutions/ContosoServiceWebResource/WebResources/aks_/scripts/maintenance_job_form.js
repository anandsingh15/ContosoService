"use strict";

var Contoso = window.Contoso || {};
window.Contoso = Contoso;

Contoso.MaintenanceJobForm = (function () {
    var COMPLETED_STAGE = 74880;
    var RETIRED_STATUS = 74876;
    var NOTIFICATIONS = {
        vehicle: "maintenance_job_vehicle_warning",
        vehicleLookup: "maintenance_job_vehicle_lookup_error",
        completionDate: "maintenance_job_completion_date_required",
        scheduledDate: "maintenance_job_scheduled_date_past"
    };

    function getFormContext(executionContext) {
        return executionContext.getFormContext();
    }

    function getValue(formContext, attributeName) {
        var attribute = formContext.getAttribute(attributeName);
        return attribute ? attribute.getValue() : null;
    }

    function clearNotification(formContext, notificationId) {
        formContext.ui.clearFormNotification(notificationId);
    }

    function setNotification(formContext, message, level, notificationId) {
        formContext.ui.setFormNotification(message, level, notificationId);
    }

    function normalizeId(id) {
        return id ? id.replace(/[{}]/g, "") : "";
    }

    function isPastDate(date) {
        if (!date || typeof date.getTime !== "function" || Number.isNaN(date.getTime())) {
            return false;
        }

        var scheduledDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        var now = new Date();
        var currentDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        return scheduledDay < currentDay;
    }

    function validateCompletionDate(formContext) {
        clearNotification(formContext, NOTIFICATIONS.completionDate);

        if (getValue(formContext, "aks_stage") === COMPLETED_STAGE &&
            !getValue(formContext, "aks_completeddate")) {
            setNotification(
                formContext,
                "A completion date will be recorded when this maintenance job is completed.",
                "INFO",
                NOTIFICATIONS.completionDate
            );
        }
    }

    function validateScheduledDate(formContext) {
        clearNotification(formContext, NOTIFICATIONS.scheduledDate);

        if (formContext.ui.getFormType() !== 1 ||
            !isPastDate(getValue(formContext, "aks_scheduleddate"))) {
            return true;
        }

        setNotification(
            formContext,
            "The scheduled date cannot be earlier than today. Correct the date before saving.",
            "ERROR",
            NOTIFICATIONS.scheduledDate
        );
        return false;
    }

    async function validateVehicle(formContext) {
        clearNotification(formContext, NOTIFICATIONS.vehicle);
        clearNotification(formContext, NOTIFICATIONS.vehicleLookup);

        var vehicle = getValue(formContext, "aks_vehicleid");
        if (!vehicle || vehicle.length === 0) {
            return;
        }

        try {
            var record = await window.Xrm.WebApi.retrieveRecord(
                "aks_vehicle",
                normalizeId(vehicle[0].id),
                "?$select=aks_status,aks_roadworthy"
            );

            if (record.aks_status === RETIRED_STATUS) {
                setNotification(
                    formContext,
                    "The selected vehicle is retired and cannot be used to complete this maintenance job.",
                    "WARNING",
                    NOTIFICATIONS.vehicle
                );
            } else if (record.aks_roadworthy === false) {
                setNotification(
                    formContext,
                    "The selected vehicle is not roadworthy and cannot be used to complete this maintenance job.",
                    "WARNING",
                    NOTIFICATIONS.vehicle
                );
            }
        } catch (error) {
            setNotification(
                formContext,
                "Vehicle status could not be checked. Try again before completing this maintenance job.",
                "WARNING",
                NOTIFICATIONS.vehicleLookup
            );
        }
    }

    function onLoad(executionContext) {
        var formContext = getFormContext(executionContext);
        validateCompletionDate(formContext);
        validateScheduledDate(formContext);
        return validateVehicle(formContext);
    }

    function onVehicleChange(executionContext) {
        return validateVehicle(getFormContext(executionContext));
    }

    function onStageChange(executionContext) {
        validateCompletionDate(getFormContext(executionContext));
    }

    function onScheduledDateChange(executionContext) {
        validateScheduledDate(getFormContext(executionContext));
    }

    function onSave(executionContext) {
        var formContext = getFormContext(executionContext);
        var eventArgs = executionContext.getEventArgs();
        eventArgs.getSaveMode();

        if (!validateScheduledDate(formContext)) {
            eventArgs.preventDefault();
        }
    }

    return {
        onLoad: onLoad,
        onVehicleChange: onVehicleChange,
        onStageChange: onStageChange,
        onScheduledDateChange: onScheduledDateChange,
        onSave: onSave
    };
})();