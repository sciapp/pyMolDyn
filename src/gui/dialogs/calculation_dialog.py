# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui

class CalculationDialog(QtGui.QDialog):

    def __init__(self, parent=None, filenames=[]):
        QtGui.QDialog.__init__(self, parent)

        vbox            = QtGui.QVBoxLayout() 
        button_hbox     = QtGui.QHBoxLayout() 
        self.file_list  = QtGui.QListWidget(self)

        for fn in filenames:
            self.file_list.addItem(fn)

        vbox.addWidget(self.file_list)
        if len(filenames) == 1:
            self.frame_chooser = LabeledFrameChooser(None, 10, 50, [i for i in range(1,40,2)], 'Frame')
            vbox.addWidget(self.frame_chooser)

        ok_button = QtGui.QPushButton('Ok', self)
        ok_button.clicked.connect(self.ok)
        button_hbox.addWidget(ok_button)

        cancel_button = QtGui.QPushButton('Cancel', self)
        cancel_button.clicked.connect(self.cancel)
        button_hbox.addWidget(cancel_button)

        vbox.addLayout(button_hbox)
        self.setLayout(vbox)
        self.setWindowTitle("Calculation Settings")

    def ok(self):
        self.done(QtGui.QDialog.Accepted)
    
    def cancel(self):
        self.done(QtGui.QDialog.Rejected)

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
