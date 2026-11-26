"""Prepare and start Project Check's local MCP with an isolated Python runtime."""

from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
PYTHON_ERROR = (
    "Project Check needs Python 3.11 or later. Install Python with python3 on PATH, "
    "then restart Codex and open a new chat."
)


def interpreter():
    if sys.version_info >= (3, 11):
        return Path(sys.executable)
    versions = ("3.14", "3.13", "3.12", "3.11")
    # Desktop-launched MCP processes can have a shorter PATH than the user's shell.
    search_dirs = [os.environ.get("PATH") or os.defpath, str(Path.home() / ".local" / "bin")]
    if sys.platform == "darwin":
        search_dirs.extend(("/opt/homebrew/bin", "/usr/local/bin"))
        for version in versions:
            search_dirs.extend((
                f"/Library/Frameworks/Python.framework/Versions/{version}/bin",
                f"/opt/homebrew/opt/python@{version}/bin",
                f"/usr/local/opt/python@{version}/bin",
            ))
    search_path = os.pathsep.join(search_dirs)
    candidates = [(f"python{version}",) for version in versions]
    candidates.extend([("python",), ("py", "-3")])
    for command, *flags in candidates:
        executable = shutil.which(command, path=search_path)
        if not executable:
            continue
        try:
            probe = subprocess.run(
                [executable, *flags, "-I", "-c",
                 "import sys; assert sys.version_info >= (3, 11); print(sys.executable)"],
                capture_output=True, text=True, timeout=5, check=True,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        return Path(probe.stdout.strip())
    raise RuntimeError(PYTHON_ERROR)


def runtime_root():
    custom = os.environ.get("PROJECT_CHECK_RUNTIME_DIR")
    if custom:
        return Path(custom).expanduser()
    if os.name == "nt":
        data = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    else:
        data = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(data) / "project-check" / "runtime"


@contextmanager
def install_lock(path):
    # OS locks release on exit, including when Codex stops an unfinished startup.
    with path.open("a+b") as stream:
        if os.name == "nt":
            from msvcrt import LK_NBLCK, locking

            if stream.seek(0, os.SEEK_END) == 0:
                stream.write(b"\0")
                stream.flush()
            deadline = time.monotonic() + 160
            while True:
                stream.seek(0)
                try:
                    locking(stream.fileno(), LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Timed out waiting for the Project Check dependency installation.") from None
                    time.sleep(0.2)
        else:
            from fcntl import LOCK_EX, flock

            flock(stream.fileno(), LOCK_EX)
        yield


def prepare_runtime():
    base_python = interpreter()
    digest = sha256(REQUIREMENTS.read_bytes())
    digest.update(os.fsencode(os.path.abspath(base_python)))
    root = runtime_root().resolve() / digest.hexdigest()[:24]
    root.mkdir(parents=True, exist_ok=True)
    environment = root / "venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    ready = root / "ready"
    with install_lock(root / "install.lock"):
        if ready.is_file() and python.is_file():
            return python
        ready.unlink(missing_ok=True)
        if environment.exists():
            shutil.rmtree(environment)
        subprocess.run(
            [str(base_python), "-I", "-m", "venv", str(environment)], check=True,
            stdin=subprocess.DEVNULL, stdout=sys.stderr, timeout=30,
        )
        subprocess.run(
            [str(python), "-I", "-m", "pip", "install", "--disable-pip-version-check",
             "--no-input", "--require-hashes", "-r", str(REQUIREMENTS)],
            check=True, stdin=subprocess.DEVNULL, stdout=sys.stderr, timeout=120,
        )
        ready.touch()
        return python


def main():
    try:
        python = prepare_runtime()
        if sys.argv[1:] == ["--prepare-only"]:
            print("Project Check Python runtime is ready.")
            return
        os.execv(str(python), [str(python), "-E", "-s", str(ROOT / "scripts" / "mcp_proxy.py"), *sys.argv[1:]])
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Project Check MCP startup failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
