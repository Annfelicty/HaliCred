"""
Metrics Collection and Monitoring for HaliCred
Provides application metrics, performance monitoring, and statistics.
"""

import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import threading
import asyncio
from contextlib import contextmanager


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricData:
    """Data structure for a metric"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: datetime


class MetricsCollector:
    """Centralized metrics collection and reporting"""

    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector

        Args:
            window_size: Number of recent metrics to keep in memory
        """
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.window_size = window_size

        # Application-specific metrics
        self.request_count = 0
        self.error_count = 0
        self.active_requests = 0
        self.total_request_duration = 0.0

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value

            # Store metric data
            metric = MetricData(
                name=name,
                type=MetricType.COUNTER,
                value=self.counters[key],
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
            self.metrics[name].append(metric)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value

            # Store metric data
            metric = MetricData(
                name=name,
                type=MetricType.GAUGE,
                value=value,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
            self.metrics[name].append(metric)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Add an observation to a histogram"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)

            # Keep only recent values
            if len(self.histograms[key]) > self.window_size:
                self.histograms[key] = self.histograms[key][-self.window_size:]

            # Store metric data
            metric = MetricData(
                name=name,
                type=MetricType.HISTOGRAM,
                value=value,
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
            self.metrics[name].append(metric)

    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to time operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.observe_histogram(f"{name}_duration_ms", duration, labels)

    def start_timer(self, name: str) -> str:
        """Start a timer and return its ID"""
        timer_id = f"{name}_{time.time()}"
        self.timers[timer_id] = time.time()
        return timer_id

    def stop_timer(self, timer_id: str) -> float:
        """Stop a timer and return duration in milliseconds"""
        if timer_id in self.timers:
            duration = (time.time() - self.timers[timer_id]) * 1000
            del self.timers[timer_id]
            return duration
        return 0.0

    def record_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float
    ):
        """Record API request metrics"""
        # Increment request counter
        self.increment_counter(
            "api_requests_total",
            labels={"method": method, "path": path, "status": str(status_code)}
        )

        # Record duration
        self.observe_histogram(
            "api_request_duration_ms",
            duration_ms,
            labels={"method": method, "path": path}
        )

        # Track error rate
        if status_code >= 400:
            self.increment_counter(
                "api_errors_total",
                labels={"method": method, "path": path, "status": str(status_code)}
            )

    def record_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        success: bool
    ):
        """Record database operation metrics"""
        self.increment_counter(
            "database_operations_total",
            labels={"operation": operation, "table": table, "success": str(success)}
        )

        self.observe_histogram(
            "database_operation_duration_ms",
            duration_ms,
            labels={"operation": operation, "table": table}
        )

    def record_external_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        success: bool
    ):
        """Record external API call metrics"""
        self.increment_counter(
            "external_api_calls_total",
            labels={"service": service, "endpoint": endpoint, "success": str(success)}
        )

        self.observe_histogram(
            "external_api_duration_ms",
            duration_ms,
            labels={"service": service, "endpoint": endpoint}
        )

    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record business-specific metrics"""
        self.set_gauge(f"business_{metric_name}", value, labels)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self._lock:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "counters": {},
                "gauges": {},
                "histograms": {}
            }

            # Summarize counters
            for key, value in self.counters.items():
                summary["counters"][key] = value

            # Summarize gauges
            for key, value in self.gauges.items():
                summary["gauges"][key] = value

            # Summarize histograms
            for key, values in self.histograms.items():
                if values:
                    sorted_values = sorted(values)
                    summary["histograms"][key] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "mean": sum(values) / len(values),
                        "p50": self._percentile(sorted_values, 50),
                        "p95": self._percentile(sorted_values, 95),
                        "p99": self._percentile(sorted_values, 99)
                    }

            return summary

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "requests": {
                    "total": self.counters.get("api_requests_total", 0),
                    "errors": self.counters.get("api_errors_total", 0),
                    "active": self.active_requests
                },
                "performance": {
                    "average_response_time_ms": (
                        self.total_request_duration / max(self.request_count, 1)
                        if self.request_count > 0 else 0
                    )
                },
                "database": {
                    "operations_total": self.counters.get("database_operations_total", 0)
                },
                "external_apis": {
                    "calls_total": self.counters.get("external_api_calls_total", 0)
                }
            }
        }

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics"""
        error_rate = 0.0
        total_requests = self.counters.get("api_requests_total", 0)
        total_errors = self.counters.get("api_errors_total", 0)

        if total_requests > 0:
            error_rate = (total_errors / total_requests) * 100

        return {
            "healthy": error_rate < 5.0,  # Consider healthy if error rate < 5%
            "error_rate_percent": error_rate,
            "active_requests": self.active_requests,
            "total_requests": total_requests,
            "total_errors": total_errors
        }

    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
            self.request_count = 0
            self.error_count = 0
            self.active_requests = 0
            self.total_request_duration = 0.0

    @staticmethod
    def _make_key(name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @staticmethod
    def _percentile(sorted_list: List[float], percentile: float) -> float:
        """Calculate percentile from sorted list"""
        if not sorted_list:
            return 0.0
        index = int(len(sorted_list) * percentile / 100)
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
        return sorted_list[index]


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Decorator for timing functions
def timed_operation(operation_name: str):
    """Decorator to time function execution"""
    def decorator(func: Callable):
        def sync_wrapper(*args, **kwargs):
            with metrics_collector.timer(operation_name):
                return func(*args, **kwargs)

        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000
                metrics_collector.observe_histogram(f"{operation_name}_duration_ms", duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator