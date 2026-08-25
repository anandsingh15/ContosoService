using System.Text.Json;
using Microsoft.Crm.Sdk.Messages;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

internal sealed record ComponentInput(string LogicalName, Guid Id);

internal sealed record RequestInput(
    string Operation,
    Uri EnvironmentUrl,
    Guid ClientId,
    Guid TenantId,
    Uri RedirectUri,
    Guid AppId,
    ComponentInput[] Components);

internal static class Program
{
    private static int Main()
    {
        try
        {
            var input = JsonSerializer.Deserialize<RequestInput>(Console.In.ReadToEnd(), new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
            }) ?? throw new InvalidOperationException("SDK request input is required");

            Validate(input);
            var connectionString = string.Join(";", new[]
            {
                "AuthType=OAuth",
                $"Url={input.EnvironmentUrl.GetLeftPart(UriPartial.Authority)}",
                $"ClientId={input.ClientId:D}",
                $"TenantId={input.TenantId:D}",
                $"RedirectUri={input.RedirectUri}",
                "LoginPrompt=Auto",
                "RequireNewInstance=true",
            });

            using var client = new ServiceClient(connectionString);
            if (!client.IsReady)
            {
                throw new InvalidOperationException("interactive Dataverse SDK authentication failed");
            }

            if (input.Operation == "resolve")
            {
                var query = new QueryExpression("entity")
                {
                    ColumnSet = new ColumnSet("entityid", "logicalname", "objecttypecode"),
                };
                query.Criteria.AddCondition(
                    "logicalname",
                    ConditionOperator.In,
                    input.Components.Select(component => component.LogicalName).Cast<object>().ToArray());
                var entities = client.RetrieveMultiple(query).Entities;
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    result = "succeeded",
                    operation = "ResolveTableComponents",
                    components = entities.Select(entity => new
                    {
                        logicalName = entity.GetAttributeValue<string>("logicalname"),
                        id = entity.Id,
                        objectTypeCode = entity.GetAttributeValue<int>("objecttypecode"),
                    }),
                }));
                return 0;
            }

            var components = new EntityReferenceCollection(
                input.Components.Select(component => new EntityReference(component.LogicalName, component.Id)).ToList());
            if (input.Operation == "add")
            {
                client.Execute(new AddAppComponentsRequest
                {
                    AppId = input.AppId,
                    Components = components,
                });
            }
            else
            {
                client.Execute(new RemoveAppComponentsRequest
                {
                    AppId = input.AppId,
                    Components = components,
                });
            }

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                result = "succeeded",
                operation = input.Operation == "add" ? "AddAppComponents" : "RemoveAppComponents",
                appId = input.AppId,
                componentCount = components.Count,
            }));
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(JsonSerializer.Serialize(new
            {
                result = "blocked",
                category = "sdk_operation_error",
                message = "Dataverse SDK app component operation failed",
                exceptionType = exception.GetType().Name,
            }));
            return 1;
        }
    }

    private static void Validate(RequestInput input)
    {
        if (input.Operation is not ("add" or "remove" or "resolve") ||
            input.EnvironmentUrl.Scheme != Uri.UriSchemeHttps ||
            (input.Operation != "resolve" && input.AppId == Guid.Empty))
        {
            throw new InvalidOperationException("SDK request target is invalid");
        }
        if (input.ClientId == Guid.Empty || input.TenantId == Guid.Empty || !input.RedirectUri.IsLoopback)
        {
            throw new InvalidOperationException("SDK delegated OAuth configuration is invalid");
        }
        if (input.Components.Length == 0 || input.Components.Any(component =>
            (input.Operation != "resolve" && component.Id == Guid.Empty) ||
                !System.Text.RegularExpressions.Regex.IsMatch(component.LogicalName, "^[a-z][a-z0-9_]*$")))
        {
            throw new InvalidOperationException("SDK component identity is invalid");
        }
    }
}