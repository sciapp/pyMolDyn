# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui
import sys
import os.path
import calculation

class FileTabDock(QtGui.QDockWidget):
    '''
        DockWidget to the 'file'-tab
    '''
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self,"file", parent)
        self.setWidget(QtGui.QWidget())

        self.layout     = QtGui.QHBoxLayout()
        self.file_tab   = FileTab(self.widget())

        self.layout.addWidget(self.file_tab)
        self.widget().setLayout(self.layout)

        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

class FileTab(QtGui.QWidget):
    '''
        tab 'file' in the main widget
    '''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.init_gui()

    def init_gui(self):
        self.vbox = QtGui.QVBoxLayout()
        self.button_hbox = QtGui.QHBoxLayout()

        self.file_button = QtGui.QPushButton('Open', self)
        self.file_button.clicked.connect(self.open_file_dialog)
        self.button_hbox.addWidget(self.file_button)

        self.delete_button = QtGui.QPushButton('Delete', self)
        self.delete_button.clicked.connect(self.remove_selected_files)
        self.button_hbox.addWidget(self.delete_button)

        self.calculate_button = QtGui.QPushButton('Calculate', self)
        self.calculate_button.clicked.connect(self.calculate)
        self.button_hbox.addWidget(self.calculate_button)
        
        self.vbox.addLayout(self.button_hbox)

        self.file_list = DragList(self)
        self.file_list.itemDoubleClicked.connect(self.calculate)
        self.file_list.itemSelectionChanged.connect(self.selection_changed)
        self.vbox.addWidget(self.file_list)

        self.frame_chooser = LabeledFrameChooser(None, 10, 50, [i for i in range(1,40,2)], 'Frame')
        self.vbox.addWidget(self.frame_chooser)

        self.setLayout(self.vbox)

    def selection_changed(self):
        sel = self.file_list.get_selection()
        if not sel or len(self.file_list.get_selection()) > 1:
            return
        filename = sel[0]
        print 'change '+filename

    def remove_selected_files(self):
        self.file_list.remove_selected_files()

    def open_file_dialog(self):
        filenames, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open dataset', '~')

        for fn in filenames:
            if fn:
                self.file_list.add_file(fn)

    def calculate(self):
        if len(self.file_list.get_selection()) > 1:
            print 'more than one dataset selected'
            return
        filename = self.file_list.get_selection()[0]
        if calculation.calculated(filename):
            print 'berechnet'
        #show dialog

        #self.frame_chooser.load_dataset(filename)


class DragList(QtGui.QListWidget):
    
    def __init__(self, parent):
        super(DragList, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)


        self.datalist = {}

    def dragMoveEvent(self, event):
        pass

    def add_file(self, path):
        bname = os.path.basename(path)
        if bname not in self.datalist and path.endswith('.xyz'):
            self.datalist[bname] = path
            self.addItem(bname)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            if e.mimeData().urls()[0].scheme() == 'file':
                e.accept()
            else:
                e.ignore()
        else:
            e.ignore()
            
    def dropEvent(self, e):
        for f in e.mimeData().urls():
            if os.path.isfile(f.path()):
                self.add_file(f.path())

    def remove_selected_files(self):
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)
            del self.datalist[item.text()]

    def get_selection(self):
        return [self.datalist[str(item.text())] for item in self.selectedItems()]

