import importlib.util
import base64
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "dataverse_web_api_executor", ROOT / "scripts" / "dataverse_web_api_executor.py"
)
executor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = executor
SPEC.loader.exec_module(executor)


class WebResourceRequestTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "component_type": "code_webres_js",
            "implementation_scope": "repository_and_dataverse_solution",
            "payload": {
                "name": "aks_/scripts/case_form.js",
                "schema_name": "aks_/scripts/case_form.js",
                "source_path": "scripts/case_form.js",
            },
            "authoring_target": {
                "component_projects": [
                    {
                        "component_type": "code_webres_*",
                        "path": "src/webresources",
                        "project_type": "web_resource_source",
                    }
                ]
            },
        }

    def test_builds_solution_aware_web_resource_create_request(self):
        request = executor.build_static_requests(
            self.row,
            "create",
            {"solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}},
        )[0]

        expected_content = base64.b64encode(
            (ROOT / "src/webresources/scripts/case_form.js").read_bytes()
        ).decode("ascii")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "webresourceset")
        self.assertEqual(request.solution_context, "header")
        self.assertEqual(request.body["name"], "aks_/scripts/case_form.js")
        self.assertEqual(request.body["displayname"], "aks_/scripts/case_form.js")
        self.assertEqual(request.body["webresourcetype"], 3)
        self.assertEqual(request.body["content"], expected_content)

    def test_builds_exact_web_resource_update_verify_and_publish_requests(self):
        capability = {"solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}}
        record_id = "11111111-1111-1111-1111-111111111111"

        update = executor.build_static_requests(
            self.row, "update", capability, resolved_id=record_id
        )[0]
        verify = executor.build_static_requests(
            self.row, "verify", {"solution_context": {"mechanism": "not_applicable"}}
        )[0]
        publish = executor.build_static_requests(
            self.row, "publish", {"solution_context": {"mechanism": "not_applicable"}},
            resolved_id=record_id,
        )[0]

        self.assertEqual(update.method, "PATCH")
        self.assertEqual(update.path, f"webresourceset({record_id})")
        self.assertIn("aks_%2Fscripts%2Fcase_form.js", verify.path)
        self.assertEqual(publish.path, "PublishXml")
        self.assertIn(record_id, publish.body["ParameterXml"])

    def test_resolves_web_resource_by_exact_canonical_name(self):
        request = executor.record_lookup_request(self.row)

        self.assertEqual(request.method, "GET")
        self.assertTrue(request.path.startswith("webresourceset?"))
        self.assertIn("aks_%2Fscripts%2Fcase_form.js", request.path)

    def test_web_resource_paths_are_runtime_whitelisted(self):
        paths = (
            ("POST", "webresourceset"),
            ("PATCH", "webresourceset(11111111-1111-1111-1111-111111111111)"),
            ("DELETE", "webresourceset(11111111-1111-1111-1111-111111111111)"),
            ("GET", "webresourceset?$select=webresourceid,name"),
        )

        for method, path in paths:
            with self.subTest(method=method, path=path):
                executor.validate_runtime_request(method, path)


class PluginRegistrationRequestTests(unittest.TestCase):
    def test_builds_solution_aware_plugin_assembly_create_request(self):
        row = {
            "component_type": "code_plugin",
            "payload": {
                "assembly": "ContosoService.Plugins",
                "class_name": "ContosoService.Plugins.MaintenanceJobCompletionPlugin",
                "schema_name": "ContosoService.Plugins.MaintenanceJobCompletionPlugin",
            },
        }

        request = executor.plugin_assembly_request(
            row,
            "create",
            assembly_content=b"signed-assembly",
        )

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "pluginassemblies")
        self.assertEqual(request.solution_context, "header")
        self.assertEqual(request.body["name"], "ContosoService.Plugins")
        self.assertEqual(request.body["sourcetype"], 0)
        self.assertEqual(request.body["isolationmode"], 2)
        self.assertEqual(
            request.body["content"],
            base64.b64encode(b"signed-assembly").decode("ascii"),
        )

    def test_builds_declared_update_step_and_preimage(self):
        step = {
            "name": "Maintenance Job Update completion and final-state guard",
            "message": "Update",
            "table": "aks_maintenancejob",
            "stage": "PreOperation",
            "mode": "Synchronous",
            "rank": 10,
            "run_as": "Calling User",
            "filtering_attributes": ["aks_stage"],
            "pre_image": {
                "alias": "PreImage",
                "columns": [
                    "aks_stage",
                    "aks_completeddate",
                    "aks_scheduleddate",
                    "aks_vehicleid",
                ],
            },
        }
        plugin_type_id = "11111111-1111-1111-1111-111111111111"
        message_id = "22222222-2222-2222-2222-222222222222"
        filter_id = "33333333-3333-3333-3333-333333333333"
        step_id = "44444444-4444-4444-4444-444444444444"

        body = executor.plugin_step_body(
            step,
            plugin_type_id=plugin_type_id,
            message_id=message_id,
            message_filter_id=filter_id,
        )
        image = executor.plugin_image_request(step, step_id)

        self.assertEqual(body["stage"], 20)
        self.assertEqual(body["mode"], 0)
        self.assertEqual(body["rank"], 10)
        self.assertEqual(body["filteringattributes"], "aks_stage")
        self.assertEqual(
            body["eventhandler_plugintype@odata.bind"],
            f"/plugintypes({plugin_type_id})",
        )
        self.assertNotIn("impersonatinguserid@odata.bind", body)
        self.assertEqual(image.path, "sdkmessageprocessingstepimages")
        self.assertEqual(image.body["imagetype"], 0)
        self.assertEqual(image.body["entityalias"], "PreImage")
        self.assertEqual(
            image.body["attributes"],
            "aks_completeddate,aks_scheduleddate,aks_stage,aks_vehicleid",
        )

    def test_builds_solution_aware_plugin_type_create_and_update_requests(self):
        row = {
            "payload": {
                "name": "Maintenance Job completion enforcement",
                "class_name": "ContosoService.Plugins.MaintenanceJobCompletionPlugin",
            }
        }
        assembly_id = "11111111-1111-1111-1111-111111111111"
        type_id = "22222222-2222-2222-2222-222222222222"

        create = executor.plugin_type_request(row, assembly_id)
        update = executor.plugin_type_request(row, assembly_id, record_id=type_id)

        self.assertEqual(create.method, "POST")
        self.assertEqual(create.path, "plugintypes")
        self.assertEqual(create.solution_context, "header")
        self.assertEqual(
            create.body["pluginassemblyid@odata.bind"],
            f"/pluginassemblies({assembly_id})",
        )
        self.assertEqual(
            create.body["typename"],
            "ContosoService.Plugins.MaintenanceJobCompletionPlugin",
        )
        self.assertEqual(update.method, "PATCH")
        self.assertEqual(update.path, f"plugintypes({type_id})")

    def test_plugin_registration_paths_are_runtime_whitelisted(self):
        paths = (
            ("POST", "pluginassemblies"),
            ("PATCH", "pluginassemblies(11111111-1111-1111-1111-111111111111)"),
            ("GET", "plugintypes?$select=plugintypeid,typename"),
            ("GET", "sdkmessages?$select=sdkmessageid,name"),
            ("GET", "sdkmessagefilters?$select=sdkmessagefilterid,primaryobjecttypecode"),
            ("POST", "sdkmessageprocessingsteps"),
            ("PATCH", "sdkmessageprocessingsteps(11111111-1111-1111-1111-111111111111)"),
            ("POST", "sdkmessageprocessingstepimages"),
            ("PATCH", "sdkmessageprocessingstepimages(11111111-1111-1111-1111-111111111111)"),
        )

        for method, path in paths:
            with self.subTest(method=method, path=path):
                executor.validate_runtime_request(method, path)


class PluginRegistrationExecutionTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "id": "DEV-0042",
            "component": "DES-04-CMP-002",
            "component_type": "code_plugin",
            "build_skill": "dataverse-procode",
            "status": "in_progress",
            "authentication_policy": "reuse_if_valid",
            "implementation_scope": "repository_and_dataverse_solution",
            "task_context_hash": "1" * 64,
            "source_plan_hash": "2" * 64,
            "authoring_target": {
                "environment_url": "https://org89912357.crm.dynamics.com",
                "solution_unique_name": "ContosoServicePluginAndCustomApi",
            },
            "payload": {
                "assembly": "ContosoService.Plugins",
                "schema_name": "ContosoService.Plugins.MaintenanceJobCompletionPlugin",
                "steps": [
                    {"name": "Create step", "message": "Create"},
                    {"name": "Update step", "message": "Update"},
                ],
            },
        }
        self.capability = {
            "http": {
                "method": "POST",
                "endpoint_family": "entity_set",
                "path_template": "pluginassemblies",
            },
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }

    def test_client_counts_successful_write_after_response(self):
        client = executor.DataverseClient(
            "https://example.crm.dynamics.com/api/data/v9.2", "token", "Solution"
        )
        response = mock.MagicMock()
        response.status = 204
        response.read.return_value = b""
        response.headers.get_content_type.return_value = "application/json"
        response.headers.get.return_value = ""
        response.__enter__.return_value = response

        with mock.patch.object(executor, "urlopen", return_value=response):
            client.request(executor.OperationRequest("POST", "pluginassemblies", {}, (), (), "header", "test"))

        self.assertEqual(client.write_attempt_count, 1)
        self.assertEqual(client.write_count, 1)

    def test_client_does_not_count_rejected_write_as_completed(self):
        client = executor.DataverseClient(
            "https://example.crm.dynamics.com/api/data/v9.2", "token", "Solution"
        )
        failure = HTTPError(
            "https://example.crm.dynamics.com/api/data/v9.2/pluginassemblies",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"error":{"code":"InvalidPluginAssemblyContent"}}'),
        )

        with (
            mock.patch.object(executor, "urlopen", side_effect=failure),
            self.assertRaises(executor.ExecutorError),
        ):
            client.request(executor.OperationRequest("POST", "pluginassemblies", {}, (), (), "header", "test"))

        self.assertEqual(client.write_attempt_count, 1)
        self.assertEqual(client.write_count, 0)

    def test_required_plugin_lookup_retries_empty_success_response(self):
        client = mock.Mock()
        client.request.side_effect = [
            executor.HttpResult(200, "", "", {"value": []}),
            executor.HttpResult(200, "", "", {"value": [{"plugintypeid": "type-id"}]}),
        ]

        with mock.patch.object(executor.time, "sleep") as sleep:
            result = executor.exact_plugin_row(
                client,
                executor.OperationRequest("GET", "plugintypes", None, (), (), "none", "test"),
                category="generated plug-in type",
                required=True,
                max_attempts=5,
            )

        self.assertEqual(result["plugintypeid"], "type-id")
        self.assertEqual(client.request.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_plugin_lookup_rejects_ambiguity_without_retry(self):
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {"value": [{"plugintypeid": "one"}, {"plugintypeid": "two"}]},
        )

        with self.assertRaises(executor.ExecutorError) as raised:
            executor.exact_plugin_row(
                client,
                executor.OperationRequest("GET", "plugintypes", None, (), (), "none", "test"),
                category="generated plug-in type",
                required=True,
                max_attempts=5,
            )

        self.assertEqual(raised.exception.category, "conflict_or_duplicate")
        self.assertEqual(client.request.call_count, 1)

    def test_plugin_failure_before_write_attempt_posts_no_evidence(self):
        client = mock.Mock(write_attempt_count=0, write_count=0)
        with (
            mock.patch.object(executor, "validate_executor_preflight", return_value=(self.capability, "https://example.crm.dynamics.com/api/data/v9.2", "Solution")),
            mock.patch.object(executor, "plugin_project_assembly_path", return_value=mock.Mock(read_bytes=mock.Mock(return_value=b"assembly-secret"))),
            mock.patch.object(executor, "acquire_token", return_value="token"),
            mock.patch.object(executor, "_transition_dev_to_in_progress"),
            mock.patch.object(executor, "DataverseClient", return_value=client),
            mock.patch.object(executor, "reconcile_plugin_registration", side_effect=executor.ExecutorError("dependency ambiguity")),
            mock.patch.object(executor, "post_evidence") as post,
            self.assertRaises(executor.ExecutorError) as raised,
        ):
            executor.execute(self.row, "create", 140, approval="", dry_run=False)

        self.assertFalse(raised.exception.action_invoked)
        post.assert_not_called()

    def test_rejected_plugin_write_posts_one_sanitized_blocked_evidence(self):
        client = mock.Mock(write_attempt_count=1, write_count=0)
        posted = []
        with (
            mock.patch.object(executor, "validate_executor_preflight", return_value=(self.capability, "https://example.crm.dynamics.com/api/data/v9.2", "Solution")),
            mock.patch.object(executor, "plugin_project_assembly_path", return_value=mock.Mock(read_bytes=mock.Mock(return_value=b"assembly-secret"))),
            mock.patch.object(executor, "acquire_token", return_value="token"),
            mock.patch.object(executor, "_transition_dev_to_in_progress"),
            mock.patch.object(executor, "DataverseClient", return_value=client),
            mock.patch.object(executor, "reconcile_plugin_registration", side_effect=executor.ExecutorError("Dataverse returned HTTP 400", category="validation_error", status=400)),
            mock.patch.object(executor, "post_evidence", side_effect=lambda payload, _issue: posted.append(payload) or {"result": "posted"}),
            self.assertRaises(executor.ExecutorError) as raised,
        ):
            executor.execute(self.row, "create", 140, approval="", dry_run=False)

        self.assertTrue(raised.exception.action_invoked)
        self.assertFalse(raised.exception.write_occurred)
        self.assertTrue(raised.exception.evidence_posted)
        self.assertEqual(len(posted), 1)
        self.assertFalse(posted[0]["write_occurred"])
        self.assertNotIn("assembly-secret", json.dumps(posted[0]))


class FakeClient:
    def __init__(self, *_args):
        self.request_count = 0
        self.posts = []

    def request_with_404_retries(self, request):
        if "Attributes(f74397ba-d298-f111-b8db-6045bd01db70)" in request.path:
            self.request_count += 1
            return executor.HttpResult(
                200,
                "",
                "",
                {
                    "MetadataId": "f74397ba-d298-f111-b8db-6045bd01db70",
                    "SchemaName": "aks_status",
                    "AttributeType": "Picklist",
                },
            )
        return self.request(request)

    def request(self, request):
        self.request_count += 1
        if request.method == "GET":
            if "LogicalName='aks_roadworthy'" in request.path:
                raise executor.ExecutorError(
                    "not found", category="not_found", status=404
                )
            schema_name = "aks_status" if "Attributes(" in request.path else ""
            return executor.HttpResult(
                200,
                "",
                "",
                {
                    "MetadataId": "998e2b9d-8f95-f111-8075-6045bd01d8e8",
                    "SchemaName": schema_name,
                    "AttributeType": "Picklist",
                    "RequiredLevel": {"Value": "ApplicationRequired"},
                },
            )
        self.posts.append(request)
        return executor.HttpResult(
            204,
            "https://example/Attributes(aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa)",
            "correlation-id",
            {},
        )


