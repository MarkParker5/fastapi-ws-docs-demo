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

from fastapi_ws_docs_demo.connection_manager import ConnectionManager
from fastapi_ws_docs_demo.message_endpoints import add_ws_message_endpoints
from fastapi_ws_docs_demo.models import (
    BodyModel,
    ErrorMessage,
    HelloMessage,
    ResponseMessage,
)
from fastapi_ws_docs_demo.openapi_schema import custom_openapi
from fastapi_ws_docs_demo.websocket_handlers import WebSocketHandlers

app = FastAPI(title="FastAPI WebSocket Demo", version="1.0.0", docs_url=None)
app.openapi = lambda: custom_openapi(app, inject = lambda: add_ws_message_endpoints(
    send = [
        HelloMessage
    ],
    receive = [
        ResponseMessage,
        ErrorMessage
    ]
)) # Set custom OpenAPI schema

# Mount static files for custom Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize connection manager and handlers
manager = ConnectionManager()
ws_handlers = WebSocketHandlers(manager)

def get_swagger_ui_html():
    return docs.get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="FastAPI WebSocket Demo - API",
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian",
            "docExpansion": "none",
        },
    )

@app.get("/docs", include_in_schema=True)
def native_swagger_ui_html():
    return get_swagger_ui_html()

@app.get("/wsdocs", include_in_schema=True)
def custom_ws_swagger_ui_html():
    with open("templates/swagger_ui.html") as f:
        return HTMLResponse(content=f.read())

@app.get("/")
async def read_root():
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}

api_router = APIRouter(tags=['API'])

@api_router.get("/api")
async def read_api():
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}

ws_router = APIRouter(tags=["WS"])

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time hello world communication. Send JSON messages with type 'hello' and receive responses."""
    await ws_handlers.handle_websocket_endpoint(websocket)

@ws_router.websocket("/ws-schemas-demo/{path_param}")
async def websocket_endpoint_2(
    websocket: WebSocket,
    path_param: int = Path(..., description='Path parameter'),
    query_param: Optional[str] = Query(None, description='Query parameter'),
    header_param: Optional[str] = Header(None, convert_underscores=False),
    cookie_param: Optional[str] = Cookie(None),
    body_param: BodyModel = Body(...),
    # form_param: Optional[str] = Form(None),
    # file_param: Optional[UploadFile] = File(None)
) -> Union[
    HelloMessage,
    ResponseMessage,
    ErrorMessage,
    None
]:
    """WS with some parameters"""
    pass

app.include_router(api_router)
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
# TODO:
# 1. proper urls for ws endpoints
# 2. custom swagger UI like here:
# https://github.com/OAI/OpenAPI-Specification/issues/55#issuecomment-1975876095
