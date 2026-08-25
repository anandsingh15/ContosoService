import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pipeline_common as P


class DevelopmentResourceResolutionTests(unittest.TestCase):
    def setUp(self):
        self.registry = P.load_development_resources()

    def resolve(self, component_type):
        return P.resolve_development_resources(
            "DES-TEST-CMP-001",
            component_type,
            "dataverse-table",
            self.registry,
        )

    def test_derived_column_preserves_declared_dataverse_mcp(self):
        required = self.resolve("schema_derived_column")["required"]

        self.assertIn("dataverse-mcp", {item["id"] for item in required})

    def test_schema_column_retains_dataverse_mcp_verification(self):
        required = self.resolve("schema_column")["required"]

        self.assertIn("dataverse-mcp", {item["id"] for item in required})

    def test_executor_managed_web_api_auth_does_not_block_readiness(self):
        target = {
            "authentication_mode": "interactive_user",
            "environment_id": "89a7081d-6701-f111-8c79-6045bd005919",
            "environment_url": "https://org89912357.crm.dynamics.com",
            "kind": "dataverse_solution",
            "solution_unique_name": "ContosoServiceApps",
        }
        resources = P.resolve_development_resources(
            "DES-TEST-CMP-APP",
            "uiux_app",
            "model-driven-ui",
            self.registry,
            target,
        )

        preflight = P.resolve_developer_preflight(
            resources,
            self.registry,
            "repository_and_dataverse_solution",
            "local_interactive",
            target,
            {"schema_name": "aks_TestApp"},
        )
        authentication = {
            step["resource"]: step
            for step in preflight["phases"]["authentication"]
        }

        self.assertFalse(authentication["dataverse-web-api"]["blocking"])
        self.assertTrue(authentication["dataverse-mcp"]["blocking"])
        self.assertNotIn("maker-portal", authentication)


class ComponentSourceSyncResolutionTests(unittest.TestCase):
    def test_derived_column_includes_formula_definition(self):
        source_sync = P.resolve_component_source_sync(
            "schema_derived_column",
            P.conventions(),
        )

        self.assertEqual(
            source_sync["paths"],
            [
                "Entities/<table>/Entity.xml",
                "Entities/<table>/Formulas/<table>-FormulaDefinitions.yaml",
            ],
        )


class SiteMapContractTests(unittest.TestCase):
    def test_rejects_group_without_subareas(self):
        violations = P.sitemap_contract_violations(
            {
                "app": "aks_TestApp",
                "areas": [{"name": "Operations", "groups": [{"name": "Work"}]}],
            }
        )

        self.assertIn(
            "areas[0].groups[0] subareas must contain at least one subarea",
            violations,
        )

    def test_accepts_named_subarea_with_canonical_table(self):
        violations = P.sitemap_contract_violations(
            {
                "app": "aks_TestApp",
                "areas": [
                    {
                        "name": "Operations",
                        "groups": [
                            {
                                "name": "Work",
                                "subareas": [
                                    {"name": "Vehicles", "table": "aks_vehicle"}
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()