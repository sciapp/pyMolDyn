import jinja2
from PySide import QtWebKit, QtGui, QtCore
import os.path
import core.elements
from collections import Counter
from core.calculation.discretization import Discretization



def render_html_atom_group(atom_number, atom_elements):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atoms.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated atoms",
                    "atom_number": atom_number,
                    "atom_elements": atom_elements,
    }

    return template.render(template_vars)

def render_html_atom(atom, atom_positions, atom_number, covalent_radius):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'atom.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of one atom",
                    "atom": atom,
                    "atom_positions": atom_positions,
                    "atom_number": atom_number,
                    "covalent_radius": covalent_radius,
    }

    return template.render(template_vars)

def render_html_cavity_center_group(surface_area, surface_volumes, surface_volumes_fraction):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_center.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of all cavities",
                    "description": "a summury of all calculated center bases cavities",
                    "surface_area": surface_area,
                    "surface_volumes": surface_volumes,
                    "surface_volumes_fraction": surface_volumes_fraction,
    }

    return template.render(template_vars)

def render_html_cavity_center(cavity, surface, volume, domains):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_center.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of one cavity",
                    "description": "a summury of one calculated center bases cavity",
                    "cavity": cavity,
                    "surface": surface,
                    "volume": volume,
                    "domains": domains,
    }

    return template.render(template_vars)

def render_html_cavity_surface_group(surface_volumes, surface_volumes_fractions):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavities_surface.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated surface based cavities",
                    "surface_volumes": surface_volumes,
                    "surface_volumes_fractions": surface_volumes_fractions,
    }

    return template.render(template_vars)

def render_html_cavity_surface(cavity, volume, domains):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'cavity_surface.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated surface based cavities",
                    "cavity": cavity,
                    "volume": volume,
                    "domains": domains,
    }

    return template.render(template_vars)

def render_html_cavity_domain_group(surface_area, surface_volumes, surface_volumes_fractions):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domains.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of all domains",
                    "description": "a summury of all calculated domains",
                    "surface_area": surface_area,
                    "surface_volumes": surface_volumes,
                    "surface_volumes_fractions": surface_volumes_fractions,
    }

    return template.render(template_vars)

def render_html_cavity_domain(domain):
    template_loader = jinja2.FileSystemLoader( searchpath="gui/tabs/statistics/templates" )
    template_env = jinja2.Environment(loader=template_loader)

    TEMPLATE_FILE = 'domains.jinja'
    template = template_env.get_template( TEMPLATE_FILE )

    #FAVORITES = ["chocolates", "lunar eclipses", "rabbits"]
    template_vars = { "title": "Summary of atoms",
                    "description": "a summury of all calculated domains",
                    "atoms": domain
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
        atom_name = self.atoms.elements[index]           # atom name from periodic systen
        atom = core.elements.names[core.elements.numbers[atom_name.upper()]]        # get full atom name
        atom_positions = self.atoms.positions[index]
        atom_number = core.elements.numbers[atom_name.upper()]
        covalent_radius = self.atoms.covalence_radii[index]
        #cavities = []
        #cavities_alt = []
        #domains = []
        #print dir(self.atoms)
        #print self.domains.volumes
        #print self.cavities_center.multicavities
        #print self.cavities_surface.multicavities

        self.webview.setHtml(render_html_atom(atom, atom_positions, atom_number, covalent_radius))

    def show_center_cavity_group(self):
        #todo real values
        surface_area = 0.0
        surface_volumes = 0.0
        surface_volumes_fractions = 0.0

        self.webview.setHtml(render_html_cavity_center_group(surface_area, surface_volumes, surface_volumes_fractions))

    def show_center_cavity(self, index):
        #print self.cavities_center.number # anzahl cavites

        cavities = self.cavities_center.multicavities[index]
        domains = []
        for cavity in cavities:
            domains.append(self.discretization.discrete_to_continuous(self.domains.centers[cavity]))
        #print self.cavities_center.triangles

        surface = self.cavities_center.surface_areas[index]
        volume = self.cavities_center.volumes[index]
        self.webview.setHtml(render_html_cavity_center(index, surface, volume, domains))

    def show_surface_cavity_group(self):
        #todo real values
        surface_volumes = 0.0
        surface_volumes_fractions = 0.0

        self.webview.setHtml(render_html_cavity_surface_group(surface_volumes, surface_volumes_fractions))

    def show_surface_cavity(self, index):
        cavities = self.cavities_surface.multicavities[index]
        domains = []

        for cavity in cavities:
            domains.append(self.discretization.discrete_to_continuous(self.domains.centers[cavity]))
        volume = self.cavities_surface.volumes[index]
        self.webview.setHtml(render_html_cavity_surface(index, volume, domains))

    def show_domain_group(self):
        #todo real values
        surface_area = 0.0
        surface_volumes = 0.0
        surface_volumes_fractions = 0.0

        self.webview.setHtml(render_html_cavity_domain_group(surface_area, surface_volumes, surface_volumes_fractions))

    def show_domain(self, index):
        domain = self.domains.centers[index]
        print domain[0], domain[1], domain[2]
        #domain_position = self.domains.position[index]

        self.webview.setHtml(render_html_cavity_domain(index))


