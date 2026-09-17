import os
import shlex
import sys
from pathlib import Path

PINNED_CBM_VERSION = "0.10.5"


def _safe_int(env_key: str, default: int) -> int:
    raw = os.environ.get(env_key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(
            f"WARNING: {env_key}={raw!r} is not a valid integer, using default {default}",
            file=sys.stderr,
        )
        return default


# ── HTTP server ────────────────────────────────────────────────────
SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
_raw_port = _safe_int("SERVER_PORT", 8003)
SERVER_PORT = max(1, min(65535, _raw_port))
if not (1 <= _raw_port <= 65535):
    print(
        f"WARNING: SERVER_PORT={_raw_port} out of [1, 65535], clamped to {SERVER_PORT}",
        file=sys.stderr,
    )

SERVER_VERSION = "0.1.0"

# ── Auth ───────────────────────────────────────────────────────────
MARM_GRAPH_API_KEY = os.environ.get("MARM_GRAPH_API_KEY", "")

# ── codebase-memory-mcp subprocess ─────────────────────────────────
CBM_BINARY_PATH = os.environ.get("CBM_BINARY_PATH", "")
_CBM_COMMAND_RAW = os.environ.get("CBM_COMMAND", "")


def cbm_spawn_command() -> list[str]:
    if CBM_BINARY_PATH:
        return [CBM_BINARY_PATH]
    if _CBM_COMMAND_RAW:
        return shlex.split(_CBM_COMMAND_RAW)
    return [sys.executable, "-m", "codebase_memory_mcp"]


CBM_STARTUP_TIMEOUT = float(_safe_int("CBM_STARTUP_TIMEOUT", 60))
CBM_CALL_TIMEOUT = float(_safe_int("CBM_CALL_TIMEOUT", 300))


def cbm_binary_provisioned() -> bool:
    """Whether an engine binary is already on disk, so spawning the child will
    not trigger the ~269MB first-run download.

    CBM_BINARY_PATH is consulted first because the Docker image pre-bakes the
    engine outside the downloader's cache directory. Checking only that cache
    path -- which is what callers used to do -- reports False for every
    containerised install: the auto-index poller then stayed dormant until some
    graph tool happened to start the engine, and the supervisor announced a
    download that never happens. A configured-but-missing path stays False, so
    this keeps agreeing with backend.verify_and_start().
    """
    if CBM_BINARY_PATH:
        return os.path.exists(CBM_BINARY_PATH)
    try:
        from codebase_memory_mcp import _cli

        return bool(_cli._bin_path(_cli._version()).exists())
    except Exception:
        return False


# ── Response bounding ──────────────────────────────────────────────
MAX_RESPONSE_BYTES = _safe_int("MARM_GRAPH_MAX_RESPONSE_BYTES", 900_000)

# ── Store location (informational) ─────────────────────────────────.
STORE_DIR = Path(
    os.environ.get("MARM_GRAPH_STORE_DIR", str(Path.home() / ".marm" / "graph"))
)

CBM_CWD = os.environ.get("CBM_CWD", "") or str(STORE_DIR)
