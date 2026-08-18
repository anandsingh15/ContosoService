using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Extensions;
using Microsoft.Xrm.Sdk.PluginTelemetry;
using System;
using System.Runtime.CompilerServices;

namespace ContosoService.Plugins
{
    public class LocalPluginContext : ILocalPluginContext
    {
        public IOrganizationService InitiatingUserService { get; }

        public IOrganizationService PluginUserService { get; }

        public IPluginExecutionContext PluginExecutionContext { get; }

        public IServiceEndpointNotificationService NotificationService { get; }

        public ITracingService TracingService { get; }

        public IServiceProvider ServiceProvider { get; }

        public IOrganizationServiceFactory OrgSvcFactory { get; }

        public ILogger Logger { get; }

        public LocalPluginContext(IServiceProvider serviceProvider)
        {
            if (serviceProvider == null)
            {
                throw new InvalidPluginExecutionException(nameof(serviceProvider));
            }

            ServiceProvider = serviceProvider;
            Logger = serviceProvider.Get<ILogger>();
            PluginExecutionContext = serviceProvider.Get<IPluginExecutionContext>();
            TracingService = new LocalTracingService(serviceProvider);
            NotificationService = serviceProvider.Get<IServiceEndpointNotificationService>();
            OrgSvcFactory = serviceProvider.Get<IOrganizationServiceFactory>();
            PluginUserService = serviceProvider.GetOrganizationService(PluginExecutionContext.UserId);
            InitiatingUserService = serviceProvider.GetOrganizationService(PluginExecutionContext.InitiatingUserId);
        }

        public void Trace(string message, [CallerMemberName] string method = null)
        {
            if (string.IsNullOrWhiteSpace(message) || TracingService == null)
            {
                return;
            }

            TracingService.Trace(method == null ? message : $"[{method}] - {message}");
        }
    }
}