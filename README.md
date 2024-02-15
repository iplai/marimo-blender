# marimo-blender

[Marimo](https://github.com/marimo-team/marimo) is a reactive notebook for Python, and this repository integrates it as an addon into Blender.

[![LICENSE](https://img.shields.io/github/license/iplai/marimo-blender)](LICENSE)
[![Python 3.10 +](https://img.shields.io/badge/python-3.10_+-blue.svg)](https://www.python.org/downloads/release/python-310/)
[![Blender](https://img.shields.io/badge/Blender-_3.6_+_-blue)](http://www.blender.org)

## Installation

To install the addon, follow these steps:

1. Download the released zip file from the repository.
2. Open Blender and go to the Preferences addon tab.
3. Click on the "Install" button and select the downloaded zip file.
4. Enable the "Blender Notebook" addon.
5. For the first time, in the addon preferences, click the "Install Dependencies" button. Blender will install the necessary Python modules, which may take 1-2 minutes depending on your network speed. 

## Usage

Once the addon is successfully installed and enabled, you can use it by following these steps:

1. In the 3D viewport, you will find a button at the top left of the header.
2. Click on the button to launch the Marimo notebook server.
3. A webpage will be automatically opened, where you can start using the Marimo notebook. 

Please note that the button will only appear if the addon is installed and enabled correctly.

If you have any further questions or issues, feel free to ask!

**Note:** Feel free to write `import bpy` in the notebook cell.
