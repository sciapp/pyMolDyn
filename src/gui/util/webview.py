# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWebEngineWidgets


_js_inject_css_template = '''\
window.onload = function() {{
    (function(css) {{
        var node = document.createElement('style');
        node.innerHTML = css;
        document.body.appendChild(node);
    }})('{css}');
}};\
'''


class WebWidget(QtWebEngineWidgets.QWebEngineView):
    class WebPage(QtWebEngineWidgets.QWebEnginePage):
        gui_link_clicked = QtCore.pyqtSignal(str)

        def __init__(self, html, css=None, *args, **kwargs):
            super(WebWidget.WebPage, self).__init__(*args, **kwargs)
            self._css = css
            self.setHtml(html)

        def setHtml(self, html):
            if html:
                css = ' '.join(self._css.split('\n'))
                js = '<script>{code}</script>'.format(code=_js_inject_css_template.format(css=css))
                html += js
            super(WebWidget.WebPage, self).setHtml(html)

        def acceptNavigationRequest(self, url, t, is_main_frame):
            if t == QtWebEngineWidgets.QWebEnginePage.NavigationTypeLinkClicked and url.scheme() == 'gui':
                self.gui_link_clicked.emit(url.path())
                return False
            else:
                return True

    def __init__(self, css=None, *args, **kwargs):
        super(WebWidget, self).__init__(*args, **kwargs)
        self._css = css
        self._webpage = None

    def set_gui_html(self, html_string):
        if html_string is None:
            html_string = ''
        if self._webpage is None:
            self._webpage = WebWidget.WebPage(html_string, self._css, parent=self)
        else:
            self._webpage.setHtml(html_string)
        self.setPage(self._webpage)
