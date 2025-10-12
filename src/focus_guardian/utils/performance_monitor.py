"""
Performance monitoring utilities for Focus Guardian.

Monitors CPU, memory, and other system resources to enable adaptive
behavior (e.g., throttling snapshot frequency if CPU is high).
"""

import psutil
import time
from dataclasses import dataclass
from typing import Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceStats:
    """Current performance statistics."""
    cpu_percent: float          # Overall CPU usage (0-100)
    memory_percent: float       # Memory usage (0-100)
    memory_mb: float            # Memory usage in MB
    disk_free_gb: float         # Free disk space in GB
    timestamp: float            # Unix timestamp


class PerformanceMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self, check_interval: float = 5.0):
        """
        Initialize performance monitor.
        
        Args:
            check_interval: How often to update stats (seconds)
        """
        self.check_interval = check_interval
        self._last_check: float = 0
        self._cached_stats: Optional[PerformanceStats] = None
        self._process = psutil.Process()
    
    def get_stats(self, force_update: bool = False) -> PerformanceStats:
        """
        Get current performance statistics.
        
        Args:
            force_update: Force immediate update (ignore cache)
            
        Returns:
            PerformanceStats object
        """
        current_time = time.time()
        
        # Use cached stats if recent enough
        if not force_update and self._cached_stats:
            if current_time - self._last_check < self.check_interval:
                return self._cached_stats
        
        # Update stats
        try:
            cpu_percent = self._process.cpu_percent(interval=0.1)
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            memory_percent = self._process.memory_percent()
            
            # Get disk space for data directory
            disk_usage = psutil.disk_usage('/')
            disk_free_gb = disk_usage.free / (1024 ** 3)  # Convert to GB
            
            stats = PerformanceStats(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                disk_free_gb=disk_free_gb,
                timestamp=current_time
            )
            
            self._cached_stats = stats
            self._last_check = current_time
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            # Return dummy stats on error
            return PerformanceStats(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                disk_free_gb=0.0,
                timestamp=current_time
            )
    
    def is_high_cpu(self, threshold: float = 80.0) -> bool:
        """Check if CPU usage is above threshold."""
        stats = self.get_stats()
        return stats.cpu_percent > threshold
    
    def is_high_memory(self, threshold: float = 80.0) -> bool:
        """Check if memory usage is above threshold."""
        stats = self.get_stats()
        return stats.memory_percent > threshold
    
    def is_low_disk_space(self, threshold_gb: float = 1.0) -> bool:
        """Check if disk space is below threshold."""
        stats = self.get_stats()
        return stats.disk_free_gb < threshold_gb
    
    def should_throttle(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0) -> bool:
        """
        Check if application should throttle due to resource constraints.
        
        Args:
            cpu_threshold: CPU percentage threshold
            memory_threshold: Memory percentage threshold
            
        Returns:
            True if throttling recommended
        """
        stats = self.get_stats()
        return stats.cpu_percent > cpu_threshold or stats.memory_percent > memory_threshold
    
    def log_stats(self) -> None:
        """Log current performance statistics."""
        stats = self.get_stats(force_update=True)
        logger.info(
            f"Performance: CPU={stats.cpu_percent:.1f}% "
            f"Memory={stats.memory_mb:.1f}MB ({stats.memory_percent:.1f}%) "
            f"Disk Free={stats.disk_free_gb:.1f}GB"
        )

