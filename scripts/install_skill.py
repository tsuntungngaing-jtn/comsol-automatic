"""Install public skill files for clients such as Codex that load a local directory.

This copies audited source files only. It neither installs Python dependencies nor
changes existing MCP connectors, local tokens, running services, or client indexes.
This is NOT an installer for Doubao's skill management list. Use Upload Skill there.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from release import ROOT, public_files


def install(skills_dir: Path, source: Path = ROOT) -> dict:
    destination = skills_dir.expanduser().resolve() / "comsol-automatic"
    if destination.exists():
        raise FileExistsError(
            f"Skill directory already exists: {destination}. No files were changed. "
            "Review an update separately; preserve local tokens and runtime files."
        )
    files = public_files(source)
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {
        "skill_installed": True,
        "directory": str(destination),
        "files": len(files),
        "mcp_configuration_changed": False,
        "client_list_visibility_verified": False,
        "next_step": "For Codex, start the next turn to discover the local skill. "
                     "For Doubao's management list, use its Upload Skill entry with the release ZIP. "
                     "Local copying does not complete that installation. Existing MCP connectors are unchanged.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    default_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--skills-dir", type=Path, default=default_home / "skills")
    args = parser.parse_args()
    print(json.dumps(install(args.skills_dir), indent=2, ensure_ascii=False))
