from PySide6 import QtCore, QtGui, QtWidgets


class AboutDialog(QtWidgets.QDialog):
    """
    Einfacher About-Dialog, der den Titel, das Icon, eine Beschreibung und eine Liste von Autoren anzeigt.
    Autoren werden als Liste von Tupeln uebergeben, in dem Format (Name (str), Mail (str))
    """

    class MailLabel(QtWidgets.QLabel):
        def __init__(self, mail, parent):
            super().__init__('<a href="mailto:%s">%s</a>' % (mail, mail), parent)
            self.mail = mail

        def mousePressEvent(self, event):
            url = QtCore.QUrl("mailto:%s" % self.mail)
            QtGui.QDesktopServices.openUrl(url)

    def __init__(self, parent, description, authors, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.title = self.parent().window().windowTitle()
        self.icon = self.parent().window().windowIcon()
        self.description = description
        self.authors = authors

        self._init_ui()

    def _init_ui(self):
        # Label
        self.lb_title = QtWidgets.QLabel("<h2>%s</h2>" % self.title, self)
        self.lb_description = QtWidgets.QLabel("<p>%s</p>" % self.description, self)
        self.lb_author = QtWidgets.QLabel("<b>%s</b>" % "Autoren:", self)
        self.lb_authors = []
        for author, mail in self.authors:
            lb_author = QtWidgets.QLabel(author, self)
            lb_mail = self.MailLabel(mail, self)
            self.lb_authors.append((lb_author, lb_mail))

        # Icon
        self.pm_icon = QtWidgets.QLabel(self)
        self.pm_icon.setPixmap(self.icon.pixmap(128, 128))

        # Layout
        self.la_main_layout = QtWidgets.QVBoxLayout()
        self.la_icon_desc_layout = QtWidgets.QHBoxLayout()
        self.la_desc_author_layout = QtWidgets.QVBoxLayout()
        self.la_authors = QtWidgets.QGridLayout()

        self.la_main_layout.addWidget(self.lb_title, alignment=QtCore.Qt.AlignHCenter)
        self.la_main_layout.addLayout(self.la_icon_desc_layout, stretch=1)
        self.la_icon_desc_layout.addWidget(self.pm_icon)
        self.la_icon_desc_layout.addLayout(self.la_desc_author_layout, stretch=1)
        self.la_desc_author_layout.addWidget(self.lb_description)
        self.la_desc_author_layout.addSpacing(5)
        self.la_desc_author_layout.addWidget(self.lb_author)
        self.la_desc_author_layout.addLayout(self.la_authors)
        self.la_authors.setContentsMargins(5, 0, 0, 0)
        for i, (lb_author, lb_mail) in enumerate(self.lb_authors):
            self.la_authors.addWidget(lb_author, i, 0)
            self.la_authors.addWidget(lb_mail, i, 1)

        self.la_main_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(self.la_main_layout)
