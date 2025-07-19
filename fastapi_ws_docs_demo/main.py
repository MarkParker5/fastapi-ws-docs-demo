from typing import Optional

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
from fastapi.routing import APIRouter
from typing_extensions import Union

from fastapi_ws_docs_demo.connection_manager import ConnectionManager
from fastapi_ws_docs_demo.models import (
    BodyModel,
    ErrorMessage,
    HelloMessage,
    ResponseMessage,
)
from fastapi_ws_docs_demo.openapi_schema import custom_openapi
from fastapi_ws_docs_demo.websocket_handlers import WebSocketHandlers

app = FastAPI(title="FastAPI WebSocket Demo", version="1.0.0", docs_url=None)
app.openapi = lambda: custom_openapi(app) # Set custom OpenAPI schema

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

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    return get_swagger_ui_html()

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
    await ws_handlers.handle_websocket_endpoint(websocket)

app.include_router(api_router)
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