class ColumnDefinitionTests(unittest.TestCase):
    def test_plain_text_honors_explicit_length_and_auditing(self):
        definition = executor.column_definition(
            {
                "name": "aks_followupkind",
                "data_type": "Text",
                "max_length": 32,
                "auditing": "enabled",
                "required_level": "None",
            }
        )

        self.assertEqual(definition["MaxLength"], 32)
        self.assertEqual(
            definition["IsAuditEnabled"],
            {"Value": True, "CanBeChanged": True},
        )

    def test_bundled_put_verifies_exact_child_payload(self):
        row = {
            "component_type": "schema_table",
            "payload": {"table": "task", "schema_name": "task"},
        }
        expected = executor.column_definition(
            {
                "name": "aks_followupkind",
                "data_type": "Text",
                "max_length": 32,
                "auditing": "enabled",
                "required_level": "None",
            }
        )
        request = executor.OperationRequest(
            "PUT",
            "EntityDefinitions(LogicalName='task')/Attributes(LogicalName='aks_followupkind')",
            expected,
            tuple(expected),
            tuple(expected),
            "header",
            "recover exact child",
            expected_body=expected,
        )

        verification = executor.verification_request(row, request)
        self.assertIn("Attributes(LogicalName='aks_followupkind')", verification.path)
        self.assertTrue(
            executor.expected_payload_matches(
                row,
                request,
                {
                    "SchemaName": "aks_followupkind",
                    "AttributeType": "String",
                    "MaxLength": 32,
                    "RequiredLevel": {"Value": "None"},
                    "IsAuditEnabled": {"Value": True},
                },
            )
        )
        self.assertFalse(
            executor.expected_payload_matches(
                row,
                request,
                {
                    "SchemaName": "aks_followupkind",
                    "AttributeType": "String",
                    "MaxLength": 100,
                    "RequiredLevel": {"Value": "None"},
                    "IsAuditEnabled": {"Value": True},
                },
            )
        )

    def test_builds_dev_0016_base_column_types(self):
        datetime = executor.column_definition(
            {
                "name": "aks_scheduleddate",
                "data_type": "DateTime",
                "behavior": "UserLocal",
                "required_level": "Recommended",
            }
        )
        decimal = executor.column_definition(
            {
                "name": "aks_labourhours",
                "data_type": "Decimal",
                "precision": 2,
                "minimum": 0,
                "required_level": "None",
            }
        )
        currency = executor.column_definition(
            {
                "name": "aks_hourlyrate",
                "data_type": "Currency",
                "minimum": 0,
                "required_level": "None",
            }
        )

        self.assertEqual(datetime["AttributeType"], "DateTime")
        self.assertEqual(datetime["DateTimeBehavior"], {"Value": "UserLocal"})
        self.assertEqual(decimal["AttributeType"], "Decimal")
        self.assertEqual(decimal["Precision"], 2)
        self.assertEqual(currency["AttributeType"], "Money")
        self.assertEqual(currency["PrecisionSource"], 2)

    def test_builds_power_fx_formula_column(self):
        definition = executor.derived_column_definition(
            {
                "name": "aks_labourcost",
                "table": "aks_maintenancejob",
                "base_data_type": "decimal",
                "derived_type": "formula",
                "formula": "aks_labourhours * Decimal(aks_hourlyrate)",
                "required_level": "None",
            }
        )

        self.assertEqual(definition["SourceType"], 3)
        self.assertEqual(
            definition["FormulaDefinition"],
            "aks_labourhours * Decimal(aks_hourlyrate)",
        )

    def test_rejects_rollup_column_before_request(self):
        with self.assertRaises(executor.ExecutorError) as raised:
            executor.derived_column_definition(
                {
                    "name": "aks_totalpartscost",
                    "table": "aks_maintenancejob",
                    "base_data_type": "decimal",
                    "derived_type": "rollup",
                    "formula": None,
                    "rollup_spec": {
                        "related_entity": "aks_jobpart",
                        "aggregate_function": "SUM",
                        "aggregate_attribute": "aks_linevalue",
                    },
                    "required_level": "None",
                }
            )

        self.assertEqual(raised.exception.category, "unsupported_operation")
        self.assertFalse(raised.exception.action_invoked)


class MembershipOnlyIdentityTests(unittest.TestCase):
    def test_uses_compiler_approved_immutable_id_without_lookup(self):
        immutable_id = "600a01e0-3499-f111-b8db-6045bd01db1c"
        row = {
            "component_type": "uiux_form",
            "payload": {
                "immutable_id": immutable_id,
                "membership_only": True,
            },
        }
        client = mock.Mock()

        self.assertEqual(
            executor.resolve_component_object_id(row, client), immutable_id
        )
        client.request.assert_not_called()

    def test_rejects_invalid_membership_only_immutable_id(self):
        row = {
            "component_type": "uiux_view",
            "payload": {
                "immutable_id": "not-a-guid",
                "membership_only": True,
            },
        }

        with self.assertRaisesRegex(
            executor.ExecutorError,
            "membership-only component has no valid immutable ID",
        ):
            executor.resolve_component_object_id(row, mock.Mock())

    def test_remove_action_uses_component_object_id(self):
        object_id = "600a01e0-3499-f111-b8db-6045bd01db1c"
        membership_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        row = {
            "component_type": "uiux_form",
            "payload": {
                "immutable_id": object_id,
                "membership_only": True,
            },
            "authoring_target": {
                "solution_unique_name": "ContosoServiceApps",
            },
        }

        with (
            mock.patch.object(
                executor,
                "resolve_solution_id",
                return_value="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            ),
            mock.patch.object(
                executor,
                "solution_component_rows",
                return_value=[
                    {
                        "componenttype": 60,
                        "solutioncomponentid": membership_id,
                    }
                ],
            ),
        ):
            request, resolved_id = executor.solution_action_request(
                row, "remove_solution_component", mock.Mock()
            )

        self.assertEqual(resolved_id, object_id)
        self.assertEqual(
            request.body["SolutionComponent"]["solutioncomponentid"], object_id
        )
        self.assertNotEqual(
            request.body["SolutionComponent"]["solutioncomponentid"], membership_id
        )

    def test_membership_only_row_verification_targets_immutable_id(self):
        immutable_id = "600a01e0-3499-f111-b8db-6045bd01db1c"
        row = {
            "component_type": "uiux_form",
            "payload": {"membership_only": True},
        }

        request = executor.row_verification_request_by_id(row, immutable_id)

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.path,
            f"systemforms({immutable_id})?$select=formid",
        )

    def test_membership_only_verification_skips_cleanup_payload_comparison(self):
        immutable_id = "600a01e0-3499-f111-b8db-6045bd01db1c"
        solution_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        row = {
            "component_type": "uiux_form",
            "implementation_scope": "repository_and_dataverse_solution",
            "payload": {"membership_only": True},
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {"formid": immutable_id},
        )

        with (
            mock.patch.object(
                executor, "resolve_solution_id", return_value=solution_id
            ),
            mock.patch.object(
                executor, "effective_solution_component_rows", return_value=[]
            ),
            mock.patch.object(executor, "expected_payload_matches") as payload_match,
        ):
            verification, resolved_id = executor.verify_result(
                row,
                client,
                immutable_id,
                deleted=False,
                membership_removed=True,
            )

        self.assertEqual(resolved_id, immutable_id)
        self.assertEqual(verification["identity"], "matched")
        self.assertEqual(verification["membership"], "matched")
        payload_match.assert_not_called()

    def test_existing_form_membership_resolution_uses_row_lookup(self):
        immutable_id = "d0031527-4399-f111-b8db-6045bd01d8e8"
        row = {
            "component_type": "uiux_form",
            "payload": {
                "form_type": "Main",
                "name": "Vehicle — Main",
                "table": "aks_vehicle",
            },
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {
                "value": [
                    {
                        "formid": immutable_id,
                        "name": "Vehicle — Main",
                        "objecttypecode": "aks_vehicle",
                        "type": 2,
                    }
                ]
            },
        )

        resolved_id = executor.resolve_component_object_id(row, client)

        self.assertEqual(resolved_id, immutable_id)
        request = client.request.call_args.args[0]
        self.assertEqual(request.method, "GET")
        self.assertTrue(request.path.startswith("systemforms?"))


