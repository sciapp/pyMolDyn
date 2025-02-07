import os.path
from collections import Counter

import jinja2
import numpy as np
from PySide6 import QtCore, QtWidgets

from ....core import elements
from ....core.calculation.discretization import Discretization
from ...util.webview import WebWidget


def render_html_atom_group(atom_number, atom_elements):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "atoms.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {
        "title": "Summary of atoms",
        "description": "a summary of all calculated atoms",
        "atom_number": atom_number,
        "atom_elements": atom_elements,
    }

    return template.render(template_vars)


def render_html_atom(
    index,
    atom_fullname,
    atom_positions,
    atom_number,
    covalent_radius,
    cutoff_radius,
    atom_color_rgb,
    bonds,
):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "atom.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {
        "title": "Summary of atoms",
        "description": "a summary of one atom",
        "index": index,
        "atom_fullname": atom_fullname,
        "atom_positions": atom_positions,
        "atom_number": atom_number,
        "covalent_radius": covalent_radius,
        "cutoff_radius": cutoff_radius,
        "atom_color_rgb": atom_color_rgb,
        "bonds": bonds,
    }

    return template.render(template_vars)


def render_html_cavity_center_group(number, surface_area, surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavities_center.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {
        "title": "Summary of all cavities",
        "description": "a summary of all calculated center bases cavities",
        "number": number,
        "surface_area": surface_area,
        "surface_volumes": surface_volumes,
        "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)


def render_html_cavity_center_group_unknown():
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavities_center_unknown.html"
    template = template_env.get_template(TEMPLATE_FILE)
    return template.render({})


def render_html_cavity_center(**kwargs):
    needed_keys = (
        "index",
        "surface",
        "volume",
        "domains",
        "volume_fraction",
        "mass_center",
        "squared_gyration_radius",
        "asphericity",
        "acylindricity",
        "anisotropy",
        "characteristic_radius",
        "is_cyclic",
    )
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavity_center.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = dict(kwargs)
    template_vars["title"] = "Summary of one cavity (domain)"
    template_vars["description"] = "a summary of one calculated cavities (domain)"
    if kwargs["surface"] is not None and kwargs["volume"] is not None:
        template_vars["surface_to_volume_ratio"] = kwargs["surface"] / kwargs["volume"]
    missing_values = tuple(key for key in needed_keys if key not in kwargs or kwargs[key] is None)
    template_vars.update((key, None) for key in missing_values)
    template_vars["missing_values"] = missing_values if len(missing_values) > 0 else None

    return template.render(template_vars)


def render_html_cavity_surface_group(number, surface_area, surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavities_surface.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {
        "title": "Summary of atoms",
        "description": "a summary of all calculated surface based cavities",
        "number": number,
        "surface_area": surface_area,
        "surface_volumes": surface_volumes,
        "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)


def render_html_cavity_surface_group_unknown():
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavities_surface_unknown.html"
    template = template_env.get_template(TEMPLATE_FILE)
    return template.render({})


def render_html_cavity_surface(**kwargs):
    needed_keys = (
        "index",
        "surface",
        "volume",
        "domains",
        "volume_fraction",
        "mass_center",
        "squared_gyration_radius",
        "asphericity",
        "acylindricity",
        "anisotropy",
        "characteristic_radius",
        "is_cyclic",
    )
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "cavity_surface.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = dict(kwargs)
    template_vars["title"] = "Summary of one cavity (domain)"
    template_vars["description"] = "a summary of one calculated cavities (domain)"
    if kwargs["surface"] is not None and kwargs["volume"] is not None:
        template_vars["surface_to_volume_ratio"] = kwargs["surface"] / kwargs["volume"]
    missing_values = tuple(key for key in needed_keys if key not in kwargs or kwargs[key] is None)
    template_vars.update((key, None) for key in missing_values)
    template_vars["missing_values"] = missing_values if len(missing_values) > 0 else None

    return template.render(template_vars)


def render_html_cavity_domain_group(number, surface_area, surface_volumes, surface_volumes_fractions):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "domains.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = {
        "title": "Summary of all cavities (domains)",
        "description": "a summary of all calculated cavities (domains)",
        "number": number,
        "surface_area": surface_area,
        "surface_volumes": surface_volumes,
        "surface_volumes_fractions": surface_volumes_fractions,
    }

    return template.render(template_vars)


def render_html_cavity_domain_group_unknown():
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "domains_unknown.html"
    template = template_env.get_template(TEMPLATE_FILE)
    return template.render({})


def render_html_cavity_domain(**kwargs):
    needed_keys = (
        "index",
        "center",
        "surface",
        "volume",
        "volume_fraction",
        "surface_cavity_index",
        "center_cavity_index",
        "mass_center",
        "squared_gyration_radius",
        "asphericity",
        "acylindricity",
        "anisotropy",
        "characteristic_radius",
        "is_cyclic",
    )
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = "domain.html"
    template = template_env.get_template(TEMPLATE_FILE)

    template_vars = dict(kwargs)
    template_vars["title"] = "Summary of one cavity (domain)"
    template_vars["description"] = "a summary of one calculated cavities (domain)"
    if kwargs["surface"] is not None and kwargs["volume"] is not None:
        template_vars["surface_to_volume_ratio"] = kwargs["surface"] / kwargs["volume"]
    missing_values = tuple(key for key in needed_keys if key not in kwargs or kwargs[key] is None)
    template_vars.update((key, None) for key in missing_values)
    template_vars["missing_values"] = missing_values if len(missing_values) > 0 else None

    return template.render(template_vars)


class HTMLWindow(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        box = QtWidgets.QVBoxLayout()
        self.webview = WebWidget(css_filepath="../tabs/statistics/templates/style.css")

        self.atoms = None
        self.cavities_center = None
        self.cavities_surface = None
        self.domains = None
        self.discretization = None

        self.tree_list = None
        self.webview.set_gui_html(None)
        self.webview.gui_link_clicked.connect(self.link_clicked)

        box.addWidget(self.webview)
        self.setLayout(box)
        box.setContentsMargins(5, 0, 0, 0)
        self.show()

    def minimumSizeHint(self):
        return QtCore.QSize(150, -1)

    def sizeHint(self):
        return QtCore.QSize(250, -1)

    def link_clicked(self, value):
        """
        examines the data of the given link by *data* an calls the specific method to render the new HTML page
        :param data: Value of the link clicked in Webview
        :return: None
        """
        value = value.split("/")
        if value[0] == "surface_cavity":
            self.show_surface_cavity(int(value[1]) - 1)
        elif value[0] == "center_cavity":
            self.show_center_cavity(int(value[1]) - 1)
        elif value[0] == "domain":
            self.show_domain(int(value[1]) - 1)
        elif value[0] == "focus":
            position = [float(value[1]), float(value[2]), float(value[3])]
            self.window().control.visualization.set_focus_on(*position)
            self.window().center.gl_widget.update()
            self.window().center.combo.setCurrentIndex(0)
            self.window().center.gl_stack.setCurrentIndex(0)
        elif value[0] == "atom":
            self.show_atom(int(value[1]))
        elif value[0] == "hideothers":
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == "atom":
                atom_index = int(value[2]) - 1
                view_tab.atom_check.indices = [atom_index]
                view_tab.atom_check.selection_checkbox_set_checked(True)
            elif value[1] == "element":
                element = elements.names[int(value[2])]
                visible_atom_indices = []
                for i, element_name in enumerate(self.atoms.elements):
                    if elements.names[elements.numbers[element_name.upper()]] == element:
                        visible_atom_indices.append(i)
                view_tab.atom_check.indices = visible_atom_indices
                view_tab.atom_check.selection_checkbox_set_checked(True)
            elif value[1] == "domain":
                domain_index = int(value[2]) - 1
                view_tab.domain_check.indices = [domain_index]
                view_tab.domain_check.selection_checkbox_set_checked(True)
            elif value[1] == "surface_cavity":
                surface_cavity_index = int(value[2]) - 1
                view_tab.surface_cavity_check.indices = [surface_cavity_index]
                view_tab.surface_cavity_check.selection_checkbox_set_checked(True)
            elif value[1] == "center_cavity":
                center_cavity_index = int(value[2]) - 1
                view_tab.center_cavity_check.indices = [center_cavity_index]
                view_tab.center_cavity_check.selection_checkbox_set_checked(True)
        elif value[0] == "addtovisible":
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == "atom":
                atom_index = int(value[2]) - 1
                view_tab.domain_check.add_indices([atom_index])
            elif value[1] == "domain":
                domain_index = int(value[2]) - 1
                view_tab.domain_check.add_indices([domain_index])
            elif value[1] == "surface_cavity":
                surface_cavity_index = int(value[2]) - 1
                view_tab.surface_cavity_check.add_indices([surface_cavity_index])
            elif value[1] == "center_cavity":
                center_cavity_index = int(value[2]) - 1
                view_tab.center_cavity_check.add_indices([center_cavity_index])
        elif value[0] == "showall":
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            view_tab = main_window.view_dock.view_tab
            if value[1] == "atoms":
                view_tab.atom_check.setChecked(True)
                view_tab.atom_check.selection_checkbox_set_checked(False)
            if value[1] == "domains":
                view_tab.domain_check.setChecked(True)
                view_tab.domain_check.selection_checkbox_set_checked(False)
            if value[1] == "surface_cavities":
                view_tab.surface_cavity_check.setChecked(True)
                view_tab.surface_cavity_check.selection_checkbox_set_checked(False)
            if value[1] == "center_cavities":
                view_tab.center_cavity_check.setChecked(True)
                view_tab.center_cavity_check.selection_checkbox_set_checked(False)
        elif value[0] == "recalculate":
            parent = self.parent()
            while parent.parent():
                parent = parent.parent()
            main_window = parent
            file_tab = main_window.file_dock.file_tab
            current_filename, current_frame = file_tab.last_shown_filename_with_frame
            file_tab.calculate({current_filename: [current_frame]})

    def update_results(self, results):
        self.atoms = results.atoms
        self.cavities_center = results.center_cavities
        self.cavities_surface = results.surface_cavities
        self.domains = results.domains
        self.discretization = Discretization(results.atoms.volume, results.resolution, True)
        self.show_atom_group()

    def show_atom_group(self):
        atom_number = self.atoms.number
        atom_elements = Counter(self.atoms.elements)

        self.webview.set_gui_html(render_html_atom_group(atom_number, atom_elements))

    def show_atom(self, index):
        if self.tree_list is not None:
            self.tree_list.select_atom(index)

        # for bond in bonds:
        #    if index not in self.atoms.bonds[bond]:
        #        self.atoms.bonds[bond].append(index)

        atom_name = self.atoms.elements[index]  # atom name from periodic systen
        atom_fullname = elements.names[elements.numbers[atom_name.decode("utf-8").upper()]]  # get full atom name
        atom_color_rgb = elements.colors[elements.numbers[atom_name.decode("utf-8").upper()]]
        atom_positions = self.atoms.positions[index]
        atom_number = elements.numbers[atom_name.decode("utf-8").upper()]
        covalent_radius = self.atoms.covalence_radii[index]
        cutoff_radius = self.atoms.radii[index]
        bonds = self.atoms.bonds[index]

        # print dir(self.domains[0])

        self.webview.set_gui_html(
            render_html_atom(
                index,
                atom_fullname,
                atom_positions,
                atom_number,
                covalent_radius,
                cutoff_radius,
                atom_color_rgb,
                bonds,
            )
        )

    def show_center_cavity_group(self):
        number = 0
        surface_area = 0.0
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_center is None:
            self.webview.set_gui_html(render_html_cavity_center_group_unknown())
            return
        number = self.cavities_center.number
        for sf in self.cavities_center.surface_areas:
            surface_area += sf
        for vl in self.cavities_center.volumes:
            volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes / self.atoms.volume.volume) * 100

        self.webview.set_gui_html(render_html_cavity_center_group(number, surface_area, volumes, volume_fraction))

    def show_center_cavity(self, index):
        if self.tree_list is not None:
            self.tree_list.select_center_cavity(index)
        attrs = self._create_attr_getter(self.cavities_center, index)
        data = {}
        data["index"] = index
        data["volume_fraction"] = 0.0
        cavities = attrs.multicavities
        domains = []
        for cavity in cavities:
            domains.append(
                (
                    cavity + 1,
                    self.discretization.discrete_to_continuous(self.domains.centers[cavity]),
                )
            )
        data["domains"] = domains

        data["surface"] = attrs.surface_areas
        data["volume"] = attrs.volumes
        data["mass_center"] = attrs.mass_centers
        data["squared_gyration_radius"] = attrs.squared_gyration_radii
        data["asphericity"] = attrs.asphericities
        data["acylindricity"] = attrs.acylindricities
        data["anisotropy"] = attrs.anisotropies
        data["characteristic_radius"] = attrs.characteristic_radii
        data["is_cyclic"] = index in self.cavities_center.cyclic_area_indices

        if self.atoms.volume is not None:
            data["volume_fraction"] = (data["volume"] / self.atoms.volume.volume) * 100

        self.webview.set_gui_html(render_html_cavity_center(**data))

    def show_surface_cavity_group(self):
        number = 0
        surface_area = 0.0
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_surface is None:
            self.webview.set_gui_html(render_html_cavity_surface_group_unknown())
            return
        number = self.cavities_surface.number
        for sf in self.cavities_surface.surface_areas:
            surface_area += sf
        for vl in self.cavities_surface.volumes:
            volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes / self.atoms.volume.volume) * 100

        self.webview.set_gui_html(render_html_cavity_surface_group(number, surface_area, volumes, volume_fraction))

    def show_surface_cavity(self, index):
        if self.tree_list is not None:
            self.tree_list.select_surface_cavity(index)
        attrs = self._create_attr_getter(self.cavities_surface, index)
        data = {}
        data["index"] = index
        data["volume_fraction"] = 0.0
        cavities = attrs.multicavities
        domains = []
        for cavity in cavities:
            domains.append(
                (
                    cavity + 1,
                    self.discretization.discrete_to_continuous(self.domains.centers[cavity]),
                )
            )
        data["domains"] = domains

        data["surface"] = attrs.surface_areas
        data["volume"] = attrs.volumes
        data["mass_center"] = attrs.mass_centers
        data["squared_gyration_radius"] = attrs.squared_gyration_radii
        data["asphericity"] = attrs.asphericities
        data["acylindricity"] = attrs.acylindricities
        data["anisotropy"] = attrs.anisotropies
        data["characteristic_radius"] = attrs.characteristic_radii
        data["is_cyclic"] = index in self.cavities_surface.cyclic_area_indices

        if self.atoms.volume is not None:
            data["volume_fraction"] = (data["volume"] / self.atoms.volume.volume) * 100

        self.webview.set_gui_html(render_html_cavity_surface(**data))

    def show_domain_group(self):
        number = 0
        surface = 0.0
        volumes = 0.0
        volume_fraction = 0.0

        if self.domains is None:
            self.webview.set_gui_html(render_html_cavity_domain_group_unknown())
            return
        number = self.domains.number
        for sf in self.domains.surface_areas:
            surface += sf
        for vl in self.domains.volumes:
            volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes / self.atoms.volume.volume) * 100

        self.webview.set_gui_html(render_html_cavity_domain_group(number, surface, volumes, volume_fraction))

    def show_domain(self, index):
        if self.tree_list is not None:
            self.tree_list.select_domain(index)
        attrs = self._create_attr_getter(self.domains, index)
        data = {}
        data["index"] = index
        discrete_center = attrs.centers
        data["center"] = self.discretization.discrete_to_continuous(discrete_center)
        data["surface"] = attrs.surface_areas
        data["volume"] = attrs.volumes
        data["volume_fraction"] = 0.0
        data["surface_cavity_index"] = None
        data["center_cavity_index"] = None
        data["mass_center"] = attrs.mass_centers
        data["squared_gyration_radius"] = attrs.squared_gyration_radii
        data["asphericity"] = attrs.asphericities
        data["acylindricity"] = attrs.acylindricities
        data["anisotropy"] = attrs.anisotropies
        data["characteristic_radius"] = attrs.characteristic_radii
        data["is_cyclic"] = index in self.domains.cyclic_area_indices

        if self.atoms.volume is not None:
            data["volume_fraction"] = (data["volume"] / self.atoms.volume.volume) * 100
        if self.domains is not None and self.cavities_surface is not None:
            for i in range(len(self.cavities_surface.multicavities)):
                if index in self.cavities_surface.multicavities[i]:
                    data["surface_cavity_index"] = i + 1
                    break
        if self.domains is not None and self.cavities_center is not None:
            for i in range(len(self.cavities_center.multicavities)):
                if index in self.cavities_center.multicavities[i]:
                    data["center_cavity_index"] = i + 1
                    break

        self.webview.set_gui_html(render_html_cavity_domain(**data))

    @staticmethod
    def _create_attr_getter(obj, index):
        class AttrGetter:
            def __init__(self, obj, index):
                self._obj = obj
                self._index = index

            def __getattr__(self, attr):
                value = getattr(self._obj, attr)
                is_numpy_array = isinstance(value, np.ndarray)
                if (is_numpy_array and len(value.shape) > 0) or (not is_numpy_array and len(value) > 0):
                    return value[self._index]
                else:
                    return None

        return AttrGetter(obj, index)
