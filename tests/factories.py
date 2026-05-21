"""Test factories for generating test data."""
import random
import string
from datetime import datetime, timedelta
from typing import Any


class Factory:
    """Base factory for generating test data."""

    @staticmethod
    def random_string(length: int = 10) -> str:
        return "".join(random.choices(string.ascii_lowercase, k=length))

    @staticmethod
    def random_email() -> str:
        return f"{Factory.random_string(8)}@test.com"

    @staticmethod
    def random_phone() -> str:
        return f"+1{random.randint(2000000000, 9999999999)}"


class UserFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        data = {
            "email": cls.random_email(),
            "password": "securepassword123",
            "full_name": f"Test {cls.random_string(5).title()}",
            "role": "user",
            "is_active": True,
        }
        data.update(overrides)
        return data

    @classmethod
    def build_admin(cls, **overrides) -> dict[str, Any]:
        return cls.build(role="admin", **overrides)


class TenantFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        name = f"Tenant {cls.random_string(6).title()}"
        data = {
            "name": name,
            "slug": name.lower().replace(" ", "-"),
            "is_active": True,
        }
        data.update(overrides)
        return data


class ProductFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        price = round(random.uniform(5.0, 500.0), 2)
        data = {
            "name": f"Product {cls.random_string(6).title()}",
            "sku": f"SKU-{cls.random_string(4).upper()}-{random.randint(100, 999)}",
            "price": price,
            "cost": round(price * random.uniform(0.3, 0.7), 2),
            "quantity": random.randint(0, 500),
            "category_id": random.randint(1, 10),
            "is_active": True,
            "description": f"Test product description {cls.random_string(20)}",
        }
        data.update(overrides)
        return data

    @classmethod
    def build_batch(cls, count: int, **overrides) -> list[dict[str, Any]]:
        return [cls.build(**overrides) for _ in range(count)]


class CustomerFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        data = {
            "name": f"Customer {cls.random_string(6).title()}",
            "email": cls.random_email(),
            "phone": cls.random_phone(),
            "address": f"{random.randint(1, 999)} {cls.random_string(8).title()} St",
            "city": random.choice(["Cairo", "Alex", "Giza", "Luxor"]),
            "is_active": True,
        }
        data.update(overrides)
        return data


class InvoiceFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        items = [
            {
                "product_id": random.randint(1, 50),
                "quantity": random.randint(1, 10),
                "unit_price": round(random.uniform(10, 200), 2),
            }
            for _ in range(random.randint(1, 5))
        ]
        subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
        tax = round(subtotal * 0.14, 2)
        data = {
            "customer_id": random.randint(1, 20),
            "items": items,
            "subtotal": round(subtotal, 2),
            "tax_amount": tax,
            "total": round(subtotal + tax, 2),
            "status": "draft",
            "notes": f"Test invoice {cls.random_string(10)}",
        }
        data.update(overrides)
        return data


class WebhookFactory(Factory):
    @classmethod
    def build(cls, **overrides) -> dict[str, Any]:
        data = {
            "url": f"https://{cls.random_string(8)}.example.com/webhook",
            "events": random.sample(
                ["invoice.created", "invoice.paid", "product.created",
                 "stock.low", "order.completed", "payment.received"],
                k=random.randint(1, 4),
            ),
            "is_active": True,
        }
        data.update(overrides)
        return data


class JournalEntryFactory(Factory):
    @classmethod
    def build_balanced(cls, amount: float = None, **overrides) -> dict[str, Any]:
        amount = amount or round(random.uniform(100, 10000), 2)
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reference": f"JE-{cls.random_string(6).upper()}",
            "description": f"Test journal entry {cls.random_string(10)}",
            "lines": [
                {"account_id": 100, "debit": amount, "credit": 0},
                {"account_id": 200, "debit": 0, "credit": amount},
            ],
        }
        data.update(overrides)
        return data
