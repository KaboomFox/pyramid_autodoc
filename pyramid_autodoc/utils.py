from pyramid.static import static_view
from pyramid.interfaces import (
    IRouteRequest,
    IViewClassifier,
    IView,
)
from pyramid.config import not_
from pyramid.compat import string_types
from zope.interface import Interface


ANY_KEY = '*'
UNKNOWN_KEY = '<unknown>'


def _get_pattern(route):
    pattern = route.pattern

    if not pattern.startswith('/'):
        pattern = '/%s' % pattern
    return pattern


def _get_request_methods(route_request_methods, view_request_methods):
    excludes = set()

    if route_request_methods:
        route_request_methods = set(route_request_methods)

    if view_request_methods:
        view_request_methods = set(view_request_methods)

        for method in view_request_methods.copy():
            if method.startswith('!'):
                view_request_methods.remove(method)
                excludes.add(method[1:])

    has_route_methods = route_request_methods is not None
    has_view_methods = len(view_request_methods) > 0
    has_methods = has_route_methods or has_view_methods

    if has_route_methods is False and has_view_methods is False:
        request_methods = [ANY_KEY]
    elif has_route_methods is False and has_view_methods is True:
        request_methods = view_request_methods
    elif has_route_methods is True and has_view_methods is False:
        request_methods = route_request_methods
    else:
        request_methods = route_request_methods.intersection(
            view_request_methods
        )

    request_methods = set(request_methods).difference(excludes)

    if has_methods and not request_methods:
        request_methods = '<route mismatch>'
    elif request_methods:
        if excludes and request_methods == set([ANY_KEY]):
            for exclude in excludes:
                request_methods.add('!%s' % exclude)

        request_methods = ','.join(sorted(request_methods))

    return request_methods


def _get_view_module(view_callable):
    if view_callable is None:
        return UNKNOWN_KEY, ''

    if hasattr(view_callable, '__name__'):
        if hasattr(view_callable, '__original_view__'):
            original_view = view_callable.__original_view__
        else:
            original_view = None

        if isinstance(original_view, static_view):
            raise Exception()

            # skip static views
            if original_view.package_name is not None:
                return '%s:%s' % (
                    original_view.package_name,
                    original_view.docroot
                ), ''
            else:
                return original_view.docroot
        else:
            view_name = view_callable.__name__
    else:
        # Currently only MultiView hits this,
        # we could just not run _get_view_module
        # for them and remove this logic
        view_name = str(view_callable)

    view_module = '%s.%s' % (
        view_callable.__module__,
        view_name,
    )

    # If pyramid wraps something in wsgiapp or wsgiapp2 decorators
    # that is currently returned as pyramid.router.decorator, lets
    # hack a nice name in:
    if view_module == 'pyramid.router.decorator':
        view_module = '<wsgiapp>'

    return view_module, view_callable.__doc__


def get_route_data(route, registry):
    pattern = _get_pattern(route)

    request_iface = registry.queryUtility(
        IRouteRequest,
        name=route.name
    )

    route_request_methods = None
    view_request_methods_order = []
    view_request_methods = {}
    view_callable = None

    route_intr = registry.introspector.get(
        'routes', route.name
    )

    if request_iface is None:
        return [
            (route.name, _get_pattern(route), UNKNOWN_KEY, ANY_KEY)
        ]

    view_callable = registry.adapters.lookup(
        (IViewClassifier, request_iface, Interface),
        IView,
        name='',
        default=None
    )

    try:
        view_module, view_docs = _get_view_module(view_callable)
    except:
        return []

    # Introspectables can be turned off, so there could be a chance
    # that we have no `route_intr` but we do have a route + callable
    if route_intr is None:
        view_request_methods[view_module] = []
        view_request_methods_order.append(view_module)
    else:
        if route_intr.get('static', False) is True:
            return [
                (route.name, route_intr['external_url'], UNKNOWN_KEY, ANY_KEY)
            ]

        route_request_methods = route_intr['request_methods']
        view_intr = registry.introspector.related(route_intr)

        if view_intr:
            for view in view_intr:
                request_method = view.get('request_methods')

                if view.get('attr') is not None:
                    view_callable = getattr(view['callable'], view['attr'])
                    view_module, view_docs = _get_view_module(view_callable)

                if request_method is not None:
                    view_callable = view['callable']

                    view_module, view_docs = _get_view_module(view_callable)

                    if view_module not in view_request_methods:
                        view_request_methods[view_module] = []
                        view_request_methods_order.append(view_module)

                    if isinstance(request_method, string_types):
                        request_method = (request_method,)
                    elif isinstance(request_method, not_):
                        request_method = ('!%s' % request_method.value,)

                    view_request_methods[view_module].extend(request_method)
                else:
                    if view_module not in view_request_methods:
                        view_request_methods[view_module] = []
                        view_request_methods_order.append(view_module)

        else:
            view_request_methods[view_module] = []
            view_request_methods_order.append(view_module)

    final_routes = []

    for view_module in view_request_methods_order:
        methods = view_request_methods[view_module]
        request_methods = _get_request_methods(
            route_request_methods,
            methods
        )

        final_routes.append((
            route.name,
            pattern,
            view_module,
            request_methods,
            view_docs,
        ))

    return final_routes
