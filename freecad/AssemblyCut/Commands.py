# -*- coding: utf-8 -*-
import os
import sys

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import FreeCAD
import FreeCADGui as Gui

_addon_root = os.path.dirname(os.path.dirname(_pkg_dir))
_ICON = os.path.join(_addon_root, "Resources", "Icons", "AssemblyCut.svg")


class AssemblyCutCommand:
    def GetResources(self):
        return {
            "MenuText": "Assembly Cut",
            "ToolTip": "Cut multiple bodies with a selected sketch",
            "Pixmap": _ICON if os.path.exists(_ICON) else "",
        }

    def Activated(self):
        from AssemblyCutCore import assembly_cut
        assembly_cut()

    def IsActive(self):
        try:
            return FreeCAD.ActiveDocument is not None
        except Exception:
            return False


Gui.addCommand("AssemblyCut_Cut", AssemblyCutCommand())
