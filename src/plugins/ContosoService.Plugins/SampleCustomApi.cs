using Microsoft.Xrm.Sdk;
using System;

namespace ContosoService.Plugins
{
    /// <summary>
    /// Backing plug-in for a Custom API (e.g. <c>aks_SampleOperation</c>).
    /// A Custom API is the ALM-friendly successor to classic custom (process) actions:
    /// register this assembly, create a Custom API message, and point its main
    /// operation at this type. Request parameters arrive on <c>InputParameters</c>
    /// and results are written to <c>OutputParameters</c> — keep the contract typed
    /// and evolve it additively (never repurpose or drop an existing parameter).
    /// Custom APIs and plug-ins intentionally share this one signed assembly.
    /// </summary>
    public class SampleCustomApi : PluginBase
    {
        // Must match the Custom API request/response parameter unique names.
        private const string InputMessageParameter = "Message";
        private const string OutputResponseParameter = "Response";

        public SampleCustomApi(string unsecureConfiguration, string secureConfiguration)
            : base(typeof(SampleCustomApi))
        {
        }

        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
            {
                throw new ArgumentNullException(nameof(localPluginContext));
            }

            var context = localPluginContext.PluginExecutionContext;

            var message = context.InputParameters.Contains(InputMessageParameter)
                ? context.InputParameters[InputMessageParameter] as string
                : string.Empty;

            localPluginContext.Trace($"SampleCustomApi received '{message}'.");

            // TODO: replace with the real operation (idempotent, least-privilege).
            context.OutputParameters[OutputResponseParameter] = $"Contoso Service received: {message}";
        }
    }
}
