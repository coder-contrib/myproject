from dataclasses import dataclass
from fastapi import Query
from sqlalchemy import asc, desc


@dataclass
class SortParams:
    sort_by: str | None
    order: str

    def apply_to_query(self, query, model):
        if not self.sort_by:
            col = getattr(model, "created_at", None)
            if col is not None:
                return query.order_by(desc(col))
            return query

        col = getattr(model, self.sort_by, None)
        if col is None:
            return query

        if self.order == "asc":
            return query.order_by(asc(col))
        return query.order_by(desc(col))


def get_sorting(
    sort: str | None = Query(None, description="Field to sort by"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
) -> SortParams:
    return SortParams(sort_by=sort, order=order)
