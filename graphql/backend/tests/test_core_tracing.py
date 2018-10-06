#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.core` module."""

import pytest
from graphql.execution.tracing import TracingMiddleware

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from .schema import schema


def test_core_backend_with_tracing():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend(tracing_middleware=TracingMiddleware())
    assert isinstance(backend, GraphQLBackend)
    document = backend.document_from_string(schema, "{ hello }")
    assert isinstance(document, GraphQLDocument)
    result = document.execute()
    assert not result.errors
    assert result.data == {"hello": "World"}

    tracing_data = result.extensions["tracing"]
    assert bool(tracing_data)
