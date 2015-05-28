from PySide import QtGui, QtCore
from collections import Counter, OrderedDict

class TreeList(QtGui.QTreeWidget):
    def __init__(self, html_view):
        QtGui.QTreeWidget.__init__(self)
        self.setColumnCount(1)
        #todo dynamic list generation from results

        # attributes get intialized by update_control method after calculation
        self.control = None
        self.atoms = None
        self.atom_number = None
        self.atom_elements = {}
        self.caveties_center = None
        self.caveties_surface = None
        self.domains = None

        self.atom_list = []
        self.caveties_center_list = []
        self.caveties_surface_list = []
        self.domains_list  = []

        self.html_view = html_view

        self.items = []
        self.update_tree_view()

        # expand all items per default
        for item in self.items:
            self.setItemExpanded(item, True)

        self.adjustSize()
        self.updateGeometry()
        self.resizeColumnToContents(0)
        self.addTopLevelItems(self.items)
        self.setHeaderHidden(True)
        self.itemSelectionChanged.connect(self.item_selection_changed)

    def item_selection_changed(self):
        if self.selectedItems():
            selected_item = self.selectedItems()[0]
            self.item_selected(selected_item, 0)

    def select_atom(self, index):
        self.setCurrentItem(self.items[0].child(index))

    def select_center_cavity(self, index):
        self.setCurrentItem(self.items[1].child(index))

    def select_surface_cavity(self, index):
        self.setCurrentItem(self.items[2].child(index))

    def select_domain(self, index):
        self.setCurrentItem(self.items[3].child(index))

    def item_selected(self, item, column):
        '''
            This method decides which element in the tree_list was clicked and calls the specific show method.
        '''
        data = item.data(0, column)
        if data == 'Atoms':
            self.html_view.show_atom_group()
        elif data.startswith('Atom '):
            index = int(data.split()[-1])-1
            self.html_view.show_atom(index)
        elif data == 'Cavities (center)':
            self.html_view.show_center_cavity_group()
        elif data == 'Cavities (surface)':
            self.html_view.show_surface_cavity_group()
        elif data == 'Cavity Domains':
            self.html_view.show_domain_group()
        elif item.parent().data(0, column) is not None:
            parent = item.parent().data(0, column)
            if data.startswith('Cavity ') and parent == "Cavities (center)":
                index = int(data.split()[-1])-1
                self.html_view.show_center_cavity(index)
            elif data.startswith('Cavity ') and parent == 'Cavities (surface)':
                index = int(data.split()[-1])-1
                self.html_view.show_surface_cavity(index)
            elif data.startswith('Domain ') and parent == 'Cavity Domains':
                index = int(data.split()[-1])-1
                self.html_view.show_domain(index)

    def update_results(self, results):
        self.atoms = results.atoms
        self.atom_number = self.atoms.number
        self.atom_elements = Counter(self.atoms.elements)
        self.caveties_center = results.center_cavities
        self.caveties_surface = results.surface_cavities
        self.domains = results.domains

        self.atom_list = ["Atom %d" % (i+1) for i in range(self.atoms.number)]
        if self.caveties_center is not None:
            self.caveties_center_list = ["Cavity %d" % (i+1) for i in range(len(self.caveties_center.multicavities))]
        if self.caveties_surface is not None:
            self.caveties_surface_list = ["Cavity %d" % (i+1) for i in range(len(self.caveties_surface.multicavities))]
        if self.domains is not None:
            self.domains_list = ["Domain %d" % (i+1) for i in range(self.domains.number)]
        #print dir(atoms)
        #print atoms.positions
        #print atoms.elements
        #print atoms.sorted_positions
        #print atoms.radii_as_indices
        #print atoms.sorted_radii
        #print atoms.volume


        self.update_tree_view()

    def update_tree_view(self):
        for index in reversed(range(self.topLevelItemCount())):
            self.takeTopLevelItem(index)
        src = OrderedDict([
            ('Atoms', self.atom_list),
            ('Cavities (center)', self.caveties_center_list),
            ('Cavities (surface)', self.caveties_surface_list),
            ('Cavity Domains', self.domains_list)])

        self.items = []
        for root, sib in src.iteritems():
            self.items.append(QtGui.QTreeWidgetItem(self, [root]))
            if sib:
                self.items[-1].addChildren([QtGui.QTreeWidgetItem(self.items[-1], [s]) for s in sib])
