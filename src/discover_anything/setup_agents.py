"""Install the bundled skills and register the MCP server with a coding agent.

Dry run by default: prints the plan. ``--yes`` applies it. Existing skill
folders are backed up, never overwritten in place.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .resources import skill_names, skills_root

CLIENT_SKILL_DIRS = {
    "claude-code": Path.home() / ".claude" / "skills",
}
MCP_NAME = "discover-anything"


def _server_command() -> list[str]:
    return [sys.executable, "-m", "discover_anything", "mcp"]


def _manual_instructions(client: str) -> str:
    command = " ".join(_server_command())
    return (
        f"Automatic setup for '{client}' isn't supported yet. To finish by hand:\n"
        f"  1. Skills: run `npx skills add karangupta8/discover-anything`, or copy the folders in\n"
        f"     {skills_root()} into your agent's skills directory (re-run with --skills-dir).\n"
        f"  2. MCP server: register a stdio server named '{MCP_NAME}' with the command:\n"
        f"     {command}\n"
    )


def plan(client: str, skills_dir: str | None) -> list[str]:
    target = Path(skills_dir) if skills_dir else CLIENT_SKILL_DIRS.get(client)
    steps = []
    if target:
        for name in skill_names():
            dest = target / name
            note = " (existing folder will be backed up)" if dest.exists() else ""
            steps.append(f"copy skill {name} → {dest}{note}")
    if client == "claude-code":
        steps.append("run: claude mcp add --scope user " + MCP_NAME + " -- "
                     + " ".join(_server_command()))
    return steps


def _copy_skills(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for name in skill_names():
        dest = target / name
        if dest.exists():
            dest.rename(dest.with_name(f"{name}.bak-{stamp}"))
        shutil.copytree(skills_root() / name, dest)


def run_setup(client: str, apply: bool = False, skills_dir: str | None = None) -> int:
    steps = plan(client, skills_dir)
    if not steps:
        print(_manual_instructions(client))
        return 0
    print("Plan:" if not apply else "Applying:")
    for step in steps:
        print(f"  - {step}")
    if not apply:
        print("\nDry run. Re-run with --yes to apply.")
        if client not in CLIENT_SKILL_DIRS:
            print(_manual_instructions(client))
        return 0

    target = Path(skills_dir) if skills_dir else CLIENT_SKILL_DIRS.get(client)
    if target:
        _copy_skills(target)
    if client == "claude-code":
        cmd = ["claude", "mcp", "add", "--scope", "user", MCP_NAME, "--", *_server_command()]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        except FileNotFoundError:
            print("`claude` CLI not found; register the MCP server by hand:\n  " + " ".join(cmd))
            return 1
        print(result.stdout.strip() or result.stderr.strip())
        if result.returncode != 0:
            return result.returncode
    elif client not in CLIENT_SKILL_DIRS:
        print(_manual_instructions(client))
    print("\nDone. Restart your agent so it loads the skills and MCP server.")
    return 0
