#!/usr/bin/env python3
"""End-to-end test: stdio handshake + tool calls through blender-connector."""
import json
import subprocess
import sys

PROC_DIR = "/home/bykiva/DevKiva_all_in/3D-Connectors/blender-connector"


def main() -> int:
    proc = subprocess.Popen(
        ["/home/bykiva/.local/bin/uv", "run", "--directory", PROC_DIR, "blender-connector"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            "PATH": "/home/bykiva/.local/bin:/usr/bin:/bin",
            "HOME": "/home/bykiva",
            "BLENDER_MCP_PORT": "9877",
        },
    )

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def recv():
        line = proc.stdout.readline()
        return json.loads(line) if line.strip() else None

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "connector-test", "version": "1.0"}}})
    init = recv()
    info = init.get("result", {}).get("serverInfo", {}) if init else {}
    print("1. INITIALIZE:", info.get("name"), info.get("version"))

    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = recv()
    names = [t["name"] for t in tools.get("result", {}).get("tools", [])] if tools else []
    print(f"2. TOOLS ({len(names)}):", ", ".join(names))

    # Real work against live Blender: scene info + create + material
    send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
          "params": {"name": "connection_status", "arguments": {}}})
    r = recv()
    print("3. connection_status:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:220])

    send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
          "params": {"name": "create_primitive",
                     "arguments": {"kind": "sphere", "name": "ConnectorTestSphere",
                                   "location": [-3.0, 0.0, 1.0], "size": 1.0}}})
    r = recv()
    print("4. create_primitive:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:220])

    send({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
          "params": {"name": "add_material",
                     "arguments": {"object_name": "ConnectorTestSphere",
                                   "material_name": "TestRed",
                                   "rgba": [0.9, 0.1, 0.1, 1.0]}}})
    r = recv()
    print("5. add_material:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:220])

    send({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
          "params": {"name": "get_scene_info", "arguments": {}}})
    r = recv()
    text = r.get("result", {}).get("content", [{}])[0].get("text", "")
    print("6. get_scene_info:", text[:300])

    proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
