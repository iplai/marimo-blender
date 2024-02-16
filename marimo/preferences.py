import threading
import bpy

from . import addon_setup

_LINES: list[str] = []


def _lines_append(line: str):
    if line.startswith('\r') and len(_LINES) > 0:
        del _LINES[-1]
        line = line[1:]
    _LINES.append(line)


class InstallPythonModules(bpy.types.Operator):
    """Install Python Module marimo dependencies"""
    bl_idname = 'marimo.install_python_modules'
    bl_label = 'Install Python Modules'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return not addon_setup.installer.is_running

    def execute(self, context):
        _LINES.clear()
        region = context.region
        addon_setup.installer.install_python_modules(
            line_callback=lambda line: _lines_append(line) or region.tag_redraw(),
            finally_callback=lambda e: region.tag_redraw(),
        )
        return {'FINISHED'}


class UninstallPythonModules(bpy.types.Operator):
    """Uninstall Python Module marimo dependencies"""
    bl_idname = 'marimo.uninstall_python_modules'
    bl_label = 'Uninstall Python Modules'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return not addon_setup.installer.is_running

    def execute(self, context):
        _LINES.clear()
        region = context.region
        addon_setup.installer.uninstall_python_modules(
            line_callback=lambda line: _lines_append(line) or region.tag_redraw(),
            finally_callback=lambda e: region.tag_redraw(),
        )
        return {'FINISHED'}


class ListPythonModules(bpy.types.Operator):
    """List Python Modules"""
    bl_idname = 'marimo.list_python_modules'
    bl_label = 'List Python Modules'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return not addon_setup.installer.is_running

    def execute(self, context):
        _LINES.clear()
        region = context.region
        addon_setup.installer.list_python_modules(
            line_callback=lambda line: _lines_append(line) or region.tag_redraw(),
            finally_callback=lambda e: region.tag_redraw(),
        )
        return {'FINISHED'}


class StartMarimoServer(bpy.types.Operator):
    """Start Marimo Server if not exist then open Browser"""
    bl_idname = 'marimo.start_server_or_open_browser'
    bl_label = 'Start Notebook Server'
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return not addon_setup.installer.is_running

    def execute(self, context):
        if not addon_setup.server.is_running:
            from .addon_utils import show_message_box
            show_message_box("Marimo Server is starting ...", "Marimo Server", "INFO")
            _LINES.clear()
            region = context.region
            port = bpy.context.preferences.addons[__package__].preferences.port
            addon_setup.server.start(
                port,
                line_callback=lambda line: _lines_append(line) or region.tag_redraw(),
                finally_callback=lambda e: region.tag_redraw()
            )
        else:
            import webbrowser
            webbrowser.open(f"http://localhost:{addon_setup.server.port}")
        return {'FINISHED'}


class StopMarimoServer(bpy.types.Operator):
    """Stop Marimo Server if exist"""
    bl_idname = 'marimo.stop_server'
    bl_label = 'Stop Notebook Server'
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return addon_setup.server.is_running

    def execute(self, context):
        addon_setup.server.stop()
        return {'FINISHED'}


class MarimoAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    port: bpy.props.IntProperty(
        name="Port of Marimo Server",
        default=2718,
    )
    show_logs: bpy.props.BoolProperty(default=False)

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        row = layout.row()
        row.prop(self, 'port')
        row.operator(StartMarimoServer.bl_idname, icon='URL')
        # row.operator(StopMarimoServer.bl_idname, icon='X')

        col = layout.column(align=True)
        flow = col.grid_flow(align=True)
        flow.row().label(text="Required Python Modules:")
        for name, is_installed in addon_setup.installer.get_required_modules().items():
            flow.row().label(text=name, icon='CHECKMARK' if is_installed else 'ERROR')
        flow = col.grid_flow(align=True)
        row = flow.row(align=True)
        row.operator(InstallPythonModules.bl_idname)
        flow.row().operator(UninstallPythonModules.bl_idname)
        flow.row().operator(ListPythonModules.bl_idname)

        col = layout.column(align=False)
        row = col.row(align=True)
        row.prop(
            self, 'show_logs',
            icon='TRIA_DOWN' if self.show_logs else 'TRIA_RIGHT',
            icon_only=True,
            emboss=False,
        )
        row.label(text='Logs')
        exit_code = addon_setup.installer.exit_code
        if addon_setup.installer.is_running:
            row.label(text="Processing ...", icon='SORTTIME')
        elif exit_code >= 0:
            row.label(text=f"Done with code: {exit_code}", icon='CHECKMARK' if exit_code == 0 else 'ERROR')

        if self.show_logs:
            box = col.box().column(align=True)
            for line in _LINES:
                box.label(text=line)
