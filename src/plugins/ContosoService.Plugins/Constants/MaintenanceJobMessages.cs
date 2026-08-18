namespace ContosoService.Plugins.Constants
{
    internal static class MaintenanceJobMessages
    {
        internal const string PreImageRequired = "The Maintenance Job update step requires the PreImage image.";
        internal const string ScheduledDateInPast = "Scheduled date cannot be earlier than today.";
        internal const string InitialCompletedStage = "A new maintenance job cannot be created as Completed.";
        internal const string ReopenCompletedJob = "A completed maintenance job cannot be reopened.";
        internal const string VehicleRequired = "Select a vehicle before completing the maintenance job.";
        internal const string RetiredVehicle = "A maintenance job cannot be completed for a retired vehicle.";
        internal const string VehicleNotRoadworthy = "The selected vehicle must be roadworthy before completing the maintenance job.";
        internal const string JobPartRequired = "Add at least one job part before completing the maintenance job.";
    }
}