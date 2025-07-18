from typing import List

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_websocket_endpoints(app: FastAPI) -> List[dict]:
    """Get all WebSocket endpoints from the FastAPI app"""
    websocket_endpoints = []

    for route in app.routes:
        if not hasattr(route, 'path') or not hasattr(route, 'endpoint'):
            continue
        if not (hasattr(route, 'route_class') and 'websocket' in str(route.route_class).lower()) and \
           not route.path.startswith('/ws') and \
           'websocket' not in str(route.endpoint).lower():
            continue

        description = getattr(route.endpoint, '__doc__', None) or f"WebSocket endpoint at {route.path}"
        websocket_endpoints.append({
            "path": route.path,
            "endpoint": route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(route.endpoint),
            "description": description.strip()
        })

    return websocket_endpoints


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

    # Ensure OpenAPI version is set
    openapi_schema["openapi"] = "3.0.2"

    # Add WebSocket routes to the schema automatically
    ws_endpoints = get_websocket_endpoints(app)

    for endpoint in ws_endpoints:
        # Default responses
        default_responses = {
            "101": {
                "description": "Switching Protocols - WebSocket connection established"
            },
            "400": {
                "description": "Bad Request - Invalid WebSocket request"
            }
        }

        openapi_schema["paths"][endpoint["path"]] = {
            "get": {
                "summary": endpoint['endpoint'].replace('_', ' ').title(),
                "description": endpoint['description'],
                "tags": ["WebSocket"],
                "operationId": f"websocket_connect_{endpoint['endpoint']}",
                "responses": default_responses
            }
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
