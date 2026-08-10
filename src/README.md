# Solution source

Store unpacked, reviewable source artifacts here. Generated binaries and packed
solution archives belong in ignored build-output directories, not in source
control.

## Layout

```text
src/
  plugins/
    ContosoService.Plugins/     Signed net462 class library — plug-ins AND Custom
                                APIs share this one assembly (pac plugin init).
  webresources/                 Client-side JS/HTML/CSS (publisher prefix aks).
  solutions/                    One unpacked folder per component-segmented
                                solution — each is the unpack_path from
                                .d365/authoring-targets.yml, populated on the
                                first verified export/unpack:
    ContosoServiceCore/                 schema_*
    ContosoServiceConfig/               config_* (excl. env-bound queue/audit)
    ContosoServiceApps/                 uiux_*
    ContosoServiceWebResource/          code_webres_*, code_pcf
    ContosoServicePluginAndCustomApi/   code_plugin, code_custom_api
    ContosoServiceSecurity/             sec_role, sec_field_profile
    ContosoServiceAutomation/           flow_*, integ_*, mcs_*
```

| Source area | Component types | Solution (unpack_path) | Build skill |
| --- | --- | --- | --- |
| `plugins/` | `code_plugin`, `code_custom_api` | `ContosoServicePluginAndCustomApi` | `dataverse-procode` |
| `webresources/` | `code_webres_*` | `ContosoServiceWebResource` | `dataverse-procode` |
| `solutions/<name>/` | per-family (see layout) | itself | ALM packaging |

Component types route to solutions through `routing`, and the source projects
rebuilt before export are declared per solution under `component_projects` — both
in [../.d365/authoring-targets.yml](../.d365/authoring-targets.yml).

## Identity

Publisher `AnandPOC`, prefix `aks`, authoring environment
`https://org89912357.crm.dynamics.com`. Seven component-segmented solutions share
this one publisher so components stay layer-compatible — see
[../.d365/authoring-targets.yml](../.d365/authoring-targets.yml).

## Build

```powershell
# Plug-ins / Custom APIs (rebuilt before the plug-in solution is exported)
dotnet build src/plugins/ContosoService.Plugins/ContosoService.Plugins.csproj

# Web resources are static source — no build step. Per-solution pack/unpack
# commands live in solutions/README.md.
```
