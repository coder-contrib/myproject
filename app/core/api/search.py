from dataclasses import dataclass
from fastapi import Query as FastAPIQuery
from sqlalchemy import or_, String, cast


@dataclass
class SearchParams:
    query: str | None
    fields: list[str] | None

    def apply_to_query(self, stmt, model, searchable_fields: list[str] | None = None):
        if not self.query:
            return stmt

        target_fields = self.fields or searchable_fields or []
        if not target_fields:
            return stmt

        conditions = []
        for field_name in target_fields:
            col = getattr(model, field_name, None)
            if col is None:
                continue
            col_type = getattr(col.property.columns[0], "type", None)
            if isinstance(col_type, String):
                conditions.append(col.ilike(f"%{self.query}%"))
            else:
                conditions.append(cast(col, String).ilike(f"%{self.query}%"))

        if conditions:
            stmt = stmt.where(or_(*conditions))
        return stmt


def get_search(
    q: str | None = FastAPIQuery(None, description="Search query"),
    fields: str | None = FastAPIQuery(None, description="Comma-separated fields to search"),
) -> SearchParams:
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    return SearchParams(query=q, fields=field_list)
