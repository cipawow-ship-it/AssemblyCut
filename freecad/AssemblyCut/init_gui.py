# -*- coding: utf-8 -*-
import os
import sys

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_addon_root = os.path.dirname(os.path.dirname(_pkg_dir))

if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import FreeCADGui as Gui
from PySide import QtCore, QtGui


class AssemblyCutWorkbench(Gui.Workbench):
    MenuText = "Assembly Cut"
    ToolTip = "Cut multiple bodies with a single sketch"
    Icon = os.path.join(_addon_root, "Resources", "Icons", "AssemblyCut.svg")

    def Initialize(self):
        import Commands
        cmds = ["AssemblyCut_Cut"]
        self.appendToolbar("Assembly Cut", cmds)
        self.appendMenu("Assembly Cut", cmds)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(AssemblyCutWorkbench())


def _inject_into_partdesign():
    try:
        import Commands

        mw = Gui.getMainWindow()
        if mw is None:
            return False

        toolbar = mw.addToolBar("Assembly Cut")
        toolbar.setObjectName("AssemblyCutToolBar")
        toolbar.setAllowedAreas(
            QtCore.Qt.TopToolBarArea | QtCore.Qt.BottomToolBarArea
        )

        icon_path = os.path.join(_addon_root, "Resources", "Icons", "AssemblyCut.svg")
        action = QtGui.QAction(mw)
        action.setText("Assembly Cut")
        action.setToolTip("Cut multiple bodies with a selected sketch")
        if os.path.exists(icon_path):
            action.setIcon(QtGui.QIcon(icon_path))

        def _triggered():
            Gui.runCommand("AssemblyCut_Cut")

        action.triggered.connect(_triggered)
        toolbar.addAction(action)

        return True
    except Exception:
        return False


_timer = QtCore.QTimer()
_timer.singleShot(3000, _inject_into_partdesign)
