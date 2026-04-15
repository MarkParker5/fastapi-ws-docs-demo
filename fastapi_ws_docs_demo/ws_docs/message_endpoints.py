"""
Generate an endpoint per WebSocket message. Alternative to declaring messages as response types on the WebSocket endpoint itself.
"""

import inspect

from pydantic import BaseModel


def add_ws_message_endpoints(
    send: list[BaseModel],
    receive: list[BaseModel],
    endpoint: str = "/ws",
    tag: str = "Web Socket",
) -> dict:  # json openapi endpoints
    """
    Generate OpenAPI endpoints per WebSocket message.
    Outbound messages (client→server) map to POST; inbound messages (server→client) map to GET.
    """
    paths: dict[str, dict] = {}
    for model in send:
        paths.update([_get_schema_for_model("post", model, endpoint, tag)])
    for model in receive:
        paths.update([_get_schema_for_model("get", model, endpoint, tag)])
    return {"paths": paths}


def _get_schema_for_model(method: str, model: BaseModel, endpoint: str, tag: str) -> tuple[str, dict]:
    # only used in add_ws_message_endpoints
    # path key is generated using '::' separator — the custom frontend identifies WS message pseudo-endpoints by this pattern
    return f"{endpoint}::{model.__name__}", {
        method: {
            "x-ws-message": True,
            "operationId": f"{method}_{endpoint}_{model.__name__}",
            "summary": inspect.cleandoc(model.__doc__ or ""),
            "description": inspect.cleandoc(model.__doc__ or ""),
            "tags": [tag],
            "requestBody": {"content": {"application/json": {"schema": model.schema()}}} if method == "post" else {},
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": model.schema(),
                        }
                    }
                }
            }
            if method == "get"
            else {},
        }
    }
