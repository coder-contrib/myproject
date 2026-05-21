from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    company_id: UUID | None = None
    branch_id: UUID | None = None
    user_id: UUID | None = None
    role: str | None = None

    @property
    def has_company(self) -> bool:
        return self.company_id is not None

    @property
    def has_branch(self) -> bool:
        return self.branch_id is not None

    def with_company(self, company_id: UUID) -> TenantContext:
        return TenantContext(
            tenant_id=self.tenant_id,
            company_id=company_id,
            branch_id=self.branch_id,
            user_id=self.user_id,
            role=self.role,
        )

    def with_branch(self, branch_id: UUID) -> TenantContext:
        return TenantContext(
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            branch_id=branch_id,
            user_id=self.user_id,
            role=self.role,
        )
