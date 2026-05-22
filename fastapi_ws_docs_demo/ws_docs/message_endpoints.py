"""
Generate an endpoint per WebSocket message. Alternative to declaring messages as response types on the WebSocket endpoint itself.
"""

import inspect

from pydantic import BaseModel


def add_ws_message_endpoints(
    send: list[type[BaseModel]],
    receive: list[type[BaseModel]],
    endpoint: str = "/ws",
    tag: str = "Web Socket",
) -> dict:  # json openapi endpoints
    """
    Generate OpenAPI endpoints per WebSocket message.
    Outbound messages (client→server) map to POST; inbound messages (server→client) map to GET.
    """
    paths: dict[str, dict] = {}
    components: dict[str, dict] = {}
    for model in send:
        path_key, path_val, defs = _get_schema_for_model("post", model, endpoint, tag)
        paths[path_key] = path_val
        components.update(defs)
    for model in receive:
        path_key, path_val, defs = _get_schema_for_model("get", model, endpoint, tag)
        paths[path_key] = path_val
        components.update(defs)
    result: dict = {"paths": paths}
    if components:
        result["components"] = {"schemas": components}
    return result


def _get_schema_for_model(method: str, model: type[BaseModel], endpoint: str, tag: str) -> tuple[str, dict, dict]:
    # path key is generated using '::' separator — the custom frontend identifies WS message pseudo-endpoints by this pattern
    raw_schema = model.model_json_schema()
    defs: dict = raw_schema.pop("$defs", {})
    # rewrite local $defs refs to top-level components/schemas refs (both in schema and in defs themselves)
    defs = _rewrite_refs(defs)
    schema_str = _rewrite_refs(raw_schema)
    return (
        f"{endpoint}::{model.__name__}",
        {
            method: {
                "x-ws-message": True,
                "operationId": f"{method}_{endpoint}_{model.__name__}",
                "summary": inspect.cleandoc(model.__doc__ or ""),
                "description": inspect.cleandoc(model.__doc__ or ""),
                "tags": [tag],
                "requestBody": {"content": {"application/json": {"schema": schema_str}}} if method == "post" else {},
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": schema_str,
                            }
                        }
                    }
                }
                if method == "get"
                else {},
            }
        },
        defs,
    )


def _rewrite_refs(obj: object) -> object:
    """Recursively rewrite '#/$defs/Foo' refs to '#/components/schemas/Foo'."""
    if isinstance(obj, dict):
        return {k: (_rewrite_refs(v) if k != "$ref" else v.replace("#/$defs/", "#/components/schemas/")) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_refs(item) for item in obj]
    return obj
