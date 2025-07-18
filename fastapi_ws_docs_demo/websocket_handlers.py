import json
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from .connection_manager import ConnectionManager
from .models import ErrorMessage, HelloMessage, ResponseMessage


class WebSocketHandlers:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def handle_websocket_endpoint(self, websocket: WebSocket):
        """Main WebSocket endpoint handler"""
        await self.manager.connect(websocket)

        # Send welcome message
        welcome_msg = ResponseMessage(
            message="Welcome to FastAPI WebSocket Demo! Send a hello message.",
            timestamp=datetime.now()
        )
        await self.manager.send_personal_message(welcome_msg.model_dump_json(), websocket)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    # Parse incoming message
                    message_data = json.loads(data)
                    await self._process_message(message_data, websocket)

                except json.JSONDecodeError:
                    error_msg = ErrorMessage(
                        message="Invalid JSON format",
                        timestamp=datetime.now()
                    )
                    await self.manager.send_personal_message(error_msg.model_dump_json(), websocket)

                except Exception as e:
                    error_msg = ErrorMessage(
                        message=f"Error processing message: {str(e)}",
                        timestamp=datetime.now()
                    )
                    await self.manager.send_personal_message(error_msg.model_dump_json(), websocket)

        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
            print("Client disconnected")

    async def _process_message(self, message_data: dict, websocket: WebSocket):
        """Process incoming WebSocket message"""
        message_type = message_data.get("type")

        if message_type == "hello":
            await self._handle_hello_message(message_data, websocket)
        else:
            # Handle unknown message type
            error_msg = ErrorMessage(
                message=f"Unknown message type: {message_type}",
                timestamp=datetime.now()
            )
            await self.manager.send_personal_message(error_msg.model_dump_json(), websocket)

    async def _handle_hello_message(self, message_data: dict, websocket: WebSocket):
        """Handle hello message type"""
        # Validate with Pydantic model
        hello_msg = HelloMessage(**message_data)

        # Create response
        response = ResponseMessage(
            message=f"Hello back! You said: {hello_msg.message}",
            timestamp=datetime.now()
        )

        # Send response back to client
        await self.manager.send_personal_message(response.model_dump_json(), websocket)

        # Broadcast to all clients
        broadcast_msg = ResponseMessage(
            message=f"User said hello: {hello_msg.message}",
            timestamp=datetime.now()
        )
        await self.manager.broadcast(broadcast_msg.model_dump_json())
