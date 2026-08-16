import importlib.util
import sys
import unittest
from pathlib import Path
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


class FakeClient:
    def __init__(self, *_args):
        self.request_count = 0
        self.posts = []

    def request_with_404_retries(self, request):
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

    def request(self, request):
        self.request_count += 1
        if request.method == "GET":
            return executor.HttpResult(
                200,
                "",
                "",
                {"MetadataId": "998e2b9d-8f95-f111-8075-6045bd01d8e8"},
            )
        self.posts.append(request)
        return executor.HttpResult(
            204,
            "https://example/Attributes(aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa)",
            "correlation-id",
            {},
        )


class BundledRecoveryTests(unittest.TestCase):
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

    def test_execute_skips_status_and_posts_only_roadworthy(self):
        capability = {
            "http": {"method": "POST", "endpoint_family": "metadata", "path_template": "EntityDefinitions(LogicalName='{table}')/Attributes"},
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
        self.assertEqual([request.body["SchemaName"] for request in client.posts], ["aks_roadworthy"])
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