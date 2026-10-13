# Blender Connector for CodeBuddy

An [MCP](https://modelcontextprotocol.io) connector that lets CodeBuddy (or any
MCP client) drive **Blender 4.2+ / 5.x** — scene inspection, object creation,
materials, rendering and arbitrary `bpy` access.

It bridges to **Blender's official MCP add-on** (Blender Lab, `id="mcp"`),
which ships with recent Blender versions — no third-party addon needed.

```
CodeBuddy ──MCP (stdio)──▶ blender-connector ──JSON/TCP :9876──▶ Blender MCP add-on ──▶ bpy
```

## Prerequisites

1. **Blender 4.2+ / 5.x** with the official **MCP add-on** installed and enabled
   (`Preferences → Add-ons`, search "MCP", maintainer *Blender Lab*).
2. Start the add-on server:
   - **GUI:** 3D viewport → `N` panel → *MCP* → **Connect**
   - **Headless:** `blender --background file.blend --command blender_mcp`

## Install — one command, no coding

You never write Python and never edit JSON. The connector runs Python inside
Blender behind the scenes — **you just talk to CodeBuddy in plain language**
("create a cube, make it blue, render a preview").

```bash
curl -fsSL https://raw.githubusercontent.com/landryvyathe/3D-Connectors/main/install.sh | bash
```

The installer:
1. checks the runner is available,
2. registers the MCP server in `~/.codebuddy/mcp.json` (backup first, idempotent),
3. tells you the two clicks needed inside Blender (install the official MCP
   add-on, press Connect).

Then **reload CodeBuddy** and start asking.

<details>
<summary>Manual setup (if you prefer editing configs yourself)</summary>

Add to `~/.codebuddy/mcp.json` (or the project `.mcp.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/landryvyathe/3D-Connectors.git", "blender-connector"]
    }
  }
}
```

Or with a local checkout:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/3D-Connectors", "blender-connector"]
    }
  }
}
```

Reload the CodeBuddy session — the `mcp__blender__*` tools then appear.

### Configuration (environment variables)

| Variable           | Default     | Meaning                        |
|--------------------|-------------|--------------------------------|
| `BLENDER_MCP_HOST` | `localhost` | Host running Blender           |
| `BLENDER_MCP_PORT` | `9876`      | Port of the Blender MCP socket |

Add them under `"env"` in the server entry, e.g.
`"env": {"BLENDER_MCP_PORT": "9877"}` for a second headless instance.

</details>

## Tools

| Tool                 | Purpose                                                        |
|----------------------|----------------------------------------------------------------|
| `execute_blender_code` | Run arbitrary Python inside Blender, return its `result` dict |
| `get_scene_info`     | Scenes and objects (name/type)                                 |
| `get_object_info`    | Transform, dimensions, materials, vertex count of one object   |
| `create_primitive`   | cube / sphere / cylinder / cone / torus / plane / monkey       |
| `add_material`       | Principled-BSDF material with a base color, assigned to object |
| `render_scene`       | Cycles CPU render to a PNG (path, samples, resolution)         |
| `save_file`          | Save the session as `.blend`                                   |
| `connection_status`  | Blender version + socket health                                |

## Example session

> "Create a cube, make it blue, and render a preview"

The connector runs `primitive_cube_add`, assigns a Principled BSDF with a blue
base color, and renders via Cycles — all through the tools above.

![Rendered cube preview](docs/example-cube.png)

It works with real assets too — here a Lamborghini model imported from
BlenderKit and rendered headless:

![Lamborghini preview](docs/example-lamborghini.png)

## Testing

With Blender running and its MCP server started:

```bash
python3 test_connector.py
```

Runs the full stdio handshake, lists tools, and performs real scene operations
(create + material + scene query) against the live Blender instance.

## License

MIT