class MembershipAddVerificationTests(unittest.TestCase):
    def test_form_effective_membership_includes_parent_table(self):
        inherited = [
            {
                "componenttype": 1,
                "rootcomponentbehavior": 0,
                "_solutionid_value": "6e0dd563-bd3d-f011-b4cc-7c1e521687a1",
            }
        ]
        row = {
            "component_type": "uiux_form",
            "payload": {"table": "aks_vehicle"},
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {"MetadataId": "96b5fd64-5d98-f111-b8db-6045bd01db70"},
        )

        with mock.patch.object(
            executor,
            "solution_component_rows",
            side_effect=[[], inherited],
        ) as membership_rows:
            rows = executor.effective_solution_component_rows(
                row,
                client,
                "d0031527-4399-f111-b8db-6045bd01d8e8",
                solution_id="6e0dd563-bd3d-f011-b4cc-7c1e521687a1",
            )

        self.assertEqual(rows, inherited)
        self.assertEqual(membership_rows.call_count, 2)
        self.assertIn(
            "EntityDefinitions(LogicalName='aks_vehicle')",
            client.request.call_args.args[0].path,
        )

    def test_derived_column_effective_membership_includes_parent_table(self):
        inherited = [
            {
                "componenttype": 1,
                "rootcomponentbehavior": 0,
                "_solutionid_value": "6e0dd563-bd3d-f011-b4cc-7c1e521687a1",
            }
        ]
        row = {
            "component_type": "schema_derived_column",
            "payload": {"table": "aks_jobpart"},
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {"MetadataId": "96b5fd64-5d98-f111-b8db-6045bd01db70"},
        )

        with mock.patch.object(
            executor,
            "solution_component_rows",
            side_effect=[[], inherited],
        ):
            rows = executor.effective_solution_component_rows(
                row,
                client,
                "1032d5a1-9399-f111-b8db-6045bd01db70",
                solution_id="6e0dd563-bd3d-f011-b4cc-7c1e521687a1",
            )

        self.assertEqual(rows, inherited)
        self.assertIn(
            "EntityDefinitions(LogicalName='aks_jobpart')",
            client.request.call_args.args[0].path,
        )

    def test_membership_lookup_filters_solution_after_exact_object_query(self):
        object_id = "d0031527-4399-f111-b8db-6045bd01d8e8"
        solution_id = "6E0DD563-BD3D-F011-B4CC-7C1E521687A1"
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {
                "value": [
                    {
                        "objectid": object_id,
                        "componenttype": 60,
                        "_solutionid_value": solution_id,
                    },
                    {
                        "objectid": object_id,
                        "componenttype": 60,
                        "_solutionid_value": "8ae58873-4d20-f111-998a-7c1e521687a1",
                    },
                ]
            },
        )

        rows = executor.solution_component_rows(
            client,
            object_id,
            solution_id=solution_id,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["_solutionid_value"], solution_id)
        path = client.request.call_args.args[0].path
        self.assertIn("objectid+eq+" + object_id, path)
        self.assertNotIn("_solutionid_value+eq", path)

    def test_form_add_uses_documented_type_without_existing_membership(self):
        object_id = "d0031527-4399-f111-b8db-6045bd01d8e8"
        row = {
            "component_type": "uiux_form",
            "authoring_target": {"solution_unique_name": "ContosoServiceCore"},
        }
        client = mock.Mock()

        with (
            mock.patch.object(executor, "resolve_solution_id"),
            mock.patch.object(
                executor,
                "resolve_component_object_id",
                return_value=object_id,
            ),
            mock.patch.object(executor, "solution_component_rows") as memberships,
        ):
            request, resolved_id = executor.solution_action_request(
                row,
                "add_solution_component",
                client,
            )

        self.assertEqual(resolved_id, object_id)
        self.assertEqual(request.body["ComponentType"], 60)
        memberships.assert_not_called()

    def test_derived_column_add_uses_documented_type_without_existing_membership(self):
        object_id = "1032d5a1-9399-f111-b8db-6045bd01db70"
        row = {
            "component_type": "schema_derived_column",
            "authoring_target": {"solution_unique_name": "ContosoServiceCore"},
        }
        client = mock.Mock()

        with (
            mock.patch.object(executor, "resolve_solution_id"),
            mock.patch.object(
                executor,
                "resolve_component_object_id",
                return_value=object_id,
            ),
            mock.patch.object(executor, "solution_component_rows") as memberships,
        ):
            request, resolved_id = executor.solution_action_request(
                row,
                "add_solution_component",
                client,
            )

        self.assertEqual(resolved_id, object_id)
        self.assertEqual(request.body["ComponentType"], 2)
        memberships.assert_not_called()

    def test_dev_0033_create_shape_resolves_live_subgrid_id(self):
        context = executor.P.read_context(executor.P.TASK_CONTEXT_PATH)
        row = next(task for task in context["tasks"] if task["id"] == "DEV-0033")
        view_id = "ad45c3e1-3c99-f111-b8db-6045bd01db70"
        client = mock.Mock()

        with mock.patch.object(
            executor,
            "resolve_record_id",
            return_value=view_id,
        ):
            subgrid_context = executor.resolve_form_subgrid_context(row, client)
            request = executor.build_static_requests(
                row,
                "create",
                executor.capability_for(row, "create"),
                form_subgrid_context=subgrid_context,
            )[0]

        self.assertIn(view_id.upper(), request.body["formxml"])
        self.assertNotIn("{SAVEDQUERY_ID}", request.body["formxml"])


