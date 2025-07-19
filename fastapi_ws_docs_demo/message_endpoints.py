from pydantic import BaseModel


def get_schema_for_model(method: str, model: BaseModel, endpoint: str, tag: str) -> tuple[str, dict]:
    return f'{endpoint}::{model.__name__}', {
        method: {
            "operationId": f"{method}_{endpoint}_{model.__name__}",
            "summary": f"{method.capitalize()} {model.__name__}",
            "description": f"{method.capitalize()} a {model.__name__} message",
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
    schema: dict[str, dict] = {}
    for model in send:
        schema.update(get_schema_for_model("post", model, endpoint, tag))
    for model in receive:
        schema.update(*get_schema_for_model("get", model, endpoint, tag))
    return schema
