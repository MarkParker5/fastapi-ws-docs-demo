import inspect
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from fastapi import FastAPI, Response, routing
from fastapi.dependencies.utils import (
    get_body_field,
    get_dependant,
    get_flat_dependant,
    get_parameterless_sub_dependant,
    get_typed_return_annotation,
)
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.models import OpenAPI
from fastapi.openapi.utils import (
    REF_TEMPLATE,
    GenerateJsonSchema,
    get_compat_model_name_map,
    get_definitions,
    get_fields_from_routes,
    get_openapi,
    get_openapi_path,
)
from fastapi.routing import (
    APIRoute,
    Match,
)
from fastapi.utils import (
    create_cloned_field,
    create_response_field,
    generate_unique_id,
)
from pydantic import BaseModel
from pydantic.utils import (  # type: ignore[no-redef]
    lenient_issubclass as lenient_issubclass,  # noqa: F401
)
from pydantic_core.core_schema import ModelField
from starlette.routing import WebSocketRoute
from starlette.types import Scope


def custom_openapi(app: FastAPI, inject: Callable[[], dict] | None = None):
    """
    Build and cache the OpenAPI schema for the app with full WebSocket support.
    Generates the base schema for all HTTP and WS routes, then merges it with the schema provided by `inject` (intended for message-endpoint schemas from `add_ws_message_endpoints`).
    """

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI WebSocket Demo",
        version="1.0.0",
        description=(
            "This is a FastAPI WebSocket-Docs demo:<ol>"
            "<li>It adds websocket endpoints to the docs; Messages are passed through the response types - all in native docs, semi-automatically.</li>"
            "<li>It also (optionally, via the inject function and a passed list of pydantic ws messages) allows you to show each websocket message as a separate route in docs (/ws::MyMessage), marking receiving and sending with get/post methods respectively. Still in the native docs.</li>"
            "<li>It also provides customized frontend for docs that render websocket messages better, and also allows testing (sending and receiving) websocket messages directly from the docs!</li>"
            "</ol>"
            "Normal docs at <a href='/docs'>Native Docs Frontend</a> </br>"
            "Customized docs at <a href='/wsdocs'>WebSocket Docs</a>"
        ),
        routes=app.routes,
    )

    # WS:

    ws_routes: List[WebSocketRoute] = [route for route in getattr(app, "routes", []) if isinstance(route, WebSocketRoute)]

    ws_openapi = get_openapi_ws(
        title="",
        version="",
        description="",
        ws_routes=ws_routes,
    )

    openapi_schema = merge(openapi_schema.copy(), ws_openapi)
    if inject:
        openapi_schema = merge(openapi_schema.copy(), inject())
    openapi_schema["openapi"] = "3.0.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def merge(a: dict, b: dict, path=[]):
    """
    Merge two OpenAPI schemas, raising an exception if there are conflicts.
    Used to merge the main REST HTTP OpenAPI schema with the WebSocket schema.
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                if not a[key]:
                    a[key] = b[key]
                elif not b[key]:
                    pass  # keep a[key]
                else:
                    raise Exception('Conflict at "' + ".".join(path + [str(key)]) + '". Values are: "' + str(a[key]) + '" and "' + str(b[key]) + '"')
        else:
            a[key] = b[key]
    return a


def get_openapi_ws(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.1.0",
    summary: Optional[str] = None,
    description: Optional[str] = None,
    ws_routes: Sequence[WebSocketRoute],
    tags: Optional[List[Dict[str, Any]]] = None,
    servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
    terms_of_service: Optional[str] = None,
    contact: Optional[Dict[str, Union[str, Any]]] = None,
    license_info: Optional[Dict[str, Union[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generate an OpenAPI schema fragment covering all WebSocket endpoints as routes.

    Each route is wrapped with `SuperWSApiRouteWrapper` so FastAPI's standard
    `get_openapi_path` processes it alongside regular HTTP routes.
    """

    ws_routes = [SuperWSApiRouteWrapper(route) for route in ws_routes]

    info: Dict[str, Any] = {"title": title, "version": version}
    if summary:
        info["summary"] = summary
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info
    output: Dict[str, Any] = {"openapi": openapi_version, "info": info}
    if servers:
        output["servers"] = servers

    components: Dict[str, Dict[str, Any]] = {}
    ws_paths: Dict[str, Dict[str, Any]] = {}
    operation_ids: Set[str] = set()
    all_fields = get_fields_from_routes(list(ws_routes or []))
    model_name_map = get_compat_model_name_map(all_fields)
    schema_generator = GenerateJsonSchema(ref_template=REF_TEMPLATE)

    field_mapping, definitions = get_definitions(
        fields=all_fields,
        schema_generator=schema_generator,
        model_name_map=model_name_map,
        separate_input_output_schemas=True,
    )

    for ws_route in ws_routes or []:
        result = get_openapi_path(
            route=ws_route,
            operation_ids=operation_ids,
            schema_generator=schema_generator,
            model_name_map=model_name_map,
            field_mapping=field_mapping,
            separate_input_output_schemas=True,
        )
        if result:
            path, _, path_definitions = result
            if path:
                ws_paths.setdefault(ws_route.path_format, {}).update(path)
            if path_definitions:
                definitions.update(path_definitions)
    if definitions:
        components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        output["components"] = components
    output["paths"] = ws_paths
    if tags:
        output["tags"] = tags
    return jsonable_encoder(OpenAPI(**output), by_alias=True, exclude_none=True)  # type: ignore


