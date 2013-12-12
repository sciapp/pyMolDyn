from PySide import QtCore, QtGui
import sys
import os.path

class FileTab(QtGui.QWidget):

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
        self.vbox.addWidget(self.file_list)

        self.frame_chooser = LabeledFrameChooser(None, 10, 50, [i for i in range(1,40,2)])
        self.vbox.addWidget(self.frame_chooser)

        self.setLayout(self.vbox)

    def calculate(self):
        pass

    def remove_selected_files(self):
        self.file_list.remove_selected_files()

    def open_file_dialog(self):
        filenames, _ = QtGui.QFileDialog.getOpenFileNames(self, 'Open dataset', '~')

        for fn in filenames:
            if fn:
                self.file_list.add_file(fn)


class DragList(QtGui.QListWidget):
    
    def __init__(self, parent):
        super(DragList, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.itemDoubleClicked.connect(self.double_click)

        self.datalist = {}

    def dragMoveEvent(self, event):
        pass

    def add_file(self, path):
        bname = os.path.basename(path)
        if bname not in self.datalist:
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

    def double_click(self):
        item = self.selectedItems()[0]
        print 'filename: {} path: {}'.format(item.text(), self.datalist[item.text()])
        
class FrameChooser(QtGui.QWidget):
    
    def __init__(self, parent, minf, maxf, calculated):
        QtGui.QWidget.__init__(self, parent)

        self.minf       = minf
        self.maxf       = maxf
        self.calculated = calculated
        self.width      = 300
        self.height     = 35
        self.selection  = self.minf
        self.h = float(self.width)/(self.maxf+1-self.minf)
        self.setMinimumSize(305, 40)

    def paintEvent(self, e):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self.draw()
        self.painter.end()

    def draw(self):
        red     = QtGui.QColor(255,180,180)
        green   = QtGui.QColor(180,255,180)
        blue    = QtGui.QColor(180,180,255)

        p = self.painter
        
        p.setPen(QtGui.QColor(0, 0, 0))
        p.setBrush(red)
        p.drawRect(0, 0, self.width, self.height)
        p.setBrush(green)
        for i in self.calculated:
            p.drawRect(i*self.h, 0, self.h, self.height)
        p.setBrush(blue)
        p.drawRect((self.selection-self.minf)*self.h, 0, self.h, self.height)

    def mousePressEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            if 0 < e.x() < self.width and 0 < e.y() < self.height:
                self.selection = self.minf + int(e.x()/self.h)
                self.repaint()
        e.ignore()

    def mouseMoveEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            if 0 < e.x() < self.width and 0 < e.y() < self.height:
                self.selection = self.minf + int(e.x()/self.h)
                self.repaint()
        e.ignore()

    def get_selection(self):
        return self.selection

    def set_selection(self, value):
        if self.minf <= value <= self.maxf:
            self.selection = value
        self.repaint()

class LabeledFrameChooser(QtGui.QWidget):

    def __init__(self, parent, minf, maxf, calculated):
        QtGui.QWidget.__init__(self, parent)
        
        hbox = QtGui.QHBoxLayout()
        
        self.fc         = FrameChooser(self, minf, maxf, calculated)
        self.lineedit   = QtGui.QLineEdit(self)

        self.lineedit.setText(str(self.fc.get_selection()))
        hbox.addWidget(self.fc)
        hbox.addWidget(self.lineedit)

        self.lineedit.returnPressed.connect(self.lineedit_return_pressed)
        
        self.setLayout(hbox)
        self.show()

    def lineedit_return_pressed(self):
        try:
            value = int(self.lineedit.text())
        except ValueError:
            print 'Enter a valid number'
            sys.exit()
        self.fc.set_selection(value)

    def mousePressEvent(self, e):
        pass

    def mouseMoveEvent(self, e):
        self.lineedit.setText(str(self.fc.get_selection()))

if __name__ == '__main__':
    app     = QtGui.QApplication(sys.argv)
    fc      = LabeledFrameChooser(None, 10, 50, [i for i in range(1,40,2)])
    sys.exit(app.exec_())

