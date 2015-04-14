import jinja2
from PySide import QtWebKit, QtGui, QtCore
import os.path
import core.elements
from collections import Counter
from core.calculation.discretization import Discretization
from gui.tabs.statistics.tree_list import TreeList



def render_html_atom_group(atom_number, atom_elements):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atoms.html'
    template = template_env.get_template( TEMPLATE_FILE )

    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated atoms",
                    "atom_number": atom_number,
                    "atom_elements": atom_elements,
    }

    return template.render(template_vars)

def render_html_atom(atom, atom_positions, atom_number, covalent_radius, atom_color_rgb):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atom.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of one atom",
                    "atom": atom,
                    "atom_positions": atom_positions,
                    "atom_number": atom_number,
                    "covalent_radius": covalent_radius,
                    "atom_color_rgb": atom_color_rgb,
    }

    return template.render(template_vars)

def render_html_cavity_center_group(surface_area, surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_center.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of all cavities",
                    "description": "a summury of all calculated center bases cavities",
                    "surface_area": surface_area,
                    "surface_volumes": surface_volumes,
                    "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)

def render_html_cavity_center(index, surface, volume, domains, cavity_count, volume_fraction):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_center.html'
    template = template_env.get_template( TEMPLATE_FILE )

    template_vars = { "title": "Summary of one cavity",
                    "description": "a summury of one calculated center bases cavity",
                    "index": index,
                    "surface": surface,
                    "volume": volume,
                    "domains": domains,
                    "cavity_count": cavity_count,
                    "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)

def render_html_cavity_surface_group(surface_volumes, volume_fraction):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_surface.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated surface based cavities",
                    "surface_volumes": surface_volumes,
                    "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)

def render_html_cavity_surface(index, volume, domains, cavity_count, volume_fraction):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_surface.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated surface based cavities",
                    "index": index,
                    "volume": volume,
                    "domains": domains,
                    "cavity_count": cavity_count,
                    "volume_fraction": volume_fraction,
    }

    return template.render(template_vars)

def render_html_cavity_domain_group(surface_area, surface_volumes, surface_volumes_fractions):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domains.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of all domains",
                    "description": "a summury of all calculated domains",
                    "surface_area": surface_area,
                    "surface_volumes": surface_volumes,
                    "surface_volumes_fractions": surface_volumes_fractions,
    }

    return template.render(template_vars)

def render_html_cavity_domain(index, domain_center, surface, volume, volume_fraction, cavities, alt_cavities):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domain.html'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of one domain",
                    "description": "a summury of one calculated domain",
                    "index": index,
                    "domain_center": domain_center,
                    "surface": surface,
                    "volume": volume,
                    "volume_fraction": volume_fraction,
                    "cavities": cavities,
                    "alt_cavities": alt_cavities,


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
        self.webview.setHtml(None)
        path = os.path.dirname(__file__)       # get dir from this file and add it to stylesheet path
        self.webview.settings().setUserStyleSheetUrl(QtCore.QUrl.fromLocalFile(path + '/templates/style.css'))
        box.addWidget(self.webview)
        self.setLayout(box)
        self.show()

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
        print dir(self.atoms)
        atom_name = self.atoms.elements[index]           # atom name from periodic systen

        atom = core.elements.names[core.elements.numbers[atom_name.upper()]]                # get full atom name
        atom_color_rgb = core.elements.colors[core.elements.numbers[atom_name.upper()]]
        atom_positions = self.atoms.positions[index]
        atom_number = core.elements.numbers[atom_name.upper()]
        covalent_radius = self.atoms.covalence_radii[index]

        #print dir(self.domains[0])

        self.webview.setHtml(render_html_atom(atom, atom_positions, atom_number, covalent_radius, atom_color_rgb))

    def show_center_cavity_group(self):
        #todo real values
        surface = 0.0
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_center is not None:
            for sf in self.cavities_center.surface_areas:
                surface += sf
            for vl in self.cavities_center.volumes:
                volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_center_group(surface, volumes, volume_fraction))

    def show_center_cavity(self, index):
        #print self.cavities_center.number # anzahl cavites

        volume_fraction = 0.0
        cavities = self.cavities_center.multicavities[index]
        domains = []
        for cavity in cavities:
            domains.append(self.discretization.discrete_to_continuous(self.domains.centers[cavity]))
        #print self.cavities_center.triangles

        surface = self.cavities_center.surface_areas[index]
        volume = self.cavities_center.volumes[index]
        cavity_count = len(cavities)

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_center(index, surface, volume, domains, cavity_count, volume_fraction))

    def show_surface_cavity_group(self):
        volumes = 0.0
        volume_fraction = 0.0
        if self.cavities_center is not None:
            for vl in self.cavities_center.volumes:
                volumes += vl

        if self.atoms.volume is not None:
            volume_fraction = (volumes/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_surface_group(volumes, volume_fraction))

    def show_surface_cavity(self, index):
        volume_fraction = 0.0
        cavities = self.cavities_surface.multicavities[index]
        domains = []

        volume = self.cavities_surface.volumes[index]
        for cavity in cavities:
            domains.append(self.discretization.discrete_to_continuous(self.domains.centers[cavity]))
        cavity_count = len(cavities)

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100

        self.webview.setHtml(render_html_cavity_surface(index, volume, domains, cavity_count, volume_fraction))

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
        domain = self.discretization.discrete_to_continuous(self.domains.centers[index])
        surface = self.domains.surface_areas[index]
        volume = self.domains.volumes[index]
        volume_fraction = 0.0
        cavities = []
        alt_cavities = []

        if self.atoms.volume is not None:
            volume_fraction = (volume/self.atoms.volume.volume)*100
        if self.domains is not None and self.cavities_center is not None and self.cavities_surface is not None:
            for cav in range(len(self.cavities_surface.multicavities)):
                for dom in self.cavities_surface.multicavities[cav]:
                    if dom == index:
                        cavities.append(cav+1)
            for cav in range(len(self.cavities_center.multicavities)):
                for dom in self.cavities_center.multicavities[cav]:
                    if dom == index:
                        alt_cavities.append(cav+1)



        #print dir(self.domains)
        #print len(self.domains.triangles)   # 96 == self.domains.number

        self.webview.setHtml(render_html_cavity_domain(index, domain, surface, volume, volume_fraction, cavities, alt_cavities))


