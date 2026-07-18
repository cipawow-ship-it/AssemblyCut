# -*- coding: utf-8 -*-
import os
import sys

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import FreeCAD
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui


class _BodyRowWidget(QtGui.QWidget):
    def __init__(self, name, checked, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.body_name = name

        layout = QtGui.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.checkbox = QtGui.QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.setMinimumWidth(20)
        self.checkbox.toggled.connect(lambda val: dialog._set_checked(name, val))
        layout.addWidget(self.checkbox)

        self.label = QtGui.QLabel(name)
        layout.addWidget(self.label, 1)

        up_btn = QtGui.QPushButton("\u25B2")
        up_btn.setFixedSize(24, 24)
        up_btn.clicked.connect(lambda: dialog._move_body(name, -1))
        layout.addWidget(up_btn)

        down_btn = QtGui.QPushButton("\u25BC")
        down_btn.setFixedSize(24, 24)
        down_btn.clicked.connect(lambda: dialog._move_body(name, +1))
        layout.addWidget(down_btn)


class AssemblyCutDialog(QtGui.QDialog):
    def __init__(self, sketch_name, body_names, preselected_names=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assembly Cut")
        self.setMinimumWidth(420)
        self.setMinimumHeight(400)

        self.preselected_names = preselected_names or set()

        layout = QtGui.QVBoxLayout(self)

        layout.addWidget(QtGui.QLabel("Sketch: " + sketch_name))
        layout.addWidget(QtGui.QLabel(""))
        layout.addWidget(QtGui.QLabel("Select bodies to cut (reorder with arrows):"))

        if preselected_names:
            pre = [n for n in body_names if n in preselected_names]
            others = [n for n in body_names if n not in preselected_names]
            self._order = pre + others
        else:
            self._order = list(body_names)

        self._checked = {n: (n in self.preselected_names) for n in self._order}

        self.list_widget = QtGui.QListWidget()
        layout.addWidget(self.list_widget)
        self._rebuild_list()

        btn_layout = QtGui.QHBoxLayout()
        select_all_btn = QtGui.QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn = QtGui.QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)

        info = QtGui.QLabel(
            "Each body will open its own Pocket dialog.\n"
            "Set depth, taper, direction for each one."
        )
        info.setStyleSheet("color: #555;")
        layout.addWidget(info)

        ok_btn = QtGui.QPushButton("Cut Bodies")
        cancel_btn = QtGui.QPushButton("Cancel")
        bottom = QtGui.QHBoxLayout()
        bottom.addWidget(ok_btn)
        bottom.addWidget(cancel_btn)
        layout.addLayout(bottom)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def _rebuild_list(self):
        self.list_widget.clear()
        for name in self._order:
            item = QtGui.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0, 32))
            item.setData(QtCore.Qt.UserRole, name)
            widget = _BodyRowWidget(name, self._checked.get(name, False), self)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _move_body(self, name, direction):
        idx = self._order.index(name)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._order):
            return
        self._order[idx], self._order[new_idx] = self._order[new_idx], self._order[idx]
        self._rebuild_list()

    def _set_checked(self, name, val):
        self._checked[name] = val

    def _select_all(self):
        for n in self._order:
            self._checked[n] = True
        self._rebuild_list()

    def _deselect_all(self):
        for n in self._order:
            self._checked[n] = False
        self._rebuild_list()

    def get_selected(self):
        return [n for n in self._order if self._checked.get(n, False)]


def _find_bodies(doc):
    bodies = []
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            bodies.append(obj)
    return bodies


def _get_selected_sketch():
    sel = Gui.Selection.getSelection()
    if not sel:
        return None
    obj = sel[0]
    if obj.TypeId == "Sketcher::SketchObject":
        return obj
    return None


