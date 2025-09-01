"""
Performance monitoring and profiling utilities for Tawnia Healthcare Analytics
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
import asyncio
import functools
import json
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MetricData:
    """Individual metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags
        }


@dataclass
class PerformanceReport:
    """Performance analysis report"""
    duration: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    operation_counts: Dict[str, int]
    error_counts: Dict[str, int]
    latency_percentiles: Dict[str, float]
    bottlenecks: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'duration': self.duration,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'operation_counts': self.operation_counts,
            'error_counts': self.error_counts,
            'latency_percentiles': self.latency_percentiles,
            'bottlenecks': self.bottlenecks,
            'recommendations': self.recommendations,
            'generated_at': datetime.now().isoformat()
        }


class MetricsCollector:
    """Advanced metrics collection and aggregation"""

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        with self._lock:
            metric = MetricData(
                timestamp=datetime.now(timezone.utc),
                value=value,
                tags=tags or {}
            )
            self.metrics[name].append(metric)

    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter"""
        with self._lock:
            self.counters[name] += value
            self.record_metric(f"{name}_total", self.counters[name], tags)

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value"""
        with self._lock:
            self.gauges[name] = value
            self.record_metric(name, value, tags)

    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        with self._lock:
            self.histograms[name].append(value)
            # Keep only recent values to prevent memory bloat
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            self.record_metric(name, value, tags)

    def get_metrics(self, name: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics data"""
        with self._lock:
            if name:
                return {name: [m.to_dict() for m in self.metrics.get(name, [])]}
            return {
                metric_name: [m.to_dict() for m in metric_data]
                for metric_name, metric_data in self.metrics.items()
            }

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        with self._lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {}
            }

            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    summary['histograms'][name] = {
                        'count': n,
                        'min': min(sorted_values),
                        'max': max(sorted_values),
                        'mean': sum(sorted_values) / n,
                        'p50': sorted_values[int(n * 0.5)],
                        'p95': sorted_values[int(n * 0.95)],
                        'p99': sorted_values[int(n * 0.99)]
                    }

            return summary


class SystemMonitor:
    """System resource monitoring"""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.monitoring = False
        self.metrics_collector = MetricsCollector()
        self.monitor_thread = None
        # Cache process instance for better performance
        self._process = psutil.Process()

    def start_monitoring(self):
        """Start system monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                self.metrics_collector.set_gauge('system.cpu.usage_percent', cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics_collector.set_gauge('system.memory.usage_percent', memory.percent)
                self.metrics_collector.set_gauge('system.memory.available_mb', memory.available / 1024 / 1024)
                self.metrics_collector.set_gauge('system.memory.used_mb', memory.used / 1024 / 1024)

                # Disk usage
                disk = psutil.disk_usage('/')
                self.metrics_collector.set_gauge('system.disk.usage_percent', disk.percent)
                self.metrics_collector.set_gauge('system.disk.free_gb', disk.free / 1024 / 1024 / 1024)

                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics_collector.set_gauge('system.network.bytes_sent', net_io.bytes_sent)
                self.metrics_collector.set_gauge('system.network.bytes_recv', net_io.bytes_recv)

                # Process info - use cached process instance
                self.metrics_collector.set_gauge('process.memory.rss_mb', self._process.memory_info().rss / 1024 / 1024)
                self.metrics_collector.set_gauge('process.cpu.percent', self._process.cpu_percent())
                self.metrics_collector.set_gauge('process.threads.count', self._process.num_threads())

            except Exception as e:
                # Sanitize error message for logging
                safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
                logger.error(f"Error in system monitoring: {safe_error}")

            time.sleep(self.interval)

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': memory.total / 1024 / 1024 / 1024,
                    'available_gb': memory.available / 1024 / 1024 / 1024,
                    'used_gb': memory.used / 1024 / 1024 / 1024,
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'usage_percent': disk.percent
                }
            }
        except Exception as e:
            # Sanitize error message for logging
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error getting system stats: {safe_error}")
            return {}


