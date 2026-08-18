namespace ContosoService.Plugins.Constants
{
    internal static class MaintenanceJobSchema
    {
        internal const string Table = "aks_maintenancejob";
        internal const string Stage = "aks_stage";
        internal const string ScheduledDate = "aks_scheduleddate";
        internal const string CompletedDate = "aks_completeddate";
        internal const string VehicleId = "aks_vehicleid";

        internal const string VehicleTable = "aks_vehicle";
        internal const string VehicleStatus = "aks_status";
        internal const string VehicleRoadworthy = "aks_roadworthy";

        internal const string JobPartTable = "aks_jobpart";
        internal const string JobPartMaintenanceJobId = "aks_maintenancejobid";

        internal const int CompletedStage = 74880;
        internal const int RetiredVehicleStatus = 74876;
    }
}