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

    def test_derived_column_omits_unused_dataverse_mcp(self):
        required = self.resolve("schema_derived_column")["required"]

        self.assertNotIn("dataverse-mcp", {item["id"] for item in required})

    def test_schema_column_retains_dataverse_mcp_verification(self):
        required = self.resolve("schema_column")["required"]

        self.assertIn("dataverse-mcp", {item["id"] for item in required})


if __name__ == "__main__":
    unittest.main()