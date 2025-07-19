from typing import List

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.routing import WebSocketRoute

from .openapi_ws_utils import get_openapi_ws


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with WebSocket support"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI WebSocket Demo",
        version="1.0.0",
        description="This is a FastAPI WebSocket demo with custom OpenAPI schema",
        routes=app.routes,
    )

    # WS:

    ws_routes: List[WebSocketRoute] = [
        route for route in getattr(app, "routes", [])
        if isinstance(route, WebSocketRoute)
    ]

    ws_openapi = get_openapi_ws(
        title="",
        version="",
        description="",
        ws_routes=ws_routes,
    )

    openapi_schema = merge(openapi_schema.copy(), ws_openapi.copy())
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def merge(a: dict, b: dict, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                if not a[key]:
                    a[key] = b[key]
                elif not b[key]:
                    pass # keep a[key]
                else:
                    raise Exception('Conflict at "' + '.'.join(path + [str(key)]) + '". Values are: "' + str(a[key]) + '" and "' + str(b[key]) + '"')
        else:
            a[key] = b[key]
    return a
