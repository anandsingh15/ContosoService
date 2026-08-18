using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.PluginTelemetry;
using System;
using System.Runtime.CompilerServices;

namespace ContosoService.Plugins
{
    public interface ILocalPluginContext
    {
        IOrganizationService InitiatingUserService { get; }

        IOrganizationService PluginUserService { get; }

        IPluginExecutionContext PluginExecutionContext { get; }

        IServiceEndpointNotificationService NotificationService { get; }

        ITracingService TracingService { get; }

        IServiceProvider ServiceProvider { get; }

        IOrganizationServiceFactory OrgSvcFactory { get; }

        ILogger Logger { get; }

        void Trace(string message, [CallerMemberName] string method = null);
    }
}