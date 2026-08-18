#!/usr/bin/env python3
"""Rebuild and pack the compiler-routed Contoso plug-in solution."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "src" / "plugins" / "ContosoService.Plugins"
PROJECT_FILE = PROJECT / "ContosoService.Plugins.csproj"
SOLUTION_NAME = "ContosoServicePluginAndCustomApi"
SOLUTION_SOURCE = ROOT / "src" / "solutions" / SOLUTION_NAME
ASSEMBLY_NAME = "ContosoService.Plugins"
ASSEMBLY_FILE = ASSEMBLY_NAME + ".dll"


class PackagingError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_checked(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise PackagingError(
            f"command exited {completed.returncode}: {' '.join(command)}"
        )


def resolve_built_assembly(project: Path = PROJECT) -> Path:
    candidates = sorted((project / "bin" / "Release").glob(f"*/{ASSEMBLY_FILE}"))
    if len(candidates) != 1 or not candidates[0].is_file():
        raise PackagingError(
            f"expected one rebuilt {ASSEMBLY_FILE} directly below bin/Release/<tfm>"
        )
    if candidates[0].stat().st_size == 0:
        raise PackagingError("rebuilt plug-in assembly is empty")
    return candidates[0]


def resolve_solution_assembly(solution_source: Path = SOLUTION_SOURCE) -> Path:
    metadata_files = sorted(
        (solution_source / "PluginAssemblies").glob("*/*.dll.data.xml")
    )
    if len(metadata_files) != 1:
        raise PackagingError(
            "expected exactly one exported plug-in assembly metadata file"
        )

    metadata = ET.parse(metadata_files[0]).getroot()
    full_name = str(metadata.attrib.get("FullName") or "")
    if full_name.split(",", 1)[0] != ASSEMBLY_NAME:
        raise PackagingError("exported plug-in assembly identity does not match the project")

    raw_file_name = str(metadata.findtext("FileName") or "").replace("\\", "/")
    relative = PurePosixPath(raw_file_name.lstrip("/"))
    if (
        not raw_file_name.startswith("/PluginAssemblies/")
        or relative.is_absolute()
        or ".." in relative.parts
        or relative.suffix.lower() != ".dll"
    ):
        raise PackagingError("exported plug-in assembly FileName is outside the solution")

    target = (solution_source / Path(*relative.parts)).resolve()
    try:
        target.relative_to(solution_source.resolve())
    except ValueError as exc:
        raise PackagingError("exported plug-in assembly path escapes the solution") from exc
    if target.parent != metadata_files[0].parent.resolve():
        raise PackagingError("assembly metadata and DLL do not resolve to one folder")
    return target


def synchronize_assembly(built: Path, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(built, target)
    built_hash = sha256(built)
    if sha256(target) != built_hash:
        raise PackagingError("packed solution assembly does not match the rebuilt project")
    return built_hash


def package_solution() -> dict[str, str]:
    if not (SOLUTION_SOURCE / "Other" / "Solution.xml").is_file():
        raise PackagingError("solution source is missing Other/Solution.xml")

    run_checked(["dotnet", "restore", str(PROJECT_FILE), "--locked-mode"])
    run_checked(
        [
            "dotnet",
            "build",
            str(PROJECT_FILE),
            "-c",
            "Release",
            "--no-restore",
            "-t:Rebuild",
        ]
    )
    built = resolve_built_assembly()
    solution_assembly = resolve_solution_assembly()
    assembly_hash = synchronize_assembly(built, solution_assembly)

    output_dir = ROOT / "src" / "solutions" / "_out"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{SOLUTION_NAME}.zip"
    output.unlink(missing_ok=True)
    run_checked(
        [
            "pac",
            "solution",
            "pack",
            "--zipfile",
            str(output),
            "--folder",
            str(SOLUTION_SOURCE),
            "--packagetype",
            "Unmanaged",
        ]
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise PackagingError("PAC did not produce a solution archive")
    return {
        "assembly_sha256": assembly_hash,
        "package": str(output.relative_to(ROOT)),
        "package_type": "Unmanaged",
        "solution": SOLUTION_NAME,
        "solution_assembly": str(solution_assembly.relative_to(ROOT)),
    }


def main() -> int:
    try:
        result = package_solution()
    except (OSError, ET.ParseError, PackagingError) as exc:
        print(json.dumps({"result": "blocked", "message": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"result": "succeeded", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())