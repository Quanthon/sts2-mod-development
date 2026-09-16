"""Read-only dependency inspection; never launches the game or installs software."""
from __future__ import annotations
import importlib.metadata
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def probe(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        return {"exit_code": result.returncode, "output": (result.stdout + result.stderr).strip()[:2500]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"error": str(error)}

def check_godot(path):
    """Check a native executable or macOS application bundle for Godot .NET."""
    if path is not None:
        path = Path(path).expanduser()
    if path and path.is_dir() and path.suffix.lower() == ".app":
        bundle = path
        info = bundle / "Contents/Info.plist"
        executable = "Godot"
        if info.is_file():
            try:
                with info.open("rb") as stream:
                    executable = plistlib.load(stream).get("CFBundleExecutable", executable)
            except (OSError, ValueError, plistlib.InvalidFileException) as error:
                return {"name": "godot", "path": str(bundle), "available": False,
                        "dotnet_supported": False, "error": f"Cannot read application bundle: {error}"}
        if not isinstance(executable, str) or "/" in executable or "\\" in executable or executable in ("", ".", ".."):
            return {"name": "godot", "path": str(bundle), "available": False,
                    "dotnet_supported": False, "error": "Invalid application executable name"}
        path = bundle / "Contents/MacOS" / executable
    detail = {"name": "godot", "path": str(path) if path else None,
              "available": False, "dotnet_supported": False}
    if path is None or not path.is_file():
        detail["error"] = "Configure a Godot executable or macOS .app bundle"
        return detail
    if platform.system() == "Windows":
        executable = path.suffix.lower() == ".exe"
    else:
        executable = os.access(path, os.X_OK)
    if not executable:
        detail["error"] = "Configured Godot file is not executable on this system"
        return detail
    result = probe([str(path), "--version"])
    detail["probe"] = result
    if result.get("error") or result.get("exit_code") != 0:
        detail["error"] = "Godot version command did not complete successfully"
        return detail
    version = next((line.strip() for line in result.get("output", "").splitlines()
                    if re.fullmatch(r"\d+\.\d+(?:\.\d+)?(?:\.[A-Za-z0-9_-]+)+", line.strip())), None)
    detail["version"] = version
    if version and "mono" in version.lower().split("."):
        detail["available"] = True
        detail["dotnet_supported"] = True
    else:
        detail["error"] = "Godot .NET/Mono build marker was not found; use a verified .NET build"
    return detail

def doctor(project):
    findings = [{"name": "python", "path": sys.executable, "version": sys.version.split()[0], "available": True}]
    for name in ("openpyxl", "Pillow"):
        try:
            version = importlib.metadata.version(name)
            findings.append({"name": name, "version": version, "available": True})
        except importlib.metadata.PackageNotFoundError:
            findings.append({"name": name, "available": False})
    paths = project.data.get("environment", {})
    configured_dotnet = paths.get("dotnet")
    if configured_dotnet:
        dotnet_path = Path(configured_dotnet).expanduser()
        dotnet = str(dotnet_path if dotnet_path.is_absolute() else project.root / dotnet_path)
    else:
        dotnet = shutil.which("dotnet")
    findings.append({"name": "dotnet", "path": dotnet, "available": bool(dotnet), "probe": probe([dotnet, "--version"]) if dotnet else None})
    for name in ("game", "godot", "tutorials", "official_reference", "sts2_agent", "mcp_server"):
        configured = paths.get(name)
        path = Path(configured).expanduser() if configured else None
        if path and not path.is_absolute():
            path = project.root / path
        if name == "godot":
            findings.append(check_godot(path))
            continue
        available = bool(path and path.exists())
        detail = {"name": name, "path": str(path) if path else None, "available": available}
        if available and name == "tutorials" and shutil.which("git"):
            detail["revision"] = probe(["git", "-C", str(path), "rev-parse", "HEAD"])
        findings.append(detail)
    project_file = project.data.get("csproj")
    if project_file and project.path(project_file).is_file():
        root = ET.parse(project.path(project_file)).getroot()
        packages = [e.attrib for e in root.iter() if e.tag.split("}")[-1] == "PackageReference"]
        frameworks = [e.text for e in root.iter() if e.tag.split("}")[-1] == "TargetFramework"]
        findings.append({"name": "project", "available": True, "frameworks": frameworks, "packages": packages,
                         "ritsulib_detected": any("RitsuLib" in p.get("Include", "") for p in packages)})
    else:
        findings.append({"name": "project", "available": False, "path": project_file})
    packages = next((f.get("packages", []) for f in findings if f["name"] == "project"), [])
    ritsu = [p for p in packages if "RitsuLib" in p.get("Include", "")]
    findings.append({"name": "ritsulib", "available": bool(ritsu), "packages": ritsu})
    names = {f["name"] for f in findings}
    # Legacy configs preserve the old full-check behavior.
    required = project.data.get("required_checks", list(names))
    if not isinstance(required, list) or any(not isinstance(name, str) or name not in names for name in required):
        raise ValueError("required_checks must list known doctor check names")
    for finding in findings:
        finding["required"] = finding["name"] in required
        result = finding.get("probe")
        if result and (result.get("error") or result.get("exit_code", 0) != 0):
            finding["available"] = False
    return {"platform": {"system": platform.system(), "architecture": platform.machine()}, "findings": findings, "declared_versions": project.data.get("versions", {}),
            "missing": [f["name"] for f in findings if f["required"] and not f.get("available")],
            "optional_missing": [f["name"] for f in findings if not f["required"] and not f.get("available")],
            "note": "Checks follow required_checks; optional missing tools do not block this workflow. Path checks do not prove game loading or MCP health."}
