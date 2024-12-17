from PySide6 import QtCore, QtWidgets


class CalculationTable(QtWidgets.QTableView):
    def __init__(self, parent):
        QtWidgets.QTableView.__init__(self, parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, data, header):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.databla = list(data)
        self.header = header

    def rowCount(self, parent):
        return len(self.databla)

    def columnCount(self, parent):
        return len(self.databla[0])

    #
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.databla[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None


#    def sort(self, col, order):
#        """sort table by given column number col"""
#        self.emit(SIGNAL("layoutAboutToBeChanged()"))
#        self.mylist = sorted(self.mylist,
#            key=operator.itemgetter(col))
#        if order == Qt.DescendingOrder:
#            self.mylist.reverse()
#        self.emit(SIGNAL("layoutChanged()"))
