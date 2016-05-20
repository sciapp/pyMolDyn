# -*- coding: utf-8 -*-

from __future__ import absolute_import


from PyQt4 import QtCore, QtGui


class LabeledComboBox(QtGui.QComboBox):

    class Delegate(QtGui.QItemDelegate):
        def __init__(self, parent):
            super(LabeledComboBox.Delegate, self).__init__(parent)

        def paint(self, painter, option, index):
            role = index.data(QtCore.Qt.AccessibleDescriptionRole)
            if role == "parent":
                option.state |= QtGui.QStyle.State_Enabled
            else:
                indent = option.fontMetrics.width(2*' ')
                option.rect.adjust(indent, 0, 0, 0)
                option.textElideMode = QtCore.Qt.ElideNone
            super(LabeledComboBox.Delegate, self).paint(painter, option, index)

    def __init__(self, label, parent=None):
        super(LabeledComboBox, self).__init__(parent)
        self._label = label
        LabeledComboBox._init_ui(self)  # Emulate static binding

    def _init_ui(self):
        self.setItemDelegate(LabeledComboBox.Delegate(self))
        label_item = QtGui.QStandardItem(self._label)
        label_item.setFlags(label_item.flags() & ~(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable))
        label_item.setData("parent", QtCore.Qt.AccessibleDescriptionRole)
        label_item_font = label_item.font()
        label_item_font.setBold(True)
        label_item.setFont(label_item_font)
        self.model().appendRow(label_item)
