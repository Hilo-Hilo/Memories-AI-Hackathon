"""
Graceful degradation strategies for Focus Guardian.

Implements adaptive behavior when components fail or resources are constrained,
allowing the application to continue operating with reduced functionality rather
than failing completely.
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils.logger import get_logger, log_performance
from ..utils.error_handler import error_handler
from ..utils.health_monitor import health_monitor
from ..utils.resource_manager import resource_manager

logger = get_logger(__name__)


class DegradationLevel(Enum):
    """Levels of graceful degradation."""
    NORMAL = "normal"           # Full functionality
    DEGRADED = "degraded"       # Reduced functionality
    MINIMAL = "minimal"         # Core functionality only
    EMERGENCY = "emergency"     # Critical functions only


class ComponentStatus(Enum):
    """Component operational status."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class DegradationStrategy:
    """Strategy for degrading a specific component."""
    component_name: str
    trigger_conditions: List[str]
    degradation_actions: List[Callable]
    recovery_conditions: List[str]
    recovery_actions: List[Callable]

    # Metadata
    priority: int = 1
    user_visible: bool = False
    description: str = ""


@dataclass
class SystemState:
    """Current system degradation state."""
    degradation_level: DegradationLevel = DegradationLevel.NORMAL
    component_status: Dict[str, ComponentStatus] = field(default_factory=dict)
    active_strategies: List[str] = field(default_factory=list)
    last_state_change: float = field(default_factory=time.time)
    recovery_attempts: int = 0

    # Performance metrics
    throughput_reduction: float = 1.0  # Multiplier for operation frequency
    quality_reduction: float = 1.0     # Multiplier for operation quality


