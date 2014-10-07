from PySide import QtGui, QtCore

class TreeList(QtGui.QTreeWidget):

    def __init__(self):
        QtGui.QTreeWidget.__init__(self)
        self.setColumnCount(1)
        src = {'Test':[],'Test2':['1','222','3'], 'Test3':['4','5'], 'Test4':[], 'Test5':['6','7','8','9'] }
        items = []

        for root, sib in src.iteritems():
            items.append(QtGui.QTreeWidgetItem(self, [root]))
            if sib:
                items[-1].addChildren([QtGui.QTreeWidgetItem(items[-1], [s]) for s in sib])

        self.addTopLevelItems(items)
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.item_clicked)

    def item_clicked(self, item, column):
        data = item.data(0, column)