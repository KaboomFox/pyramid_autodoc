"""
Sphinx extension that is able to convert pyramid routes to rst
"""
import sys

import docutils
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from pyramid.paster import bootstrap
from pyramid.compat import PY3
from pyramid.config import Configurator
from pyramid_autodoc.utils import get_route_data


class RouteDirective(Directive):
    """ Route directive.

    Injects sections in the documentation about the routes registered in the
    given module.

    Usage, in a sphinx documentation::

        .. pyramid-autodoc::
            :ini: development.ini
    """
    has_content = True
    option_spec = {'ini': directives.unchanged}
    domain = 'pyramid'
    doc_field_types = []

    def __init__(self, *args, **kwargs):
        super(RouteDirective, self).__init__(*args, **kwargs)
        self.env = self.state.document.settings.env

    def run(self):
        ini_file = self.options.get('ini')
        env = bootstrap(ini_file)
        registry = env['registry']
        config = Configurator(registry=registry)
        mapper = config.get_routes_mapper()

        try:  # only supported in pyramid 1.6
            routes = mapper.get_routes(include_static=True)
        except:
            routes = mapper.get_routes()

        mapped_routes = []

        for route in routes:
            route_data = get_route_data(route, registry)

            for name, pattern, view, method, docs in route_data:
                mapped_routes.append({
                    'name': name,
                    'pattern': pattern,
                    'view': view,
                    'method': method,
                    'docs': trim(docs),
                })

        custom_nodes = []

        for mapped_route in mapped_routes:
            env = self.state.document.settings.env
            route_id = "route-%d" % env.new_serialno('route')
            route_node = nodes.section(ids=[route_id])
            title = mapped_route['pattern']

            route_node += nodes.title(text=title)

            real_table = nodes.table('')
            group = nodes.tgroup('', cols=2)
            real_table += group
            group += nodes.colspec('', colwidth=10)
            group += nodes.colspec('', colwidth=90)
            body = nodes.tbody('')
            group += body

            def get_row(*column_texts):
                row = nodes.row('')
                for text in column_texts:
                    node = nodes.paragraph('', '', nodes.Text(text))
                    row += nodes.entry('', node)

                return row

            body += get_row('Module', mapped_route['view'])
            body += get_row('Request Method', mapped_route['method'])
            body += get_row('Route Name', mapped_route['name'])

            route_node.append(real_table)

            if mapped_route['docs']:
                route_node += rst2node(
                    mapped_route['view'], mapped_route['docs']
                )

            custom_nodes.append(route_node)

        return custom_nodes


def trim(docstring):
    """
    Remove the tabs to spaces, and remove the extra spaces / tabs that are in
    front of the text in docstrings.

    Implementation taken from http://www.python.org/dev/peps/pep-0257/
    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    res = '\n'.join(trimmed)
    if not PY3 and not isinstance(res, unicode):
        res = res.decode('utf8')
    return res


class Env(object):
    temp_data = {}
    docname = ''


def rst2node(doc_name, data):
    """Converts a reStructuredText into its node
    """
    if not data:
        return
    parser = docutils.parsers.rst.Parser()
    document = docutils.utils.new_document('<%s>' % doc_name)
    document.settings = docutils.frontend.OptionParser().get_default_values()
    document.settings.tab_width = 4
    document.settings.pep_references = False
    document.settings.rfc_references = False
    document.settings.env = Env()
    parser.parse(data, document)
    if len(document.children) == 1:
        return document.children[0]
    else:
        par = docutils.nodes.paragraph()
        for child in document.children:
            par += child
        return par


def setup(app):
    """Hook the directives when Sphinx ask for it."""
    app.add_directive('pyramid-autodoc', RouteDirective)
