"""Socket transport for Blender's official MCP add-on (Blender Lab, id "mcp").

The add-on listens for null-byte-delimited JSON requests of the form::

    {"type": "execute", "code": "<python>", "strict_json": true}\0

and answers with JSON responses (``{"status": "ok", "result": {...}}`` or an
error object), optionally followed by captured stdout/stderr. The executed
code must assign a dict to a variable named ``result``.
"""

from __future__ import annotations

import json
import os
import socket

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
DEFAULT_TIMEOUT = 300.0
_RECV_SIZE = 65536


class BlenderConnectionError(RuntimeError):
    """Raised when the Blender MCP socket cannot be reached or misbehaves."""


class BlenderExecutionError(RuntimeError):
    """Raised when code executed inside Blender raises or returns an error."""


def get_connection_params() -> tuple[str, int]:
    """Resolve host/port from the environment (matches the official client)."""
    host = os.environ.get("BLENDER_MCP_HOST", DEFAULT_HOST)
    port = int(os.environ.get("BLENDER_MCP_PORT", str(DEFAULT_PORT)))
    return host, port


def execute(code: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Run *code* inside Blender and return the ``result`` dict.

    Raises :class:`BlenderConnectionError` on transport problems and
    :class:`BlenderExecutionError` when Blender reports an execution error.
    """
    host, port = get_connection_params()
    request = json.dumps({"type": "execute", "code": code, "strict_json": True}) + "\0"
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(request.encode("utf-8"))
            buf = bytearray()
            while b"\0" not in buf:
                chunk = sock.recv(_RECV_SIZE)
                if not chunk:
                    raise BlenderConnectionError(
                        "Blender closed the connection before sending a response"
                    )
                buf.extend(chunk)
    except (OSError, socket.timeout) as ex:
        raise BlenderConnectionError(
            f"cannot reach Blender MCP server on {host}:{port} — "
            f"is Blender running with the MCP add-on started? ({type(ex).__name__}: {ex})"
        ) from ex

    payload = bytes(buf).split(b"\0", 1)[0].decode("utf-8")
    response = json.loads(payload)
    if response.get("status") != "ok":
        message = response.get("message", "unknown error")
        stderr = response.get("stderr")
        if stderr:
            message = f"{message}\nstderr:\n{stderr}"
        raise BlenderExecutionError(message)
    return response.get("result", {})
