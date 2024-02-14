import bpy
import threading
from marimo._server.api.lifespans import LIFESPANS
from marimo._server.start import start
from marimo._server.utils import find_free_port

LIFESPANS.lifespans = [lifespan for lifespan in LIFESPANS.lifespans if lifespan.__name__ != "signal_handler"]

marimo_thread: threading.Thread = None
port = find_free_port(2718)


def server_thread_function():
    start(
        development_mode=True,
        quiet=False,
        host="",
        port=port,
        headless=False,
        filename=None,
        mode='edit',
        include_code=True,
        watch=False,
    )


class MarimoServerManager(bpy.types.Operator):
    """Start Marimo Server if not exist then open Browser"""
    bl_idname = 'marimo.start_server_or_open_browser'
    bl_label = 'Start Reactive Notebook'

    def execute(self, context):
        global marimo_thread
        if marimo_thread is None or not marimo_thread.is_alive():
            marimo_thread = threading.Thread(target=server_thread_function)
            # marimo_thread.daemon = True
            marimo_thread.start()
        else:
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")
        return {'FINISHED'}


def marimo_header_btn(self: bpy.types.Menu, context):
    self.layout.operator(MarimoServerManager.bl_idname, icon='CURRENT_FILE', text="")


def register():
    bpy.types.VIEW3D_HT_header.append(marimo_header_btn)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(marimo_header_btn)
