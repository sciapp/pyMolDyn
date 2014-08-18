from PySide import QtCore, QtGui, QtOpenGL
import visualization
import gl_widget
import main_window

t = None

class UpdateGLEvent(QtCore.QEvent):

    def __init__(self):
        global t
        t = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())
        QtCore.QEvent.__init__(self, t)

class MyApplication(QtGui.QApplication):
    def __init__(self, args):
        QtGui.QApplication.__init__(self, args)
        self.installEventFilter(self)

    def eventFilter(self, receiver, event):
        print(receiver, event.type(), t)
        global t
        if(event.type() == QtCore.QEvent.MouseMove and isinstance(receiver, gl_widget.GLWidget)):
            if receiver.dataset_loaded:
                if event.buttons() & QtCore.Qt.LeftButton:
                    dx = event.x() - receiver.x
                    dy = event.y() - receiver.y
                    receiver.vis.rotate_mouse(dx, dy)
                    receiver.x = event.x()
                    receiver.y = event.y()
                    receiver.updateGL()
            return True
                    
        if(event.type() == QtCore.QEvent.Wheel and isinstance(receiver, gl_widget.GLWidget)):
            if receiver.dataset_loaded:
                receiver.update_needed = True
                if event.modifiers() != QtCore.Qt.ShiftModifier:
                    if event.orientation() == QtCore.Qt.Orientation.Vertical:
                        receiver.vis.zoom(event.delta())
                else:
                    rot_v = 0.1
                    if event.orientation() == QtCore.Qt.Orientation.Horizontal:
                        receiver.vis.rotate_mouse(event.delta()*rot_v, 0)
                    else:
                        receiver.vis.rotate_mouse(0, event.delta()*rot_v )

                QtGui.QApplication.postEvent(receiver, UpdateGLEvent())
                return True
                
        if(event.type() == QtCore.QEvent.MouseButtonPress and isinstance(receiver, gl_widget.GLWidget)):
            if receiver.dataset_loaded:
                if event.buttons() and QtCore.Qt.LeftButton:
                    receiver.x = event.x()
                    receiver.y = event.y()
                    return True
                    
        if(event.type() == t and isinstance(receiver, gl_widget.GLWidget)):
            print("abgefangen")
            if receiver.update_needed:
                receiver.updateGL()
                receiver.update_needed = False
                return True
            
        if(event.type() == QtCore.QEvent.KeyPress and isinstance(receiver, gl_widget.GLWidget)):
            if receiver.dataset_loaded:
                receiver.vis.process_key(event)
            
                if event.key() == QtCore.Qt.Key_Right:
                    receiver.vis.process_key('right')
                elif event.key() == QtCore.Qt.Key_Left:
                    receiver.vis.process_key('left')
                elif event.key() == QtCore.Qt.Key_Up:
                    receiver.vis.process_key('up')
                elif event.key() == QtCore.Qt.Key_Down:
                    receiver.vis.process_key('down')
                elif event.key() == QtCore.Qt.Key_D:
                    receiver.vis.process_key('d')
                elif event.key() == QtCore.Qt.Key_C:
                    receiver.vis.process_key('c')
                elif event.key() == QtCore.Qt.Key_F:
                    receiver.vis.process_key('f')
                else:
                    event.ignore()
                receiver.updateGL()
                return True
            
        if(event.type() == QtCore.QEvent.KeyPress and isinstance(receiver, main_window.MainWindow)):
            if event.key() == QtCore.Qt.Key_M:
                if not self.isFullScreen():
                    for dock in self.docks:
                        dock.hide()
                    self.showFullScreen()
                else:
                    for dock in self.docks:
                        dock.show()
                    self.showNormal()
                return True
      
        return super(MyApplication, self).eventFilter(receiver, event)