def _find_intersecting_bodies(doc, sketch, bodies):
    try:
        wires = sketch.Shape.Wires
        if not wires:
            return [b.Label for b in bodies]

        largest = max(wires, key=lambda w: abs(w.Length))
        face = Part.Face(largest)
        z_axis = sketch.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))

        solid_pos = face.extrude(z_axis * 10000.0)
        solid_neg = face.extrude(z_axis * -10000.0)
        bb_pos = solid_pos.BoundBox
        bb_neg = solid_neg.BoundBox
    except Exception:
        return [b.Label for b in bodies]

    result = []
    for body in bodies:
        try:
            body_bb = body.Shape.BoundBox
            hit = False

            if bb_pos.intersect(body_bb):
                common = body.Shape.common(solid_pos)
                if common and common.Volume > 0:
                    hit = True

            if not hit and bb_neg.intersect(body_bb):
                common = body.Shape.common(solid_neg)
                if common and common.Volume > 0:
                    hit = True

            if hit:
                result.append(body.Label)
        except Exception:
            pass
    return result


def _copy_sketch_into_body(doc, src_sketch, target_body):
    new_sketch = target_body.newObject("Sketcher::SketchObject", src_sketch.Label + "_Copy")

    geo_list = []
    for geo in src_sketch.Geometry:
        copied = geo.copy()
        geo_list.append(copied)

    new_sketch.addGeometry(geo_list, False)
    new_sketch.Placement = src_sketch.Placement.copy()
    doc.recompute()
    return new_sketch


class _CutProcessor(QtCore.QObject):
    def __init__(self, sketch, bodies):
        super().__init__()
        self.sketch = sketch
        self.bodies = list(bodies)
        self.current_idx = 0
        self.copies = {}
        self.waiting_for_dialog = False
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._on_tick)

    def start(self):
        if not self.bodies:
            return
        doc = FreeCAD.ActiveDocument

        for body in self.bodies:
            try:
                new_sketch = _copy_sketch_into_body(doc, self.sketch, body)
                doc.recompute()
                self.copies[body.Name] = new_sketch
            except Exception as e:
                QtGui.QMessageBox.warning(
                    None, "Assembly Cut",
                    "Error copying sketch into " + body.Label + ":\n" + str(e)
                )
                return

        self.current_idx = 0
        self._process_next()

    def _process_next(self):
        if self.current_idx >= len(self.bodies):
            doc = FreeCAD.ActiveDocument
            if doc:
                doc.recompute()
            return

        body = self.bodies[self.current_idx]
        copy_sketch = self.copies.get(body.Name)

        if copy_sketch is None:
            self.current_idx += 1
            self._process_next()
            return

        try:
            body.ViewObject.doubleClicked()
        except Exception:
            pass

        doc = FreeCAD.ActiveDocument
        if doc:
            doc.recompute()

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(
            FreeCAD.ActiveDocument.Name,
            copy_sketch.Name
        )

        self.waiting_for_dialog = True
        Gui.runCommand("PartDesign_Pocket")
        self.timer.start()

    def _on_tick(self):
        if not self.waiting_for_dialog:
            return

        has_panel = False
        try:
            editing = Gui.ActiveDocument.getInEdit()
            has_panel = (editing is not None)
        except Exception:
            has_panel = False

        if not has_panel:
            self.timer.stop()
            self.waiting_for_dialog = False

            doc = FreeCAD.ActiveDocument
            if doc:
                doc.recompute()

            self.current_idx += 1
            QtCore.QTimer.singleShot(300, self._process_next)


_active_processor = None


def assembly_cut():
    global _active_processor

    doc = FreeCAD.ActiveDocument
    if doc is None:
        QtGui.QMessageBox.warning(None, "Assembly Cut", "No active document.")
        return

    sketch = _get_selected_sketch()
    if sketch is None:
        QtGui.QMessageBox.warning(
            None, "Assembly Cut",
            "Select a Sketch first, then run this command."
        )
        return

    bodies = _find_bodies(doc)
    if not bodies:
        QtGui.QMessageBox.information(
            None, "Assembly Cut", "No PartDesign::Body found in document."
        )
        return

    body_names = [b.Label for b in bodies]
    preselected = _find_intersecting_bodies(doc, sketch, bodies)
    dialog = AssemblyCutDialog(sketch.Label, body_names, preselected)
    if dialog.exec_() != QtGui.QDialog.Accepted:
        return

    selected_names = dialog.get_selected()
    if not selected_names:
        return

    name_to_body = {b.Label: b for b in bodies}
    selected_bodies = [name_to_body[n] for n in selected_names]

    _active_processor = _CutProcessor(sketch, selected_bodies)
    _active_processor.start()
