# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from PyQt4 import QtCore, QtGui
from twin_view_widget import TwinViewWidget


class MainWindow(QtGui.QMainWindow):
    def __init__(self, non_translated_data, translated_data, merge_groups, mask, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self._init_ui(non_translated_data, translated_data, merge_groups, mask)

    def _init_ui(self, non_translated_data, translated_data, merge_groups, mask):
        self._grid_vis = TwinViewWidget(self, non_translated_data, translated_data, merge_groups, mask)
        self.setCentralWidget(self._grid_vis)
        self._status_bar = StatusBar(self)
        self.setStatusBar(self._status_bar)

    @property
    def index(self):
        return self._status_bar.index

    @index.setter
    def index(self, value):
        self._status_bar.index = value

    @property
    def show_box(self):
        return self._status_bar.show_box

    @show_box.setter
    def show_box(self, value):
        self._status_bar.show_box = value

    @property
    def show_all_areas(self):
        return self._status_bar.show_all_areas

    @show_all_areas.setter
    def show_all_areas(self, value):
        self._status_bar.show_all_areas = value

    @property
    def show_subparts(self):
        return self._status_bar.show_subparts

    @show_subparts.setter
    def show_subparts(self, value):
        self._status_bar.show_subparts = value

    @property
    def show_link(self):
        return self._status_bar.show_link

    @show_link.setter
    def show_link(self, value):
        self._status_bar.show_link = value

    @property
    def show_translation(self):
        return self._status_bar.show_translation

    @show_translation.setter
    def show_translation(self, value):
        self._status_bar.show_translation = value

    @property
    def show_merging_history(self):
        return self._status_bar.show_merging_history

    @show_merging_history.setter
    def show_merging_history(self, value):
        self._status_bar.show_merging_history = value

    @property
    def show_merging_result(self):
        return self._status_bar.show_merging_result

    @show_merging_result.setter
    def show_merging_result(self, value):
        self._status_bar.show_merging_result = value

    @property
    def show_merging_translation(self):
        return self._status_bar.show_merging_translation

    @show_merging_translation.setter
    def show_merging_translation(self, value):
        self._status_bar.show_merging_translation = value


class StatusBar(QtGui.QStatusBar):
    def __init__(self, *args, **kwargs):
        super(StatusBar, self).__init__(*args, **kwargs)
        self._index = 0
        self._show_box = False
        self._show_all_areas = True
        self._show_subparts = False
        self._show_link = False
        self._show_translation = False
        self._show_merging_history = False
        self._show_merging_result = False
        self._show_merging_translation = False
        self._init_ui()

    def _init_ui(self):
        self._index_label = QtGui.QLabel(self)
        self._show_box_label = QtGui.QLabel(self)
        self._show_all_areas_label = QtGui.QLabel(self)
        self._show_subparts_label = QtGui.QLabel(self)
        self._show_link_label = QtGui.QLabel(self)
        self._show_translation_label = QtGui.QLabel(self)
        self._show_merging_history_label = QtGui.QLabel(self)
        self._show_merging_result_label = QtGui.QLabel(self)
        self._show_merging_translation_label = QtGui.QLabel(self)
        for label in (self._index_label, self._show_box_label, self._show_all_areas_label, self._show_subparts_label,
                      self._show_link_label, self._show_translation_label, self._show_merging_history_label,
                      self._show_merging_result_label, self._show_merging_translation_label):
            label.setFont(QtGui.QFont('Menlo'))
            self.addPermanentWidget(label)
        # call property setters to set labels correctly
        self.index = self._index
        self.show_box = self._show_box
        self.show_all_areas = self._show_all_areas
        self.show_subparts = self._show_subparts
        self.show_link = self._show_link
        self.show_translation = self._show_translation
        self.show_merging_history = self._show_merging_history
        self.show_merging_result = self._show_merging_result
        self.show_merging_translation = self._show_merging_translation

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value
        self._index_label.setText('group index: {:2d}'.format(self._index))

    @property
    def show_box(self):
        return self._show_box

    @show_box.setter
    def show_box(self, value):
        self._show_box = value
        self._show_box_label.setText('show box: {}'.format(self._show_box))

    @property
    def show_all_areas(self):
        return self._show_all_areas

    @show_all_areas.setter
    def show_all_areas(self, value):
        self._show_all_areas = value
        self._show_all_areas_label.setText('show all areas: {}'.format(self._show_all_areas))

    @property
    def show_subparts(self):
        return self._show_subparts

    @show_subparts.setter
    def show_subparts(self, value):
        self._show_subparts = value
        self._show_subparts_label.setText('show subparts: {}'.format(self._show_subparts))

    @property
    def show_link(self):
        return self._show_link

    @show_link.setter
    def show_link(self, value):
        self._show_link = value
        self._show_link_label.setText('show link: {}'.format(self._show_link))

    @property
    def show_translation(self):
        return self._show_translation

    @show_translation.setter
    def show_translation(self, value):
        self._show_translation = value
        self._show_translation_label.setText('show translation: {}'.format(self._show_translation))

    @property
    def show_merging_history(self):
        return self._show_merging_history

    @show_merging_history.setter
    def show_merging_history(self, value):
        self._show_merging_history = value
        self._show_merging_history_label.setText('show merging history: {}'.format(self._show_merging_history))

    @property
    def show_merging_result(self):
        return self._show_merging_result

    @show_merging_result.setter
    def show_merging_result(self, value):
        self._show_merging_result = value
        self._show_merging_result_label.setText('show merging result: {}'.format(self._show_merging_result))

    @property
    def show_merging_translation(self):
        return self._show_merging_translation

    @show_merging_translation.setter
    def show_merging_translation(self, value):
        self._show_merging_translation = value
        self._show_merging_translation_label.setText('show merging translation: {}'.format(
            self._show_merging_translation)
        )
