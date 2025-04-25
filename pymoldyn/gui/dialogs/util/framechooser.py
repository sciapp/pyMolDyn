from PySide6 import QtCore, QtGui, QtWidgets


class LabeledFrameChooser(QtWidgets.QWidget):
    value_changed = QtCore.Signal()

    def __init__(self, parent, num_frames, calculated, text):
        QtWidgets.QWidget.__init__(self, parent)

        self.framebar = FrameBar(self, num_frames, calculated)
        self.text = text
        self.num_frames = num_frames

        self.init_gui()

    def init_gui(self):

        hbox = QtWidgets.QHBoxLayout()
        vbox = QtWidgets.QVBoxLayout()

        self.lineedit = QtWidgets.QLineEdit(self)

        #        self.lineedit.setMinimumSize(30, 1)
        #        self.lineedit.setMaximumSize(40, 40)

        self.update_lineedit()
        self.lineedit.setAlignment(QtCore.Qt.AlignRight)
        self.lineedit.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        hbox.addWidget(QtWidgets.QLabel(self.text + ":", self), 0)
        hbox.addWidget(self.lineedit, 1)
        # hbox.addWidget(QtWidgets.QLabel('/'+str(self.maxf), self))
        # hbox.addStretch()

        vbox.addLayout(hbox)
        vbox.addWidget(self.framebar)

        self.lineedit.returnPressed.connect(self.lineedit_return_pressed)

        self.setLayout(vbox)
        self.show()

    def emit_value_changed(self):
        self.value_changed.emit()

    #    def load_dataset(self, filename):
    #        self.framebar.load_dataset(filename)

    def set_calculated_frames(self, calculated):
        self.framebar.set_calculated(calculated)

    def lineedit_return_pressed(self):
        try:
            l_1 = [int(i.strip()) for i in str(self.lineedit.text()).split(",")]
            # translate indices from human to machine
            l = [i - 1 for i in l_1]  # noqa: E741
        except ValueError:
            print("Enter a valid number")
        self.framebar.set_selection(l)

    def mousePressEvent(self, e):
        self.update_lineedit()

    def mouseMoveEvent(self, e):
        self.update_lineedit()

    def update_lineedit(self):
        sel = self.framebar.get_selection()
        # translate indices from machine to human
        sel_1 = [i + 1 for i in sel]
        s_1 = ", ".join([str(i) for i in sel_1])
        self.lineedit.setText(s_1)

    def value(self):
        return self.framebar.get_selection()


class FrameBar(QtWidgets.QWidget):

    def __init__(self, parent, num_frames, calculated):
        QtWidgets.QWidget.__init__(self, parent)

        self.parent = parent
        self.num_frames = num_frames
        self.calculated = calculated
        self.width = 300
        self.height = 10
        self.selection = [0]
        self.last_clicked = 0

        self.setMinimumSize(self.width + 5, self.height + 5)

    def draw(self):
        red = QtGui.QColor(255, 180, 180)
        green = QtGui.QColor(180, 255, 180)
        blue = QtGui.QColor(180, 180, 255)
        self.h = float(self.width) / (self.num_frames)

        p = self.painter

        p.setPen(QtCore.Qt.NoPen)

        p.setBrush(red)
        p.drawRect(0, 0, self.width, self.height)
        p.setBrush(green)
        for frame in self.calculated:
            i = frame
            p.drawRect(i * self.h, 1, self.h, self.height - 1)
        p.setBrush(blue)
        for sel in self.selection:
            i = sel
            p.drawRect(i * self.h, 1, self.h, self.height - 1)
        p.setPen(QtCore.Qt.SolidLine)
        p.setBrush(QtCore.Qt.NoBrush)
        for i in range(self.num_frames):
            p.drawLine((i + 1) * self.h, 0, (i + 1) * self.h, self.height)
        p.drawRect(0, 0, self.width, self.height)

    def mousePressEvent(self, e):
        self.process_mouse_press(e)
        e.ignore()

    def set_calculated(self, calculated):
        self.calculated = calculated
        self.repaint()

    def process_mouse_press(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            clicked = int(e.x() / self.h)
            if 0 < e.x() < self.width and 0 < e.y() < self.height:
                self.process_mouse_event(clicked, e)
        e.ignore()

    def process_mouse_event(self, clicked, e):
        if e.modifiers() == QtCore.Qt.ShiftModifier:
            if self.last_clicked:
                for i in range(min(self.last_clicked, clicked), max(self.last_clicked, clicked) + 1):
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
        self.parent.emit_value_changed()

    def mouseMoveEvent(self, e):
        if e.buttons() and QtCore.Qt.LeftButton:
            clicked = int(e.x() / self.h)
            if 0 < e.x() < self.width:
                self.process_mouse_event(clicked, e)
        e.ignore()

    def get_selection(self):
        return self.selection

    def set_selection(self, l):  # noqa: E741
        for value in l:
            if not 0 <= value < self.num_frames:
                l.remove(value)
            self.selection = l
            self.repaint()

    def paintEvent(self, e):
        self.painter = QtGui.QPainter()
        self.painter.begin(self)
        self.draw()
        self.painter.end()


#    def load_dataset(self, filename):
#        n_frames = calculation.count_frames(filename)
#        self.minf = 1
#        self.maxf = n_frames
#        self.calculated = [0]
#        self.selection = [0]
#        self.repaint()
