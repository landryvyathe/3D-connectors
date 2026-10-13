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

## Install & register in CodeBuddy

Add to `~/.codebuddy/mcp.json` (or the project `.mcp.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/landryvyathe/3D-Connectors.git#subdirectory=blender-connector", "blender-connector"]
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
      "args": ["run", "--directory", "/path/to/3D-Connectors/blender-connector", "blender-connector"]
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
base color, and renders via Cycles — all through the same tools above.

## Repository layout

This connector lives in the [`blender-connector/`](blender-connector/) folder of
the **3D-Connectors** repo, so connectors for other 3D tools (Maya, Houdini, …)
can be added side by side later.

## License

MIT
