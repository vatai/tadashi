#!/bin/env python3
from fastmcp import FastMCP

from tadashi import apps, translators

mcp = FastMCP("tadashi")

app: apps.App | None = None


def current_app() -> apps.App:
    if app is None:
        raise ValueError("No app has been created yet. Call create_app first.")
    return app


@mcp.tool()
def load_app_class(name: str):
    return True


@mcp.tool()
def create_app(
    app_cls: str,
    args: dict,
    translator: str | None = None,
    targs: dict | None = None,
) -> dict:
    """Create or replace the current Tadashi app instance.

    Args:
        app_cls: Name of the Tadashi app class to instantiate.
        args: Constructor arguments passed to the selected app class.
        translator: Translator class used with the app (default is None).
        targs: Constructor arguments passed to the selected app class (default is None).

    Returns:
        A dictionary describing the created app and its schedule trees.
    """
    global app

    cls = getattr(apps, app_cls)
    if translator:
        tcls = getattr(translators, translator)
        args["translator"] = tcls(**(targs or {}))

    app = cls(**args)

    return {
        "source": str(app.source),
        "output_binary": str(app.output_binary),
        "scops": [s.schedule_tree[0].yaml_str for s in app.scops],
    }


@mcp.tool()
def get_all_transformations() -> list:
    """Return all available transformations for the current app."""
    return current_app().get_all_transformations()


@mcp.tool()
def reset_scops() -> bool:
    """Reset the current app's SCoPs."""
    current_app().reset_scops()
    return True


@mcp.tool()
def transform_list(transformation_list: list) -> bool:
    """Apply a list of transformations to the current app."""
    current_app().transform_list(transformation_list)
    return True


@mcp.tool()
def compile_app(extra_compiler_options: list[str] | None = None) -> bool:
    """Compile the current app."""
    current_app().compile(extra_compiler_options or [])
    return True


@mcp.tool()
def measure(repeat: int = 1) -> float:
    """Measure the runtime of the current app."""
    return current_app().measure(repeat=repeat)


@mcp.tool()
def generate_code(
    alt_infix: str | None = None,
    ephemeral: bool = True,
    populate_scops: bool = False,
    ensure_legality: bool = True,
) -> dict:
    """Generate transformed code and replace the current app with it."""
    global app

    app = current_app().generate_code(
        alt_infix=alt_infix,
        ephemeral=ephemeral,
        populate_scops=populate_scops,
        ensure_legality=ensure_legality,
    )

    return {
        "source": str(app.source),
        "output_binary": str(app.output_binary),
    }


def server():
    mcp.run()
