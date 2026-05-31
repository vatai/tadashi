#!/bin/env python3
import importlib

from fastmcp import FastMCP

from tadashi import apps, translators

mcp = FastMCP("tadashi")

app: apps.App | None = None


@mcp.tool
def load_app_class(name: str):
    return True


@mcp.tool()
def create_app(
    app_cls: str,
    args: dict[str, str],
    translator: str | None = None,
    targs: dict[str, str] | None = None,
) -> str:
    """Create a Tadashi app instance from a named app class.

    Args:
        app_cls: Name of the Tadashi app class to instantiate.
        args: Constructor arguments passed to the selected app class.
        translator: Translator class used with the app (default is None).
        targs: Constructor arguments passed to the selected app class (default is None).

    Returns:
        A list of yaml strings describing the schedule tree of each scop.
    """
    # create an Polybench app with benchmark "gemm" arg
    app_cls = getattr(apps, app_cls)
    if translator:
        tcls = getattr(translators, translator)
        tobj = tcls(**targs)
        args["translator"] = tobj
    app = app_cls(**args)
    return [s.schedule_tree[0].yaml_str for s in app.scops]


def server():
    mcp.run()