class PerformanceProfiler:
    """Advanced performance profiling decorator and context manager"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.active_profiles: Dict[str, Dict[str, Any]] = {}

    def profile(self, operation_name: str = None, track_memory: bool = True):
        """Decorator for profiling function performance"""
        def decorator(func: Callable):
            name = operation_name or f"{func.__module__}.{func.__name__}"

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._profile_async(func, name, track_memory, *args, **kwargs)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return self._profile_sync(func, name, track_memory, *args, **kwargs)
                return sync_wrapper

        return decorator

    def _profile_sync(self, func: Callable, name: str, track_memory: bool, *args, **kwargs):
        """Profile synchronous function"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss if track_memory else 0

        try:
            result = func(*args, **kwargs)
            self.metrics_collector.increment_counter(f"{name}.success")
            return result

        except Exception as e:
            self.metrics_collector.increment_counter(f"{name}.error")
            self.metrics_collector.increment_counter(f"{name}.error.{type(e).__name__}")
            raise

        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            self.metrics_collector.record_histogram(f"{name}.duration", duration)
            self.metrics_collector.increment_counter(f"{name}.calls")

            if track_memory:
                end_memory = psutil.Process().memory_info().rss
                memory_delta = (end_memory - start_memory) / 1024 / 1024  # MB
                self.metrics_collector.record_histogram(f"{name}.memory_delta", memory_delta)

    async def _profile_async(self, func: Callable, name: str, track_memory: bool, *args, **kwargs):
        """Profile asynchronous function"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss if track_memory else 0

        try:
            result = await func(*args, **kwargs)
            self.metrics_collector.increment_counter(f"{name}.success")
            return result

        except Exception as e:
            self.metrics_collector.increment_counter(f"{name}.error")
            self.metrics_collector.increment_counter(f"{name}.error.{type(e).__name__}")
            raise

        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            self.metrics_collector.record_histogram(f"{name}.duration", duration)
            self.metrics_collector.increment_counter(f"{name}.calls")

            if track_memory:
                end_memory = psutil.Process().memory_info().rss
                memory_delta = (end_memory - start_memory) / 1024 / 1024  # MB
                self.metrics_collector.record_histogram(f"{name}.memory_delta", memory_delta)

    def start_profile(self, name: str) -> str:
        """Start a named profiling session"""
        profile_id = f"{name}_{int(time.time() * 1000)}"
        self.active_profiles[profile_id] = {
            'name': name,
            'start_time': time.perf_counter(),
            'start_memory': psutil.Process().memory_info().rss
        }
        return profile_id

    def end_profile(self, profile_id: str) -> Dict[str, Any]:
        """End a profiling session and return results"""
        if profile_id not in self.active_profiles:
            raise ValueError(f"Profile {profile_id} not found")

        profile_data = self.active_profiles.pop(profile_id)
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss

        duration = end_time - profile_data['start_time']
        memory_delta = (end_memory - profile_data['start_memory']) / 1024 / 1024  # MB

        # Record metrics
        name = profile_data['name']
        self.metrics_collector.record_histogram(f"{name}.duration", duration)
        self.metrics_collector.record_histogram(f"{name}.memory_delta", memory_delta)

        return {
            'name': name,
            'duration': duration,
            'memory_delta_mb': memory_delta,
            'start_time': profile_data['start_time'],
            'end_time': end_time
        }


class PerformanceAnalyzer:
    """Analyze performance data and generate insights"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def analyze_performance(self, time_window: timedelta = None) -> PerformanceReport:
        """Generate comprehensive performance analysis"""
        if time_window is None:
            time_window = timedelta(hours=1)

        cutoff_time = datetime.now() - time_window
        summary = self.metrics_collector.get_summary()

        # Calculate overall metrics
        duration = time_window.total_seconds()
        memory_usage = self._analyze_memory_usage(summary)
        cpu_usage = self._analyze_cpu_usage(summary)
        operation_counts = summary.get('counters', {})
        error_counts = {k: v for k, v in operation_counts.items() if 'error' in k}
        latency_percentiles = self._calculate_latency_percentiles(summary)

        # Identify bottlenecks and generate recommendations
        bottlenecks = self._identify_bottlenecks(summary)
        recommendations = self._generate_recommendations(summary, bottlenecks)

        return PerformanceReport(
            duration=duration,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            operation_counts=operation_counts,
            error_counts=error_counts,
            latency_percentiles=latency_percentiles,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )

    def _analyze_memory_usage(self, summary: Dict[str, Any]) -> Dict[str, float]:
        """Analyze memory usage patterns"""
        memory_metrics = {}
        gauges = summary.get('gauges', {})

        for key, value in gauges.items():
            if 'memory' in key:
                memory_metrics[key] = value

        return memory_metrics

    def _analyze_cpu_usage(self, summary: Dict[str, Any]) -> float:
        """Analyze CPU usage"""
        gauges = summary.get('gauges', {})
        return gauges.get('system.cpu.usage_percent', 0.0)

    def _calculate_latency_percentiles(self, summary: Dict[str, Any]) -> Dict[str, float]:
        """Calculate latency percentiles from histogram data"""
        percentiles = {}
        histograms = summary.get('histograms', {})

        for metric_name, stats in histograms.items():
            if 'duration' in metric_name:
                percentiles[f"{metric_name}.p50"] = stats.get('p50', 0)
                percentiles[f"{metric_name}.p95"] = stats.get('p95', 0)
                percentiles[f"{metric_name}.p99"] = stats.get('p99', 0)

        return percentiles

    def _identify_bottlenecks(self, summary: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Check high error rates
        counters = summary.get('counters', {})
        for metric, count in counters.items():
            if 'error' in metric and count > 10:
                bottlenecks.append(f"High error rate in {metric}: {count} errors")

        # Check slow operations
        histograms = summary.get('histograms', {})
        for metric_name, stats in histograms.items():
            if 'duration' in metric_name and stats.get('p95', 0) > 5.0:  # 5 seconds
                bottlenecks.append(f"Slow operation {metric_name}: p95={stats['p95']:.2f}s")

        # Check high memory usage
        gauges = summary.get('gauges', {})
        memory_percent = gauges.get('system.memory.usage_percent', 0)
        if memory_percent > 80:
            bottlenecks.append(f"High memory usage: {memory_percent:.1f}%")

        cpu_percent = gauges.get('system.cpu.usage_percent', 0)
        if cpu_percent > 80:
            bottlenecks.append(f"High CPU usage: {cpu_percent:.1f}%")

        return bottlenecks

    def _generate_recommendations(self, summary: Dict[str, Any], bottlenecks: List[str]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        # General recommendations based on bottlenecks
        if any('High memory usage' in b for b in bottlenecks):
            recommendations.extend([
                "Consider implementing memory pooling for frequently allocated objects",
                "Review data processing batch sizes to reduce memory peaks",
                "Enable garbage collection monitoring and tuning"
            ])

        if any('High CPU usage' in b for b in bottlenecks):
            recommendations.extend([
                "Consider implementing asynchronous processing for CPU-intensive tasks",
                "Review algorithm complexity and optimize hot paths",
                "Implement caching for frequently computed results"
            ])

        if any('Slow operation' in b for b in bottlenecks):
            recommendations.extend([
                "Implement operation timeouts to prevent hanging requests",
                "Consider breaking down large operations into smaller chunks",
                "Add caching for expensive operations"
            ])

        if any('High error rate' in b for b in bottlenecks):
            recommendations.extend([
                "Implement circuit breaker pattern for failing services",
                "Add retry logic with exponential backoff",
                "Improve input validation and error handling"
            ])

        # Always include general best practices
        recommendations.extend([
            "Monitor key performance indicators regularly",
            "Set up alerting for performance degradation",
            "Implement performance testing in CI/CD pipeline"
        ])

        return recommendations


# Global instances
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor()
performance_profiler = PerformanceProfiler(metrics_collector)
performance_analyzer = PerformanceAnalyzer(metrics_collector)


def export_performance_report(report: PerformanceReport, file_path: Path) -> bool:
    """Export performance report to JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Performance report exported to {file_path}")
        return True
    except Exception as e:
        # Sanitize error message for logging
        safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
        logger.error(f"Failed to export performance report: {safe_error}")
        return False


# Context manager for profiling code blocks
class ProfileBlock:
    """Context manager for profiling code blocks"""

    def __init__(self, name: str, profiler: PerformanceProfiler = None):
        self.name = name
        self.profiler = profiler or performance_profiler
        self.profile_id = None

    def __enter__(self):
        self.profile_id = self.profiler.start_profile(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profile_id:
            try:
                result = self.profiler.end_profile(self.profile_id)
                logger.info(f"Profile {self.name} completed: {result['duration']:.3f}s")
            except Exception as e:
                # Handle exceptions in cleanup without affecting original exception
                safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
                logger.error(f"Error ending profile {self.name}: {safe_error}")
