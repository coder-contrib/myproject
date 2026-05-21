import os
from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")  # json or text
    log_output: str = os.getenv("LOG_OUTPUT", "stdout")  # stdout, file, both
    log_file_path: str = os.getenv("LOG_FILE_PATH", "./logs/app.log")
    log_max_size_mb: int = int(os.getenv("LOG_MAX_SIZE_MB", "100"))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "10"))
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    metrics_prefix: str = os.getenv("METRICS_PREFIX", "ceramix_erp")
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))
    error_tracking_enabled: bool = os.getenv("ERROR_TRACKING_ENABLED", "true").lower() == "true"
    error_sample_rate: float = float(os.getenv("ERROR_SAMPLE_RATE", "1.0"))
    performance_slow_threshold_ms: int = int(os.getenv("PERF_SLOW_THRESHOLD_MS", "1000"))
    audit_log_enabled: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "90"))


monitoring_config = MonitoringConfig()
