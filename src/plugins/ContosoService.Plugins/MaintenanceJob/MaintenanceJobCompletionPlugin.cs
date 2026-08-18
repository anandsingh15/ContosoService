using ContosoService.Plugins.Constants;
using ContosoService.Plugins.Services;
using Microsoft.Xrm.Sdk;
using System;

namespace ContosoService.Plugins
{
    public class MaintenanceJobCompletionPlugin : PluginBase
    {
        internal const int CompletedStage = MaintenanceJobSchema.CompletedStage;
        internal const int RetiredVehicleStatus = MaintenanceJobSchema.RetiredVehicleStatus;

        private readonly MaintenanceJobCompletionService service;

        public MaintenanceJobCompletionPlugin()
            : this(() => DateTime.UtcNow)
        {
        }

        public MaintenanceJobCompletionPlugin(string unsecureConfiguration, string secureConfiguration)
            : this(() => DateTime.UtcNow)
        {
        }

        internal MaintenanceJobCompletionPlugin(Func<DateTime> utcNow)
            : base(typeof(MaintenanceJobCompletionPlugin))
        {
            service = new MaintenanceJobCompletionService(utcNow);
        }

        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
            {
                throw new ArgumentNullException(nameof(localPluginContext));
            }

            var context = localPluginContext.PluginExecutionContext;
            if (!context.InputParameters.Contains("Target") ||
                !(context.InputParameters["Target"] is Entity target) ||
                target.LogicalName != MaintenanceJobSchema.Table)
            {
                return;
            }

            if (string.Equals(context.MessageName, "Create", StringComparison.OrdinalIgnoreCase))
            {
                ValidateCreate(target);
                return;
            }

            if (!string.Equals(context.MessageName, "Update", StringComparison.OrdinalIgnoreCase) ||
                !target.Contains(MaintenanceJobSchema.Stage))
            {
                return;
            }

            if (!context.PreEntityImages.Contains("PreImage"))
            {
                throw new InvalidPluginExecutionException(MaintenanceJobMessages.PreImageRequired);
            }

            ValidateUpdate(
                target,
                context.PreEntityImages["PreImage"],
                context.PrimaryEntityId,
                localPluginContext.PluginUserService);
        }

        internal void ValidateCreate(Entity target)
        {
            service.ValidateCreate(target);
        }

        internal void ValidateUpdate(
            Entity target,
            Entity preImage,
            Guid maintenanceJobId,
            IOrganizationService organizationService)
        {
            service.ValidateUpdate(target, preImage, maintenanceJobId, organizationService);
        }
    }
}