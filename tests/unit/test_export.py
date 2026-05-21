"""Unit tests for report export functionality."""
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


@pytest.mark.unit
class TestReportExporter:
    def test_export_to_csv(self):
        from app.reports.export import ReportExporter

        exporter = ReportExporter()
        data = [
            {"product": "Widget A", "quantity": 100, "revenue": 2999.00},
            {"product": "Widget B", "quantity": 50, "revenue": 1499.50},
        ]
        result = exporter.export_to_csv(data, "sales_report")
        assert result is not None
        content = result.decode("utf-8") if isinstance(result, bytes) else result
        assert "product" in content
        assert "Widget A" in content
        assert "2999" in content

    def test_export_to_csv_empty_data(self):
        from app.reports.export import ReportExporter

        exporter = ReportExporter()
        result = exporter.export_to_csv([], "empty_report")
        assert result is not None

    def test_export_to_excel(self):
        from app.reports.export import ReportExporter

        exporter = ReportExporter()
        data = [
            {"product": "Widget A", "quantity": 100, "revenue": 2999.00},
            {"product": "Widget B", "quantity": 50, "revenue": 1499.50},
        ]
        result = exporter.export_to_excel(data, "sales_report")
        assert result is not None
        assert isinstance(result, bytes)
        # Check for xlsx magic bytes (PK zip header)
        assert result[:2] == b"PK"

    def test_export_to_excel_with_formatting(self):
        from app.reports.export import ReportExporter

        exporter = ReportExporter()
        data = [
            {"date": "2026-01-01", "amount": 1500.00, "category": "Sales"},
        ]
        result = exporter.export_to_excel(
            data, "financial_report",
            sheet_name="Financials",
            currency_columns=["amount"],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_to_pdf(self):
        from app.reports.export import ReportExporter

        exporter = ReportExporter()
        data = [
            {"product": "Widget A", "quantity": 100, "revenue": 2999.00},
        ]
        try:
            result = exporter.export_to_pdf(data, "sales_report", title="Sales Report")
            assert result is not None
            assert isinstance(result, bytes)
            assert result[:4] == b"%PDF"
        except ImportError:
            pytest.skip("WeasyPrint not installed")
