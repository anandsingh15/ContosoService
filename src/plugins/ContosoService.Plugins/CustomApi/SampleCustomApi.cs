using Microsoft.Xrm.Sdk;
using System;

namespace ContosoService.Plugins
{
    public class SampleCustomApi : PluginBase
    {
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
            context.OutputParameters[OutputResponseParameter] = $"Contoso Service received: {message}";
        }
    }
}