# Copyright 2024 Marimo. All rights reserved.
"""The marimo library.

marimo is a Python library for making reactive notebooks that double as apps.

marimo is designed to be:

    1. simple
    2. immersive
    3. interactive
    4. seamless
    5. fun
"""

__all__ = [
    "App",
    "MarimoStopError",
    "accordion",
    "as_html",
    "audio",
    "callout",
    "capture_stdout",
    "capture_stderr",
    "center",
    "defs",
    "doc",
    "download",
    "hstack",
    "Html",
    "icon",
    "image",
    "left",
    "md",
    "mermaid",
    "mpl",
    "output",
    "plain_text",
    "pdf",
    "redirect_stderr",
    "redirect_stdout",
    "refs",
    "right",
    "stat",
    "state",
    "status",
    "stop",
    "style",
    "tabs",
    "tree",
    "ui",
    "video",
    "vstack",
]
__version__ = "0.2.5"
try:
    from marimo._ast.app import App
    from marimo._output.doc import doc
    from marimo._output.formatting import as_html
    from marimo._output.hypertext import Html
    from marimo._output.justify import center, left, right
    from marimo._output.md import md
    from marimo._plugins import ui
    from marimo._plugins.stateless import mpl, status
    from marimo._plugins.stateless.accordion import accordion
    from marimo._plugins.stateless.audio import audio
    from marimo._plugins.stateless.callout import callout
    from marimo._plugins.stateless.download import download
    from marimo._plugins.stateless.flex import hstack, vstack
    from marimo._plugins.stateless.icon import icon
    from marimo._plugins.stateless.image import image
    from marimo._plugins.stateless.mermaid import mermaid
    from marimo._plugins.stateless.pdf import pdf
    from marimo._plugins.stateless.plain_text import plain_text
    from marimo._plugins.stateless.stat import stat
    from marimo._plugins.stateless.style import style
    from marimo._plugins.stateless.tabs import tabs
    from marimo._plugins.stateless.tree import tree
    from marimo._plugins.stateless.video import video
    from marimo._runtime import output
    from marimo._runtime.capture import (
        capture_stderr,
        capture_stdout,
        redirect_stderr,
        redirect_stdout,
    )
    from marimo._runtime.control_flow import MarimoStopError, stop
    from marimo._runtime.runtime import defs, refs
    from marimo._runtime.state import state
except (ModuleNotFoundError, ImportError):
    pass
# -----------------------------------------------------------------------------
# Make marimo work as a blender addon
# -----------------------------------------------------------------------------

bl_info = {
    "name": "Blender Notebook",
    "author": "iplai",
    "description": "Reactive notebook for Python integrated in blender",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "View 3D > Header Menu > Notebook",
    "doc_url": "https://github.com/iplai/marimo-blender",
    "tracker_url": "https://github.com/iplai/marimo-blender/issues",
    "warning": "",
    "category": "Generic"
}

import bpy
import threading


dependencies = [
    # For maintainable cli
    "click>=8.0,<9",
    # For python 3.8 compatibility
    "importlib_resources>=5.10.2; python_version < \"3.9\"",
    # code completion
    "jedi>=0.18.0",
    # compile markdown to html
    "markdown>=3.4,<4",
    # add features to markdown
    "pymdown-extensions>=9.0,<11",
    # syntax highlighting of code in markdown
    "pygments>=2.13,<3",
    # for reading, writing configs
    "tomlkit>= 0.12.0",
    # web server
    # - 0.22.0 introduced timeout-graceful-shutdown, which we use
    "uvicorn >= 0.22.0",
    # web framework
    # - 0.26.1 introduced lifespans, which we use
    # - starlette 0.36.0 introduced a bug
    "starlette>=0.26.1,!=0.36.0",
    # websockets for use with starlette
    "websockets >= 10.0.0,<13.0.0",
    # python <=3.10 compatibility
    "typing_extensions>=4.4.0; python_version < \"3.10\"",
    # for rst parsing
    "docutils>=0.17.0",
    # for cell formatting; if user version is not compatible, no-op
    # so no lower bound needed
    "black",
]

marimo_thread: threading.Thread = None
marimo_port: int = None


class MarimoAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    port: bpy.props.IntProperty(
        name="Port of Marimo Server",
        default=2718,
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "port")
        row.operator(MarimoInstallDependencies.bl_idname, icon='FILE_REFRESH', text="Install Dependencies")
        # row.operator(MarimoUninstallDependencies.bl_idname, icon='X', text="Uninstall Dependencies")


def server_thread_function(port: int):
    from marimo._server.start import start
    from marimo._server.utils import find_free_port
    # from marimo._server.api.lifespans import LIFESPANS
    # LIFESPANS.lifespans = [lifespan for lifespan in LIFESPANS.lifespans if lifespan.__name__ != "signal_handler"]
    global marimo_port
    marimo_port = find_free_port(port)
    start(
        development_mode=True,
        quiet=False,
        host="",
        port=marimo_port,
        headless=False,
        filename=None,
        mode='edit',
        include_code=True,
        watch=False,
    )


class MarimoInstallDependencies(bpy.types.Operator):
    """Check and install dependencies for Marimo"""
    bl_idname = 'marimo.install_dependencies'
    bl_label = 'Marimo: Install Dependencies'

    def execute(self, context):
        from .installation import ensure_packages_are_installed
        ensure_packages_are_installed([d.split(">=")[0].strip() for d in dependencies])
        self.report({'INFO'}, "Dependencies installed")
        return {'FINISHED'}


class MarimoUninstallDependencies(bpy.types.Operator):
    """Uninstall dependencies for Marimo"""
    bl_idname = 'marimo.uninstall_dependencies'
    bl_label = 'Marimo: Uninstall Dependencies'

    def execute(self, context):
        from .installation import uninstall_package
        for d in dependencies:
            name = d.split(">=")[0].strip()
            uninstall_package(name)
        return {'FINISHED'}


class MarimoServerManager(bpy.types.Operator):
    """Start Marimo Server if not exist then open Browser"""
    bl_idname = 'marimo.start_server_or_open_browser'
    bl_label = 'Start Reactive Notebook'

    def execute(self, context):
        global marimo_thread
        if marimo_thread is None or not marimo_thread.is_alive():
            port = bpy.context.preferences.addons[__name__].preferences.port
            marimo_thread = threading.Thread(target=server_thread_function, args=(port,))
            # marimo_thread.daemon = True
            marimo_thread.start()
        else:
            import webbrowser
            webbrowser.open(f"http://localhost:{marimo_port}")
        return {'FINISHED'}


def marimo_header_btn(self: bpy.types.Menu, context):
    self.layout.operator(MarimoServerManager.bl_idname, icon='CURRENT_FILE', text="")


classes = (
    MarimoInstallDependencies,
    MarimoUninstallDependencies,
    MarimoAddonPreferences,
    MarimoServerManager,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(marimo_header_btn)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_HT_header.remove(marimo_header_btn)
    marimo_thread and marimo_thread.join(1.0)