class BundledRecoveryTests(unittest.TestCase):
    def test_metadata_put_verification_retries_stale_payload(self):
        metadata_id = "3d58a33a-0e9f-f111-b8dc-6045bd01db70"
        row = {
            "component_type": "schema_table",
            "implementation_scope": "repository_only",
            "payload": {"table": "task"},
        }
        expected = {
            "SchemaName": "aks_followupkey",
            "AttributeType": "String",
            "MaxLength": 200,
            "RequiredLevel": {"Value": "None"},
            "IsAuditEnabled": {"Value": True},
        }
        request = executor.OperationRequest(
            "PUT",
            "EntityDefinitions(LogicalName='task')/Attributes(LogicalName='aks_followupkey')",
            expected,
            tuple(expected),
            tuple(expected),
            "header",
            "recover exact child",
            expected_body=expected,
        )
        client = mock.Mock()
        client.request_with_404_retries.side_effect = [
            executor.HttpResult(
                200,
                "",
                "",
                {
                    "MetadataId": metadata_id,
                    "SchemaName": "aks_followupkey",
                    "AttributeType": "String",
                    "MaxLength": 100,
                    "RequiredLevel": {"Value": "None"},
                    "IsAuditEnabled": {"Value": True},
                },
            ),
            executor.HttpResult(
                200,
                "",
                "",
                {"@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata", **expected, "MetadataId": metadata_id},
            ),
        ]

        with mock.patch.object(executor.time, "sleep") as sleep:
            verification, resolved_id = executor.verify_result(
                row,
                client,
                metadata_id,
                deleted=False,
                request=request,
            )

        self.assertEqual(verification["payload"], "matched")
        self.assertEqual(resolved_id, metadata_id)
        self.assertEqual(client.request_with_404_retries.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_evidence_omits_odata_annotation_from_changed_fields(self):
        row = {
            "id": "DEV-0047",
            "component": "DES-05-CMP-003",
            "component_type": "schema_table",
            "build_skill": "dataverse-table",
            "implementation_scope": "repository_and_dataverse_solution",
            "task_context_hash": "1" * 64,
            "source_plan_hash": "2" * 64,
            "payload": {"schema_name": "task", "table": "task"},
            "authoring_target": {
                "environment_url": "https://org89912357.crm.dynamics.com",
                "solution_unique_name": "ContosoServiceCore",
            },
        }
        request = executor.OperationRequest(
            "PUT",
            "metadata",
            {},
            ("@odata.type", "MaxLength"),
            ("@odata.type", "MaxLength"),
            "header",
            "recover exact child",
        )

        payload = executor.evidence_payload(
            row,
            161,
            "update",
            request,
            result="blocked",
            status="verification mismatch",
            error_code="verification_mismatch",
            message="payload mismatch",
            immutable_id="3d58a33a-0e9f-f111-b8dc-6045bd01db70",
            correlation_id="",
            verification={"identity": "matched", "payload": "mismatch", "membership": "not-run"},
            write_occurred=True,
        )

        self.assertEqual(payload["response"]["changed_fields"], ["MaxLength"])

    def test_bundled_child_inherits_parent_table_solution_membership(self):
        row = {
            "component_type": "schema_table",
            "payload": {"table": "aks_vehicle"},
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "",
            {"MetadataId": "5f484590-ad95-f111-8075-6045bd01d8e8"},
        )
        parent_membership = {
            "componenttype": 1,
            "rootcomponentbehavior": 0,
            "_solutionid_value": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        }

        with mock.patch.object(
            executor,
            "solution_component_rows",
            side_effect=[[], [parent_membership]],
        ) as membership_rows:
            rows = executor.effective_solution_component_rows(
                row,
                client,
                "f74397ba-d298-f111-b8db-6045bd01db70",
                solution_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            )

        self.assertEqual(rows, [parent_membership])
        self.assertEqual(membership_rows.call_count, 2)
        self.assertEqual(
            membership_rows.call_args_list[1].args[1],
            "5f484590-ad95-f111-8075-6045bd01d8e8",
        )

    def test_bundled_publish_verifies_each_child_not_parent_table(self):
        row = {
            "component_type": "schema_table",
            "implementation_scope": "repository_and_dataverse_solution",
            "payload": {
                "operation": "extend",
                "schema_name": "aks_maintenancejob",
                "table": "aks_maintenancejob",
                "columns": [
                    {
                        "name": "aks_labourhours",
                        "data_type": "Decimal",
                        "required_level": "None",
                    },
                    {
                        "name": "aks_hourlyrate",
                        "data_type": "Currency",
                        "required_level": "None",
                    },
                ],
            },
        }
        publish_request = executor.OperationRequest(
            "POST",
            "PublishXml",
            {"ParameterXml": "<importexportxml />"},
            ("ParameterXml",),
            ("published_customizations",),
            "none",
            "publish only the exact component scope",
        )

        with (
            mock.patch.object(
                executor,
                "capability_for",
                return_value={
                    "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}
                },
            ),
            mock.patch.object(
                executor,
                "verify_result",
                side_effect=[
                    ({"identity": "matched", "payload": "matched", "membership": "matched"}, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                    ({"identity": "matched", "payload": "matched", "membership": "matched"}, "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                ],
            ) as verify,
        ):
            result, immutable_id = executor.verify_publish_result(
                row, mock.Mock(), publish_request
            )

        self.assertEqual(result["membership"], "matched")
        self.assertEqual(immutable_id, "")
        self.assertEqual(verify.call_count, 2)
        verified_requests = [call.kwargs["request"] for call in verify.call_args_list]
        self.assertEqual(
            [request.body["SchemaName"] for request in verified_requests],
            ["aks_labourhours", "aks_hourlyrate"],
        )
        self.assertTrue(
            all(request.path.endswith("/Attributes") for request in verified_requests)
        )

    def test_execute_skips_status_and_posts_only_roadworthy(self):
        capability = {
            "http": {"method": "POST", "endpoint_family": "metadata", "path_template": "EntityDefinitions(LogicalName='{table}')/Attributes"},
            "recovery_http": {"method": "PUT", "endpoint_family": "metadata", "path_template": "EntityDefinitions(LogicalName='{table}')/Attributes(LogicalName='{identity}')"},
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }
        row = {
            "id": "DEV-0025",
            "component": "DES-02-CMP-001",
            "component_type": "schema_table",
            "build_skill": "dataverse-table",
            "status": "in_progress",
            "authentication_policy": "reuse_if_valid",
            "implementation_scope": "repository_and_dataverse_solution",
            "task_context_hash": "1" * 64,
            "source_plan_hash": "2" * 64,
            "authoring_target": {
                "environment_url": "https://org89912357.crm.dynamics.com",
                "solution_unique_name": "ContosoServiceCore",
            },
            "payload": {
                "operation": "extend",
                "schema_name": "aks_vehicle",
                "table": "aks_vehicle",
                "columns": [
                    {"name": "aks_status", "data_type": "Choice", "choice": "aks_vehiclestatus", "required_level": "ApplicationRequired"},
                    {"name": "aks_roadworthy", "data_type": "Boolean", "required_level": "ApplicationRequired"},
                ],
            },
        }
        client = FakeClient()
        posted = []

        def verify(_row, _client, immutable_id, **_kwargs):
            return ({"identity": "matched", "payload": "matched", "membership": "matched"}, immutable_id)

        with (
            mock.patch.object(executor, "validate_bundled_recovery_evidence"),
            mock.patch.object(executor, "validate_executor_preflight", return_value=(capability, "https://org89912357.crm.dynamics.com/api/data/v9.2", "ContosoServiceCore")) as preflight,
            mock.patch.object(executor, "acquire_token", return_value="token"),
            mock.patch.object(executor, "_transition_dev_to_in_progress"),
            mock.patch.object(executor, "DataverseClient", return_value=client),
            mock.patch.object(executor, "verify_result", side_effect=verify),
            mock.patch.object(executor, "validate_capability_request"),
            mock.patch.object(executor, "post_evidence", side_effect=lambda payload, _issue: posted.append(payload) or {"result": "posted"}),
        ):
            outputs = executor.execute(
                row,
                "verify",
                57,
                approval="",
                dry_run=False,
                verification_id="f74397ba-d298-f111-b8db-6045bd01db70",
            )

        self.assertEqual(preflight.call_args.args[1], "update")
        self.assertEqual(
            [(request.expected_body or request.body)["SchemaName"] for request in client.posts],
            ["aks_status", "aks_roadworthy"],
        )
        self.assertEqual([request.method for request in client.posts], ["PUT", "POST"])
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["request"]["operation"], "complete bundled schema_table extension recovery")
        self.assertEqual(posted[0]["operation"]["api_operation"], "complete bundled schema_table extension recovery")
        self.assertEqual(outputs[0]["evidence"], "posted")


class LegacyFormPayloadTests(unittest.TestCase):
    def test_dev_0026_quick_create_payload_is_normalized(self):
        payload = {
            "form_type": "Quick Create",
            "name": "Vehicle Quick Create",
            "schema_name": "aks_vehicle_quickcreate",
            "sections": [
                {
                    "columns": ["aks_registrationnumber", "aks_vin"],
                    "name": "Vehicle identifiers",
                }
            ],
            "table": "aks_vehicle",
        }

        self.assertEqual(executor.form_type_code(payload), 7)
        form_xml = executor.formxml(payload)

        self.assertIn('section name="vehicle_identifiers"', form_xml)
        self.assertIn('description="Vehicle identifiers"', form_xml)
        self.assertIn('datafieldname="aks_registrationnumber"', form_xml)
        self.assertIn('datafieldname="aks_vin"', form_xml)

    def test_legacy_form_normalization_runs_through_request_builder(self):
        payload = {
            "form_type": "Quick Create",
            "name": "Vehicle Quick Create",
            "schema_name": "aks_vehicle_quickcreate",
            "sections": [
                {
                    "columns": ["aks_registrationnumber", "aks_vin"],
                    "name": "Vehicle identifiers",
                }
            ],
            "table": "aks_vehicle",
        }
        row = {
            "component_type": "uiux_form",
            "payload": payload,
            "authoring_target": {"solution_unique_name": "ContosoServiceApps"},
        }
        capability = {
            "http": {
                "method": "POST",
                "endpoint_family": "entity_set",
                "path_template": "systemforms",
            },
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }

        request = executor.build_static_requests(row, "create", capability)[0]

        self.assertEqual(request.path, "systemforms")
        self.assertEqual(request.body["type"], 7)
        self.assertIn('section name="vehicle_identifiers"', request.body["formxml"])


class LegacyViewPayloadTests(unittest.TestCase):
    def test_dev_0029_numeric_choice_filter_runs_through_request_builder(self):
        row = {
            "component_type": "uiux_view",
            "payload": {
                "columns": [
                    "aks_registrationnumber (sort ascending)",
                    "aks_vin",
                    "aks_status",
                    "aks_roadworthy",
                    "aks_depotid",
                ],
                "filter": "aks_status equals 74873 (Active)",
                "name": "Active Vehicles",
                "schema_name": "aks_activevehicles",
                "table": "aks_vehicle",
            },
            "authoring_target": {"solution_unique_name": "ContosoServiceApps"},
        }
        capability = {
            "http": {
                "method": "POST",
                "endpoint_family": "entity_set",
                "path_template": "savedqueries",
            },
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }

        request = executor.build_static_requests(row, "create", capability)[0]

        self.assertIn(
            '<condition attribute="aks_status" operator="eq" value="74873" />',
            request.body["fetchxml"],
        )
        self.assertIn(
            '<order attribute="aks_registrationnumber" descending="false" />',
            request.body["fetchxml"],
        )

    def test_dev_0027_inline_sort_runs_through_request_builder(self):
        row = {
            "component_type": "uiux_view",
            "payload": {
                "columns": [
                    "aks_jobnumber (sort descending)",
                    "aks_technicianid",
                    "createdon",
                    "modifiedon",
                ],
                "filter": (
                    "Related Maintenance Jobs through aks_vehicle_maintenancejob "
                    "for the current Vehicle"
                ),
                "name": "Vehicle Maintenance History",
                "schema_name": "aks_vehicle_maintenancehistory",
                "table": "aks_maintenancejob",
            },
            "authoring_target": {"solution_unique_name": "ContosoServiceApps"},
        }
        capability = {
            "http": {
                "method": "POST",
                "endpoint_family": "entity_set",
                "path_template": "savedqueries",
            },
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }

        request = executor.build_static_requests(row, "create", capability)[0]

        self.assertEqual(request.path, "savedqueries")
        self.assertEqual(request.body["querytype"], 0)
        self.assertIn('<attribute name="aks_jobnumber" />', request.body["fetchxml"])
        self.assertIn(
            '<order attribute="aks_jobnumber" descending="true" />',
            request.body["fetchxml"],
        )
        self.assertNotIn("aks_vehicle_maintenancejob", request.body["fetchxml"])


class LegacyMainFormSubgridTests(unittest.TestCase):
    @staticmethod
    def current_row(dev_id):
        context = executor.P.read_context(executor.P.TASK_CONTEXT_PATH)
        return next(row for row in context["tasks"] if row["id"] == dev_id)

    def test_dev_0028_related_records_subgrid_runs_through_request_builder(self):
        row = {
            "component_type": "uiux_form",
            "payload": {
                "form_type": "Main",
                "name": "Vehicle Main",
                "schema_name": "aks_vehicle_main",
                "sections": [
                    {"name": "Header", "columns": ["aks_status", "aks_roadworthy"]},
                    {
                        "name": "Maintenance history",
                        "read_only": True,
                        "records": "Only Related Records",
                        "relationship": "aks_vehicle_maintenancejob",
                        "subgrid": "aks_vehicle_maintenancehistory",
                    },
                ],
                "table": "aks_vehicle",
            },
            "authoring_target": {"solution_unique_name": "ContosoServiceApps"},
        }
        capability = {
            "http": {
                "method": "POST",
                "endpoint_family": "entity_set",
                "path_template": "systemforms",
            },
            "solution_context": {"mechanism": "MSCRM.SolutionUniqueName"},
        }

        request = executor.build_static_requests(
            row,
            "create",
            capability,
            form_subgrid_context={
                "aks_vehicle_maintenancehistory": {
                    "table": "aks_maintenancejob",
                    "view_id": "ad45c3e1-3c99-f111-b8db-6045bd01db70",
                }
            },
        )[0]

        self.assertEqual(request.path, "systemforms")
        self.assertIn('control id="aks_vehicle_maintenancehistory"', request.body["formxml"])
        self.assertIn("<TargetEntityType>aks_maintenancejob</TargetEntityType>", request.body["formxml"])
        self.assertIn("<RelationshipName>aks_vehicle_maintenancejob</RelationshipName>", request.body["formxml"])
        self.assertIn("{AD45C3E1-3C99-F111-B8DB-6045BD01DB70}", request.body["formxml"])
        self.assertIn("<IsUserView>false</IsUserView>", request.body["formxml"])
        self.assertIn("<ChartGridMode>Grid</ChartGridMode>", request.body["formxml"])
        self.assertNotIn("<ViewIds>", request.body["formxml"])
        normalized = request.body["formxml"].replace(
            "</parameters>", "<EnableViewPicker>false</EnableViewPicker></parameters>"
        ).replace("<form>", '<form addedbyplatform="true">')
        self.assertTrue(
            executor.formxml_semantically_matches(request.body["formxml"], normalized)
        )
        self.assertFalse(
            executor.formxml_semantically_matches(
                request.body["formxml"],
                normalized.replace(
                    "aks_vehicle_maintenancejob", "aks_vehicle_wrongrelationship"
                ),
            )
        )

    def test_dev_0033_context_resolves_exact_compiler_view_dependency(self):
        row = self.current_row("DEV-0033")

        context = executor.resolve_form_subgrid_context(row)

        self.assertEqual(
            context,
            {
                "aks_vehicle_maintenancehistory": {
                    "table": "aks_maintenancejob",
                    "view_id": "{savedquery_id}",
                }
            },
        )

    def test_form_verification_preserves_resolved_expected_xml(self):
        row = self.current_row("DEV-0033")
        capability = executor.capability_for(row, "create")
        context = {
            "aks_vehicle_maintenancehistory": {
                "table": "aks_maintenancejob",
                "view_id": "ad45c3e1-3c99-f111-b8db-6045bd01db70",
            }
        }
        create_request = executor.build_static_requests(
            row, "create", capability, form_subgrid_context=context
        )[0]

        verify_request = executor.verification_request(row, create_request)

        self.assertEqual(verify_request.method, "GET")
        self.assertIsNone(verify_request.body)
        self.assertEqual(verify_request.expected_body, create_request.body)


if __name__ == "__main__":
    unittest.main()