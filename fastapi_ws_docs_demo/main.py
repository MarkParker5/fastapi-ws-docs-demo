import json
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

app = FastAPI(title="FastAPI WebSocket Demo", version="1.0.0")

# Pydantic models for WebSocket messages
class HelloMessage(BaseModel):
    type: str = "hello"
    message: str
    timestamp: datetime | None = None

class ResponseMessage(BaseModel):
    type: str = "response"
    message: str
    timestamp: datetime | None = None

class ErrorMessage(BaseModel):
    type: str = "error"
    message: str
    timestamp: datetime | None = None

# Connection manager to handle multiple WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

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

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI WebSocket Demo",
        version="1.0.0",
        description="This is a FastAPI WebSocket demo with custom OpenAPI schema",
        routes=app.routes,
    )

    # Add WebSocket routes to the schema automatically
    ws_endpoints = get_websocket_endpoints(app)

    for endpoint in ws_endpoints:
        openapi_schema["paths"][endpoint["path"]] = {
            "get": {
                "x-websocket-method": "CONNECT",
                "summary": endpoint['endpoint'].replace('_', ' ').title(),
                "description": endpoint["description"],
                "tags": ["WebSocket"],
                "responses": {
                    "200": {
                        "description": "WebSocket connection established"
                    }
                }
            }
        }

    app.openapi_schema = openapi_schema

    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
async def read_root():
    return {"message": "FastAPI WebSocket Demo", "docs": "/docs", "websocket": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time hello world communication. Send JSON messages with type 'hello' and receive responses."""
    await manager.connect(websocket)

    # Send welcome message
    welcome_msg = ResponseMessage(
        message="Welcome to FastAPI WebSocket Demo! Send a hello message.",
        timestamp=datetime.now()
    )
    await manager.send_personal_message(welcome_msg.model_dump_json(), websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                # Parse incoming message
                message_data = json.loads(data)

                if message_data.get("type") == "hello":
                    # Validate with Pydantic model
                    hello_msg = HelloMessage(**message_data)

                    # Create response
                    response = ResponseMessage(
                        message=f"Hello back! You said: {hello_msg.message}",
                        timestamp=datetime.now()
                    )

                    # Send response back to client
                    await manager.send_personal_message(response.model_dump_json(), websocket)

                    # Broadcast to all clients
                    broadcast_msg = ResponseMessage(
                        message=f"User said hello: {hello_msg.message}",
                        timestamp=datetime.now()
                    )
                    await manager.broadcast(broadcast_msg.model_dump_json())

                else:
                    # Handle unknown message type
                    error_msg = ErrorMessage(
                        message=f"Unknown message type: {message_data.get('type')}",
                        timestamp=datetime.now()
                    )
                    await manager.send_personal_message(error_msg.model_dump_json(), websocket)

            except json.JSONDecodeError:
                error_msg = ErrorMessage(
                    message="Invalid JSON format",
                    timestamp=datetime.now()
                )
                await manager.send_personal_message(error_msg.model_dump_json(), websocket)

            except Exception as e:
                error_msg = ErrorMessage(
                    message=f"Error processing message: {str(e)}",
                    timestamp=datetime.now()
                )
                await manager.send_personal_message(error_msg.model_dump_json(), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

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

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
