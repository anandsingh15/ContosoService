using Microsoft.Xrm.Sdk;
using System;
using System.ServiceModel;

namespace ContosoService.Plugins
{
    public abstract class PluginBase : IPlugin
    {
        protected string PluginClassName { get; }

        internal PluginBase(Type pluginClassName)
        {
            PluginClassName = pluginClassName.ToString();
        }

        public void Execute(IServiceProvider serviceProvider)
        {
            if (serviceProvider == null)
            {
                throw new InvalidPluginExecutionException(nameof(serviceProvider));
            }

            var localPluginContext = new LocalPluginContext(serviceProvider);
            localPluginContext.Trace(
                $"Entered {PluginClassName}.Execute() Correlation Id: " +
                $"{localPluginContext.PluginExecutionContext.CorrelationId}, Initiating User: " +
                $"{localPluginContext.PluginExecutionContext.InitiatingUserId}");

            try
            {
                ExecuteDataversePlugin(localPluginContext);
            }
            catch (FaultException<OrganizationServiceFault> organizationServiceFault)
            {
                localPluginContext.Trace($"Exception: {organizationServiceFault}");
                throw new InvalidPluginExecutionException(
                    $"OrganizationServiceFault: {organizationServiceFault.Message}",
                    organizationServiceFault);
            }
            finally
            {
                localPluginContext.Trace($"Exiting {PluginClassName}.Execute()");
            }
        }

        protected virtual void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
        }
    }
}