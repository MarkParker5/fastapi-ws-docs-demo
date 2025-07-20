import inspect
from typing import (
    Tuple,
    get_args,
    get_origin,
)

from fastapi import Response, routing
from fastapi.dependencies.utils import (
    get_body_field,
    get_dependant,
    get_flat_dependant,
    get_parameterless_sub_dependant,
    get_typed_return_annotation,
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
from starlette.types import Scope
from typing_extensions import Union


class SuperWSApiRouteWrapper(routing.APIWebSocketRoute):
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

        self.tags = ["Web Socket",]
        self.methods = {'HEAD'}
        self.status_code = 101
        self.response_class = Response
        self.response_description = 'Switching Protocols'

        self.include_in_schema = True
        self.description = self.summary = inspect.cleandoc(self.endpoint.__doc__ or '')
        self.generate_unique_id_function = generate_unique_id
        self.unique_id = self.operation_id = self.generate_unique_id_function(self)

        self.callbacks = []
        self.openapi_extra = None
        self.deprecated = False
        self._embed_body_fields = True # _should_embed_body_fields(self._flat_dependant.body_params)

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
        if self.response_model:# and is_body_allowed_for_status_code(self.status_code):
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
                responses[2000+i] = {
                    "model": sub_model,
                    "name": f"Response_{self.unique_id}_{i}",
                    "description": sub_model.__name__,
                    "x-ws-endpoint": True,
                    "content": {
                        "application/json": {
                            "schema": sub_model.schema(),
                        }
                    }
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
            child_scope['route'] = self
        return match, child_scope

    @property
    def __class__(self): # fake isinstance to pass filters
        return APIRoute
