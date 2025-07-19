from typing import Any, Dict, List, Optional, Sequence, Set, Union

from fastapi.encoders import jsonable_encoder
from fastapi.openapi.models import OpenAPI
from fastapi.openapi.utils import (
    REF_TEMPLATE,
    GenerateJsonSchema,
    get_compat_model_name_map,
    get_definitions,
    get_fields_from_routes,
    get_openapi_path,
)
from starlette.routing import WebSocketRoute

from .super_wrapper import SuperWSApiRouteWrapper


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
