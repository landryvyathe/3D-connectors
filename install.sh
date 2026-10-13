#!/usr/bin/env bash
# One-command installer for the Blender MCP connector.
#
#   curl -fsSL https://raw.githubusercontent.com/landryvyathe/3D-Connectors/main/install.sh | bash
#
# What it does:
#   1. Checks that uvx (the runner) is available
#   2. Registers the connector into ~/.codebuddy/mcp.json (backup made first, idempotent)
#   3. Probes the Blender MCP socket and prints what to do next
#
# You never write Python or edit JSON by hand.

set -euo pipefail

REPO_URL="https://github.com/landryvyathe/3D-Connectors.git"
SERVER_KEY="blender"
CONFIG="${CODEBUDDY_CONFIG:-$HOME/.codebuddy/mcp.json}"

log() { printf '\033[1;36m[3D-Connectors]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[3D-Connectors]\033[0m %s\n' "$*" >&2; }

# --- 1. runner (uvx) --------------------------------------------------------
if [ -x "$HOME/.local/bin/uvx" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v uvx >/dev/null 2>&1; then
    err "uvx is required to run the connector without any manual setup."
    err "Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
UVX="$(command -v uvx)"
log "runner found: $UVX"

# --- 2. register into CodeBuddy config --------------------------------------
python3 - "$CONFIG" "$UVX" "$REPO_URL" "$SERVER_KEY" <<'PY'
import json
import os
import shutil
import sys
import time

config_path, uvx, repo_url, server_key = sys.argv[1:5]
os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)

cfg = {}
if os.path.exists(config_path):
    backup = f"{config_path}.bak-{int(time.time())}"
    shutil.copy2(config_path, backup)
    print(f"backup: {backup}")
    try:
        with open(config_path, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except json.JSONDecodeError:
        print(f"warning: {config_path} is not valid JSON; rewriting it")
        cfg = {}

cfg.setdefault("mcpServers", {})[server_key] = {
    "command": uvx,
    "args": ["--from", f"git+{repo_url}", "blender-connector"],
}

with open(config_path, "w", encoding="utf-8") as fh:
    json.dump(cfg, fh, indent=2)
    fh.write("\n")
print(f"registered '{server_key}' server in {config_path}")
PY

# --- 3. probe Blender --------------------------------------------------------
if python3 - "$@" <<'PY'
import socket
import sys
host, port = "localhost", int(sys.argv[1] if len(sys.argv) > 1 else 9876)
try:
    socket.create_connection((host, port), timeout=3).close()
    sys.exit(0)
except OSError:
    sys.exit(1)
PY
then
    log "Blender MCP server detected on port 9876 — you are ready to go."
else
    log "Blender is not reachable yet (that is fine). Finish these two steps when you want to use it:"
    cat <<'EOF'

  1. In Blender:  Edit > Preferences > Get Extensions  ->  search "MCP"
     (maintainer: Blender Lab)  ->  Install.
  2. Still in Blender: open the 3D viewport, press N, open the MCP panel,
     and click "Connect".

Then just reload CodeBuddy and ask, e.g.: "create a cube and make it blue".
EOF
fi

log "Done. Reload CodeBuddy, then talk to it:  \"create a cube, make it blue, render a preview\""