class SuperWSApiRouteWrapper(routing.APIWebSocketRoute):
    """
    Wraps an `APIWebSocketRoute` to make it appear as a regular `APIRoute` so
    FastAPI's `get_openapi_path` processes it and includes it in the OpenAPI schema.
    """

    def __init__(self, route: routing.APIWebSocketRoute) -> None:

        self.dependency_overrides_provider = None

        super().__init__(
            path=route.path,
            endpoint=route.endpoint,
            name=route.name,
            dependencies=route.dependencies,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )

        # generate some metadata

        self.tags = [
            "Web Socket",
        ]
        self.methods = {"HEAD"}
        self.status_code = 101
        self.response_class = Response
        self.response_description = "Switching Protocols"

        self.include_in_schema = True
        self.description = self.summary = inspect.cleandoc(self.endpoint.__doc__ or "")
        self.generate_unique_id_function = generate_unique_id
        self.unique_id = self.operation_id = self.generate_unique_id_function(self)

        self.callbacks = []
        self.openapi_extra = None
        self.deprecated = False
        self._embed_body_fields = True  # _should_embed_body_fields(self._flat_dependant.body_params)

        # self.response_model_by_alias = True
        # self.response_model_exclude_unset = False
        # self.response_model_exclude_defaults = False
        # self.response_model_exclude_none = False

        return_annotation = get_typed_return_annotation(self.endpoint)
        if lenient_issubclass(return_annotation, Response):
            response_model = None
        else:
            response_model = return_annotation

        self.response_model = response_model
        if self.response_model:  # and is_body_allowed_for_status_code(self.status_code):
            self.response_field = create_response_field(
                name="Response_" + self.unique_id,
                type_=self.response_model,
                mode="serialization",
            )
            self.secure_cloned_response_field = create_cloned_field(self.response_field)
        else:
            self.response_field = None
            self.secure_cloned_response_field = None

        self._flat_dependant = get_flat_dependant(self.dependant)

        responses = {}
        i = 0
        if get_origin(self.response_model) is Union:
            for sub_model in get_args(self.response_model):
                if not issubclass(sub_model, BaseModel):
                    continue
                i += 1
                responses[2000 + i] = {
                    "model": sub_model,
                    "name": f"Response_{self.unique_id}_{i}",
                    "description": sub_model.__name__,
                    "x-ws-endpoint": True,
                    "content": {
                        "application/json": {
                            "schema": sub_model.schema(),
                        }
                    },
                }

        self.responses = responses

        response_fields = {}
        for additional_status_code, response in self.responses.items():
            assert isinstance(response, dict), "An additional response must be a dict"
            model = response.get("model")
            if model:
                response_name = response.get("name", f"Response_{additional_status_code}_{self.unique_id}")
                response_field = create_response_field(name=response_name, type_=model)
                response_fields[additional_status_code] = response_field

        if response_fields:
            self.response_fields: dict[int | str, ModelField] = response_fields
        else:
            self.response_fields = {}

        self.dependant = get_dependant(path=self.path_format, call=self.endpoint)
        for depends in self.dependencies[::-1]:
            self.dependant.dependencies.insert(
                0,
                get_parameterless_sub_dependant(depends=depends, path=self.path_format),
            )
        self.body_field = get_body_field(dependant=self.dependant, name=self.unique_id)

    def matches(self, scope: Scope) -> Tuple[Match, Scope]:
        match, child_scope = super().matches(scope)
        if match != Match.NONE:
            child_scope["route"] = self
        return match, child_scope

    @property
    def __class__(self):
        # fake isinstance to pass filters, without this the route is not recognized as an API route and is not added to the OpenAPI schema
        return APIRoute
