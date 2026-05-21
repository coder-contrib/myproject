from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.seeds.seeder import DatabaseSeeder
from app.core.security.jwt import hash_password


@DatabaseSeeder.register("permissions", order=10)
async def seed_permissions(db: AsyncSession) -> None:
    from app.modules.users.models import Permission

    existing = await db.execute(select(Permission).limit(1))
    if existing.scalar_one_or_none():
        return

    modules = ["users", "tenants", "crm", "inventory", "sales", "purchases",
               "accounting", "treasury", "hr", "manufacturing", "reports", "notifications"]
    actions = ["create", "read", "update", "delete", "export"]

    permissions = []
    for module in modules:
        for action in actions:
            permissions.append(Permission(
                name=f"{module}.{action}",
                module=module,
                action=action,
                scope="tenant",
                description=f"{action.capitalize()} {module}",
            ))

    permissions.append(Permission(name="admin.full_access", module="admin", action="all", scope="system"))
    permissions.append(Permission(name="admin.manage_users", module="admin", action="manage_users", scope="tenant"))
    permissions.append(Permission(name="admin.manage_roles", module="admin", action="manage_roles", scope="tenant"))

    db.add_all(permissions)
    await db.flush()


@DatabaseSeeder.register("default_roles", order=20)
async def seed_default_roles(db: AsyncSession) -> None:
    from app.modules.users.models import Role, Permission, RolePermission

    existing = await db.execute(select(Role).where(Role.is_system == True).limit(1))
    if existing.scalar_one_or_none():
        return

    all_perms = await db.execute(select(Permission))
    permissions = {p.name: p for p in all_perms.scalars().all()}

    # Super Admin role
    admin_role = Role(name="super_admin", description="Full system access", is_system=True, tenant_id=None)
    db.add(admin_role)
    await db.flush()

    for perm in permissions.values():
        db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

    # Manager role
    manager_role = Role(name="manager", description="Department manager", is_system=True, tenant_id=None)
    db.add(manager_role)
    await db.flush()

    manager_perms = [p for name, p in permissions.items() if not name.startswith("admin.")]
    for perm in manager_perms:
        db.add(RolePermission(role_id=manager_role.id, permission_id=perm.id))

    # Employee role
    employee_role = Role(name="employee", description="Standard employee", is_system=True, tenant_id=None)
    db.add(employee_role)
    await db.flush()

    employee_perms = [p for name, p in permissions.items() if ".read" in name or ".create" in name]
    for perm in employee_perms:
        db.add(RolePermission(role_id=employee_role.id, permission_id=perm.id))

    # Viewer role
    viewer_role = Role(name="viewer", description="Read-only access", is_system=True, tenant_id=None)
    db.add(viewer_role)
    await db.flush()

    viewer_perms = [p for name, p in permissions.items() if ".read" in name]
    for perm in viewer_perms:
        db.add(RolePermission(role_id=viewer_role.id, permission_id=perm.id))

    await db.flush()


@DatabaseSeeder.register("demo_tenant", order=30)
async def seed_demo_tenant(db: AsyncSession) -> None:
    from app.modules.tenants.models import Tenant, Company, Branch
    from app.modules.users.models import User, Role

    existing = await db.execute(select(Tenant).limit(1))
    if existing.scalar_one_or_none():
        return

    tenant = Tenant(name="Demo Organization", subscription_status="active")
    db.add(tenant)
    await db.flush()

    company = Company(
        tenant_id=tenant.id,
        name="Demo Company",
        phone="+1234567890",
        address="123 Demo Street",
    )
    db.add(company)
    await db.flush()

    branch = Branch(
        tenant_id=tenant.id,
        company_id=company.id,
        name="Main Branch",
        address="123 Demo Street",
    )
    db.add(branch)
    await db.flush()

    admin_role = await db.execute(select(Role).where(Role.name == "super_admin", Role.is_system == True))
    role = admin_role.scalar_one_or_none()

    admin_user = User(
        tenant_id=tenant.id,
        full_name="System Admin",
        email="admin@demo.com",
        password_hash=hash_password("Admin@123"),
        role_id=role.id if role else None,
        branch_id=branch.id,
        is_active=True,
        is_verified=True,
    )
    db.add(admin_user)
    await db.flush()
