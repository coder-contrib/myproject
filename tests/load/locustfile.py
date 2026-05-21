"""Load testing with Locust.

Run with:
    locust -f tests/load/locustfile.py --host http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host http://localhost:8000 \
        --headless -u 100 -r 10 --run-time 60s
"""
from locust import HttpUser, task, between, tag, events
import random
import json


class ERPUser(HttpUser):
    """Simulates a typical ERP user performing various operations."""
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        """Login on user start."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "testpassword123",
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @tag("read", "products")
    @task(10)
    def list_products(self):
        """Browse product catalog."""
        page = random.randint(1, 5)
        self.client.get(f"/api/v1/products/?page={page}&size=20")

    @tag("read", "products")
    @task(5)
    def get_product(self):
        """View single product."""
        product_id = random.randint(1, 100)
        self.client.get(f"/api/v1/products/{product_id}")

    @tag("read", "products")
    @task(3)
    def search_products(self):
        """Search products."""
        terms = ["widget", "bolt", "gear", "motor", "cable", "sensor"]
        self.client.get(f"/api/v1/products/?search={random.choice(terms)}")

    @tag("read", "sales")
    @task(8)
    def list_invoices(self):
        """Browse invoices."""
        self.client.get("/api/v1/sales/invoices/?page=1&size=20")

    @tag("read", "sales")
    @task(3)
    def get_invoice(self):
        """View single invoice."""
        invoice_id = random.randint(1, 50)
        self.client.get(f"/api/v1/sales/invoices/{invoice_id}")

    @tag("write", "sales")
    @task(2)
    def create_invoice(self):
        """Create a new invoice."""
        items = [
            {
                "product_id": random.randint(1, 50),
                "quantity": random.randint(1, 10),
                "unit_price": round(random.uniform(10, 500), 2),
            }
            for _ in range(random.randint(1, 5))
        ]
        self.client.post("/api/v1/sales/invoices/", json={
            "customer_id": random.randint(1, 20),
            "items": items,
        })

    @tag("read", "inventory")
    @task(5)
    def check_stock(self):
        """Check stock levels."""
        self.client.get("/api/v1/inventory/stock/")

    @tag("write", "inventory")
    @task(2)
    def stock_movement(self):
        """Record stock movement."""
        self.client.post("/api/v1/inventory/movements/", json={
            "product_id": random.randint(1, 50),
            "warehouse_id": random.randint(1, 3),
            "quantity": random.randint(1, 20),
            "movement_type": random.choice(["in", "out"]),
            "reference": f"LOAD-TEST-{random.randint(1000, 9999)}",
        })

    @tag("read", "reports")
    @task(4)
    def dashboard_overview(self):
        """Load dashboard."""
        self.client.get("/api/v1/reports/dashboard/overview")

    @tag("read", "reports")
    @task(2)
    def sales_trend(self):
        """View sales trend."""
        self.client.get("/api/v1/reports/dashboard/sales-trend?period=30d")

    @tag("read", "monitoring")
    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health")

    @tag("read", "ai")
    @task(1)
    def ai_query(self):
        """AI query assistant."""
        questions = [
            "What are total sales this month?",
            "Show me top 5 products by revenue",
            "Which customers have overdue invoices?",
            "What is our current inventory value?",
        ]
        self.client.post("/api/v1/ai/query", json={
            "question": random.choice(questions),
        })


class POSUser(HttpUser):
    """Simulates a POS terminal user - high frequency, low latency requirements."""
    wait_time = between(0.5, 2)
    token = None

    def on_start(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "cashier@test.com",
            "password": "testpassword123",
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @tag("pos", "read")
    @task(15)
    def scan_product(self):
        """Product lookup (barcode scan simulation)."""
        sku = f"SKU-{random.randint(1, 200):04d}"
        self.client.get(f"/api/v1/products/?sku={sku}")

    @tag("pos", "write")
    @task(5)
    def quick_sale(self):
        """Complete a POS sale."""
        self.client.post("/api/v1/sales/invoices/", json={
            "customer_id": None,  # walk-in customer
            "items": [
                {
                    "product_id": random.randint(1, 100),
                    "quantity": random.randint(1, 3),
                    "unit_price": round(random.uniform(5, 100), 2),
                }
            ],
            "payment_method": random.choice(["cash", "card", "mobile"]),
            "is_pos": True,
        })

    @tag("pos", "read")
    @task(3)
    def check_price(self):
        """Price check."""
        product_id = random.randint(1, 100)
        self.client.get(f"/api/v1/products/{product_id}")


class ReportingUser(HttpUser):
    """Simulates a manager/analyst generating reports - infrequent but heavy queries."""
    wait_time = between(5, 15)
    token = None

    def on_start(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "manager@test.com",
            "password": "testpassword123",
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @tag("reports", "heavy")
    @task(3)
    def full_dashboard(self):
        """Load complete dashboard."""
        self.client.get("/api/v1/reports/dashboard/overview")
        self.client.get("/api/v1/reports/dashboard/sales-trend?period=30d")
        self.client.get("/api/v1/reports/dashboard/top-products?limit=10")
        self.client.get("/api/v1/reports/dashboard/top-customers?limit=10")

    @tag("reports", "heavy")
    @task(2)
    def financial_reports(self):
        """Generate financial reports."""
        self.client.get(
            "/api/v1/reports/financial/profit-loss?start_date=2026-01-01&end_date=2026-03-31"
        )

    @tag("reports", "heavy")
    @task(2)
    def analytics(self):
        """Run analytics."""
        self.client.get(
            "/api/v1/reports/analytics/revenue-breakdown?group_by=category"
        )
        self.client.get(
            "/api/v1/reports/analytics/customer-analytics?period=90d"
        )

    @tag("reports", "export")
    @task(1)
    def export_report(self):
        """Export report to Excel."""
        self.client.get(
            "/api/v1/reports/export/sales?format=xlsx&start_date=2026-01-01&end_date=2026-01-31"
        )

    @tag("ai", "heavy")
    @task(1)
    def ai_executive_summary(self):
        """Generate AI executive summary."""
        self.client.post("/api/v1/ai/reports/generate", json={
            "report_type": "executive_summary",
        })
