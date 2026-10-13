# 3D Connectors

A collection of **MCP connectors** that let AI coding assistants
([CodeBuddy](https://www.codebuddy.ai), Claude, …) drive **3D software**.

| Connector | Target | Status |
|-----------|--------|--------|
| [`blender-connector`](blender-connector/) | Blender 4.2+ / 5.x (official MCP add-on) | ✅ working |

## What is a connector?

Each folder here is an installable **MCP (Model Context Protocol) server**
package. Register it once in your assistant's MCP config and it gains tools to
inspect scenes, create/modify objects, apply materials, render previews and
save files — conversationally.

## Quick start (Blender)

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

See [`blender-connector/README.md`](blender-connector/README.md) for the full
setup, including how to start Blender's MCP server headless.

## Adding a connector for another tool

Create a folder `<tool>-connector/` containing a standard Python package with a
`pyproject.toml` and an MCP stdio entry point. Keep each connector
self-contained and document its prerequisites in its own README.

## License

MIT — see [LICENSE](LICENSE).
