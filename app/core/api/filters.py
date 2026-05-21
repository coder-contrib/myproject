from dataclasses import dataclass, field
from fastapi import Query, Request


@dataclass
class FilterParams:
    filters: dict[str, str] = field(default_factory=dict)

    def apply_to_query(self, query, model):
        for key, value in self.filters.items():
            col = getattr(model, key, None)
            if col is None:
                continue
            if value.startswith("gte:"):
                query = query.where(col >= value[4:])
            elif value.startswith("lte:"):
                query = query.where(col <= value[4:])
            elif value.startswith("gt:"):
                query = query.where(col > value[3:])
            elif value.startswith("lt:"):
                query = query.where(col < value[3:])
            elif value.startswith("ne:"):
                query = query.where(col != value[3:])
            elif value.startswith("in:"):
                values = value[3:].split(",")
                query = query.where(col.in_(values))
            elif value.startswith("like:"):
                query = query.where(col.ilike(f"%{value[5:]}%"))
            else:
                query = query.where(col == value)
        return query


async def get_filters(request: Request) -> FilterParams:
    reserved = {"page", "per_page", "sort", "order", "q", "search", "fields"}
    filters = {}
    for key, value in request.query_params.items():
        if key not in reserved:
            filters[key] = value
    return FilterParams(filters=filters)
