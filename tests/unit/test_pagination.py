"""Unit tests for pagination utilities."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestPagination:
    def test_pagination_params_defaults(self):
        from app.core.pagination import PaginationParams

        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20

    def test_pagination_params_custom(self):
        from app.core.pagination import PaginationParams

        params = PaginationParams(page=3, size=50)
        assert params.page == 3
        assert params.size == 50

    def test_pagination_params_offset(self):
        from app.core.pagination import PaginationParams

        params = PaginationParams(page=3, size=20)
        assert params.offset == 40

    def test_pagination_params_page_minimum(self):
        from app.core.pagination import PaginationParams

        params = PaginationParams(page=0, size=20)
        assert params.page >= 1

    def test_pagination_params_size_maximum(self):
        from app.core.pagination import PaginationParams

        params = PaginationParams(page=1, size=1000)
        assert params.size <= 100

    def test_paginated_response_structure(self):
        from app.core.pagination import PaginatedResponse

        response = PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            total=50,
            page=1,
            size=20,
            pages=3,
        )
        assert response.items == [{"id": 1}, {"id": 2}]
        assert response.total == 50
        assert response.pages == 3

    def test_paginated_response_has_next(self):
        from app.core.pagination import PaginatedResponse

        response = PaginatedResponse(
            items=[], total=50, page=1, size=20, pages=3
        )
        assert response.has_next is True

    def test_paginated_response_last_page(self):
        from app.core.pagination import PaginatedResponse

        response = PaginatedResponse(
            items=[], total=50, page=3, size=20, pages=3
        )
        assert response.has_next is False
