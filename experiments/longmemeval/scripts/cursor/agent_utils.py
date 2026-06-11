import os
import shlex
from pathlib import Path


def cursor_agent_script():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    script = Path(local_app_data) / "cursor-agent" / "agent.ps1"
    return script if script.exists() else None


def build_agent_argv(agent_command, extra_args):
    tokens = shlex.split(agent_command, posix=False)
    if tokens and tokens[0] == "agent":
        tokens = tokens[1:]

    if os.name == "nt":
        agent_script = cursor_agent_script()
        if agent_script is None:
            raise RuntimeError(
                "Cursor agent CLI not found. Install with: "
                "irm 'https://cursor.com/install?win32=true' | iex"
            )
        return [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(agent_script),
            *tokens,
            *extra_args,
        ]

    return ["agent", *tokens, *extra_args]
