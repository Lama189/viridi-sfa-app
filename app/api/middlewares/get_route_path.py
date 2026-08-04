from starlette.requests import Request


def get_route_path(request: Request):
    route = request.scope.get("route")
    return route.path if route else request.url.path
