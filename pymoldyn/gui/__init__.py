import faulthandler
import importlib
import io
import os
import signal
import sys


def start_batch():
    # The user actually wants to use startBatch.py instead of startGUI.py
    # This is implemented here as both Linux and OS X use completely
    # different ways to implement the pymoldyn executable, but both call
    # startGUI.py.
    from ..cli import main as cli_main

    if sys.argv[1] == "--batch":
        del sys.argv[1]
    cli_main()


def test_gui_dependencies():
    gui_dependencies = {
        "gr3": "gr",
        "OpenGL": "PyOpenGL",
        "PySide6": "PySide6",
    }

    missing_dependencies = []
    for dep in gui_dependencies:
        try:
            importlib.import_module(dep)
        except ImportError:
            missing_dependencies.append(dep)
    if missing_dependencies:
        print(
            "The following GUI dependencies are missing: "
            + f"{', '.join(gui_dependencies[dep] for dep in missing_dependencies)}",
            file=sys.stderr,
        )
        print(
            "Please install them (or `pip install pymoldyn[gui]`) and try again.",
            file=sys.stderr,
        )
        return False
    return True


def start_gui():
    from PySide6 import QtCore, QtWidgets

    from ..core import file
    from ..core.control import Control
    from . import main_window

    # By default, GR3 uses software rendering. Set `GR3_USE_OPENGL=1` to activate hardware accelerated OpenGL rendering.
    # This is needed, otherwise the Qt OpenGL widget cannot work.
    # TODO: Try software rendering without an OpenGL widget since the software renderer often has even better
    # performance.
    os.environ["GR3_USE_OPENGL"] = "1"

    file.SEARCH_PATH = os.getcwd()
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    app = QtWidgets.QApplication(sys.argv)
    control = Control()
    window = main_window.MainWindow(control)

    app.setOrganizationName("Forschungszentrum Jülich GmbH")
    app.setOrganizationDomain("fz-juelich.de")
    app.setApplicationName("pyMolDyn")

    # Let the Python interpreter run every 50ms...
    timer = QtCore.QTimer()
    timer.start(50)
    timer.timeout.connect(lambda: None)
    # ... to allow it to quit the application on SIGINT (Ctrl-C)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    filenames = sys.argv[1:]
    for filename in filenames:
        if filename:
            window.file_dock.file_tab.disable_files_in_menu_and_open(filename)
            window.update_submenu_recent_files()
    screen_geom = window.screen().availableGeometry()
    window.setGeometry(
        (screen_geom.width() - window.width()) / 2,
        (screen_geom.height() - window.height()) / 2,
        window.width(),
        window.height(),
    )
    sys.exit(app.exec())


def main():
    try:
        # NSLog on macOS raises an `io.UnsupportedOperation` when `fileno` is called
        # `faulthandler` raises RuntimeError if `sys.stderr` is `None` (`noconsole` mode on Windows)
        faulthandler.enable(file=sys.stderr, all_threads=True)
    except (io.UnsupportedOperation, RuntimeError):
        pass
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        start_batch()
    else:
        if not test_gui_dependencies():
            sys.exit(1)
        start_gui()


if __name__ == "__main__":
    main()
