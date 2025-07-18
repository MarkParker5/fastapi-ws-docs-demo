import uvicorn
from fastapi import FastAPI, WebSocket

from fastapi_ws_docs_demo.connection_manager import ConnectionManager
from fastapi_ws_docs_demo.openapi_schema import custom_openapi, get_websocket_endpoints
from fastapi_ws_docs_demo.websocket_handlers import WebSocketHandlers

# Create FastAPI app
app = FastAPI(title="FastAPI WebSocket Demo", version="1.0.0")

# Initialize connection manager and handlers
manager = ConnectionManager()
ws_handlers = WebSocketHandlers(manager)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

@app.get("/")
async def read_root():
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time hello world communication. Send JSON messages with type 'hello' and receive responses."""
    await ws_handlers.handle_websocket_endpoint(websocket)

@app.websocket("/ws-2")
async def websocket_endpoint(websocket: WebSocket, param1: str, param2: int):
    """WS with some parameters"""
    await ws_handlers.handle_websocket_endpoint(websocket)

if __name__ == "__main__":
    # Print all WebSocket endpoints
    ws_endpoints = get_websocket_endpoints(app)
    print("WebSocket Endpoints:")
    print("=" * 50)
    for endpoint in ws_endpoints:
        print(f"Path: {endpoint['path']}")
        print(f"Endpoint: {endpoint['endpoint']}")
        print(f"Description: {endpoint['description']}")
        print("-" * 30)

    if not ws_endpoints:
        print("No WebSocket endpoints found")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
