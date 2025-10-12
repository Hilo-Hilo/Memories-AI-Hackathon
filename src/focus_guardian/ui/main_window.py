"""
Main application window for Focus Guardian.

PyQt6-based window with menu bar, status bar, system tray integration,
and tabbed interface for dashboard, reports, and settings.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar,
    QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from ..core.config import Config
from ..core.database import Database
from ..core.models import QualityProfile
from ..session.session_manager import SessionManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    # Signals for cross-thread communication
    distraction_alert = pyqtSignal(dict)  # Distraction event from detector
    micro_break_suggestion = pyqtSignal(dict)  # Micro-break suggestion
    
    def __init__(self, config: Config, database: Database):
        """
        Initialize main window.
        
        Args:
            config: Configuration manager
            database: Database interface
        """
        super().__init__()
        
        self.config = config
        self.database = database
        
        # Create UI queue for receiving messages from background threads
        from queue import Queue
        self.ui_queue = Queue()
        
        # Session manager
        self.session_manager = SessionManager(config, database, self.ui_queue)
        
        # Session state
        self.current_session_id = None
        self.session_active = False
        self.session_start_time = None
        self.session_elapsed_seconds = 0
        self.session_paused_at = None
        self.session_total_paused_seconds = 0
        
        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_system_tray()
        self._setup_timers()
        
        # Connect signals
        self.distraction_alert.connect(self._handle_distraction_alert)
        self.micro_break_suggestion.connect(self._handle_micro_break_suggestion)
        
        # Start UI queue processor
        self._ui_queue_timer = QTimer()
        self._ui_queue_timer.timeout.connect(self._process_ui_queue)
        self._ui_queue_timer.start(100)  # Process every 100ms
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup main UI layout."""
        self.setWindowTitle("Focus Guardian - ADHD Distraction Analysis")
        self.setMinimumSize(900, 600)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Dashboard tab (main view)
        self.dashboard_tab = self._create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Reports tab
        self.reports_tab = self._create_reports_tab()
        self.tabs.addTab(self.reports_tab, "Reports")
        
        # Settings tab
        self.settings_tab = self._create_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
    
    def _create_dashboard_tab(self) -> QWidget:
        """Create dashboard tab for active session view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Focus Session Dashboard")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Session info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_widget.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        self.session_status_label = QLabel("No active session")
        self.session_status_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        self.session_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.session_status_label)
        
        self.session_timer_label = QLabel("00:00:00")
        self.session_timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #3498db;")
        self.session_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.session_timer_label)
        
        self.task_label = QLabel("Task: None")
        self.task_label.setStyleSheet("font-size: 16px; color: #34495e;")
        self.task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.task_label)
        
        layout.addWidget(info_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("Start Focus Session")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_button.clicked.connect(self._on_start_session)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.pause_button.clicked.connect(self._on_pause_session)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop Session")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_button.clicked.connect(self._on_stop_session)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Stats display
        stats_label = QLabel("Session Statistics")
        stats_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(stats_label)
        
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        
        self.snapshots_label = QLabel("Snapshots: 0")
        self.snapshots_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.snapshots_label)
        
        self.distractions_label = QLabel("Distractions: 0")
        self.distractions_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.distractions_label)
        
        self.focus_ratio_label = QLabel("Focus: 0%")
        self.focus_ratio_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.focus_ratio_label)
        
        layout.addWidget(stats_widget)
        
        # Stretch to push everything to top
        layout.addStretch()
        
        return widget
    
    def _create_reports_tab(self) -> QWidget:
        """Create reports tab for session history."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Session Reports")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(label)
        
        placeholder = QLabel("Session history will appear here")
        placeholder.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        return widget
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings tab for configuration."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Settings")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(label)
        
        # API Keys section
        api_section = QLabel("API Configuration")
        api_section.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(api_section)
        
        # Check API keys
        openai_key = self.config.get_openai_api_key()
        hume_key = self.config.get_hume_api_key()
        mem_key = self.config.get_memories_api_key()
        
        openai_status = QLabel(
            f"OpenAI: {'✓ Configured' if openai_key else '✗ Not configured'}"
        )
        openai_status.setStyleSheet(
            f"color: {'#27ae60' if openai_key else '#e74c3c'}; font-size: 14px;"
        )
        layout.addWidget(openai_status)
        
        hume_status = QLabel(
            f"Hume AI: {'✓ Configured' if hume_key else '✗ Not configured'}"
        )
        hume_status.setStyleSheet(
            f"color: {'#27ae60' if hume_key else '#e74c3c'}; font-size: 14px;"
        )
        layout.addWidget(hume_status)
        
        mem_status = QLabel(
            f"Memories.ai: {'✓ Configured' if mem_key else '✗ Not configured'}"
        )
        mem_status.setStyleSheet(
            f"color: {'#27ae60' if mem_key else '#e74c3c'}; font-size: 14px;"
        )
        layout.addWidget(mem_status)
        
        layout.addStretch()
        
        return widget
    
    def _setup_menu_bar(self):
        """Setup menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_session_action = QAction("&New Session", self)
        new_session_action.triggered.connect(self._on_start_session)
        file_menu.addAction(new_session_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_system_tray(self):
        """Setup system tray icon."""
        # TODO: Add actual icon file
        self.tray_icon = QSystemTrayIcon(self)
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        # self.tray_icon.show()  # Enable when icon is available
    
    def _setup_timers(self):
        """Setup UI update timers."""
        # Session timer (updates every second)
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        
        # Stats timer (updates every 5 seconds)
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
    
    def _on_start_session(self):
        """Handle start session button click."""
        from datetime import datetime
        
        logger.info("Start session requested")
        
        # TODO: Show task input dialog
        task_name = "Focus Work"  # Placeholder
        
        self.session_status_label.setText(f"Session Active")
        self.task_label.setText(f"Task: {task_name}")
        
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        self.session_active = True
        self.session_start_time = datetime.now()
        self.session_elapsed_seconds = 0
        self.session_paused_at = None
        self.session_total_paused_seconds = 0
        self.session_timer.start(1000)  # Update every second
        self.stats_timer.start(5000)     # Update every 5 seconds
        
        self.status_bar.showMessage("Focus session started")
        
        # Start actual session
        try:
            self.current_session_id = self.session_manager.start_session(
                task_name=task_name,
                quality_profile=QualityProfile.STD,
                screen_enabled=True
            )
            logger.info(f"Session manager started: {self.current_session_id}")
        except Exception as e:
            logger.error(f"Failed to start session: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start session: {str(e)}\n\nCheck that your camera is available."
            )
            # Revert UI state
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.session_active = False
            return
    
    def _on_pause_session(self):
        """Handle pause session button click."""
        from datetime import datetime
        
        logger.info("Pause session requested")
        
        if self.pause_button.text() == "Pause":
            # Pausing: record when we paused
            self.pause_button.setText("Resume")
            self.session_paused_at = datetime.now()
            self.session_timer.stop()
            self.status_bar.showMessage("Session paused")
            
            # Pause session manager
            try:
                self.session_manager.pause_session()
            except Exception as e:
                logger.error(f"Failed to pause session: {e}")
        else:
            # Resuming: calculate total paused time
            self.pause_button.setText("Pause")
            if self.session_paused_at:
                pause_duration = (datetime.now() - self.session_paused_at).total_seconds()
                self.session_total_paused_seconds += pause_duration
                self.session_paused_at = None
            self.session_timer.start(1000)
            self.status_bar.showMessage("Session resumed")
            
            # Resume session manager
            try:
                self.session_manager.resume_session()
            except Exception as e:
                logger.error(f"Failed to resume session: {e}")
    
    def _on_stop_session(self):
        """Handle stop session button click."""
        logger.info("Stop session requested")
        
        reply = QMessageBox.question(
            self,
            "Stop Session",
            "Are you sure you want to stop the current session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_timer.stop()
            self.stats_timer.stop()
            
            self.session_status_label.setText("No active session")
            self.session_timer_label.setText("00:00:00")
            self.task_label.setText("Task: None")
            
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("Pause")  # Reset text
            self.stop_button.setEnabled(False)
            
            self.session_active = False
            self.session_start_time = None
            self.session_elapsed_seconds = 0
            self.session_paused_at = None
            self.session_total_paused_seconds = 0
            self.status_bar.showMessage("Session stopped")
            
            # Stop session manager
            try:
                self.session_manager.stop_session()
                logger.info("Session manager stopped")
            except Exception as e:
                logger.error(f"Failed to stop session: {e}", exc_info=True)
    
    def _update_session_timer(self):
        """Update session timer display."""
        if not self.session_active or self.session_start_time is None:
            return
        
        from datetime import datetime
        
        # Calculate elapsed time, excluding paused time
        total_elapsed = (datetime.now() - self.session_start_time).total_seconds()
        active_elapsed = total_elapsed - self.session_total_paused_seconds
        self.session_elapsed_seconds = int(active_elapsed)
        
        # Format as HH:MM:SS
        hours = self.session_elapsed_seconds // 3600
        minutes = (self.session_elapsed_seconds % 3600) // 60
        seconds = self.session_elapsed_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.session_timer_label.setText(time_str)
    
    def _update_stats(self):
        """Update session statistics display."""
        if not self.session_active:
            return
        
        try:
            stats = self.session_manager.get_session_stats()
            
            self.snapshots_label.setText(f"Snapshots: {stats['total_snapshots']}")
            self.distractions_label.setText(f"Distractions: {stats['total_events']}")
            self.focus_ratio_label.setText(f"Focus: {stats['focus_ratio']*100:.0f}%")
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def _process_ui_queue(self):
        """Process messages from background threads."""
        try:
            from queue import Empty
            
            # Check if there are any messages in the UI queue
            try:
                message = self.ui_queue.get_nowait()
                
                if message:
                    msg_type = message.get("type")
                    
                    if msg_type == "distraction_alert":
                        self.distraction_alert.emit(message)
                    elif msg_type == "micro_break_suggestion":
                        self.micro_break_suggestion.emit(message)
            except Empty:
                pass
        except Exception as e:
            # Ignore errors in queue processing
            pass
    
    def _handle_distraction_alert(self, alert_data: dict):
        """Handle distraction alert from detector."""
        logger.info(f"🔔 DISTRACTION ALERT RECEIVED: {alert_data}")
        
        # Get alert details
        message = alert_data.get("message", "Distraction detected")
        distraction_type = alert_data.get("distraction_type", "Unknown")
        confidence = alert_data.get("confidence", 0.0)
        vision_votes = alert_data.get("vision_votes", {})
        
        # Build detailed message
        details = f"Type: {distraction_type}\nConfidence: {confidence:.0%}"
        
        if vision_votes:
            details += "\n\nDetected patterns:"
            for label, count in vision_votes.items():
                details += f"\n  • {label}: {count}/3 snapshots"
        
        # Show alert dialog
        QMessageBox.warning(
            self,
            "🔔 Focus Alert - Distraction Detected",
            f"{message}\n\n{details}\n\n"
            f"Refocus on your task: {self.task_label.text().replace('Task: ', '')}",
            QMessageBox.StandardButton.Ok
        )
        
        logger.info("Alert dialog shown to user")
    
    def _handle_micro_break_suggestion(self, suggestion_data: dict):
        """Handle micro-break suggestion."""
        logger.info(f"Micro-break suggestion: {suggestion_data}")
        
        message = suggestion_data.get("message", "Consider taking a break")
        
        QMessageBox.information(
            self,
            "Micro-Break Suggestion",
            message,
            QMessageBox.StandardButton.Ok
        )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Focus Guardian",
            "<h2>Focus Guardian v0.1.0</h2>"
            "<p>ADHD distraction analysis desktop application</p>"
            "<p>Snapshot-based AI detection with K=3 hysteresis voting</p>"
            "<p>© 2025 Focus Guardian Team</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.session_active:
            reply = QMessageBox.question(
                self,
                "Quit Application",
                "A session is active. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        logger.info("Application closing")
        event.accept()

