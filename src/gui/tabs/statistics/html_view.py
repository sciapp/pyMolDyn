import jinja2
from PyQt4 import QtWebKit, QtGui, QtCore
import os.path
import core.elements
import core.bonds
from collections import Counter
from core.calculation.discretization import Discretization
from gui.tabs.statistics.tree_list import TreeList


def render_html_atom_group(atom_number, atom_elements):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atoms.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of atoms",
                     "description": "a summary of all calculated atoms",
                     "atom_number": atom_number,
                     "atom_elements": atom_elements
                     }

    return template.render(template_vars)


def render_html_atom(index, atom_fullname, atom_positions, atom_number, covalent_radius, atom_color_rgb, bonds):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atom.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of atoms",
                     "description": "a summary of one atom",
                     "index": index,
                     "atom_fullname": atom_fullname,
                     "atom_positions": atom_positions,
                     "atom_number": atom_number,
                     "covalent_radius": covalent_radius,
                     "atom_color_rgb": atom_color_rgb,
                     "bonds": bonds,
                     }

    return template.render(template_vars)


def render_html_cavity_center_group(surface_area, surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_center.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of all cavities",
                     "description": "a summary of all calculated center bases cavities",
                     "surface_area": surface_area,
                     "surface_volumes": surface_volumes,
                     "volume_fraction": volume_fraction,
                     }

    return template.render(template_vars)


def render_html_cavity_center(index, surface, volume, domains, volume_fraction, squared_gyration_radius,
                              asphericity, acylindricity, anisotropy, is_cyclic):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_center.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of one cavity",
                     "description": "a summary of one calculated center bases cavity",
                     "index": index,
                     "surface": surface,
                     "volume": volume,
                     "surface_to_volume_ratio": surface / volume,
                     "domains": domains,
                     "volume_fraction": volume_fraction,
                     "squared_gyration_radius": squared_gyration_radius,
                     "asphericity": asphericity,
                     "acylindricity": acylindricity,
                     "anisotropy": anisotropy,
                     "is_cyclic": is_cyclic
                     }

    return template.render(template_vars)


def render_html_cavity_surface_group(surface_area, surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_surface.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of atoms",
                     "description": "a summary of all calculated surface based cavities",
                     "surface_area": surface_area,
                     "surface_volumes": surface_volumes,
                     "volume_fraction": volume_fraction,
                     }

    return template.render(template_vars)


def render_html_cavity_surface(index, surface, volume, domains, volume_fraction, squared_gyration_radius,
                               asphericity, acylindricity, anisotropy, is_cyclic):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_surface.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of atoms",
                     "description": "a summary of all calculated surface based cavities",
                     "index": index,
                     "surface": surface,
                     "volume": volume,
                     "surface_to_volume_ratio": surface / volume,
                     "domains": domains,
                     "volume_fraction": volume_fraction,
                     "squared_gyration_radius": squared_gyration_radius,
                     "asphericity": asphericity,
                     "acylindricity": acylindricity,
                     "anisotropy": anisotropy,
                     "is_cyclic": is_cyclic
                     }

    return template.render(template_vars)


def render_html_cavity_domain_group(surface_area, surface_volumes, surface_volumes_fractions):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domains.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of all cavities (domains)",
                     "description": "a summary of all calculated cavities (domains)",
                     "surface_area": surface_area,
                     "surface_volumes": surface_volumes,
                     "surface_volumes_fractions": surface_volumes_fractions,
                     }

    return template.render(template_vars)


def render_html_cavity_domain(index, domain_center, surface, volume, volume_fraction, surface_cavity_index,
                              center_cavity_index, squared_gyration_radius, asphericity, acylindricity, anisotropy,
                              is_cyclic):
    template_loader = jinja2.FileSystemLoader(searchpath="gui/tabs/statistics/templates")
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domain.html'
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {"title": "Summary of one cavity (domain)",
                     "description": "a summary of one calculated cavities (domain)",
                     "index": index,
                     "domain_center": domain_center,
                     "surface": surface,
                     "volume": volume,
                     "surface_to_volume_ratio": surface / volume,
                     "volume_fraction": volume_fraction,
                     "surface_cavity_index": surface_cavity_index,
                     "center_cavity_index": center_cavity_index,
                     "squared_gyration_radius": squared_gyration_radius,
                     "asphericity": asphericity,
                     "acylindricity": acylindricity,
                     "anisotropy": anisotropy,
                     "is_cyclic": is_cyclic
                     }

    return template.render(template_vars)


