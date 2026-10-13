"""CodeBuddy MCP connector for Blender.

Bridges the Model Context Protocol to Blender's official MCP add-on socket
(Blender Lab, ``id="mcp"``, ships with Blender 4.2+/5.x), exposing scene
inspection, object creation, materials, rendering and arbitrary ``bpy`` access
as MCP tools.

Run: ``blender-connector`` (stdio MCP server).

Configuration (environment variables):
    BLENDER_MCP_HOST   Blender host          (default: localhost)
    BLENDER_MCP_PORT   Blender addon port   (default: 9876)
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .connection import (
    BlenderConnectionError,
    BlenderExecutionError,
    execute,
    get_connection_params,
)

mcp = FastMCP("blender")

_PRIMITIVES = ("cube", "sphere", "cylinder", "cone", "torus", "plane", "monkey")


def _run(code: str, timeout: float | None = None) -> str:
    """Execute *code* in Blender and return the JSON result (or error text)."""
    try:
        result = execute(code, timeout=timeout) if timeout else execute(code)
    except BlenderExecutionError as ex:
        return json.dumps({"status": "error", "message": str(ex)})
    except BlenderConnectionError as ex:
        return json.dumps({"status": "error", "message": str(ex)})
    return json.dumps({"status": "ok", "result": result})


@mcp.tool()
def execute_blender_code(code: str) -> str:
    """Execute arbitrary Python code inside Blender and return its ``result``.

    The code runs with full ``bpy`` access. Assign the value you want returned
    to a dict named ``result``, e.g.::

        import bpy
        result = {"objects": [o.name for o in bpy.context.scene.objects]}
    """
    return _run(code)


@mcp.tool()
def get_scene_info() -> str:
    """List the scenes, their objects (name/type) and the active scene name."""
    return _run(
        "import bpy\n"
        "result = {\n"
        "    'active_scene': bpy.context.scene.name,\n"
        "    'scenes': [s.name for s in bpy.data.scenes],\n"
        "    'objects': [\n"
        "        {'name': o.name, 'type': o.type}\n"
        "        for o in bpy.context.scene.objects\n"
        "    ],\n"
        "}\n"
    )


@mcp.tool()
def get_object_info(name: str) -> str:
    """Inspect one object: type, location, rotation, scale, dimensions, materials."""
    return _run(
        "import bpy\n"
        f"obj = bpy.data.objects.get({name!r})\n"
        "if obj is None:\n"
        f'    result = {{"error": "object {name!r} not found"}}\n'
        "else:\n"
        "    result = {\n"
        "        'name': obj.name, 'type': obj.type,\n"
        "        'location': list(obj.location),\n"
        "        'rotation_euler': list(obj.rotation_euler),\n"
        "        'scale': list(obj.scale),\n"
        "        'dimensions': list(obj.dimensions),\n"
        "        'materials': [m.name for m in obj.data.materials] if obj.data and hasattr(obj.data, 'materials') else [],\n"
        "        'vertex_count': len(obj.data.vertices) if obj.type == 'MESH' else None,\n"
        "    }\n"
    )


@mcp.tool()
def create_primitive(
    kind: str,
    name: str = "",
    location: list[float] | None = None,
    size: float = 2.0,
) -> str:
    """Create a primitive mesh. ``kind``: cube, sphere, cylinder, cone, torus, plane or monkey."""
    kind = kind.lower().strip()
    if kind not in _PRIMITIVES:
        return json.dumps(
            {"status": "error", "message": f"unknown kind {kind!r}; choose from {list(_PRIMITIVES)}"}
        )
    loc = location or [0.0, 0.0, 0.0]
    ops = {
        "cube": "primitive_cube_add(size={s})",
        "sphere": "primitive_uv_sphere_add(radius={r})",
        "cylinder": "primitive_cylinder_add(radius={r}, depth={d})",
        "cone": "primitive_cone_add(radius1={r}, depth={d})",
        "torus": "primitive_torus_add(major_radius={r})",
        "plane": "primitive_plane_add(size={s})",
        "monkey": "primitive_monkey_add(size={s})",
    }
    call = ops[kind].format(s=size, r=size / 2, d=size * 2)
    code = (
        "import bpy\n"
        f"bpy.ops.mesh.{call}\n"
        f"obj = bpy.context.active_object\n"
        f"obj.location = {tuple(loc)!r}\n"
        + (f"obj.name = {name!r}\n" if name else "")
        + "result = {'created': obj.name, 'type': obj.type, 'location': list(obj.location)}\n"
    )
    return _run(code)


@mcp.tool()
def add_material(
    object_name: str,
    material_name: str = "ConnectorMaterial",
    rgba: list[float] | None = None,
) -> str:
    """Create (or reuse) a Principled-BSDF material and assign it to an object."""
    color = rgba or [0.8, 0.8, 0.8, 1.0]
    if len(color) != 4:
        return json.dumps({"status": "error", "message": "rgba must have 4 components"})
    code = (
        "import bpy\n"
        f"obj = bpy.data.objects.get({object_name!r})\n"
        "if obj is None:\n"
        f'    result = {{"error": "object {object_name!r} not found"}}\n'
        "else:\n"
        f"    mat = bpy.data.materials.get({material_name!r}) or bpy.data.materials.new({material_name!r})\n"
        "    mat.use_nodes = True\n"
        "    bsdf = mat.node_tree.nodes.get('Principled BSDF')\n"
        f"    bsdf.inputs['Base Color'].default_value = {tuple(color)!r}\n"
        f"    mat.diffuse_color = {tuple(color)!r}\n"
        "    if obj.data.materials:\n"
        "        obj.data.materials[0] = mat\n"
        "    else:\n"
        "        obj.data.materials.append(mat)\n"
        f"    result = {{'object': obj.name, 'material': mat.name, 'base_color': list(bsdf.inputs['Base Color'].default_value)}}\n"
    )
    return _run(code)


@mcp.tool()
def render_scene(
    output_path: str,
    samples: int = 32,
    resolution: list[int] | None = None,
) -> str:
    """Render the current scene (Cycles CPU) to *output_path* (e.g. ``/tmp/preview.png``)."""
    res = resolution or [640, 480]
    code = (
        "import bpy\n"
        "scene = bpy.context.scene\n"
        "scene.render.engine = 'CYCLES'\n"
        "scene.cycles.device = 'CPU'\n"
        f"scene.cycles.samples = {int(samples)}\n"
        "scene.cycles.use_denoising = False\n"
        f"scene.render.resolution_x = {int(res[0])}\n"
        f"scene.render.resolution_y = {int(res[1])}\n"
        f"scene.render.filepath = {output_path!r}\n"
        "bpy.ops.render.render(write_still=True)\n"
        f"result = {{'rendered': {output_path!r}}}\n"
    )
    return _run(code, timeout=600.0)


@mcp.tool()
def save_file(filepath: str) -> str:
    """Save the current Blender session to a ``.blend`` file."""
    code = (
        "import bpy\n"
        f"bpy.ops.wm.save_as_mainfile(filepath={filepath!r})\n"
        f"result = {{'saved': bpy.data.filepath}}\n"
    )
    return _run(code)


@mcp.tool()
def connection_status() -> str:
    """Report connector settings and whether the Blender socket answers."""
    host, port = get_connection_params()
    return _run(
        "import bpy\n"
        "result = {\n"
        "    'blender_version': bpy.app.version_string,\n"
        "    'background': bpy.app.background,\n"
        "    'scene': bpy.context.scene.name,\n"
        "    'object_count': len(bpy.context.scene.objects),\n"
        "}\n",
        timeout=15.0,
    ) + f" (connector target: {host}:{port})"


def main() -> None:
    """Entry point for the ``blender-connector`` script."""
    mcp.run()


if __name__ == "__main__":
    main()
