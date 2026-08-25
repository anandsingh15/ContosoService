import importlib.util
import base64
import io
import json
import sys
import unittest
import xml.etree.ElementTree as ET
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


class AppModuleRequestTests(unittest.TestCase):
    APP_ID = "11111111-1111-1111-1111-111111111111"
    TABLE_ID = "22222222-2222-2222-2222-222222222222"
    TABLE_COMPONENT_ID = "88888888-8888-8888-8888-888888888888"
    ROLE_ID = "33333333-3333-3333-3333-333333333333"
    SITEMAP_ID = "44444444-4444-4444-4444-444444444444"
    BUSINESS_UNIT_ID = "55555555-5555-5555-5555-555555555555"

    def setUp(self):
        profiles = executor.P.load_dataverse_capabilities()["profiles"]
        self.app_capability = profiles["app-create"]
        self.app_update_capability = profiles["app-update"]
        self.app_delete_capability = profiles["app-delete"]
        self.sitemap_capability = profiles["sitemap-create"]

    def test_sdk_bridge_passes_only_exact_compiler_bound_components(self):
        row = {
            "authoring_target": {
                "environment_url": "https://example.crm.dynamics.com"
            }
        }
        completed = mock.Mock(
            returncode=0,
            stdout=json.dumps({"result": "succeeded", "componentCount": 1}),
            stderr="",
        )

        with (
            mock.patch.object(
                executor,
                "validate_oauth_public_client",
                return_value={
                    "client_id": "66666666-6666-6666-6666-666666666666",
                    "tenant_id": "77777777-7777-7777-7777-777777777777",
                    "redirect_uri": "http://localhost",
                },
            ),
            mock.patch.object(executor.subprocess, "run", return_value=completed) as run,
        ):
            executor.invoke_sdk_app_components(
                row, self.APP_ID, [("entity", self.TABLE_ID)]
            )

        payload = json.loads(run.call_args.kwargs["input"])
        self.assertEqual(payload["appId"], self.APP_ID)
        self.assertEqual(
            payload["components"],
            [{"logicalName": "entity", "id": self.TABLE_ID}],
        )
        self.assertEqual(run.call_args.kwargs["cwd"], str(ROOT))
        self.assertNotIn("token", json.dumps(payload).lower())
        self.assertEqual(payload["operation"], "add")

    def test_sdk_resolver_returns_distinct_internal_table_component_ids(self):
        row = {
            "authoring_target": {
                "environment_url": "https://example.crm.dynamics.com"
            }
        }
        completed = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "result": "succeeded",
                    "components": [
                        {
                            "logicalName": "account",
                            "id": self.TABLE_COMPONENT_ID,
                            "objectTypeCode": 1,
                        }
                    ],
                }
            ),
            stderr="",
        )

        with (
            mock.patch.object(
                executor,
                "validate_oauth_public_client",
                return_value={
                    "client_id": "66666666-6666-6666-6666-666666666666",
                    "tenant_id": "77777777-7777-7777-7777-777777777777",
                    "redirect_uri": "http://localhost",
                },
            ),
            mock.patch.object(executor.subprocess, "run", return_value=completed) as run,
        ):
            resolved = executor.resolve_sdk_table_component_ids(row, ["account"])

        self.assertEqual(resolved, {"account": self.TABLE_COMPONENT_ID})
        payload = json.loads(run.call_args.kwargs["input"])
        self.assertEqual(payload["operation"], "resolve")
        self.assertEqual(payload["components"][0]["logicalName"], "account")

    def test_app_verification_uses_platform_unique_name_without_publisher_prefix(self):
        row = {
            "component_type": "uiux_app",
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
            },
        }

        static_request = executor.build_static_requests(
            row, "verify", self.app_capability
        )[0]
        lookup_request = executor.row_lookup_request(row)

        for request in (static_request, lookup_request):
            self.assertIn("ContosoService", request.path)
            self.assertNotIn("aks_ContosoService", request.path)

    def test_app_create_and_update_explicitly_target_unified_interface(self):
        row = {
            "component_type": "uiux_app",
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
            },
        }

        create_request = executor.build_static_requests(
            row, "create", self.app_capability
        )[0]
        update_request = executor.build_static_requests(
            row,
            "update",
            self.app_update_capability,
            resolved_id=self.APP_ID,
        )[0]

        for request in (create_request, update_request):
            self.assertEqual(request.body["clienttype"], 4)
            self.assertIn("clienttype", request.changed_fields)

    def test_app_immutable_verification_requires_unified_interface(self):
        row = {
            "component_type": "uiux_app",
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
            },
        }

        request = executor.row_verification_request_by_id(row, self.APP_ID)

        self.assertIn("clienttype", request.path)
        self.assertTrue(
            executor.expected_payload_matches(
                row, request, {"name": "Contoso Service", "clienttype": 4}
            )
        )
        self.assertFalse(
            executor.expected_payload_matches(
                row, request, {"name": "Contoso Service", "clienttype": 2}
            )
        )

    def test_app_update_publishes_before_verifying_published_payload(self):
        row = {
            "component_type": "uiux_app",
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
            },
        }
        client = mock.Mock()
        events = []

        def request(operation):
            if operation.path == "PublishXml":
                events.append("publish")
                return executor.HttpResult(204, "", "publish-correlation", {})
            self.fail(f"unexpected request: {operation.method} {operation.path}")

        client.request.side_effect = request
        verification = {
            "identity": "matched",
            "payload": "matched",
            "membership": "matched",
        }

        def verify_result(*args, **kwargs):
            events.append("verify")
            return verification, self.APP_ID

        with mock.patch.object(executor, "verify_result", side_effect=verify_result) as verify:
            result, publish_request, correlation_id = executor.complete_app_update(
                row,
                client,
                self.app_update_capability,
                self.APP_ID,
            )

        self.assertEqual(result, verification)
        self.assertEqual(publish_request.path, "PublishXml")
        self.assertEqual(correlation_id, "publish-correlation")
        self.assertEqual(events, ["publish", "verify"])
        verify.assert_called_once()

    def test_cleanup_removes_only_exact_approved_malformed_memberships(self):
        expected_ids = [
            "10000000-0000-0000-0000-000000000001",
            "10000000-0000-0000-0000-000000000002",
            "10000000-0000-0000-0000-000000000003",
            "10000000-0000-0000-0000-000000000004",
            "10000000-0000-0000-0000-000000000005",
        ]
        malformed_object_id = "90000000-0000-0000-0000-000000000009"
        malformed_row_ids = [
            f"80000000-0000-0000-0000-{index:012d}" for index in range(1, 6)
        ]
        sitemap_row = {
            "appmodulecomponentid": "70000000-0000-0000-0000-000000000007",
            "componenttype": 62,
            "objectid": self.SITEMAP_ID,
        }
        expected_rows = [
            {
                "appmodulecomponentid": f"60000000-0000-0000-0000-{index:012d}",
                "componenttype": 1,
                "objectid": object_id,
            }
            for index, object_id in enumerate(expected_ids, start=1)
        ]
        malformed_rows = [
            {
                "appmodulecomponentid": row_id,
                "componenttype": 1,
                "objectid": malformed_object_id,
            }
            for row_id in malformed_row_ids
        ]
        row = {
            "id": "DEV-0062",
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
                "tables": ["one", "two", "three", "four", "five"],
            },
        }
        approval = (
            f"REMOVE-APP-COMPONENTS DEV-0062 app={self.APP_ID} "
            f"rows={','.join(malformed_row_ids)} objects={malformed_object_id}"
        )
        client = mock.Mock()
        publish_result = executor.HttpResult(204, "", "publish-correlation", {})
        events = []

        component_snapshots = iter(
            [expected_rows + malformed_rows + [sitemap_row], expected_rows + [sitemap_row]]
        )

        def read_components(*_args):
            events.append("read")
            return next(component_snapshots)

        def remove_components(*_args, **_kwargs):
            events.append("remove")

        def publish_components(*_args):
            events.append("publish")
            return publish_result

        with (
            mock.patch.object(
                executor,
                "resolve_app_table_components",
                return_value=[{"entityid": object_id} for object_id in expected_ids],
            ),
            mock.patch.object(
                executor,
                "appmodule_component_rows",
                side_effect=read_components,
            ),
            mock.patch.object(
                executor,
                "invoke_sdk_app_components",
                side_effect=remove_components,
            ) as sdk_remove,
            mock.patch.object(
                executor,
                "invoke_capability_suboperation",
                side_effect=publish_components,
            ) as publish,
        ):
            request, correlation_id = executor.cleanup_malformed_app_components(
                row,
                client,
                self.app_update_capability,
                self.APP_ID,
                approval,
            )

        self.assertEqual(request.path, "RemoveAppComponents")
        sdk_remove.assert_called_once_with(
            row,
            self.APP_ID,
            [("entity", malformed_object_id)] * 5,
            operation="remove",
        )
        self.assertEqual(len(request.body["Components"]), 5)
        self.assertEqual(publish.call_args.args[2], "publish_app")
        self.assertEqual(correlation_id, "publish-correlation")
        self.assertEqual(events, ["read", "remove", "publish", "read"])

    def test_cleanup_rejects_non_exact_approval_before_sdk_write(self):
        expected_ids = [
            f"10000000-0000-0000-0000-{index:012d}" for index in range(1, 6)
        ]
        malformed = [
            {
                "appmodulecomponentid": f"80000000-0000-0000-0000-{index:012d}",
                "componenttype": 1,
                "objectid": "90000000-0000-0000-0000-000000000009",
            }
            for index in range(1, 6)
        ]
        row = {
            "id": "DEV-0062",
            "payload": {"tables": ["one", "two", "three", "four", "five"]},
        }
        expected = [
            {
                "appmodulecomponentid": f"60000000-0000-0000-0000-{index:012d}",
                "componenttype": 1,
                "objectid": object_id,
            }
            for index, object_id in enumerate(expected_ids, start=1)
        ]

        with (
            mock.patch.object(
                executor,
                "resolve_app_table_components",
                return_value=[{"entityid": object_id} for object_id in expected_ids],
            ),
            mock.patch.object(
                executor,
                "appmodule_component_rows",
                return_value=expected + malformed,
            ),
            mock.patch.object(executor, "invoke_sdk_app_components") as sdk_remove,
            self.assertRaises(executor.ExecutorError) as raised,
        ):
            executor.cleanup_malformed_app_components(
                row,
                mock.Mock(),
                self.app_update_capability,
                self.APP_ID,
                "not-approved",
            )

        self.assertEqual(raised.exception.category, "validation_error")
        sdk_remove.assert_not_called()

    def test_sdk_bridge_reports_sanitized_failure(self):
        row = {
            "authoring_target": {
                "environment_url": "https://example.crm.dynamics.com"
            }
        }
        completed = mock.Mock(
            returncode=1,
            stdout="",
            stderr='{"message":"sensitive platform detail","exceptionType":"FaultException"}',
        )

        with (
            mock.patch.object(
                executor,
                "validate_oauth_public_client",
                return_value={
                    "client_id": "66666666-6666-6666-6666-666666666666",
                    "tenant_id": "77777777-7777-7777-7777-777777777777",
                    "redirect_uri": "http://localhost",
                },
            ),
            mock.patch.object(executor.subprocess, "run", return_value=completed),
            self.assertRaises(executor.ExecutorError) as raised,
        ):
            executor.invoke_sdk_app_components(
                row, self.APP_ID, [("entity", self.TABLE_ID)]
            )

        self.assertEqual(raised.exception.category, "sdk_operation_error")
        self.assertIn("FaultException", str(raised.exception))
        self.assertNotIn("sensitive", str(raised.exception))

    def test_builds_documented_appmodule_create_request(self):
        row = {
            "component_type": "uiux_app",
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
                "tables": ["account", "contact"],
                "roles": ["aks_ContosoServiceReader"],
            },
        }

        request = executor.build_static_requests(
            row,
            "create",
            {"solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}},
        )[0]

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "appmodules")
        self.assertEqual(
            request.body,
            {
                "name": "Contoso Service",
                "clienttype": 4,
                "uniquename": "ContosoService",
                "webresourceid": "953b9fac-1e5e-e611-80d6-00155ded156f",
            },
        )
        self.assertNotIn("appmodulexml", request.body)

        lookup = executor.app_lookup_request("aks_ContosoService")
        self.assertIn("aks_ContosoService", lookup.path)

    def test_configures_and_verifies_declared_tables_without_roles(self):
        row = {
            "depends_on": ["DEV-0056"],
            "payload": {
                "tables": ["account"],
                "roles": ["aks_ContosoServiceReader"],
            }
        }
        client = mock.Mock()
        client.service_root = "https://example.crm.dynamics.com/api/data/v9.2"

        def request(operation):
            if operation.path.startswith("EntityDefinitions"):
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {
                        "MetadataId": self.TABLE_ID,
                        "LogicalName": "account",
                        "EntitySetName": "accounts",
                    },
                )
            if operation.path == "RetrieveAppComponents(AppModuleId=" + self.APP_ID + ")":
                return executor.HttpResult(
                    200, "", "", {"value": [{"entityid": self.TABLE_ID}]}
                )
            return executor.HttpResult(204, "", "correlation-id", {})

        client.request.side_effect = request

        with (
            mock.patch.object(
                executor,
                "resolve_sdk_table_component_ids",
                return_value={"account": self.TABLE_COMPONENT_ID},
            ),
            mock.patch.object(executor, "invoke_sdk_app_components") as sdk_add,
            mock.patch.object(
                executor,
                "app_dependency_component_ids",
                side_effect=[set(), {self.TABLE_COMPONENT_ID}],
            ) as dependencies,
        ):
            operation, correlation_id, wrote_components = executor.configure_app_shell(
                row, client, self.app_capability, self.APP_ID
            )

        self.assertEqual(operation.path, "AddAppComponents")
        self.assertEqual(
            operation.body,
            {
                "AppId": self.APP_ID,
                "Components": [
                    {
                        "@odata.type": "Microsoft.Dynamics.CRM.entity",
                        "entityid": self.TABLE_COMPONENT_ID,
                    }
                ],
            },
        )
        self.assertNotIn("@odata.id", json.dumps(operation.body))
        sdk_add.assert_called_once_with(
            row, self.APP_ID, [("account", self.TABLE_COMPONENT_ID)]
        )
        self.assertEqual(dependencies.call_count, 2)
        self.assertFalse(
            any(
                "appmoduleroles_association" in call.args[0].path
                for call in client.request.call_args_list
            )
        )
        self.assertEqual(correlation_id, "")
        self.assertTrue(wrote_components)

    def test_attaches_sitemap_validates_and_publishes_app(self):
        row = {"payload": {"app": "aks_ContosoService"}}
        client = mock.Mock()
        client.service_root = "https://example.crm.dynamics.com/api/data/v9.2"

        def request(operation):
            if operation.path.startswith("appmodules?"):
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {
                        "value": [
                            {
                                "appmoduleid": self.APP_ID,
                                "uniquename": "ContosoService",
                            }
                        ]
                    },
                )
            if operation.path == "RetrieveAppComponents(AppModuleId=" + self.APP_ID + ")":
                return executor.HttpResult(
                    200, "", "", {"value": [{"sitemapid": self.SITEMAP_ID}]}
                )
            if operation.path == "ValidateApp(AppModuleId=" + self.APP_ID + ")":
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {"AppValidationResponse": {"ValidationSuccess": True}},
                )
            if operation.path.startswith("roles?"):
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {"value": [{"roleid": self.ROLE_ID, "name": "Contoso Service Reader"}]},
                )
            if operation.path.startswith("businessunits?"):
                return executor.HttpResult(
                    200, "", "", {"value": [{"businessunitid": self.BUSINESS_UNIT_ID}]}
                )
            if operation.path.startswith("appmodules(") and operation.method == "GET":
                return executor.HttpResult(
                    200, "", "", {"appmoduleroles_association": [{"roleid": self.ROLE_ID}]}
                )
            return executor.HttpResult(204, "", "correlation-id", {})

        client.request.side_effect = request

        app_row = {
            "depends_on": ["DEV-0056"],
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "schema_name": "aks_ContosoService",
                "roles": ["aks_ContosoServiceReader"],
            },
        }
        with (
            mock.patch.object(executor, "app_dependency_row", return_value=app_row),
            mock.patch.object(executor, "invoke_sdk_app_components") as sdk_add,
            mock.patch.object(
                executor,
                "app_dependency_component_ids",
                side_effect=[set(), {self.SITEMAP_ID}],
            ) as dependencies,
            mock.patch.object(
                executor,
                "declared_app_role_names",
                return_value={"aks_ContosoServiceReader": "Contoso Service Reader"},
            ),
        ):
            operation, correlation_id = executor.complete_app_navigation(
                row, client, self.sitemap_capability, self.SITEMAP_ID
            )

        self.assertEqual(operation.path, "PublishXml")
        self.assertIn(self.APP_ID, operation.body["ParameterXml"])
        sdk_add.assert_called_once_with(row, self.APP_ID, [("sitemap", self.SITEMAP_ID)])
        self.assertEqual(dependencies.call_count, 2)
        paths = [call.args[0].path for call in client.request.call_args_list]
        self.assertLess(paths.index("PublishXml"), next(i for i, path in enumerate(paths) if "appmoduleroles_association" in path))
        self.assertEqual(correlation_id, "correlation-id")

    def test_app_operation_paths_are_runtime_whitelisted(self):
        paths = (
            ("POST", "AddAppComponents"),
            ("GET", f"RetrieveAppComponents(AppModuleId={self.APP_ID})"),
            ("GET", f"ValidateApp(AppModuleId={self.APP_ID})"),
            (
                "POST",
                f"appmodules({self.APP_ID})/appmoduleroles_association/$ref",
            ),
            ("POST", "PublishXml"),
            (
                "GET",
                f"dependencies?$filter=dependentcomponentobjectid%20eq%20{self.APP_ID}",
            ),
        )

        for method, path in paths:
            with self.subTest(method=method, path=path):
                executor.validate_runtime_request(method, path)

    def test_app_recovery_targets_immutable_row_without_create(self):
        row = {"component_type": "uiux_app"}

        request = executor.app_recovery_request(row, self.APP_ID)

        self.assertEqual(request.method, "GET")
        self.assertTrue(
            request.path.startswith(
                "appmodules/Microsoft.Dynamics.CRM.RetrieveUnpublishedMultiple()?"
            )
        )
        self.assertIn(self.APP_ID, request.path)
        self.assertNotEqual(request.path, "appmodules")
        executor.validate_runtime_request(request.method, request.path)

    def test_resolves_exact_unpublished_app_when_not_yet_published(self):
        client = mock.Mock()
        client.request.side_effect = [
            executor.HttpResult(200, "", "", {"value": []}),
            executor.HttpResult(
                200,
                "",
                "",
                {
                    "value": [
                        {
                            "appmoduleid": self.APP_ID,
                            "uniquename": "ContosoService",
                        }
                    ]
                },
            ),
        ]

        app_id = executor.resolve_app_id(
            client, self.sitemap_capability, "ContosoService"
        )

        self.assertEqual(app_id, self.APP_ID)
        self.assertIn(
            "RetrieveUnpublishedMultiple",
            client.request.call_args_list[1].args[0].path,
        )

    def test_app_cleanup_targets_only_immutable_unpublished_row(self):
        row = {
            "component_type": "uiux_app",
            "payload": {
                "name": "Contoso Service",
                "schema_name": "aks_ContosoService",
            },
        }

        recovery, deletion = executor.app_cleanup_requests(
            row, self.app_delete_capability, self.APP_ID
        )

        self.assertIn("RetrieveUnpublishedMultiple", recovery.path)
        self.assertIn(self.APP_ID, recovery.path)
        self.assertEqual(deletion.method, "DELETE")
        self.assertEqual(deletion.path, f"appmodules({self.APP_ID})")
        executor.validate_capability_request(self.app_delete_capability, deletion)

    def test_sitemap_recovery_request_targets_exact_created_row(self):
        row = {
            "component_type": "uiux_sitemap",
            "payload": {
                "app": "aks_ContosoService",
                "name": "Contoso Service navigation",
                "schema_name": "aks_ContosoServiceSiteMap",
                "areas": [
                    {
                        "name": "Fleet Operations",
                        "groups": [
                            {
                                "name": "Fleet",
                                "subareas": [
                                    {"name": "Vehicles", "table": "aks_vehicle"}
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        request = executor.row_verification_request_by_id(row, self.SITEMAP_ID)

        self.assertEqual(request.method, "GET")
        self.assertTrue(request.path.startswith(f"sitemaps({self.SITEMAP_ID})?"))
        self.assertIn("sitemapnameunique", request.path)
        self.assertIn("sitemapxml", request.path)
        self.assertEqual(
            request.expected_body["sitemapnameunique"],
            "aks_ContosoServiceSiteMap",
        )
        self.assertIs(executor.verification_request(row, request), request)
        executor.validate_runtime_request(request.method, request.path)

    def test_sitemap_update_verification_uses_immutable_id(self):
        row = {
            "component_type": "uiux_sitemap",
            "implementation_scope": "repository_and_dataverse_solution",
            "authoring_target": {"solution_unique_name": "ContosoServiceApps"},
            "payload": {
                "app": "aks_ContosoService",
                "name": "Contoso Service navigation",
                "schema_name": "aks_ContosoServiceSiteMap",
                "areas": [
                    {
                        "name": "Fleet Operations",
                        "groups": [
                            {
                                "name": "Fleet",
                                "subareas": [
                                    {"name": "Vehicles", "table": "aks_vehicle"}
                                ],
                            }
                        ],
                    }
                ],
            },
        }
        client = mock.Mock()
        client.request.return_value = executor.HttpResult(
            200,
            "",
            "correlation-id",
            {
                "sitemapid": self.SITEMAP_ID,
                "sitemapname": "Contoso Service navigation",
                "sitemapnameunique": "aks_ContosoServiceSiteMap",
                "sitemapxml": executor.sitemapxml(row["payload"]),
            },
        )

        with (
            mock.patch.object(executor, "resolve_solution_id", return_value="solution-id"),
            mock.patch.object(executor, "membership_object_id", return_value=self.SITEMAP_ID),
            mock.patch.object(
                executor,
                "effective_solution_component_rows",
                return_value=[{"_solutionid_value": "solution-id"}],
            ),
            mock.patch.object(
                executor,
                "declared_solution_ids",
                return_value={"ContosoServiceApps": "solution-id"},
            ),
        ):
            verification, resolved_id = executor.verify_result(
                row,
                client,
                self.SITEMAP_ID,
                deleted=False,
                request=executor.OperationRequest(
                    "PATCH",
                    f"sitemaps({self.SITEMAP_ID})",
                    {
                        "sitemapnameunique": "aks_ContosoServiceSiteMap",
                        "sitemapxml": executor.sitemapxml(row["payload"]),
                    },
                    ("sitemapnameunique", "sitemapxml"),
                    ("sitemapnameunique", "sitemapxml"),
                    "header",
                    "update exact sitemap",
                ),
            )

        self.assertEqual(resolved_id, self.SITEMAP_ID)
        self.assertEqual(verification["identity"], "matched")
        self.assertTrue(
            client.request.call_args.args[0].path.startswith(
                f"sitemaps({self.SITEMAP_ID})?"
            )
        )

    def test_rejects_undeclared_aggregate_suboperation(self):
        request = executor.OperationRequest(
            "POST",
            "AddAppComponents",
            {},
            (),
            (),
            "none",
            "test",
        )

        with self.assertRaises(executor.ExecutorError):
            executor.validate_capability_suboperation({}, "add_table_components", request)

    def test_failed_app_validation_stops_before_publish(self):
        row = {"payload": {"app": "aks_ContosoService"}}
        client = mock.Mock()

        def request(operation):
            if operation.path.startswith("appmodules?"):
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {
                        "value": [
                            {
                                "appmoduleid": self.APP_ID,
                                "uniquename": "ContosoService",
                            }
                        ]
                    },
                )
            if operation.path == "RetrieveAppComponents(AppModuleId=" + self.APP_ID + ")":
                return executor.HttpResult(
                    200, "", "", {"value": [{"sitemapid": self.SITEMAP_ID}]}
                )
            if operation.path == "ValidateApp(AppModuleId=" + self.APP_ID + ")":
                return executor.HttpResult(
                    200,
                    "",
                    "",
                    {"AppValidationResponse": {"ValidationSuccess": False}},
                )
            return executor.HttpResult(204, "", "correlation-id", {})

        client.request.side_effect = request
        app_row = {
            "authoring_target": {"publisher_prefix": "aks"},
            "payload": {
                "schema_name": "aks_ContosoService",
                "roles": [],
            },
        }

        with (
            mock.patch.object(executor, "app_dependency_row", return_value=app_row),
            mock.patch.object(executor, "invoke_sdk_app_components") as sdk_add,
            mock.patch.object(
                executor,
                "app_dependency_component_ids",
                side_effect=[set(), {self.SITEMAP_ID}],
            ),
            self.assertRaises(executor.ExecutorError) as raised,
        ):
            executor.complete_app_navigation(
                row, client, self.sitemap_capability, self.SITEMAP_ID
            )

        self.assertEqual(raised.exception.category, "verification_mismatch")
        sdk_add.assert_called_once_with(row, self.APP_ID, [("sitemap", self.SITEMAP_ID)])
        self.assertNotIn(
            "PublishXml", [call.args[0].path for call in client.request.call_args_list]
        )


class SiteMapRequestTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "component_type": "uiux_sitemap",
            "payload": {
                "app": "aks_ContosoService",
                "name": "Contoso Service navigation",
                "schema_name": "aks_ContosoServiceSiteMap",
                "areas": [
                    {
                        "name": "Fleet Operations",
                        "groups": [
                            {
                                "name": "Fleet",
                                "subareas": [
                                    {"name": "Vehicles", "table": "aks_vehicle"},
                                    {
                                        "name": "Maintenance Jobs",
                                        "table": "aks_maintenancejob",
                                    },
                                    {"name": "Job Parts", "table": "aks_jobpart"},
                                ],
                            }
                        ],
                    },
                    {
                        "name": "Customers",
                        "groups": [
                            {
                                "name": "Service Network",
                                "subareas": [
                                    {"name": "Depots", "table": "account"},
                                    {"name": "Technicians", "table": "contact"},
                                ],
                            }
                        ],
                    },
                ],
            },
        }

    def test_builds_complete_deterministic_sitemap_xml(self):
        xml = executor.sitemapxml(self.row["payload"])
        root = ET.fromstring(xml)

        areas = root.findall("Area")
        groups = root.findall("./Area/Group")
        subareas = root.findall("./Area/Group/SubArea")
        self.assertEqual(len(areas), 2)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(subareas), 5)
        self.assertEqual(
            {subarea.attrib["Entity"] for subarea in subareas},
            {"aks_vehicle", "aks_maintenancejob", "aks_jobpart", "account", "contact"},
        )
        ids = [element.attrib["Id"] for element in [*areas, *groups, *subareas]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(" " not in value for value in ids))
        self.assertEqual(executor.sitemapxml(self.row["payload"]), xml)

    def test_builds_documented_sitemap_row_fields(self):
        request = executor.build_static_requests(
            self.row,
            "create",
            {"solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}},
        )[0]

        self.assertEqual(request.path, "sitemaps")
        self.assertEqual(request.body["sitemapname"], "Contoso Service navigation")
        self.assertEqual(
            request.body["sitemapnameunique"], "aks_ContosoServiceSiteMap"
        )
        self.assertNotIn("name", request.body)
        self.assertEqual(len(ET.fromstring(request.body["sitemapxml"]).findall(".//SubArea")), 5)


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


class ConnectionReferenceRequestTests(unittest.TestCase):
    def test_builds_standard_connector_request_from_logical_id(self):
        row = {
            "component_type": "integ_connection_ref",
            "implementation_scope": "repository_and_dataverse_solution",
            "payload": {
                "connector": "shared_commondataserviceforapps",
                "name": "Dataverse - Automated follow-up",
                "schema_name": "aks_DataverseAutomatedFollowUp",
            },
        }

        request = executor.build_static_requests(
            row,
            "create",
            {"solution_context": {"mechanism": "MSCRM.SolutionUniqueName"}},
        )[0]

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "connectionreferences")
        self.assertEqual(request.solution_context, "header")
        self.assertEqual(
            request.body,
            {
                "connectionreferencelogicalname": "aks_DataverseAutomatedFollowUp",
                "connectionreferencedisplayname": "Dataverse - Automated follow-up",
                "connectorid": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
            },
        )


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
            mock.patch.object(executor, "validate_interrupted_write_evidence"),
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