class GracefulDegradationManager:
    """Manages graceful degradation strategies."""

    def __init__(self):
        self._state = SystemState()
        self._strategies: Dict[str, DegradationStrategy] = {}
        self._degradation_callbacks: List[Callable] = []
        self._recovery_callbacks: List[Callable] = []

        # Initialize default strategies
        self._initialize_default_strategies()

        logger.info("Graceful degradation manager initialized")

    def _initialize_default_strategies(self) -> None:
        """Initialize default degradation strategies."""

        # API-related strategies
        self.register_strategy(DegradationStrategy(
            component_name="openai_vision_api",
            trigger_conditions=[
                "circuit_breaker_open",
                "rate_limit_exceeded",
                "network_timeout"
            ],
            degradation_actions=[
                self._reduce_api_calls,
                self._increase_retry_delays,
                self._fallback_to_caching
            ],
            recovery_conditions=[
                "circuit_breaker_closed",
                "network_restored"
            ],
            recovery_actions=[
                self._restore_api_calls,
                self._normalize_retry_delays
            ],
            priority=1,
            user_visible=True,
            description="Reduce API calls and increase delays when OpenAI Vision API is unavailable"
        ))

        # Resource-related strategies
        self.register_strategy(DegradationStrategy(
            component_name="resource_management",
            trigger_conditions=[
                "high_memory_usage",
                "high_cpu_usage",
                "disk_space_low"
            ],
            degradation_actions=[
                self._reduce_worker_count,
                self._increase_cleanup_frequency,
                self._pause_non_essential_features
            ],
            recovery_conditions=[
                "memory_usage_normal",
                "cpu_usage_normal",
                "disk_space_available"
            ],
            recovery_actions=[
                self._restore_worker_count,
                self._normalize_cleanup_frequency,
                self._resume_features
            ],
            priority=2,
            user_visible=False,
            description="Reduce resource usage when system is under pressure"
        ))

        # Database strategies
        self.register_strategy(DegradationStrategy(
            component_name="database",
            trigger_conditions=[
                "connection_failed",
                "query_timeout",
                "lock_timeout"
            ],
            degradation_actions=[
                self._queue_database_operations,
                self._reduce_query_frequency,
                self._switch_to_readonly_mode
            ],
            recovery_conditions=[
                "connection_restored",
                "performance_normal"
            ],
            recovery_actions=[
                self._process_queued_operations,
                self._restore_query_frequency,
                self._restore_readwrite_mode
            ],
            priority=3,
            user_visible=True,
            description="Queue operations and reduce frequency when database is slow"
        ))

    def register_strategy(self, strategy: DegradationStrategy) -> None:
        """Register a degradation strategy."""
        self._strategies[strategy.component_name] = strategy
        logger.info(f"Registered degradation strategy for {strategy.component_name}")

    def add_degradation_callback(self, callback: Callable) -> None:
        """Add callback for degradation events."""
        self._degradation_callbacks.append(callback)

    def add_recovery_callback(self, callback: Callable) -> None:
        """Add callback for recovery events."""
        self._recovery_callbacks.append(callback)

    def check_and_apply_degradation(self) -> bool:
        """Check conditions and apply appropriate degradation strategies."""
        changed = False

        # Check each strategy's trigger conditions
        for strategy_name, strategy in self._strategies.items():
            if self._should_trigger_strategy(strategy):
                if strategy_name not in self._state.active_strategies:
                    self._apply_strategy(strategy)
                    changed = True

        return changed

    def check_and_attempt_recovery(self) -> bool:
        """Check recovery conditions and attempt to restore functionality."""
        changed = False

        # Check if any active strategies should be recovered
        for strategy_name in self._state.active_strategies.copy():
            strategy = self._strategies[strategy_name]
            if self._should_recover_strategy(strategy):
                self._recover_strategy(strategy)
                changed = True

        return changed

    def get_current_state(self) -> Dict[str, Any]:
        """Get current degradation state."""
        return {
            "degradation_level": self._state.degradation_level.value,
            "component_status": {k: v.value for k, v in self._state.component_status.items()},
            "active_strategies": self._state.active_strategies,
            "throughput_reduction": self._state.throughput_reduction,
            "quality_reduction": self._state.quality_reduction,
            "last_state_change": self._state.last_state_change,
            "recovery_attempts": self._state.recovery_attempts
        }

    def force_degradation_level(self, level: DegradationLevel) -> None:
        """Force the system to a specific degradation level."""
        old_level = self._state.degradation_level
        self._state.degradation_level = level
        self._state.last_state_change = time.time()

        logger.warning(f"System degradation level forced from {old_level.value} to {level.value}")

        # Notify callbacks
        for callback in self._degradation_callbacks:
            try:
                callback(level, "forced")
            except Exception as e:
                logger.error(f"Degradation callback failed: {e}")

    def _should_trigger_strategy(self, strategy: DegradationStrategy) -> bool:
        """Check if a strategy's trigger conditions are met."""
        # Check circuit breaker states
        cb_stats = error_handler.get_error_stats()
        circuit_breakers = cb_stats.get('circuit_breaker_states', {})

        for condition in strategy.trigger_conditions:
            if condition == "circuit_breaker_open":
                # Check if any circuit breaker is open
                if any(cb.get('state') == 'open' for cb in circuit_breakers.values()):
                    return True

            elif condition.startswith("high_") and condition.endswith("_usage"):
                # Check resource usage thresholds
                resource_type = condition[5:-6]  # Extract "memory", "cpu", etc.
                if self._check_resource_threshold(resource_type):
                    return True

            elif condition == "network_timeout":
                # Check for recent network errors
                error_stats = error_handler.get_error_stats()
                recent_errors = error_stats.get('recent_errors', [])
                network_errors = [
                    err for err in recent_errors
                    if 'network' in err.get('category', '')
                ]
                if len(network_errors) > 3:  # Arbitrary threshold
                    return True

        return False

    def _should_recover_strategy(self, strategy: DegradationStrategy) -> bool:
        """Check if a strategy's recovery conditions are met."""
        # Check circuit breaker states
        cb_stats = error_handler.get_error_stats()
        circuit_breakers = cb_stats.get('circuit_breaker_states', {})

        for condition in strategy.recovery_conditions:
            if condition == "circuit_breaker_closed":
                # Check if all circuit breakers are closed
                if all(cb.get('state') == 'closed' for cb in circuit_breakers.values()):
                    continue  # This condition is met, check others
                else:
                    return False  # This condition is not met

            elif condition.startswith("memory_usage_normal"):
                if resource_manager.get_resource_usage().memory_mb < 400:  # Below warning threshold
                    continue
                else:
                    return False

            elif condition == "network_restored":
                # Check if recent network errors have decreased
                error_stats = error_handler.get_error_stats()
                recent_errors = error_stats.get('recent_errors', [])
                network_errors = [
                    err for err in recent_errors[-10:]  # Last 10 errors
                    if 'network' in err.get('category', '')
                ]
                if len(network_errors) < 2:  # Significantly reduced
                    continue
                else:
                    return False

        return True  # All conditions met

    def _apply_strategy(self, strategy: DegradationStrategy) -> None:
        """Apply a degradation strategy."""
        logger.warning(f"Applying degradation strategy for {strategy.component_name}")

        self._state.active_strategies.append(strategy.component_name)
        self._state.last_state_change = time.time()

        # Update degradation level based on strategy priority
        if strategy.priority <= 1:
            self._state.degradation_level = max(self._state.degradation_level, DegradationLevel.DEGRADED)
        elif strategy.priority <= 2:
            self._state.degradation_level = max(self._state.degradation_level, DegradationLevel.MINIMAL)

        # Execute degradation actions
        for action in strategy.degradation_actions:
            try:
                action()
            except Exception as e:
                logger.error(f"Degradation action failed for {strategy.component_name}: {e}")

        # Update component status
        self._state.component_status[strategy.component_name] = ComponentStatus.DEGRADED

        # Notify callbacks
        for callback in self._degradation_callbacks:
            try:
                callback(strategy.component_name, "degraded")
            except Exception as e:
                logger.error(f"Degradation callback failed: {e}")

    def _recover_strategy(self, strategy: DegradationStrategy) -> None:
        """Recover from a degradation strategy."""
        logger.info(f"Recovering from degradation strategy for {strategy.component_name}")

        self._state.active_strategies.remove(strategy.component_name)
        self._state.last_state_change = time.time()
        self._state.recovery_attempts += 1

        # Execute recovery actions
        for action in strategy.recovery_actions:
            try:
                action()
            except Exception as e:
                logger.error(f"Recovery action failed for {strategy.component_name}: {e}")

        # Update component status
        self._state.component_status[strategy.component_name] = ComponentStatus.OPERATIONAL

        # Check if we can improve degradation level
        self._update_degradation_level()

        # Notify callbacks
        for callback in self._recovery_callbacks:
            try:
                callback(strategy.component_name, "recovered")
            except Exception as e:
                logger.error(f"Recovery callback failed: {e}")

    def _update_degradation_level(self) -> None:
        """Update overall degradation level based on active strategies."""
        if not self._state.active_strategies:
            self._state.degradation_level = DegradationLevel.NORMAL
        elif any(self._strategies[name].priority <= 1 for name in self._state.active_strategies):
            self._state.degradation_level = DegradationLevel.DEGRADED
        elif any(self._strategies[name].priority <= 2 for name in self._state.active_strategies):
            self._state.degradation_level = DegradationLevel.MINIMAL
        else:
            self._state.degradation_level = DegradationLevel.EMERGENCY

    def _check_resource_threshold(self, resource_type: str) -> bool:
        """Check if a resource threshold is exceeded."""
        usage = resource_manager.get_resource_usage()

        if resource_type == "memory":
            return usage.memory_mb > 600  # Above warning threshold
        elif resource_type == "cpu":
            return usage.cpu_percent > 80  # Above warning threshold
        elif resource_type == "disk":
            return usage.disk_free_gb < 1.0  # Less than 1GB free

        return False

    # Degradation actions
    def _reduce_api_calls(self) -> None:
        """Reduce API call frequency."""
        # This would modify the snapshot scheduler to reduce frequency
        logger.info("Reducing API call frequency due to service issues")
        self._state.throughput_reduction = 0.5  # Reduce to 50% frequency

    def _increase_retry_delays(self) -> None:
        """Increase retry delays for failed operations."""
        logger.info("Increasing retry delays for failed operations")
        # This would modify retry backoff timing

    def _fallback_to_caching(self) -> None:
        """Enable caching for API responses."""
        logger.info("Enabling API response caching")
        # This would enable caching mechanisms

    def _restore_api_calls(self) -> None:
        """Restore normal API call frequency."""
        logger.info("Restoring normal API call frequency")
        self._state.throughput_reduction = 1.0

    def _normalize_retry_delays(self) -> None:
        """Normalize retry delays."""
        logger.info("Normalizing retry delays")
        # This would restore normal retry timing

    def _reduce_worker_count(self) -> None:
        """Reduce number of worker threads."""
        logger.info("Reducing worker thread count due to resource pressure")
        # This would modify thread pool sizes

    def _increase_cleanup_frequency(self) -> None:
        """Increase garbage collection frequency."""
        logger.info("Increasing cleanup frequency")
        # This would reduce cleanup intervals

    def _pause_non_essential_features(self) -> None:
        """Pause non-essential features."""
        logger.info("Pausing non-essential features")
        # This would disable features like cloud uploads, reports, etc.

    def _restore_worker_count(self) -> None:
        """Restore normal worker count."""
        logger.info("Restoring normal worker count")
        # This would restore thread pool sizes

    def _normalize_cleanup_frequency(self) -> None:
        """Normalize cleanup frequency."""
        logger.info("Normalizing cleanup frequency")
        # This would restore cleanup intervals

    def _resume_features(self) -> None:
        """Resume paused features."""
        logger.info("Resuming paused features")
        # This would re-enable disabled features

    def _queue_database_operations(self) -> None:
        """Queue database operations instead of immediate execution."""
        logger.info("Queueing database operations")
        # This would enable operation queuing

    def _reduce_query_frequency(self) -> None:
        """Reduce database query frequency."""
        logger.info("Reducing database query frequency")
        # This would batch or reduce queries

    def _switch_to_readonly_mode(self) -> None:
        """Switch database to read-only mode."""
        logger.info("Switching to read-only database mode")
        # This would disable write operations

    def _process_queued_operations(self) -> None:
        """Process queued database operations."""
        logger.info("Processing queued database operations")
        # This would process queued operations

    def _restore_query_frequency(self) -> None:
        """Restore normal query frequency."""
        logger.info("Restoring normal database query frequency")
        # This would restore normal query patterns

    def _restore_readwrite_mode(self) -> None:
        """Restore read-write database mode."""
        logger.info("Restoring read-write database mode")
        # This would re-enable write operations


