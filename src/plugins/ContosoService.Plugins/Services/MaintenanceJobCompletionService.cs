using ContosoService.Plugins.Constants;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;
using System;

namespace ContosoService.Plugins.Services
{
    internal sealed class MaintenanceJobCompletionService
    {
        private readonly Func<DateTime> utcNow;

        internal MaintenanceJobCompletionService(Func<DateTime> utcNow)
        {
            this.utcNow = utcNow ?? throw new ArgumentNullException(nameof(utcNow));
        }

        internal void ValidateCreate(Entity target)
        {
            var scheduledDate = target.GetAttributeValue<DateTime?>(MaintenanceJobSchema.ScheduledDate);
            if (scheduledDate.HasValue && scheduledDate.Value.Date < utcNow().Date)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.ScheduledDateInPast);
            }

            if (target.GetAttributeValue<OptionSetValue>(MaintenanceJobSchema.Stage)?.Value == MaintenanceJobSchema.CompletedStage)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.InitialCompletedStage);
            }
        }

        internal void ValidateUpdate(
            Entity target,
            Entity preImage,
            Guid maintenanceJobId,
            IOrganizationService organizationService)
        {
            var previousStage = preImage.GetAttributeValue<OptionSetValue>(MaintenanceJobSchema.Stage)?.Value;
            var requestedStage = target.GetAttributeValue<OptionSetValue>(MaintenanceJobSchema.Stage)?.Value;

            if (previousStage == MaintenanceJobSchema.CompletedStage && requestedStage != MaintenanceJobSchema.CompletedStage)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.ReopenCompletedJob);
            }

            if (requestedStage != MaintenanceJobSchema.CompletedStage || previousStage == MaintenanceJobSchema.CompletedStage)
            {
                return;
            }

            var vehicle = Effective<EntityReference>(target, preImage, MaintenanceJobSchema.VehicleId);
            if (vehicle == null)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.VehicleRequired);
            }

            var vehicleRow = organizationService.Retrieve(
                MaintenanceJobSchema.VehicleTable,
                vehicle.Id,
                new ColumnSet(MaintenanceJobSchema.VehicleStatus, MaintenanceJobSchema.VehicleRoadworthy));
            if (vehicleRow.GetAttributeValue<OptionSetValue>(MaintenanceJobSchema.VehicleStatus)?.Value == MaintenanceJobSchema.RetiredVehicleStatus)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.RetiredVehicle);
            }

            if (vehicleRow.GetAttributeValue<bool?>(MaintenanceJobSchema.VehicleRoadworthy) != true)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.VehicleNotRoadworthy);
            }

            var parts = new QueryExpression(MaintenanceJobSchema.JobPartTable)
            {
                ColumnSet = new ColumnSet(false),
                TopCount = 1,
                Criteria = new FilterExpression(LogicalOperator.And)
            };
            parts.Criteria.AddCondition(
                MaintenanceJobSchema.JobPartMaintenanceJobId,
                ConditionOperator.Equal,
                maintenanceJobId);
            if (organizationService.RetrieveMultiple(parts).Entities.Count == 0)
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.JobPartRequired);
            }

            if (!Effective<DateTime?>(target, preImage, MaintenanceJobSchema.CompletedDate).HasValue)
            {
                target[MaintenanceJobSchema.CompletedDate] = utcNow();
            }
        }

        private static T Effective<T>(Entity target, Entity preImage, string attribute)
        {
            return target.Contains(attribute)
                ? target.GetAttributeValue<T>(attribute)
                : preImage.GetAttributeValue<T>(attribute);
        }
    }
}