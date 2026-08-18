import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pack_plugin_solution", ROOT / "scripts" / "pack_plugin_solution.py"
)
packaging = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(packaging)


class PluginSolutionPackagingTests(unittest.TestCase):
    def test_resolves_metadata_declared_solution_assembly(self):
        with tempfile.TemporaryDirectory() as directory:
            solution = Path(directory)
            assembly_dir = solution / "PluginAssemblies" / "ContosoAssembly-ID"
            assembly_dir.mkdir(parents=True)
            metadata = assembly_dir / "ContosoServicePlugins.dll.data.xml"
            metadata.write_text(
                '<PluginAssembly FullName="ContosoService.Plugins, Version=1.0.0.0">'
                '<FileName>/PluginAssemblies/ContosoAssembly-ID/ContosoServicePlugins.dll</FileName>'
                '</PluginAssembly>',
                encoding="utf-8",
            )

            resolved = packaging.resolve_solution_assembly(solution)

            self.assertEqual(resolved, assembly_dir / "ContosoServicePlugins.dll")

    def test_rejects_metadata_path_outside_solution(self):
        with tempfile.TemporaryDirectory() as directory:
            solution = Path(directory)
            assembly_dir = solution / "PluginAssemblies" / "ContosoAssembly-ID"
            assembly_dir.mkdir(parents=True)
            (assembly_dir / "ContosoServicePlugins.dll.data.xml").write_text(
                '<PluginAssembly FullName="ContosoService.Plugins, Version=1.0.0.0">'
                '<FileName>/PluginAssemblies/../outside.dll</FileName>'
                '</PluginAssembly>',
                encoding="utf-8",
            )

            with self.assertRaises(packaging.PackagingError):
                packaging.resolve_solution_assembly(solution)

    def test_synchronizes_rebuilt_assembly_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            built = root / "build" / "ContosoService.Plugins.dll"
            target = root / "solution" / "ContosoServicePlugins.dll"
            built.parent.mkdir()
            built.write_bytes(b"rebuilt-plugin")

            digest = packaging.synchronize_assembly(built, target)

            self.assertEqual(target.read_bytes(), b"rebuilt-plugin")
            self.assertEqual(digest, packaging.sha256(built))


if __name__ == "__main__":
    unittest.main()