import sys
import subprocess
import os
import textwrap
from pathlib import Path


python_path = Path(sys.executable)
cwd_for_subprocesses = python_path.parent


def handle_fatal_error(message: str):
    print()
    print("#" * 80)
    for line in message.splitlines():
        print(">  ", line)
    print("#" * 80)
    print()
    sys.exit(1)


def ensure_packages_are_installed(package_names):
    if packages_are_installed(package_names):
        return

    cmd = [str(python_path), "-m", "pip", "install", "--upgrade", "pip"]
    print(' '.join(cmd[2:]))
    subprocess.run(cmd, cwd=cwd_for_subprocesses)
    install_packages(package_names)


def packages_are_installed(package_names: list[str]):
    return all(module_can_be_imported(name) for name in package_names if name.isidentifier())


def install_packages(package_names):
    if not module_can_be_imported("pip"):
        print("pip is not installed. Please install it manually.")
        return

    for name in package_names:
        ensure_package_is_installed(name)

    assert packages_are_installed(package_names)


def ensure_package_is_installed(name):
    if not module_can_be_imported(name):
        install_package(name)


def install_package(name: str):
    target = get_package_install_directory()
    cmd = [str(python_path), "-m", "pip", "install", name, '--target', target]
    print(' '.join(cmd[2:-2]))
    subprocess.run(cmd, cwd=cwd_for_subprocesses)

    if name.isidentifier() and not module_can_be_imported(name):
        handle_fatal_error(f"could not install {name}")


def uninstall_package(name: str):
    cmd = [str(python_path), "-m", "pip", "uninstall", name, '-y']
    print(' '.join(cmd[2:-1]))
    subprocess.run(cmd, cwd=cwd_for_subprocesses)


def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path

    handle_fatal_error("Don't know where to install packages. Please make a bug report.")


def module_can_be_imported(name):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


def handle_cannot_install_packages(package_names):
    handle_fatal_error(textwrap.dedent(f'''\
        Installing packages in Python distributions, that
        don't come with Blender, is not allowed currently.
        Please enable 'blender.allowModifyExternalPython'
        in VS Code or install those packages yourself:

        {str(package_names):53}\
    '''))
