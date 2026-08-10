"use strict";

// Web resource authored here, packaged into the solution as: aks_/scripts/case_form.js
//
// Registration (declarative, travels with the solution):
//   Form Properties -> Events -> Form Libraries: add this web resource.
//   Event Handlers: OnLoad -> Contoso.CaseForm.onLoad, OnSave -> Contoso.CaseForm.onSave.
//   Always tick "Pass execution context as first parameter".
//
// Ground rules (see dataverse-procode / code_webres reference):
//   - Business rules first; JavaScript only for what rules can't express.
//   - Use the supported client API (Xrm) and formContext — never global Xrm.Page
//     or DOM manipulation. Client-side checks are UX, not security.
var Contoso = window.Contoso || {};

Contoso.CaseForm = (function () {
    function onLoad(executionContext) {
        var formContext = executionContext.getFormContext();

        // TODO: real load logic. Prefer form-property registration over runtime
        // addOnChange/addOnSave inside OnLoad (which fires handlers repeatedly).
        void formContext;
    }

    function onSave(executionContext) {
        var formContext = executionContext.getFormContext();
        var eventArgs = executionContext.getEventArgs();

        // Example guard: block save when a required field is empty.
        // var title = formContext.getAttribute("title");
        // if (title && !title.getValue()) {
        //     eventArgs.preventDefault();
        //     formContext.ui.setFormNotification("Title is required.", "ERROR", "title_required");
        // }
        void eventArgs;
    }

    return {
        onLoad: onLoad,
        onSave: onSave
    };
})();
