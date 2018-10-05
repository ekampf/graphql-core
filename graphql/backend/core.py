from functools import partial
from promise import Promise
from six import string_types

from ..execution import execute, ExecutionResult
from ..execution.tracing import TracingMiddleware
from ..language.base import parse, print_ast
from ..language import ast
from ..validation import validate

from .base import GraphQLBackend, GraphQLDocument

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Optional, Union
    from .base import GraphQLDocument
    from ..language.ast import Document
    from ..type.schema import GraphQLSchema
    from ..execution.base import ExecutionResult
    from rx import Observable


def execute_and_validate(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    tracing_middleware,  # type: TracingMiddleware
    *args,  # type: Any
    **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Observable]

    tracing_middleware.validation_start()
    try:
        do_validation = kwargs.get("validate", True)
        if do_validation:
            validation_errors = validate(schema, document_ast)
            if validation_errors:
                return ExecutionResult(errors=validation_errors, invalid=True)
    finally:
        tracing_middleware.validation_end()

    if tracing_middleware.enabled:
        middleware = kwargs.get("middleware") or []
        middleware.append(tracing_middleware)
        kwargs["middleware"] = middleware

    result = execute(schema, document_ast, *args, **kwargs)

    tracing_middleware.end()
    if tracing_middleware.enabled:
        if isinstance(result, Promise):
            def on_resolve(tracing_m, data):
                data.extensions["tracing"] = tracing_m.get_tracing_extension_dict()

            result = Promise.resolve(result).then(partial(on_resolve, tracing_middleware))
        else:
            result.extensions["tracing"] = tracing_middleware.get_tracing_extension_dict()

    return result


class GraphQLCoreBackend(GraphQLBackend):
    """GraphQLCoreBackend will return a document using the default
    graphql executor"""

    def __init__(self, executor=None, tracing=False):
        # type: (Optional[Any], bool) -> None
        self.execute_params = {"executor": executor}
        self.tracing_middleware = TracingMiddleware(tracing)

    def document_from_string(self, schema, document_string):
        # type: (GraphQLSchema, Union[Document, str]) -> GraphQLDocument

        self.tracing_middleware.start()

        self.tracing_middleware.parsing_start()
        try:
            if isinstance(document_string, ast.Document):
                document_ast = document_string
                document_string = print_ast(document_ast)
            else:
                assert isinstance(
                    document_string, string_types
                ), "The query must be a string"
                document_ast = parse(document_string)

            return GraphQLDocument(
                schema=schema,
                document_string=document_string,
                document_ast=document_ast,
                execute=partial(
                    execute_and_validate,
                    schema,
                    document_ast,
                    self.tracing_middleware,
                    **self.execute_params
                ),
            )
        finally:
            self.tracing_middleware.parsing_end()
