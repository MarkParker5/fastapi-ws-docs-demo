# FastAPI WebSocket OpenAPI Docs

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Demo project showing two approaches to documenting WebSocket endpoints in FastAPI's OpenAPI/Swagger UI** — including message schemas, interactive testing, both native and a WebSocket-tuned Swagger frontend.

Provides a custom OpenAPI schema generator that automatically includes WebSocket routes in FastAPI docs. Optionally, you can also register lists of send/receive Pydantic message models to expose each as a separate pseudo-route (`/ws::MyMessage`) with `GET`/`POST` methods — all rendered in both the native Swagger UI and a custom WebSocket-aware frontend.

---

## Features

- **WebSocket endpoints in OpenAPI** — WS routes appear in the schema alongside REST endpoints
- **Pydantic message schemas** — inbound and outbound message types are fully documented
- **Two documentation approaches** — pick the one that fits your API style (see below)
- **Native Swagger UI** at `/docs` — standard FastAPI docs with WS support layered in
- **Custom WebSocket Swagger UI** at `/wsdocs` — renders WS messages clearly and supports interactive send/receive testing directly from the browser
- **All FastAPI parameter types supported** — path, query, header, cookie, and body params on WS endpoints

---

## How It Works

### Approach 1 — WS Endpoint Responses

Declare message models as a `Union[...]` return type annotation on the WebSocket endpoint. Each union member appears as a response schema on that single endpoint entry in the docs.

```fastapi_ws_docs_demo/main.py
@app.websocket("/ws-schemas-demo/{path_param}")
async def websocket_endpoint(
    ... # any params you want, like normal endpoint
) -> Union[HelloMessage, ResponseMessage, ErrorMessage, None]:
    ...

...

app.openapi = lambda: custom_openapi(app)
```

Best for: showing all possible messages in one place, minimal setup.

### Approach 2 — Additional Message Endpoints

Each WebSocket message gets its own pseudo-REST endpoint like `/ws::MyMessage`. Outbound messages (client → server) are mapped to `POST`; inbound messages (server → client) are mapped to `GET`. 

Works with native swagger, but the custom (`/wsdocs`) frontend recognises the `::` separator and renders these as WebSocket message entries, while also adding live ws connection and message sending features.

```fastapi_ws_docs_demo/main.py
app.openapi = lambda: custom_openapi(app, inject=lambda: add_ws_message_endpoints(
    send=[HelloMessage],
    receive=[ResponseMessage, ErrorMessage],
))
```

Best for: granular per-message documentation with richer metadata.

Both approaches can be used together.

---

## Project Structure

```
fastapi_ws_docs_demo/
├── domain/                  # Example WebSocket app (no docs generation)
│   ├── models.py            # Pydantic message models
│   ├── connection_manager.py
│   └── websocket_handlers.py
├── ws_docs/                 # WebSocket docs generation
│   ├── message_endpoints.py # Generates per-message OpenAPI pseudo-endpoints
│   └── openapi_schema.py    # Extends FastAPI's OpenAPI schema generation with WS support
└── main.py                  # App entry point and example usage

static/                      # Assets for the custom WebSocket Swagger UI
templates/
└── swagger_ui.html          # Custom WebSocket-tuned Swagger UI template
```

---

## Run Demo

Requires [Poetry](https://python-poetry.org/).

```sh
poetry install && poetry run uvicorn fastapi_ws_docs_demo.main:app --reload
```

Then open:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Native Swagger UI with WebSocket support |
| `http://localhost:8000/wsdocs` | Custom WebSocket-tuned Swagger UI |

## Installation

**Soon...**

Open an issue if you need a PyPI package — fast response guaranteed.

Pull Requests with improvements are welcome.

---

## Tech Stack

[FastAPI](https://fastapi.tiangolo.com) · [Pydantic](https://docs.pydantic.dev) · [OpenAPI 3.0](https://swagger.io/specification/) · [Starlette](https://www.starlette.io) · [Uvicorn](https://www.uvicorn.org)
