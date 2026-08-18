using Microsoft.Xrm.Sdk;
using System;

namespace ContosoService.Plugins
{
    public class LocalTracingService : ITracingService
    {
        private readonly ITracingService tracingService;
        private DateTime previousTraceTime;

        public LocalTracingService(IServiceProvider serviceProvider)
        {
            var utcNow = DateTime.UtcNow;
            var context = (IExecutionContext)serviceProvider.GetService(typeof(IExecutionContext));
            var initialTimestamp = context.OperationCreatedOn > utcNow
                ? utcNow
                : context.OperationCreatedOn;

            tracingService = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            previousTraceTime = initialTimestamp;
        }

        public void Trace(string message, params object[] args)
        {
            var utcNow = DateTime.UtcNow;
            var deltaMilliseconds = utcNow.Subtract(previousTraceTime).TotalMilliseconds;

            try
            {
                tracingService.Trace(
                    args == null || args.Length == 0
                        ? $"[+{deltaMilliseconds:N0}ms] - {message}"
                        : $"[+{deltaMilliseconds:N0}ms] - {string.Format(message, args)}");
            }
            catch (FormatException exception)
            {
                throw new InvalidPluginExecutionException(
                    $"Failed to write trace message due to error {exception.Message}",
                    exception);
            }

            previousTraceTime = utcNow;
        }
    }
}