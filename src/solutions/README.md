# Solution source (component-segmented)

Unpacked, source-controlled form of the **Contoso Service** Dataverse solutions,
managed with SolutionPackager (`pac solution pack` / `unpack`) — no `.cdsproj` /
MSBuild solution project.

Components are split across seven single-publisher solutions so each layer ships
independently. Each folder below is the `unpack_path` declared for that solution
in [../../.d365/authoring-targets.yml](../../.d365/authoring-targets.yml) and is
populated on the first verified export/unpack, so a folder may hold only
`.gitkeep` until its first component is built.

| Solution unique name | Folder | Component families |
| --- | --- | --- |
| `ContosoServiceCore` | `ContosoServiceCore/` | `schema_*` |
| `ContosoServiceConfig` | `ContosoServiceConfig/` | `config_*` (excl. env-bound queue/audit) |
| `ContosoServiceApps` | `ContosoServiceApps/` | `uiux_*` |
| `ContosoServiceWebResource` | `ContosoServiceWebResource/` | `code_webres_*`, `code_pcf` |
| `ContosoServicePluginAndCustomApi` | `ContosoServicePluginAndCustomApi/` | `code_plugin`, `code_custom_api` |
| `ContosoServiceSecurity` | `ContosoServiceSecurity/` | `sec_role`, `sec_field_profile` |
| `ContosoServiceAutomation` | `ContosoServiceAutomation/` | `flow_*`, `integ_*`, `mcs_*` |

Shared identity: publisher `AnandPOC`, prefix `aks`, authoring environment
`https://org89912357.crm.dynamics.com`. Packed/exported `*.zip` archives go to
`_out/` and are git-ignored.

> Live `pac` commands require an interactive sign-in to the authoring
> environment. Only ever authenticate against `org89912357.crm.dynamics.com`.

## One-time: authenticate

```powershell
pac auth create --environment https://org89912357.crm.dynamics.com
```

## Pull a solution into source

Export the unmanaged solution and unpack it over its own folder (run from the
repo root; substitute the unique name and matching unpack_path folder):

```powershell
pac solution export --name ContosoServiceCore --path src\solutions\_out --managed false --overwrite
pac solution unpack --zipfile src\solutions\_out\ContosoServiceCore.zip --folder src\solutions\ContosoServiceCore --packagetype Unmanaged --allowDelete
```

## Pack a solution from source

```powershell
# Unmanaged (dev)
pac solution pack --zipfile src\solutions\_out\ContosoServiceCore.zip --folder src\solutions\ContosoServiceCore --packagetype Unmanaged

# Managed (release)
pac solution pack --zipfile src\solutions\_out\ContosoServiceCore_managed.zip --folder src\solutions\ContosoServiceCore --packagetype Managed
```

## Plug-ins / Custom APIs

The plug-in assembly is built separately ([../plugins](../plugins)); plug-ins and
Custom APIs share the one `ContosoService.Plugins.dll`. It is declared as a
`component_projects` entry on `ContosoServicePluginAndCustomApi` (project_type
`dotnet_class_library`), so the framework rebuilds it before that solution is
exported. Register it once (Plugin Registration Tool or Maker portal) so the
assembly, its steps, and Custom APIs become solution components:

```powershell
dotnet build src\plugins\ContosoService.Plugins\ContosoService.Plugins.csproj -c Release
pac plugin push --type Assembly --pluginId <assembly-id> --pluginFile src\plugins\ContosoService.Plugins\bin\Release\net462\ContosoService.Plugins.dll
```

Then `pac solution export` + `unpack` for `ContosoServicePluginAndCustomApi`
captures the registration and Custom API metadata.

## Build outputs

`_out/` and any `*.zip` are build artifacts and are git-ignored — commit only the
unpacked source under each solution folder.
