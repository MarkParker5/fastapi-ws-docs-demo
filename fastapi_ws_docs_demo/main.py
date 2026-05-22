from typing import Optional, Union

import uvicorn
from fastapi import (
    Body,
    Cookie,
    FastAPI,
    Header,
    Path,
    Query,
    WebSocket,
)
from fastapi.openapi import docs
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles

from fastapi_ws_docs_demo.domain.connection_manager import ConnectionManager
from fastapi_ws_docs_demo.domain.models import (
    BodyModel,
    ErrorMessage,
    HelloMessage,
    ResponseMessage,
)
from fastapi_ws_docs_demo.domain.websocket_handlers import WebSocketHandlers
from fastapi_ws_docs_demo.ws_docs.message_endpoints import add_ws_message_endpoints
from fastapi_ws_docs_demo.ws_docs.openapi_schema import custom_openapi

app = FastAPI(
    title="FastAPI WebSocket Demo",
    version="1.0.0",
    docs_url=None,
    description=(
        "This is a FastAPI WebSocket-Docs demo:<ol>"
        "<li>It adds websocket endpoints to the docs; Messages are passed through the response types - all in native docs, semi-automatically.</li>"
        "<li>It also (optionally, via the inject function and a passed list of pydantic ws messages) allows you to show each websocket message as a separate route in docs (/ws::MyMessage), marking receiving and sending with get/post methods respectively. Still in the native docs.</li>"
        "<li>It also provides customized frontend for docs that render websocket messages better, and also allows testing (sending and receiving) websocket messages directly from the docs!</li>"
        "</ol>"
        "Normal docs at <a href='/docs'>Native Docs Frontend</a> </br>"
        "Customized docs at <a href='/wsdocs'>WebSocket Docs</a>"
    ),
)
manager = ConnectionManager()
ws_handlers = WebSocketHandlers(manager)

# DOCS

app.openapi = lambda: custom_openapi(
    app,
    inject=lambda: add_ws_message_endpoints(
        # add ws messages as standalone endpoints (alternative to ws endpoint responses)
        send=[HelloMessage],
        receive=[ResponseMessage, ErrorMessage],
    ),
)  # Set custom OpenAPI schema


@app.get("/docs", include_in_schema=True)
def native_swagger_ui_html():
    return docs.get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="FastAPI WebSocket Demo - API",
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian",
            "docExpansion": "none",
        },
    )


# Mount static files for custom ws-tuned Swagger UI

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/wsdocs", include_in_schema=True)
def custom_ws_swagger_ui_html():
    with open("templates/swagger_ui.html") as f:
        return HTMLResponse(content=f.read())


# ENDPOINTS


@app.get("/")
async def read_root():
    """Plain HTTP endpoint for testing purposes."""
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}


api_router = APIRouter(tags=["API"])  # routers are just for testing purposes; they don't affect ws docs work.


@api_router.get("/api")
async def read_api():
    """Plain HTTP endpoint for testing purposes."""
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}


ws_router = APIRouter(
    tags=["WS"]
)  # tags don't work with ws endpoints; they always have Web Sockets tag unless other is passed to the schema generator; a separate ws router is not required for docs to work


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Primary demo WebSocket endpoint. Accepts JSON messages with type 'hello' and sends back response or error messages."""
    await ws_handlers.handle_websocket_endpoint(websocket)


@ws_router.websocket("/ws-schemas-demo/{path_param}")
async def websocket_endpoint_2(
    websocket: WebSocket,
    path_param: int = Path(..., description="Path parameter"),
    query_param: Optional[str] = Query(None, description="Query parameter"),
    header_param: Optional[str] = Header(None, convert_underscores=False),
    cookie_param: Optional[str] = Cookie(None),
    body_param: BodyModel = Body(...),
    # form_param: Optional[str] = Form(None),
    # file_param: Optional[UploadFile] = File(None)
) -> Union[  # this will display all message schemas as responses
    HelloMessage, ResponseMessage, ErrorMessage, None
]:
    """Demo WebSocket endpoint showing that WS docs work with all FastAPI parameter types: path, query, header, cookie, and body."""
    pass


app.include_router(api_router)
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
