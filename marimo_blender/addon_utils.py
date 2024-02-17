import bpy


def show_message_box(message="", title="Message Box", icon='INFO'):
    """A hack that uses a popup menu as a message box"""

    def draw(self: bpy.types.UIPopupMenu, context):
        for line in message.split('\n'):
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