class HTMLWindow(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        box = QtGui.QVBoxLayout()
        self.webview = QtWebKit.QWebView()

        self.atoms = None
        self.cavities_center = None
        self.cavities_surface = None
        self.domains = None
        self.discretization = None

        self.tree_list = None
        self.webview.setHtml(None)
        self.webview.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.webview.linkClicked.connect(self.link_clicked)
        path = os.path.dirname(__file__)       # get dir from this file and add it to stylesheet path
        self.webview.settings().setUserStyleSheetUrl(QtCore.QUrl.fromLocalFile(path + '/templates/style.css'))

        box.addWidget(self.webview)
        self.setLayout(box)
        box.setContentsMargins(5, 0, 0, 0)
        self.show()

    def link_clicked(self, data):
        '''
        examines the data of the given link by *data* an calls the specific method to render the new HTML page
        :param data: Value of the link clicked in Webview
        :return: None
        '''
        value = data.toString()
        value = value.split(":")
        if value[0] == "surface_cavity":
            self.show_surface_cavity(int(value[1])-1)
        elif value[0] == "center_cavity":
            self.show_center_cavity(int(value[1])-1)
        elif value[0] == "domain":
            self.show_domain(int(value[1])-1)
        elif value[0] == "focus":
            position = [float(value[1]),float(value[2]),float(value[3])]
            self.window().control.visualization.set_focus_on(*position)
            self.window().center.gl_widget.update()
            self.window().center.combo.setCurrentIndex(0)
            self.window().center.gl_stack.setCurrentIndex(0)
        elif value[0] == "atom":
            self.show_atom(int(value[1]))
        elif value[0] == 'hideothers':
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == 'atom':
                atom_index = int(value[2])-1
                view_tab.atom_check.indices = [atom_index]
            elif value[1] == 'element':
                element = core.elements.names[int(value[2])]
                visible_atom_indices = []
                for i, element_name in enumerate(self.atoms.elements):
                    if core.elements.names[core.elements.numbers[element_name.upper()]] == element:
                        visible_atom_indices.append(i)
                view_tab.atom_check.indices = visible_atom_indices
            elif value[1] == 'domain':
                domain_index = int(value[2])-1
                view_tab.domain_check.indices = [domain_index]
            elif value[1] == 'surface_cavity':
                surface_cavity_index = int(value[2])-1
                view_tab.surface_cavity_check.indices = [surface_cavity_index]
            elif value[1] == 'center_cavity':
                center_cavity_index = int(value[2])-1
                view_tab.center_cavity_check.indices = [center_cavity_index]
        elif value[0] == 'addtovisible':
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == 'atom':
                atom_index = int(value[2])-1
                view_tab.domain_check.add_indices([atom_index])
            elif value[1] == 'domain':
                domain_index = int(value[2])-1
                view_tab.domain_check.add_indices([domain_index])
            elif value[1] == 'surface_cavity':
                surface_cavity_index = int(value[2])-1
                view_tab.surface_cavity_check.add_indices([surface_cavity_index])
            elif value[1] == 'center_cavity':
                center_cavity_index = int(value[2])-1
                view_tab.center_cavity_check.add_indices([center_cavity_index])
        elif value[0] == 'showall':
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == 'atoms':
                view_tab.atom_check.setChecked(True)
                view_tab.atom_check.selection_checkbox_set_checked(False)
            if value[1] == 'domains':
                view_tab.domain_check.setChecked(True)
                view_tab.domain_check.selection_checkbox_set_checked(False)
            if value[1] == 'surface_cavities':
                view_tab.surface_cavity_check.setChecked(True)
                view_tab.surface_cavity_check.selection_checkbox_set_checked(False)
            if value[1] == 'center_cavities':
                view_tab.center_cavity_check.setChecked(True)
                view_tab.center_cavity_check.selection_checkbox_set_checked(False)

    def update_results(self, results):
        self.atoms = results.atoms
        self.cavities_center = results.center_cavities
        self.cavities_surface = results.surface_cavities
        self.domains = results.domains
        self.discretization = Discretization(results.atoms.volume, results.resolution, True)

    def show_atom_group(self):
        atom_number = self.atoms.number
        atom_elements = Counter(self.atoms.elements)

        self.webview.setHtml(render_html_atom_group(atom_number, atom_elements))

    def show_atom(self, index):
        if self.tree_list is not None:
            self.tree_list.select_atom(index)

        #for bond in bonds:
        #    if index not in self.atoms.bonds[bond]:
        #        self.atoms.bonds[bond].append(index)

        atom_name = self.atoms.elements[index]           # atom name from periodic systen
        atom_fullname = core.elements.names[core.elements.numbers[atom_name.upper()]]                # get full atom name
        atom_color_rgb = core.elements.colors[core.elements.numbers[atom_name.upper()]]
        atom_positions = self.atoms.positions[index]
        atom_number = core.elements.numbers[atom_name.upper()]
        covalent_radius = self.atoms.covalence_radii[index]
        bonds = self.atoms.bonds[index]


        #print dir(self.domains[0])

        self.webview.setHtml(render_html_atom(index, atom_fullname, atom_positions, atom_number, covalent_radius, atom_color_rgb, bonds))

    def show_center_cavity_group(self):
        surface_area = 0.0
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_center is not None:
            for sf in self.cavities_center.surface_areas:
                surface_area += sf
            for vl in self.cavities_center.volumes:
                volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_center_group(surface_area, volumes, volume_fraction))

    def show_center_cavity(self, index):
        if self.tree_list is not None:
            self.tree_list.select_center_cavity(index)
        #print self.cavities_center.number # anzahl cavites

        volume_fraction = 0.0
        cavities = self.cavities_center.multicavities[index]
        domains = []
        for cavity in cavities:
            domains.append((cavity+1, self.discretization.discrete_to_continuous(self.domains.centers[cavity])))
        #print self.cavities_center.triangles

        surface = self.cavities_center.surface_areas[index]
        volume = self.cavities_center.volumes[index]
        squared_gyration_radius = self.cavities_center.squared_gyration_radii[index]
        asphericity = self.cavities_center.asphericities[index]
        acylindricity = self.cavities_center.acylindricities[index]
        anisotropy = self.cavities_center.anisotropies[index]
        is_cyclic = index in self.cavities_center.cyclic_area_indices

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_center(index, surface, volume, domains, volume_fraction,
                                                       squared_gyration_radius, asphericity, acylindricity,
                                                       anisotropy, is_cyclic))

    def show_surface_cavity_group(self):
        surface_area = 0.0
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_surface is not None:
            for sf in self.cavities_center.surface_areas:
                surface_area += sf
            for vl in self.cavities_surface.volumes:
                volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_surface_group(surface_area, volumes, volume_fraction))

    def show_surface_cavity(self, index):
        if self.tree_list is not None:
            self.tree_list.select_surface_cavity(index)
        volume_fraction = 0.0
        cavities = self.cavities_surface.multicavities[index]
        domains = []

        surface = self.cavities_surface.surface_areas[index]
        volume = self.cavities_surface.volumes[index]
        squared_gyration_radius = self.cavities_surface.squared_gyration_radii[index]
        asphericity = self.cavities_surface.asphericities[index]
        acylindricity = self.cavities_surface.acylindricities[index]
        anisotropy = self.cavities_surface.anisotropies[index]
        is_cyclic = index in self.cavities_surface.cyclic_area_indices
        for cavity in cavities:
            domains.append((cavity+1, self.discretization.discrete_to_continuous(self.domains.centers[cavity])))

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_surface(index, surface, volume, domains, volume_fraction,
                                                        squared_gyration_radius, asphericity, acylindricity,
                                                        anisotropy, is_cyclic))

    def show_domain_group(self):
        surface = 0.0
        volumes = 0.0
        volume_fraction = 0.0

        if self.domains is not None:
            for sf in self.domains.surface_areas:
                surface += sf
            for vl in self.domains.volumes:
                volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_domain_group(surface, volumes, volume_fraction))

    def show_domain(self, index):
        if self.tree_list is not None:
            self.tree_list.select_domain(index)
        domain = self.discretization.discrete_to_continuous(self.domains.centers[index])
        surface = self.domains.surface_areas[index]
        volume = self.domains.volumes[index]
        volume_fraction = 0.0
        surface_cavity_index = None
        center_cavity_index = None
        squared_gyration_radius = self.domains.squared_gyration_radii[index]
        asphericity = self.domains.asphericities[index]
        acylindricity = self.domains.acylindricities[index]
        anisotropy = self.domains.anisotropies[index]
        is_cyclic = index in self.domains.cyclic_area_indices

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100
        if self.domains is not None and self.cavities_surface is not None:
            for i in range(len(self.cavities_surface.multicavities)):
                if index in self.cavities_surface.multicavities[i]:
                    surface_cavity_index = i+1
                    break
        if self.domains is not None and self.cavities_center is not None:
            for i in range(len(self.cavities_center.multicavities)):
                if index in self.cavities_center.multicavities[i]:
                    center_cavity_index = i+1
                    break

        self.webview.setHtml(render_html_cavity_domain(index, domain, surface, volume, volume_fraction,
                                                       surface_cavity_index, center_cavity_index,
                                                       squared_gyration_radius, asphericity, acylindricity, anisotropy,
                                                       is_cyclic))

