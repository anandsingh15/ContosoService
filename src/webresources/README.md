# Web resources

Client-side web resources (JavaScript, HTML, CSS, images) authored as reviewable
source, then packaged into the `ContosoService` solution.

## Naming

All web resources carry the publisher prefix **`aks`**. The web resource *name*
uses a virtual path, e.g. this folder's script is registered as:

```text
aks_/scripts/case_form.js
```

Keep the physical path under `src/webresources/` aligned with the virtual name so
source and solution content stay easy to correlate.

## Layout

```text
src/webresources/
  scripts/      JavaScript form/ribbon libraries (client API)
  html/         HTML web resources (optional)
  css/          Stylesheets (optional)
  images/       Icons and images (optional)
```

## How these reach the solution

Web resources are solution components. To bind a script to the `ContosoService`
solution use the standard export -> unpack cycle (see
[../solutions/README.md](../solutions/README.md)); the unpacked resource appears
under the solution's `src/WebResources/` with a `.data.xml` metadata sidecar.
Author and review the code here, register events declaratively on the form, and
let the solution pack carry the component.

## Rules

- Business rules first — use JavaScript only for logic rules cannot express.
- Use the supported client API (`Xrm`, `formContext`); never `Xrm.Page` or direct
  DOM manipulation.
- Pass the execution context as the first handler parameter and resolve
  `formContext` from it.
- Client-side validation is UX only, never a security control.
