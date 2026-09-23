"""Kernel-enforced limits on what bash can touch.

Policy: Read system, write ONLY inside the project directory, deny network.
Mechanism:
- macOS: Apple Seatbelt sandbox-exec (adapted from OpenAI Codex).
- Linux: Bubblewrap (bwrap) unshared namespaces.
- Windows: Direct execution fallback.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

# macOS Seatbelt Profile (Scheme DSL)
PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""

def wrap(command: str) -> list[str] | None:
    """Wrap a shell command in an OS sandbox if supported."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "myagent.sb"
        profile.write_text(PROFILE, encoding="utf-8")
        return ["sandbox-exec", "-f", str(profile), "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            "--dev", "/dev",
            "--proc", "/proc",
            "--unshare-net",
            "--die-with-parent",
            "/bin/sh", "-c", command,
        ]

    return None  # Windows or Linux without bubblewrap

def name() -> str:
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"

def run(command: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Execute command safely wrapped in an OS sandbox when available."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
