import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_development_environment as V


class PackageVersionResultTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "src" / "Plugin"
        self.project.mkdir(parents=True)
        (self.project / "Plugin.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup>'
            '<PackageReference Include="Microsoft.PowerPlatform.Dataverse.Client" '
            'Version="1.1.32" />'
            "</ItemGroup></Project>",
            encoding="utf-8",
        )
        self.step = {
            "package": "Microsoft.PowerPlatform.Dataverse.Client",
            "expected_version": "1.1.32",
            "project_paths": ["src/Plugin"],
        }

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_lock(self, resolved="1.1.32"):
        (self.project / "packages.lock.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "dependencies": {
                        "net462": {
                            "Microsoft.PowerPlatform.Dataverse.Client": {
                                "type": "Direct",
                                "resolved": resolved,
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_exact_manifest_and_lock_version_are_ready(self):
        self.write_lock()

        status, _ = V.package_version_result(self.step, self.root)

        self.assertEqual("ready", status)

    def test_mismatched_lock_version_is_blocked(self):
        self.write_lock("1.1.31")

        status, _ = V.package_version_result(self.step, self.root)

        self.assertEqual("blocked", status)


if __name__ == "__main__":
    unittest.main()