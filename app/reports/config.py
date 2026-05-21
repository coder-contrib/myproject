import os
from dataclasses import dataclass


@dataclass
class ReportConfig:
    export_path: str = os.getenv("REPORT_EXPORT_PATH", "./exports")
    pdf_engine: str = os.getenv("REPORT_PDF_ENGINE", "weasyprint")
    excel_engine: str = os.getenv("REPORT_EXCEL_ENGINE", "openpyxl")
    max_export_rows: int = int(os.getenv("REPORT_MAX_ROWS", "50000"))
    cache_ttl: int = int(os.getenv("REPORT_CACHE_TTL", "300"))
    materialized_view_refresh_interval: int = int(os.getenv("REPORT_MV_REFRESH", "900"))
    company_name: str = os.getenv("REPORT_COMPANY_NAME", "Ceramix AI ERP")
    currency_symbol: str = os.getenv("REPORT_CURRENCY", "$")
    date_format: str = os.getenv("REPORT_DATE_FORMAT", "%Y-%m-%d")


report_config = ReportConfig()
