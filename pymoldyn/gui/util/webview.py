# -*- coding: utf-8 -*-

import os.path
from PySide6 import QtCore
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
)  # QtWebKit is deprecated since Pyside2

has_qtwebengine = True


_js_inject_css_template = """\
window.onload = function() {{
    (function(css) {{
        var node = document.createElement('style');
        node.innerHTML = css;
        document.body.appendChild(node);
    }})('{css}');
}};\
"""

if has_qtwebengine:

    class WebWidget(QWebEngineView):
        gui_link_clicked = QtCore.Signal(str)

        class WebPage(QWebEnginePage):
            gui_link_clicked = QtCore.Signal(str)

            def __init__(self, html, css=None, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._css = css
                self.setHtml(html)

            def setHtml(self, html):
                if html:
                    css = " ".join(self._css.split("\n"))
                    js = "<script>{code}</script>".format(
                        code=_js_inject_css_template.format(css=css)
                    )
                    html += js
                super(WebWidget.WebPage, self).setHtml(html)

            def acceptNavigationRequest(self, url, t, is_main_frame):
                if (
                    t == QWebEnginePage.NavigationTypeLinkClicked
                    and url.scheme() == "gui"
                ):
                    self.gui_link_clicked.emit(url.path())
                    return False
                else:
                    return True

        def __init__(self, css_filepath=None, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if css_filepath is None:
                self._css = None
            else:
                css_filepath = os.path.join(os.path.dirname(__file__), css_filepath)
                with open(css_filepath) as f:
                    self._css = f.read()
            self._webpage = None

        def set_gui_html(self, html_string):
            if html_string is None:
                html_string = ""
            if self._webpage is None:
                self._webpage = WebWidget.WebPage(html_string, self._css, parent=self)
                self._webpage.gui_link_clicked.connect(
                    self.gui_link_clicked.emit
                )  # Forward signal
            else:
                self._webpage.setHtml(html_string)
            self.setPage(self._webpage)

else:

    class WebWidget(QWebView):
        gui_link_clicked = QtCore.Signal(str)

        class WebPage(QWebPage):
            gui_link_clicked = QtCore.Signal(str)

            def __init__(self, html, css, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._css = css
                self.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
                self.linkClicked.connect(self._link_clicked)
                self.setHtml(html)

            def setHtml(self, html):
                if html:
                    css = " ".join(self._css.split("\n"))
                    js = "<script>{code}</script>".format(
                        code=_js_inject_css_template.format(css=css)
                    )
                    html += js
                self.mainFrame().setHtml(html)

            def _link_clicked(self, data):
                value = data.toString()
                if value.startswith("gui:"):
                    self.gui_link_clicked.emit(value[4:])

        def __init__(self, css_filepath=None, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if css_filepath is None:
                self._css = None
            else:
                with open(css_filepath) as f:
                    self._css = f.read()
            self._webpage = None

        def set_gui_html(self, html_string):
            if html_string is None:
                html_string = ""
            if self._webpage is None:
                self._webpage = WebWidget.WebPage(html_string, self._css, parent=self)
                self._webpage.gui_link_clicked.connect(
                    self.gui_link_clicked.emit
                )  # Forward signal
            else:
                self._webpage.setHtml(html_string)
            self.setPage(self._webpage)