# Global degradation manager instance
degradation_manager = GracefulDegradationManager()


def initialize_graceful_degradation() -> None:
    """Initialize graceful degradation system."""
    logger.info("Initializing graceful degradation system")

    # Register with health monitor for automatic degradation
    def health_alert_callback(alert):
        if alert.severity in ["high", "critical"]:
            degradation_manager.check_and_apply_degradation()

    health_monitor.add_alert_callback(health_alert_callback)

    # Periodic recovery checks
    def periodic_recovery_check():
        degradation_manager.check_and_attempt_recovery()

        # Schedule next check in 60 seconds
        import threading
        timer = threading.Timer(60.0, periodic_recovery_check)
        timer.daemon = True
        timer.start()

    # Start periodic recovery checks
    periodic_recovery_check()


def get_degradation_status() -> Dict[str, Any]:
    """Get current degradation status."""
    return degradation_manager.get_current_state()


def apply_emergency_degradation() -> None:
    """Apply emergency degradation level."""
    degradation_manager.force_degradation_level(DegradationLevel.EMERGENCY)


def get_system_capabilities() -> Dict[str, Any]:
    """Get current system capabilities based on degradation level."""
    state = degradation_manager.get_current_state()

    capabilities = {
        "snapshot_analysis": True,
        "cloud_upload": state["degradation_level"] != DegradationLevel.EMERGENCY.value,
        "real_time_alerts": state["throughput_reduction"] > 0.3,
        "report_generation": state["degradation_level"] in ["normal", "degraded"],
        "database_writes": state["degradation_level"] != DegradationLevel.EMERGENCY.value,
        "api_calls": state["throughput_reduction"] > 0.1
    }

    return capabilities


def check_feature_availability(feature_name: str) -> bool:
    """Check if a specific feature is available under current degradation level."""
    capabilities = get_system_capabilities()
    return capabilities.get(feature_name, False)
