import jinja2
from PySide import QtWebKit, QtGui


def load_html():
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "test.jinja"
    template = template_env.get_template( TEMPLATE_FILE )

    FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]

    template_vars = { "title": "Test Example",
                     "description": "A simple inquiry of function.",
                     "favorites": FAVORITES
    }

    return template.render(template_vars)


class HTMLWindow(QtGui.QWidget):

    def __init__(self, html):
        QtGui.QWidget.__init__(self)

        box = QtGui.QVBoxLayout()
        webview = QtWebKit.QWebView()

        webview.setHtml(html)
        box.addWidget(webview)
        self.setLayout(box)
        self.show()


