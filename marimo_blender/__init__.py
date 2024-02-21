bl_info = {
    "name": "Blender Notebook",
    "author": "iplai",
    "description": "Reactive notebook for Python integrated in blender",
    "blender": (2, 80, 0),
    "version": (0, 2, 7),
    "location": "View 3D > Header Menu > Notebook",
    "doc_url": "https://github.com/iplai/marimo-blender",
    "tracker_url": "https://github.com/iplai/marimo-blender/issues",
    "warning": "",
    "category": "Generic"
}

import bpy

from .preferences import (
    MarimoAddonPreferences,
    InstallPythonModules,
    InstallPythonModule,
    UninstallPythonModules,
    ListPythonModules,
    StartMarimoServer,
    StopMarimoServer
)


def marimo_header_btn(self: bpy.types.Menu, context):
    self.layout.operator(StartMarimoServer.bl_idname, icon='CURRENT_FILE', text="")


class MARIMO_PT_main_panel(bpy.types.Panel):
    bl_label = "Notebook"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Marimo'

    def draw(self, context):
        layout = self.layout
        pref = context.preferences.addons[__package__].preferences
        # layout.prop(pref, "server_port")
        layout.prop(pref, "filename", text="File Path")
        layout.operator(StartMarimoServer.bl_idname, icon='URL', text="Start Notebook Server")


classes = (
    MARIMO_PT_main_panel,
    MarimoAddonPreferences,
    InstallPythonModules,
    InstallPythonModule,
    UninstallPythonModules,
    ListPythonModules,
    StartMarimoServer,
    StopMarimoServer
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(marimo_header_btn)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_HT_header.remove(marimo_header_btn)
    from .addon_setup import server
    # server.stop()
