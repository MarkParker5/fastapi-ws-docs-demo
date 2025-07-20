import inspect

from pydantic import BaseModel


def get_schema_for_model(method: str, model: BaseModel, endpoint: str, tag: str) -> tuple[str, dict]:
    return f'{endpoint}::{model.__name__}', {
        method: {
            "x-ws-message": True,
            "operationId": f"{method}_{endpoint}_{model.__name__}",
            "summary": inspect.cleandoc(model.__doc__ or ''),
            "description": inspect.cleandoc(model.__doc__ or ''),
            "tags": [tag],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": model.schema()
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "OK"
                }
            }
        }
    }

def add_ws_message_endpoints(
    send: list[BaseModel],
    receive: list[BaseModel],
    endpoint: str ="/ws",
    tag: str = "Web Socket",
) -> dict: # json openapi endpoints
    paths: dict[str, dict] = {}
    for model in send:
        paths.update([get_schema_for_model("post", model, endpoint, tag)])
    for model in receive:
        paths.update([get_schema_for_model("get", model, endpoint, tag)])
    return {
        "paths": paths
    }
