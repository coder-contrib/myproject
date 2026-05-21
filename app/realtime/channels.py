class Channel:
    """Channel naming conventions for WebSocket pub/sub."""

    @staticmethod
    def notifications(tenant_id: str, user_id: str) -> str:
        return f"notifications:{tenant_id}:{user_id}"

    @staticmethod
    def pos_session(tenant_id: str, session_id: str) -> str:
        return f"pos:{tenant_id}:{session_id}"

    @staticmethod
    def pos_branch(tenant_id: str, branch_id: str) -> str:
        return f"pos_branch:{tenant_id}:{branch_id}"

    @staticmethod
    def dashboard(tenant_id: str) -> str:
        return f"dashboard:{tenant_id}"

    @staticmethod
    def dashboard_branch(tenant_id: str, branch_id: str) -> str:
        return f"dashboard:{tenant_id}:{branch_id}"

    @staticmethod
    def inventory(tenant_id: str) -> str:
        return f"inventory:{tenant_id}"

    @staticmethod
    def sales(tenant_id: str) -> str:
        return f"sales:{tenant_id}"