class FrameBar(QtGui.QWidget):

    def __init__(self, parent, minf, maxf, calculated):
        QtGui.QWidget.__init__(self, parent)
        
        self.minf           = minf
        self.maxf           = maxf
        self.calculated     = calculated
        self.width          = 300
        self.height         = 10 
        self.selection      = [self.minf]
        self.last_clicked   = self.minf 

        self.setMinimumSize(self.width+5, self.height+5)

    def draw(self):
        red     = QtGui.QColor(255,180,180)
        green   = QtGui.QColor(180,255,180)
        blue    = QtGui.QColor(180,180,255)
        self.h  = float(self.width)/(self.maxf+1-self.minf)

        p = self.painter
        
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(red)
        p.drawRect(0, 0, self.width, self.height)
        p.setBrush(green)
        for i in self.calculated:
            p.drawRect(i*self.h, 1, self.h, self.height-1)
        p.setBrush(blue)
        for sel in self.selection:
            p.drawRect((sel-self.minf)*self.h, 1, self.h, self.height-1)
        p.setPen(QtCore.Qt.SolidLine)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRect(0, 0, self.width, self.height)

    def mousePressEvent(self, e):
        self.process_mouse_press(e)
        e.ignore()

    def process_mouse_press(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            clicked = self.minf + int(e.x()/self.h)
            if 0 < e.x() < self.width and 0 < e.y() < self.height:
                if e.modifiers() == QtCore.Qt.ShiftModifier:
                    if self.last_clicked:
                        for i in range(min(self.last_clicked, clicked), max(self.last_clicked, clicked)+1):
                            if i not in self.selection:
                                self.selection.append(i)
                        self.selection.sort()
                elif e.modifiers() == QtCore.Qt.CTRL:
                    if clicked not in self.selection:
                        self.selection.append(clicked)
                        self.selection.sort()
                else:
                    self.selection = [clicked]
            self.last_clicked = clicked
            self.repaint()

#e.modifiers() != QtCore.Qt.ShiftModifier
    def mouseMoveEvent(self, e):
        self.process_mouse_press(e)
        e.ignore()

    def get_selection(self):
        return self.selection

    def set_selection(self, value):
        if self.minf <= value <= self.maxf:
            self.selection = [value]
        self.repaint()

    def paintEvent(self, e):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self.draw()
        self.painter.end()

    def load_dataset(self, filename):
        n_frames = calculation.count_frames(filename)
        self.minf = 1
        self.maxf = n_frames
        self.calculated = [0]
        self.selection = [0]
        self.repaint()

class LabeledFrameChooser(QtGui.QWidget):
    
    def __init__(self, parent, minf, maxf, calculated, text):
        QtGui.QWidget.__init__(self, parent)
        
        self.framebar   = FrameBar(self, minf, maxf, calculated)
        self.text       = text
        self.maxf       = maxf

        self.init_gui()

    def init_gui(self):
        
        hbox = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()
    
        self.lineedit   = QtGui.QLineEdit(self)

        self.lineedit.setMinimumSize(30, 1)
        self.lineedit.setMaximumSize(40, 40)
        
        self.lineedit.setText(str(self.framebar.get_selection()))
        self.lineedit.setAlignment(QtCore.Qt.AlignRight)
        self.lineedit.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)        

        hbox.addWidget(QtGui.QLabel(self.text+':', self))
        hbox.addWidget(self.lineedit)
        hbox.addWidget(QtGui.QLabel('/'+str(self.maxf), self))
        hbox.addStretch()

        vbox.addLayout(hbox)
        vbox.addWidget(self.framebar)

        self.lineedit.returnPressed.connect(self.lineedit_return_pressed)
        
        self.setLayout(vbox)
        self.show()

    def load_dataset(self, filename):
        self.framebar.load_dataset(filename)

    def lineedit_return_pressed(self):
        try:
            value = int(self.lineedit.text())
        except ValueError:
            print 'Enter a valid number'
            sys.exit()
        self.framebar.set_selection(value)

    def mousePressEvent(self, e):
        self.lineedit.setText(str(self.framebar.get_selection()))

    def mouseMoveEvent(self, e):
        self.lineedit.setText(str(self.framebar.get_selection()))

if __name__ == '__main__':
    app     = QtGui.QApplication(sys.argv)
    fc      = LabeledFrameChooser(None, 10, 50, [i for i in range(1,40,2)], 'Frame')
    sys.exit(app.exec_())

