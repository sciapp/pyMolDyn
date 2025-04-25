import gl_widget
import main_window
from PySide6 import QtCore, QtGui

ignore_list = [
    QtCore.QEvent.Type.HideToParent,
    QtCore.QEvent.Type.DynamicPropertyChange,
    QtCore.QEvent.Type.ChildRemoved,
    QtCore.QEvent.Type.Destroy,
    QtCore.QEvent.Type.WinIdChange,
    QtCore.QEvent.Type.ActionChanged,
    QtCore.QEvent.Type.Hide,
    QtCore.QEvent.Type.ShortcutOverride,
    QtCore.QEvent.Type.KeyPress,
    QtCore.QEvent.Type.Timer,
    QtCore.QEvent.Type.Close,
    QtCore.QEvent.Type.WindowDeactivate,
    QtCore.QEvent.Type.FocusIn,
    QtCore.QEvent.Type.Style,
    QtCore.QEvent.Type.ApplicationActivate,
    QtCore.QEvent.Type.Paint,
    QtCore.QEvent.Type.FocusOut,
    QtCore.QEvent.Type.DeferredDelete,
    QtCore.QEvent.Type.Resize,
    QtCore.QEvent.Type.Move,
    QtCore.QEvent.Type.LayoutRequest,
    QtCore.QEvent.Type.ChildAdded,
    QtCore.QEvent.Type.Show,
    QtCore.QEvent.Type.ShowToParent,
    QtCore.QEvent.Type.WindowActivate,
    QtCore.QEvent.Type.Polish,
    QtCore.QEvent.Type.ChildPolished,
    QtCore.QEvent.Type.PolishRequest,
    QtCore.QEvent.Type.MetaCall,
    QtCore.QEvent.Type.MacGLWindowChange,
    QtCore.QEvent.Type.ActivationChange,
    QtCore.QEvent.Type.WindowStateChange,
    QtCore.QEvent.Type.ParentChange,
    QtCore.QEvent.Type.Create,
    QtCore.QEvent.Type.MacGLClearDrawable,
    QtCore.QEvent.Type.FontChange,
    QtCore.QEvent.Type.PaletteChange,
    QtCore.QEvent.Type.HoverEnter,
    QtCore.QEvent.Type.Enter,
    QtCore.QEvent.Type.HoverMove,
    QtCore.QEvent.Type.MouseButtonRelease,
    QtCore.QEvent.Type.MouseTrackingChange,
    QtCore.QEvent.Type.CursorChange,
    QtCore.QEvent.Type.WindowTitleChange,
    QtCore.QEvent.Type.ContentsRectChange,
    QtCore.QEvent.Type.AcceptDropsChange,
    QtCore.QEvent.Type.MouseTrackingChange,
    QtCore.QEvent.Type.ZOrderChange,
    QtCore.QEvent.Type.MouseMove,
    QtCore.QEvent.Type.Leave,
    QtCore.QEvent.Type.HoverLeave,
    QtCore.QEvent.Type.ApplicationDeactivated,
    QtCore.QEvent.Type.EnabledChange,
    QtCore.QEvent.Type.WindowBlocked,
    QtCore.QEvent.Type.EnabledChange,
    QtCore.QEvent.Type.WindowUnblocked,
    QtCore.QEvent.Type.KeyRelease,
    QtCore.QEvent.Type.NativeGesture,
    QtCore.QEvent.Type.KeyboardLayoutChange,
    QtCore.QEvent.Type.ToolTip,
]
test = QtCore.QEvent.registerEventType()
t = QtCore.QEvent.Type(test)


class UpdateGLEvent(QtCore.QEvent):

    def __init__(self):
        global t
        QtCore.QEvent.__init__(self, t)


class MyApplication(QtGui.QApplication):
    def __init__(self, args):
        QtGui.QApplication.__init__(self, args)
        self.installEventFilter(self)

    def eventFilter(self, receiver, event):
        global ignore_list
        # print(receiver, event.type(), t)
        global t
        if event.type() == QtCore.QEvent.MouseMove and isinstance(receiver, gl_widget.GLWidget):
            if receiver.dataset_loaded:
                if event.buttons() & QtCore.Qt.LeftButton:
                    dx = event.x() - receiver.x
                    dy = event.y() - receiver.y
                    receiver.vis.rotate_mouse(dx, dy)
                    receiver.x = event.x()
                    receiver.y = event.y()
                    receiver.updateGL()
            return True

        if event.type() == QtCore.QEvent.Wheel and isinstance(receiver, gl_widget.GLWidget):
            if receiver.dataset_loaded:
                receiver.update_needed = True
                if event.modifiers() != QtCore.Qt.ShiftModifier:
                    if event.orientation() == QtCore.Qt.Orientation.Vertical:
                        receiver.vis.zoom(event.delta())
                else:
                    rot_v = 0.1
                    if event.orientation() == QtCore.Qt.Orientation.Horizontal:
                        receiver.vis.rotate_mouse(event.delta() * rot_v, 0)
                    else:
                        receiver.vis.rotate_mouse(0, event.delta() * rot_v)

                QtGui.QApplication.postEvent(receiver, UpdateGLEvent())
                return True

        if event.type() == QtCore.QEvent.MouseButtonPress and isinstance(receiver, gl_widget.GLWidget):
            if receiver.dataset_loaded:
                if event.buttons() and QtCore.Qt.LeftButton:
                    receiver.x = event.x()
                    receiver.y = event.y()
                    return True

        if event.type() == t and isinstance(receiver, gl_widget.GLWidget):
            if receiver.update_needed:
                receiver.updateGL()
                receiver.update_needed = False
            return True

        if event.type() == QtCore.QEvent.KeyPress and isinstance(receiver, gl_widget.GLWidget):
            if receiver.dataset_loaded:
                rot_v_key = 15
                if event.key() == QtCore.Qt.Key_Right:
                    receiver.vis.rotate_mouse(rot_v_key, 0)
                elif event.key() == QtCore.Qt.Key_Left:
                    receiver.vis.rotate_mouse(-rot_v_key, 0)
                elif event.key() == QtCore.Qt.Key_Up:
                    receiver.vis.rotate_mouse(0, -rot_v_key)
                elif event.key() == QtCore.Qt.Key_Down:
                    receiver.vis.rotate_mouse(0, rot_v_key)
                elif event.key() == QtCore.Qt.Key_D:  # Domains
                    receiver.vis.create_scene(False)
                elif event.key() == QtCore.Qt.Key_C:  # Cavities
                    receiver.vis.create_scene(True)
                elif event.key() == QtCore.Qt.Key_F:  # center based cavities
                    receiver.vis.create_scene(True, True)
                else:
                    event.ignore()
                receiver.updateGL()
                return True

        if event.type() == QtCore.QEvent.KeyPress and isinstance(receiver, main_window.MainWindow):
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

        if event.type() not in ignore_list:
            print(event.type(), event)
        return super(MyApplication, self).eventFilter(receiver, event)
