"""
Resource management and optimization utilities for Focus Guardian.

Provides comprehensive resource monitoring, memory leak prevention,
and adaptive resource allocation to ensure the application remains
stable and performant under various conditions.
"""

import gc
import psutil
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import weakref

from ..utils.logger import get_logger, log_performance, get_metrics
from ..utils.health_monitor import health_monitor

logger = get_logger(__name__)


@dataclass
class ResourceUsage:
    """Snapshot of resource usage."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    thread_count: int
    open_files: int
    disk_usage_gb: float

    # Memory breakdown
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size

    # Thread information
    daemon_threads: int
    alive_threads: int


@dataclass
class MemoryProfile:
    """Memory usage profile for leak detection."""
    baseline_mb: float
    current_mb: float
    growth_rate_mb_per_hour: float
    peak_mb: float
    allocations: int = 0
    deallocations: int = 0

    # GC statistics
    gc_collections: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0})


class ResourceThresholds:
    """Configurable resource thresholds for adaptive behavior."""

    # Memory thresholds (MB)
    MEMORY_WARNING_MB = 500
    MEMORY_CRITICAL_MB = 800
    MEMORY_LEAK_THRESHOLD_MB_PER_HOUR = 50

    # CPU thresholds
    CPU_WARNING_PERCENT = 70
    CPU_CRITICAL_PERCENT = 90

    # Thread thresholds
    MAX_THREADS = 50
    MAX_DAEMON_THREADS = 30

    # Disk thresholds (GB)
    DISK_WARNING_GB = 2.0
    DISK_CRITICAL_GB = 0.5

    # File handle thresholds
    MAX_OPEN_FILES = 200

    # Cleanup intervals (seconds)
    GC_CLEANUP_INTERVAL = 300  # 5 minutes
    MEMORY_CHECK_INTERVAL = 60  # 1 minute
    THREAD_CLEANUP_INTERVAL = 120  # 2 minutes


class ResourceManager:
    """Comprehensive resource management system."""

    def __init__(self):
        self._process = psutil.Process()
        self._baseline_memory = None
        self._memory_history: deque = deque(maxlen=100)
        self._resource_history: deque = deque(maxlen=200)

        # Thread management
        self._thread_refs: weakref.WeakSet = weakref.WeakSet()
        self._cleanup_callbacks: List[Callable] = []

        # Memory profiling
        self._memory_profile = MemoryProfile(baseline_mb=0, current_mb=0, growth_rate_mb_per_hour=0, peak_mb=0)

        # Adaptive behavior flags
        self._throttling_active = False
        self._memory_pressure = False
        self._cpu_pressure = False

        # Monitoring timers
        self._monitoring_active = False
        self._gc_timer: Optional[threading.Timer] = None
        self._memory_timer: Optional[threading.Timer] = None

        logger.info("Resource manager initialized")

    def start_monitoring(self) -> None:
        """Start resource monitoring and cleanup timers."""
        if self._monitoring_active:
            logger.warning("Resource monitoring already active")
            return

        self._monitoring_active = True

        # Initialize baseline
        self._establish_baseline()

        # Start periodic cleanup
        self._schedule_gc_cleanup()
        self._schedule_memory_check()

        logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False

        # Cancel timers
        if self._gc_timer:
            self._gc_timer.cancel()
            self._gc_timer = None

        if self._memory_timer:
            self._memory_timer.cancel()
            self._memory_timer = None

        logger.info("Resource monitoring stopped")

    def register_cleanup_callback(self, callback: Callable) -> None:
        """Register a cleanup callback for resource management."""
        self._cleanup_callbacks.append(callback)

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage snapshot."""
        try:
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent(interval=0.1)

            # Thread information
            all_threads = threading.enumerate()
            daemon_threads = sum(1 for t in all_threads if t.daemon)
            alive_threads = len(all_threads)

            # File handles (approximate)
            try:
                open_files = len(self._process.open_files())
            except (psutil.AccessDenied, AttributeError):
                open_files = 0

            # Disk usage for data directory
            data_dir = Path.home() / "Focus Guardian" / "data"
            if data_dir.exists():
                disk_usage = psutil.disk_usage(str(data_dir))
                disk_usage_gb = disk_usage.used / (1024 ** 3)
            else:
                disk_usage = psutil.disk_usage('/')
                disk_usage_gb = disk_usage.used / (1024 ** 3)

            return ResourceUsage(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_info.rss / (1024 * 1024),
                memory_percent=self._process.memory_percent(),
                thread_count=alive_threads,
                open_files=open_files,
                disk_usage_gb=disk_usage_gb,
                rss_mb=memory_info.rss / (1024 * 1024),
                vms_mb=memory_info.vms / (1024 * 1024),
                daemon_threads=daemon_threads,
                alive_threads=alive_threads
            )

        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return ResourceUsage(
                timestamp=time.time(),
                cpu_percent=0,
                memory_mb=0,
                memory_percent=0,
                thread_count=0,
                open_files=0,
                disk_usage_gb=0,
                rss_mb=0,
                vms_mb=0,
                daemon_threads=0,
                alive_threads=0
            )

    def check_resource_pressure(self) -> Dict[str, bool]:
        """Check if system is under resource pressure."""
        usage = self.get_resource_usage()

        pressure = {
            "memory_pressure": usage.memory_mb > ResourceThresholds.MEMORY_WARNING_MB,
            "cpu_pressure": usage.cpu_percent > ResourceThresholds.CPU_WARNING_PERCENT,
            "disk_pressure": usage.disk_usage_gb > (100 - ResourceThresholds.DISK_WARNING_GB),
            "thread_pressure": usage.thread_count > ResourceThresholds.MAX_THREADS,
            "file_pressure": usage.open_files > ResourceThresholds.MAX_OPEN_FILES
        }

        # Update state
        self._memory_pressure = pressure["memory_pressure"]
        self._cpu_pressure = pressure["cpu_pressure"]

        return pressure

    def should_throttle(self) -> bool:
        """Check if operations should be throttled due to resource pressure."""
        pressure = self.check_resource_pressure()

        # Throttle if critical pressure in multiple areas
        critical_pressure_count = sum([
            pressure["memory_pressure"] and self._memory_pressure,
            pressure["cpu_pressure"] and self._cpu_pressure,
            pressure["disk_pressure"],
            pressure["thread_pressure"]
        ])

        return critical_pressure_count >= 2

    def adaptive_throttle(self) -> Dict[str, Any]:
        """Apply adaptive throttling based on resource pressure."""
        if not self._throttling_active:
            pressure = self.check_resource_pressure()

            if self.should_throttle():
                self._throttling_active = True

                # Determine throttling strategy
                throttle_config = {
                    "reduce_snapshot_frequency": pressure["memory_pressure"] or pressure["cpu_pressure"],
                    "reduce_upload_workers": pressure["memory_pressure"],
                    "pause_non_essential_features": pressure["memory_pressure"] and pressure["cpu_pressure"],
                    "increase_gc_frequency": pressure["memory_pressure"]
                }

                logger.warning(f"Resource pressure detected, applying throttling: {throttle_config}")

                return throttle_config

        return {}

    def force_memory_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup and garbage collection."""
        logger.info("Forcing memory cleanup")

        # Run garbage collection
        gc.collect()

        # Clear internal caches
        self._memory_history.clear()

        # Trigger cleanup callbacks
        cleanup_results = {}
        for callback in self._cleanup_callbacks:
            try:
                result = callback()
                cleanup_results[callback.__name__] = result
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
                cleanup_results[callback.__name__] = f"error: {e}"

        # Update memory profile
        current_usage = self.get_resource_usage()
        self._memory_history.append(current_usage.memory_mb)

        return {
            "gc_collected": gc.get_count(),
            "memory_before_mb": self._memory_profile.current_mb,
            "memory_after_mb": current_usage.memory_mb,
            "cleanup_results": cleanup_results
        }

    def detect_memory_leak(self) -> Dict[str, Any]:
        """Analyze memory usage for potential leaks."""
        if len(self._memory_history) < 10:
            return {"leak_detected": False, "reason": "insufficient_data"}

        # Calculate growth rate
        recent_memory = list(self._memory_history)[-10:]
        baseline = min(recent_memory) if recent_memory else 0

        if self._baseline_memory is None:
            self._baseline_memory = baseline

        current_memory = recent_memory[-1]
        growth_mb = current_memory - self._baseline_memory

        # Calculate hourly growth rate
        time_span_hours = (time.time() - self._memory_history[0]) / 3600 if len(self._memory_history) > 1 else 1
        growth_rate = growth_mb / max(time_span_hours, 0.1)

        # Update memory profile
        self._memory_profile.current_mb = current_memory
        self._memory_profile.growth_rate_mb_per_hour = growth_rate
        self._memory_profile.peak_mb = max(self._memory_profile.peak_mb, current_memory)

        # Detect potential leaks
        leak_detected = growth_rate > ResourceThresholds.MEMORY_LEAK_THRESHOLD_MB_PER_HOUR

        return {
            "leak_detected": leak_detected,
            "baseline_mb": self._baseline_memory,
            "current_mb": current_memory,
            "growth_mb": growth_mb,
            "growth_rate_mb_per_hour": growth_rate,
            "peak_mb": self._memory_profile.peak_mb,
            "recommendations": self._get_leak_recommendations(leak_detected, growth_rate)
        }

    def _get_leak_recommendations(self, leak_detected: bool, growth_rate: float) -> List[str]:
        """Get recommendations for memory leak mitigation."""
        recommendations = []

        if leak_detected:
            recommendations.append("Memory leak detected - consider restarting application")

        if growth_rate > ResourceThresholds.MEMORY_LEAK_THRESHOLD_MB_PER_HOUR * 0.5:
            recommendations.append("Enable more frequent garbage collection")
            recommendations.append("Review thread lifecycle management")
            recommendations.append("Check for circular references in data structures")

        if self._memory_profile.peak_mb > ResourceThresholds.MEMORY_WARNING_MB:
            recommendations.append("Monitor for large object allocations")
            recommendations.append("Consider implementing object pooling")

        return recommendations

    def get_resource_report(self) -> Dict[str, Any]:
        """Get comprehensive resource usage report."""
        usage = self.get_resource_usage()
        leak_analysis = self.detect_memory_leak()
        pressure = self.check_resource_pressure()

        return {
            "current_usage": usage.__dict__,
            "memory_analysis": leak_analysis,
            "resource_pressure": pressure,
            "throttling_active": self._throttling_active,
            "recommendations": leak_analysis.get("recommendations", [])
        }

    def _establish_baseline(self) -> None:
        """Establish baseline memory usage."""
        logger.info("Establishing resource baseline")

        # Take multiple samples to get stable baseline
        samples = []
        for _ in range(5):
            usage = self.get_resource_usage()
            samples.append(usage.memory_mb)
            time.sleep(0.1)

        self._baseline_memory = sum(samples) / len(samples)
        self._memory_profile.baseline_mb = self._baseline_memory

        logger.info(f"Resource baseline established: {self._baseline_memory:.1f}MB")

    def _schedule_gc_cleanup(self) -> None:
        """Schedule periodic garbage collection cleanup."""
        if not self._monitoring_active:
            return

        def gc_cleanup():
            try:
                # Run garbage collection
                collected = gc.collect()

                # Update GC statistics
                counts = gc.get_count()
                for i, count in enumerate(counts):
                    self._memory_profile.gc_collections[i] = count

                logger.debug(f"GC cleanup completed, objects collected: {collected}")

            except Exception as e:
                logger.error(f"GC cleanup failed: {e}")

            # Schedule next cleanup
            if self._monitoring_active:
                self._gc_timer = threading.Timer(ResourceThresholds.GC_CLEANUP_INTERVAL, gc_cleanup)
                self._gc_timer.daemon = True
                self._gc_timer.start()

        # Start first cleanup
        gc_cleanup()

    def _schedule_memory_check(self) -> None:
        """Schedule periodic memory usage checks."""
        if not self._monitoring_active:
            return

        def memory_check():
            try:
                # Record current memory usage
                usage = self.get_resource_usage()
                self._memory_history.append(usage.memory_mb)

                # Check for pressure and throttling
                if self.should_throttle() and not self._throttling_active:
                    logger.warning("Resource pressure detected, enabling throttling")
                    self._throttling_active = True

                # Auto-cleanup if memory usage is high
                if usage.memory_mb > ResourceThresholds.MEMORY_WARNING_MB:
                    logger.info("High memory usage detected, triggering cleanup")
                    self.force_memory_cleanup()

            except Exception as e:
                logger.error(f"Memory check failed: {e}")

            # Schedule next check
            if self._monitoring_active:
                self._memory_timer = threading.Timer(ResourceThresholds.MEMORY_CHECK_INTERVAL, memory_check)
                self._memory_timer.daemon = True
                self._memory_timer.start()

        # Start first check
        memory_check()

    def register_thread(self, thread: threading.Thread) -> None:
        """Register a thread for monitoring and cleanup."""
        self._thread_refs.add(thread)

    def cleanup_dead_threads(self) -> int:
        """Clean up dead thread references."""
        initial_count = len(self._thread_refs)
        self._thread_refs = weakref.WeakSet(t for t in self._thread_refs if t.is_alive())
        cleaned_count = initial_count - len(self._thread_refs)

        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} dead thread references")

        return cleaned_count


# Global resource manager instance
resource_manager = ResourceManager()


def initialize_resource_management() -> None:
    """Initialize resource management."""
    resource_manager.start_monitoring()


def get_resource_status() -> Dict[str, Any]:
    """Get current resource status."""
    return resource_manager.get_resource_report()


def force_resource_cleanup() -> Dict[str, Any]:
    """Force resource cleanup."""
    return resource_manager.force_memory_cleanup()


def check_resource_health() -> Dict[str, Any]:
    """Check overall resource health."""
    return {
        "resource_usage": resource_manager.get_resource_usage().__dict__,
        "memory_leak": resource_manager.detect_memory_leak(),
        "resource_pressure": resource_manager.check_resource_pressure(),
        "throttling_needed": resource_manager.should_throttle()
    }


class ResourceGuard:
    """Context manager for resource-constrained operations."""

    def __init__(self, operation_name: str, max_duration_seconds: float = 30.0):
        self.operation_name = operation_name
        self.max_duration = max_duration_seconds
        self.start_time = None
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time

            # Log performance
            log_performance(self.logger, self.operation_name, duration * 1000)

            # Check for excessive duration
            if duration > self.max_duration:
                self.logger.warning(
                    f"Operation {self.operation_name} exceeded expected duration: {duration:.2f}s > {self.max_duration}s"
                )

            # Record current memory usage for monitoring
            usage = resource_manager.get_resource_usage()
            resource_manager._memory_history.append(usage.memory_mb)


def adaptive_delay(base_delay: float = 1.0) -> float:
    """Calculate adaptive delay based on resource pressure."""
    if resource_manager.should_throttle():
        # Increase delay when under resource pressure
        return base_delay * 2.0
    elif resource_manager._cpu_pressure:
        # Moderate increase for CPU pressure
        return base_delay * 1.5
    else:
        return base_delay


def get_optimal_worker_count() -> int:
    """Get optimal worker count based on system resources."""
    cpu_count = psutil.cpu_count() or 2
    memory_mb = resource_manager.get_resource_usage().memory_mb

    # Base workers on CPU cores, but limit based on memory
    base_workers = min(cpu_count, 4)  # Cap at 4 workers

    if memory_mb > ResourceThresholds.MEMORY_WARNING_MB:
        # Reduce workers under memory pressure
        base_workers = max(1, base_workers - 1)

    if resource_manager.should_throttle():
        # Further reduce under critical pressure
        base_workers = max(1, base_workers - 1)

    return base_workers
