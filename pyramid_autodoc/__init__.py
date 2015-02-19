"""
Sphinx extension that is able to convert pyramid routes to rst
"""
import sys

import docutils
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from pyramid.paster import bootstrap
from pyramid.compat import PY3
from pyramid.compat import string_types
from pyramid.config import Configurator
from pyramid_autodoc.utils import get_route_data, ANY_KEY
from sphinxcontrib.autohttp.common import http_directive
from sphinxcontrib import httpdomain
from docutils.statemachine import ViewList
from sphinx import addnodes
from sphinx.util.nodes import nested_parse_with_titles
import re


class RouteDirective(Directive):
    """ Route directive.

    Injects sections in the documentation about the routes registered in the
    given module.

    Usage, in a sphinx documentation::

        .. pyramid-autodoc:: development.ini
            :skip: ^/status
            :match: ^/v1
    """
    has_content = True
    required_arguments = 1
    option_spec = {
        'match-path': directives.unchanged,
        'match-module': directives.unchanged,
        'skip-path': directives.unchanged,
        'match-module': directives.unchanged,
        'format': directives.unchanged,
        'link-code': directives.flag,
        'link-code-pattern': directives.unchanged,
    }

    def __init__(self, *args, **kwargs):
        super(RouteDirective, self).__init__(*args, **kwargs)
        self.env = self.state.document.settings.env

    def matches_pattern(self, filters, value):
        if filters is not None:
            for path_filter in filters:
                if re.match(path_filter, value):
                    return True

        return False

    def get_routes(self, ini_file, path_blacklist=None, path_whitelist=None,
                   module_blacklist=None, module_whitelist=None):
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
            for name, pattern, view, method, docs, src in route_data:
                if path_blacklist:
                    if self.matches_pattern(path_blacklist, pattern):
                        continue

                if path_whitelist:
                    if not self.matches_pattern(path_whitelist, pattern):
                        continue

                if module_blacklist:
                    if self.matches_pattern(module_blacklist, view):
                        continue

                if module_whitelist:
                    if not self.matches_pattern(module_whitelist, view):
                        continue

                mapped_routes.append({
                    'name': name,
                    'pattern': pattern,
                    'view': view,
                    'method': method,
                    'docs': trim(docs),
                    'view_module': src.get('module_name'),
                    'view_callable': src.get('callable_name'),
                    'source_lines': src.get('source_lines'),
                })

        return mapped_routes

    def make_httpdomain_rst(self, mapped_routes):
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()

        routes = {}

        for route in mapped_routes:
            if route['method'] == ANY_KEY:
                method = 'any'
            else:
                method = route['method']

            directives = http_directive(
                method,
                route['pattern'],
                route['docs'],
            )

            routes[(method, route['pattern'])] = route

            for line in directives:
                result.append(line, '<autopyramid>')

        nested_parse_with_titles(self.state, result, node)

        for objnode in node.traverse(addnodes.desc):
            if objnode.get('domain') != 'http':
                continue

            for signode in objnode:
                if not isinstance(signode, addnodes.desc_signature):
                    continue
                method = signode.get('method')
                path = signode.get('path')
                mapped_route = routes.get((method, path))
                if not method or not path or not mapped_route:
                    continue

                xref_node = self._make_view_source_xref(mapped_route)
                if not xref_node:
                    continue

                xref_node += nodes.inline('', '[source]',
                                          classes=['viewcode-link'])

                source_node = addnodes.only(expr='html')
                source_node += xref_node

                signode += source_node

        return node.children

    def make_custom_rst(self, mapped_routes):
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
                    if isinstance(text, string_types):
                        text_node = nodes.Text(text)
                    else:
                        text_node = text

                    node = nodes.paragraph('', '', text_node)
                    row += nodes.entry('', node)

                return row

            view_node = self._make_view_source_xref(mapped_route)
            if view_node:
                view_node += nodes.Text(mapped_route['view'])
            else:
                view_node = mapped_route['view']

            body += get_row('Module', view_node)
            body += get_row('Request Method', mapped_route['method'])
            body += get_row('Route Name', mapped_route['name'])

            route_node.append(real_table)

            if mapped_route['docs']:
                route_node += rst2node(
                    mapped_route['view'], mapped_route['docs']
                )

            custom_nodes.append(route_node)

        return custom_nodes

    def _make_view_source_xref(self, mapped_route):
        if 'link-code' not in self.options or \
                not mapped_route['view_callable'] or \
                not mapped_route['view_module'] or \
                not mapped_route['source_lines']:
            return

        env = self.state.document.settings.env
        link_code_pattern = self.options.get('link-code-pattern')

        if link_code_pattern:
            filepath = mapped_route['view_module'].replace('.', '/') + '.py'
            uri = link_code_pattern.format(
                file=filepath,
                lineno_start=mapped_route['source_lines'][0],
                lineno_end=mapped_route['source_lines'][1],
            )
            xref_node = nodes.reference('', '', internal=False, refuri=uri)

        else:
            if 'sphinx.ext.viewcode' not in env.config.extensions:
                return

            source_page = (
                '_modules/' + mapped_route['view_module'].replace('.', '/'))

            xref_node = addnodes.pending_xref(
                '', reftype='viewcode', refdomain='std', refexplicit=False,
                reftarget=source_page,
                refid=mapped_route['view_callable'],
                refdoc=env.docname)

        return xref_node

    def run(self):
        ini_file = self.arguments[0]
        fmt = self.options.get('format', 'custom')
        path_blacklist = self.options.get('skip-path', '').split() or None
        path_whitelist = self.options.get('match-path', '').split() or None
        module_blacklist = self.options.get('skip-module', '').split() or None
        module_whitelist = self.options.get('match-module', '').split() or None

        routes = self.get_routes(
            ini_file,
            path_blacklist=path_blacklist,
            path_whitelist=path_whitelist,
            module_blacklist=module_blacklist,
            module_whitelist=module_whitelist,
        )

        if fmt == 'custom':
            return self.make_custom_rst(routes)
        elif fmt == 'httpdomain':
            return self.make_httpdomain_rst(routes)
        else:
            raise Exception('Unsupported format %s' % fmt)


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
    if 'http' not in app.domains:
        httpdomain.setup(app)

    app.add_directive('autopyramid', RouteDirective)
