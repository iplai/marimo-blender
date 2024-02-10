bl_info = {
    "name": "Blender Notebook",
    "description": "Reactive notebook for Python integrated in blender",
    "author": "iplai",
    "blender": (2, 8, 0),
    "category": "Node",
    "version": (0, 0, 1),
    "location": "View 3D > Header Menu > Notebook",
    "warning": "",
    "doc_url": "https://github.com/iplai/marimo-blender",
    "tracker_url": "https://github.com/iplai/marimo-blender/issues",
    "category": "System"
}

import importlib, inspect, types, typing, pkgutil, pathlib

import bpy, bpy_extras


def _get_all_submodules(directory: pathlib.Path):
    return list(_iter_submodules(directory, directory.name))


def _iter_submodules(path, package_name):
    for name in sorted(_iter_submodule_names(path)):
        yield importlib.import_module("." + name, package_name)


def _iter_submodule_names(path, root=""):
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):
        if is_package:
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from _iter_submodule_names(sub_path, sub_root)
        else:
            yield root + module_name


def _get_ordered_classes_to_register(modules):
    return _toposort(_get_register_deps_dict(modules))


def _get_register_deps_dict(modules):
    my_classes = set(_iter_my_classes(modules))
    my_classes_by_idname = {cls.bl_idname: cls for cls in my_classes if hasattr(cls, "bl_idname")}

    deps_dict = {}
    for cls in my_classes:
        deps_dict[cls] = set(_iter_my_register_deps(cls, my_classes, my_classes_by_idname))
    return deps_dict


def _iter_my_register_deps(cls, my_classes, my_classes_by_idname):
    yield from _iter_my_deps_from_annotations(cls, my_classes)
    yield from _iter_my_deps_from_parent_id(cls, my_classes_by_idname)


def _iter_my_deps_from_annotations(cls, my_classes):
    if bpy_extras.object_utils.AddObjectHelper in cls.__bases__:
        return
    for value in typing.get_type_hints(cls, {}, {}).values():
        dependency = _get_dependency_from_annotation(value)
        if dependency is not None:
            if dependency in my_classes:
                yield dependency


def _get_dependency_from_annotation(value):
    if bpy.app.version >= (2, 93):
        if isinstance(value, bpy.props._PropertyDeferred):
            return value.keywords.get("type")
    else:
        if isinstance(value, tuple) and len(value) == 2:
            if value[0] in (bpy.props.PointerProperty, bpy.props.CollectionProperty):
                return value[1]["type"]
    return None


def _iter_my_deps_from_parent_id(cls, my_classes_by_idname: dict):
    if bpy.types.Panel in cls.__bases__:
        parent_idname = getattr(cls, "bl_parent_id", None)
        if parent_idname is not None:
            parent_cls = my_classes_by_idname.get(parent_idname)
            if parent_cls is not None:
                yield parent_cls


def _iter_my_classes(modules):
    base_type_names = 'Panel Operator PropertyGroup AddonPreferences Header Menu Node NodeSocket NodeTree UIList RenderEngine Gizmo GizmoGroup KeyingSetInfo'.split()
    base_types = [getattr(bpy.types, name) for name in base_type_names]
    for cls in _get_classes_in_modules(modules):
        if any(base in base_types for base in cls.__bases__):
            if not getattr(cls, "is_registered", False):
                yield cls


def _get_classes_in_modules(modules):
    classes = set()
    for module in modules:
        for cls in _iter_classes_in_module(module):
            classes.add(cls)
    return classes


def _iter_classes_in_module(module: types.ModuleType):
    for value in module.__dict__.values():
        if inspect.isclass(value):
            yield value


def _toposort(deps_dict: dict):
    """Find order to register to solve dependencies"""
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value: deps_dict[value] - sorted_values for value in unsorted}
    return sorted_list


_modules = _get_all_submodules(pathlib.Path(__file__).parent)
_ordered_classes = _get_ordered_classes_to_register(_modules)


def register():
    for cls in _ordered_classes:
        bpy.utils.register_class(cls)

    for module in _modules:
        if hasattr(module, "register"):
            module.register()


def unregister():
    for cls in reversed(_ordered_classes):
        bpy.utils.unregister_class(cls)

    for module in _modules:
        if hasattr(module, "unregister"):
            module.unregister()
