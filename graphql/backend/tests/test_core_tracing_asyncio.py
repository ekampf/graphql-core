#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.core` module."""

import pytest

asyncio = pytest.importorskip("asyncio")

from graphql.execution.tracing import TracingAsyncioMiddleware
from graphql.execution.executors.asyncio import AsyncioExecutor

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from ...type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString


async def async_hello_resolver(*_, **__):
    await asyncio.sleep(2)
    return "Async World"

schema = GraphQLSchema(GraphQLObjectType(
    "Query", lambda: {
        "hello": GraphQLField(GraphQLString, resolver=lambda *_: "World"),
        "async_hello": GraphQLField(GraphQLString, resolver=async_hello_resolver)
    }
))


def test_core_backend_with_tracing_asyncio():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend(executor=AsyncioExecutor(), tracing_middleware=TracingAsyncioMiddleware())
    assert isinstance(backend, GraphQLBackend)
    document = backend.document_from_string(schema, "{ hello, async_hello }")
    assert isinstance(document, GraphQLDocument)
    result = document.execute()
    assert not result.errors
    assert result.data == {"hello": "World", "async_hello": "Async World"}

    tracing_data = result.extensions["tracing"]
    assert bool(tracing_data)
