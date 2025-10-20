"""
Main application window for Focus Guardian.

PyQt6-based window with menu bar, status bar, system tray integration,
and tabbed interface for dashboard, reports, and settings.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication,
    QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from ..core.config import Config
from ..core.database import Database
from ..core.models import QualityProfile
from ..session.session_manager import SessionManager
from ..utils.logger import get_logger
from ..ai.summary_generator import AISummaryGenerator
from ..ai.emotion_aware_messaging import EmotionAwareMessenger, EmotionState

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

        # Cloud upload tracking
        self.active_uploads = {}  # Dict[session_id, List[job_id]]
        self.active_refresh_jobs = set()  # Set[job_id] - Track jobs being refreshed
        self.job_last_checked = {}  # Dict[job_id, timestamp] - Track when jobs were last checked
        self.job_auto_refresh_timers = {}  # Dict[job_id, QTimer] - Auto-refresh timers for PROCESSING jobs

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_system_tray()
        self._setup_timers()

        # Set minimum window size to prevent layout issues
        self.setMinimumSize(1000, 700)
        
        # Connect signals
        self.distraction_alert.connect(self._handle_distraction_alert)
        self.micro_break_suggestion.connect(self._handle_micro_break_suggestion)
        
        # Start UI queue processor
        self._ui_queue_timer = QTimer()
        self._ui_queue_timer.timeout.connect(self._process_ui_queue)
        self._ui_queue_timer.start(100)  # Process every 100ms
        
        # Task history for quick selection
        self.task_history = self._load_task_history()
        
        # Initialize AI components
        self.ai_summary_generator = None
        self.emotion_messenger = EmotionAwareMessenger()
        
        # Initialize AI summary generator if API key available
        openai_key = self.config.get_openai_api_key()
        if openai_key:
            try:
                self.ai_summary_generator = AISummaryGenerator(openai_key, self.database)
                logger.info("AI summary generator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AI summary generator: {e}")
        
        logger.info("Main window initialized")
    
    def _load_task_history(self) -> list:
        """Load task history from database."""
        try:
            # Get last 10 unique task names from recent sessions
            sessions = self.database.get_all_sessions(limit=50)
            task_names = []
            seen = set()
            
            for session in sessions:
                if session.task_name and session.task_name not in seen:
                    task_names.append(session.task_name)
                    seen.add(session.task_name)
                    if len(task_names) >= 10:
                        break
            
            return task_names
        except Exception as e:
            logger.error(f"Failed to load task history: {e}")
            return []
    
    def _save_task_to_history(self, task_name: str) -> None:
        """Save task to history (updates on session start)."""
        if task_name and task_name not in self.task_history:
            self.task_history.insert(0, task_name)
            self.task_history = self.task_history[:10]  # Keep only last 10
    
    def _show_task_input_dialog(self) -> str:
        """Show task input dialog with history dropdown."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QDialogButtonBox, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Start Focus Session")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instruction_label = QLabel("What task are you working on?")
        instruction_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(instruction_label)
        
        # Combo box with editable text (history + custom input)
        task_input = QComboBox()
        task_input.setEditable(True)
        task_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        task_input.setPlaceholderText("Enter task name or select from history...")
        
        # Add history items
        if self.task_history:
            task_input.addItems(self.task_history)
        else:
            # Default suggestions if no history
            task_input.addItems([
                "Focus Work",
                "Coding Session",
                "Writing Session",
                "Study Session",
                "Design Work",
                "Research"
            ])
        
        task_input.setCurrentText("")  # Start with empty input
        task_input.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(task_input)
        
        # Hint label
        hint_label = QLabel("Tip: Press Enter to start quickly")
        hint_label.setStyleSheet("font-size: 11px; color: #7f8c8d; font-style: italic; margin-top: 5px;")
        layout.addWidget(hint_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Focus the input field
        task_input.setFocus()
        
        # Allow Enter key to submit
        def on_return_pressed():
            if task_input.currentText().strip():
                dialog.accept()
        
        task_input.lineEdit().returnPressed.connect(on_return_pressed)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_name = task_input.currentText().strip()
            if task_name:
                # Save to history
                self._save_task_to_history(task_name)
                return task_name
        
        return None  # User cancelled
    
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
        
        # Enhanced session status with colored indicator
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.setSpacing(10)
        
        self.session_status_icon = QLabel("⚫")
        self.session_status_icon.setStyleSheet("font-size: 24px;")
        status_layout.addWidget(self.session_status_icon)
        
        self.session_status_label = QLabel("No active session")
        self.session_status_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        status_layout.addWidget(self.session_status_label)
        
        # Recording indicators (hidden by default)
        self.recording_indicators = QLabel("📷 🖥️")
        self.recording_indicators.setStyleSheet("font-size: 16px; margin-left: 10px;")
        self.recording_indicators.setVisible(False)
        status_layout.addWidget(self.recording_indicators)
        
        info_layout.addWidget(status_container)
        
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
        
        # Enhanced stats display with visual indicators
        stats_label = QLabel("Session Statistics")
        stats_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(stats_label)
        
        stats_widget = QWidget()
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        stats_layout = QVBoxLayout(stats_widget)
        
        # First row: Counters (clickable for details)
        counters_layout = QHBoxLayout()
        
        # Make labels clickable buttons for detailed view
        self.snapshots_label = QPushButton("📸 Snapshots: 0")
        self.snapshots_label.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                color: #3498db;
                font-weight: bold;
                background: transparent;
                border: none;
                text-align: left;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        self.snapshots_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snapshots_label.setToolTip("Click to see detailed snapshot analysis")
        self.snapshots_label.clicked.connect(self._show_snapshot_details)
        counters_layout.addWidget(self.snapshots_label)
        
        self.distractions_label = QPushButton("⚠️ Distractions: 0")
        self.distractions_label.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                color: #e74c3c;
                font-weight: bold;
                background: transparent;
                border: none;
                text-align: left;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        self.distractions_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.distractions_label.setToolTip("Click to see distraction breakdown and voting details")
        self.distractions_label.clicked.connect(self._show_distraction_details)
        counters_layout.addWidget(self.distractions_label)
        
        self.focus_ratio_label = QPushButton("✓ Focus: 100%")
        self.focus_ratio_label.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                color: #27ae60;
                font-weight: bold;
                background: transparent;
                border: none;
                text-align: left;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        self.focus_ratio_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.focus_ratio_label.setToolTip("Click to see detailed focus analysis")
        self.focus_ratio_label.clicked.connect(self._show_focus_details)
        counters_layout.addWidget(self.focus_ratio_label)
        
        stats_layout.addLayout(counters_layout)
        
        # Second row: Progress bar for focus ratio
        from PyQt6.QtWidgets import QProgressBar
        self.focus_progress_bar = QProgressBar()
        self.focus_progress_bar.setRange(0, 100)
        self.focus_progress_bar.setValue(100)
        self.focus_progress_bar.setTextVisible(False)
        self.focus_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                height: 20px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                   stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        stats_layout.addWidget(self.focus_progress_bar)
        
        # Third row: Cost estimate
        self.cost_label = QLabel("💰 Estimated cost: $0.00")
        self.cost_label.setStyleSheet("font-size: 12px; color: #95a5a6; margin-top: 5px;")
        stats_layout.addWidget(self.cost_label)
        
        layout.addWidget(stats_widget)
        
        # Stretch to push everything to top
        layout.addStretch()
        
        return widget
    
    def _create_reports_tab(self) -> QWidget:
        """Create reports tab for session history."""
        from PyQt6.QtWidgets import QScrollArea, QFrame

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header_layout = QHBoxLayout()
        label = QLabel("Session Reports")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(label)

        # Refresh all button
        self.refresh_all_btn = QPushButton("🔄 Refresh All")
        self.refresh_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_all_btn.setToolTip("Refresh status of all processing cloud jobs")
        self.refresh_all_btn.clicked.connect(self._on_refresh_all_sessions)
        header_layout.addWidget(self.refresh_all_btn)
        
        # Batch Upload All button
        self.batch_upload_btn = QPushButton("☁️ Upload All Completed")
        self.batch_upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.batch_upload_btn.setToolTip("Upload all completed sessions that haven't been uploaded yet")
        self.batch_upload_btn.clicked.connect(self._on_batch_upload_sessions)
        header_layout.addWidget(self.batch_upload_btn)
        
        header_layout.addStretch()

        layout.addLayout(header_layout)
        
        # Search and filter bar
        filter_layout = QHBoxLayout()
        
        # Search box
        from PyQt6.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search sessions by task name...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_box)
        
        # Filter dropdown
        from PyQt6.QtWidgets import QComboBox
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Sessions",
            "Today",
            "This Week",
            "This Month",
            "With Cloud Analysis",
            "Without Cloud Analysis",
            "Upload Failed"
        ])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 150px;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        layout.addLayout(filter_layout)

        # Scroll area for sessions list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Container for session cards
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(10)
        self.sessions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.sessions_container)
        layout.addWidget(scroll_area)

        # Load sessions on tab creation
        self._load_sessions_list()

        return widget
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings tab for configuration."""
        from PyQt6.QtWidgets import QComboBox, QGroupBox, QFormLayout, QScrollArea, QFrame
        from ..capture.screen_capture import WebcamCapture

        # Create main widget
        widget = QWidget()

        # Create scroll area for the entire settings content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create scrollable content widget
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(20)

        label = QLabel("Settings")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(label)

        # Camera Selection section
        camera_group = QGroupBox("Webcam Selection")
        camera_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        camera_layout = QFormLayout(camera_group)

        # INFO: Don't enumerate cameras on startup to avoid activating Continuity Camera
        # User must click "Refresh List" to scan for cameras

        # Camera dropdown - start with only saved config
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("Auto-detect (FaceTime HD)", -1)

        # Add saved camera from config if it's not auto-detect
        saved_index = self.config.get_camera_index()
        saved_name = self.config.get_camera_name()
        if saved_index != -1:
            self.camera_combo.addItem(f"{saved_name}", saved_index)

        # Set current selection to saved config
        combo_index = self.camera_combo.findData(saved_index)
        if combo_index >= 0:
            self.camera_combo.setCurrentIndex(combo_index)

        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        camera_layout.addRow("Camera:", self.camera_combo)

        # Instruction label
        instruction_label = QLabel(
            "Click 'Refresh List' to scan for available cameras"
        )
        instruction_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        camera_layout.addRow("", instruction_label)

        # Camera status label
        self.camera_status_label = QLabel(
            f"✓ Current: {self.config.get_camera_name()}"
        )
        self.camera_status_label.setStyleSheet("color: #27ae60; font-size: 13px;")
        camera_layout.addRow("Status:", self.camera_status_label)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()

        # Preview button
        preview_btn = QPushButton("Show Live Preview")
        preview_btn.clicked.connect(self._show_camera_preview)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(preview_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self._refresh_camera_list)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(refresh_btn)

        camera_layout.addRow("", button_layout)

        layout.addWidget(camera_group)

        # API Keys section
        api_group = QGroupBox("API Configuration")
        api_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        api_layout = QVBoxLayout(api_group)

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
        api_layout.addWidget(openai_status)

        hume_status = QLabel(
            f"Hume AI: {'✓ Configured' if hume_key else '✗ Not configured'}"
        )
        hume_status.setStyleSheet(
            f"color: {'#27ae60' if hume_key else '#e74c3c'}; font-size: 14px;"
        )
        api_layout.addWidget(hume_status)

        mem_status = QLabel(
            f"Memories.ai: {'✓ Configured' if mem_key else '✗ Not configured'}"
        )
        mem_status.setStyleSheet(
            f"color: {'#27ae60' if mem_key else '#e74c3c'}; font-size: 14px;"
        )
        api_layout.addWidget(mem_status)

        layout.addWidget(api_group)

        # Cloud Features section
        cloud_group = QGroupBox("Cloud Features (Post-Session Analysis)")
        cloud_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        cloud_layout = QVBoxLayout(cloud_group)

        # Master switch for cloud features
        self.cloud_features_checkbox = QCheckBox("Enable Cloud Features")
        self.cloud_features_checkbox.setChecked(self.config.is_cloud_features_enabled())
        self.cloud_features_checkbox.setStyleSheet("font-size: 14px; font-weight: normal;")
        self.cloud_features_checkbox.stateChanged.connect(self._on_cloud_features_toggled)
        cloud_layout.addWidget(self.cloud_features_checkbox)

        # Description
        cloud_desc = QLabel(
            "Upload session videos to cloud services for advanced post-processing analysis.\n"
            "Videos are only uploaded AFTER the session ends if auto-upload is enabled."
        )
        cloud_desc.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-left: 20px;")
        cloud_desc.setWordWrap(True)
        cloud_layout.addWidget(cloud_desc)

        # Spacer
        cloud_layout.addSpacing(10)

        # Hume AI section
        hume_container = QWidget()
        hume_layout = QVBoxLayout(hume_container)
        hume_layout.setContentsMargins(20, 0, 0, 0)

        self.hume_ai_checkbox = QCheckBox("Enable Hume AI (Emotion Analysis)")
        self.hume_ai_checkbox.setChecked(self.config.is_hume_ai_enabled())
        self.hume_ai_checkbox.setStyleSheet("font-size: 13px; font-weight: normal;")
        self.hume_ai_checkbox.stateChanged.connect(self._on_hume_ai_toggled)
        self.hume_ai_checkbox.setEnabled(self.config.is_cloud_features_enabled())
        hume_layout.addWidget(self.hume_ai_checkbox)

        self.hume_auto_upload_checkbox = QCheckBox("Auto-upload after each session")
        self.hume_auto_upload_checkbox.setChecked(self.config.is_hume_ai_auto_upload())
        self.hume_auto_upload_checkbox.setStyleSheet("font-size: 12px; font-weight: normal; margin-left: 20px;")
        self.hume_auto_upload_checkbox.stateChanged.connect(self._on_hume_auto_upload_toggled)
        self.hume_auto_upload_checkbox.setEnabled(
            self.config.is_cloud_features_enabled() and self.config.is_hume_ai_enabled()
        )
        hume_layout.addWidget(self.hume_auto_upload_checkbox)

        hume_info = QLabel("Analyzes facial expressions for emotion timeline (frustration, boredom, stress)")
        hume_info.setStyleSheet("color: #95a5a6; font-size: 10px; margin-left: 40px;")
        hume_info.setWordWrap(True)
        hume_layout.addWidget(hume_info)

        cloud_layout.addWidget(hume_container)

        # Spacer
        cloud_layout.addSpacing(10)

        # Memories.ai section
        memories_container = QWidget()
        memories_layout = QVBoxLayout(memories_container)
        memories_layout.setContentsMargins(20, 0, 0, 0)

        self.memories_ai_checkbox = QCheckBox("Enable Memories.ai (Pattern Analysis)")
        self.memories_ai_checkbox.setChecked(self.config.is_memories_ai_enabled())
        self.memories_ai_checkbox.setStyleSheet("font-size: 13px; font-weight: normal;")
        self.memories_ai_checkbox.stateChanged.connect(self._on_memories_ai_toggled)
        self.memories_ai_checkbox.setEnabled(self.config.is_cloud_features_enabled())
        memories_layout.addWidget(self.memories_ai_checkbox)

        self.memories_auto_upload_checkbox = QCheckBox("Auto-upload after each session")
        self.memories_auto_upload_checkbox.setChecked(self.config.is_memories_ai_auto_upload())
        self.memories_auto_upload_checkbox.setStyleSheet("font-size: 12px; font-weight: normal; margin-left: 20px;")
        self.memories_auto_upload_checkbox.stateChanged.connect(self._on_memories_auto_upload_toggled)
        self.memories_auto_upload_checkbox.setEnabled(
            self.config.is_cloud_features_enabled() and self.config.is_memories_ai_enabled()
        )
        memories_layout.addWidget(self.memories_auto_upload_checkbox)

        memories_info = QLabel("Comprehensive VLM analysis: task detection, app usage, distraction patterns")
        memories_info.setStyleSheet("color: #95a5a6; font-size: 10px; margin-left: 40px;")
        memories_info.setWordWrap(True)
        memories_layout.addWidget(memories_info)

        cloud_layout.addWidget(memories_container)

        # Privacy notice
        privacy_notice = QLabel(
            "Privacy: Full videos stay local by default. They are only uploaded to cloud services "
            "when you enable auto-upload or manually request cloud analysis."
        )
        privacy_notice.setStyleSheet("color: #e67e22; font-size: 11px; margin-top: 10px; font-style: italic;")
        privacy_notice.setWordWrap(True)
        cloud_layout.addWidget(privacy_notice)

        # Cloud Storage Management button
        storage_mgmt_btn = QPushButton("🗄️ Manage Cloud Storage")
        storage_mgmt_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        storage_mgmt_btn.clicked.connect(self._on_manage_cloud_storage)
        cloud_layout.addWidget(storage_mgmt_btn)

        layout.addWidget(cloud_group)

        layout.addStretch()

        # Set the scroll widget as the scroll area's widget
        scroll_area.setWidget(scroll_widget)

        # Create main layout for the tab widget
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        return widget

    def _on_camera_changed(self, index: int):
        """Handle camera selection change."""
        camera_index = self.camera_combo.itemData(index)
        camera_name = self.camera_combo.itemText(index)

        # Save to config
        self.config.set_camera_config(camera_index, camera_name)

        # Update status
        self.camera_status_label.setText(f"✓ Saved: {camera_name}")
        self.camera_status_label.setStyleSheet("color: #27ae60; font-size: 13px;")

        # Show warning if session is active
        if self.session_active:
            QMessageBox.information(
                self,
                "Camera Changed",
                "Camera selection saved. Please stop and restart your session to apply the new camera."
            )
        else:
            # Update status to show it's ready
            self.camera_status_label.setText(f"✓ Ready: {camera_name}")

    def _refresh_camera_list(self):
        """Refresh the list of available cameras."""
        from ..capture.screen_capture import WebcamCapture

        # Show loading message
        self.camera_status_label.setText("⏳ Scanning for cameras...")
        self.camera_status_label.setStyleSheet("color: #f39c12; font-size: 13px;")
        QApplication.processEvents()  # Update UI immediately

        try:
            logger.info("Scanning for cameras (this may activate Continuity Camera)...")
            cameras = WebcamCapture.enumerate_cameras()

            # DEBUG: Log what we got
            logger.info(f"DEBUG: enumerate_cameras returned {len(cameras)} cameras:")
            for cam in cameras:
                logger.info(f"  DEBUG: index={cam['index']}, name={cam['name']}")

            if not cameras:
                QMessageBox.information(
                    self,
                    "No Cameras Found",
                    "No cameras were detected. Make sure your camera is connected."
                )
                return

            # Save current selection
            current_index = self.config.get_camera_index()

            # Clear and repopulate
            self.camera_combo.clear()
            self.camera_combo.addItem("Auto-detect (FaceTime HD)", -1)
            for cam in cameras:
                self.camera_combo.addItem(cam["name"], cam["index"])

            # Restore current selection
            combo_index = self.camera_combo.findData(current_index)
            if combo_index >= 0:
                self.camera_combo.setCurrentIndex(combo_index)
            else:
                # Default to auto-detect if saved camera not found
                self.camera_combo.setCurrentIndex(0)

            # Update status
            self.camera_status_label.setText(f"✓ Found {len(cameras)} camera(s)")
            self.camera_status_label.setStyleSheet("color: #27ae60; font-size: 13px;")

            logger.info(f"Camera list refreshed: {len(cameras)} cameras found")

            # Show success message with helpful instructions
            camera_list = "\n".join([f"• {cam['name']}" for cam in cameras])
            QMessageBox.information(
                self,
                "Cameras Detected",
                f"Found {len(cameras)} camera(s):\n\n{camera_list}\n\n" +
                "Use 'Show Live Preview' to verify which camera is at each index."
            )

        except Exception as e:
            logger.error(f"Failed to refresh camera list: {e}", exc_info=True)
            self.camera_status_label.setText("❌ Scan failed")
            self.camera_status_label.setStyleSheet("color: #e74c3c; font-size: 13px;")
            QMessageBox.warning(
                self,
                "Camera Refresh Failed",
                f"Could not scan for cameras: {str(e)}"
            )

    def _show_camera_preview(self):
        """Show live camera preview window."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtCore import QTimer
        from PyQt6.QtGui import QImage, QPixmap
        import cv2
        import numpy as np

        camera_index = self.camera_combo.itemData(self.camera_combo.currentIndex())
        camera_name = self.camera_combo.currentText()

        # Create preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"Camera Preview - {camera_name}")
        preview_dialog.setMinimumSize(640, 480)

        layout = QVBoxLayout(preview_dialog)

        # Video label
        video_label = QLabel()
        video_label.setStyleSheet("border: 2px solid #bdc3c7;")
        layout.addWidget(video_label)

        # Status label
        status_label = QLabel(f"Camera: {camera_name} (Index: {camera_index})")
        status_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        layout.addWidget(status_label)

        # Try to open camera
        try:
            # OpenCV supports -1 as default camera on macOS, so use it directly
            actual_index = camera_index
            logger.info(f"Showing camera preview for index {actual_index}")

            cap = cv2.VideoCapture(actual_index)

            if not cap.isOpened():
                QMessageBox.critical(
                    self,
                    "Camera Error",
                    f"Could not open camera at index {actual_index}"
                )
                return

            # Set up timer to update frames
            def update_frame():
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

                    # Scale to fit label
                    scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                        video_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    video_label.setPixmap(scaled_pixmap)

            timer = QTimer(preview_dialog)
            timer.timeout.connect(update_frame)
            timer.start(33)  # ~30 FPS

            # Cleanup on close
            def cleanup():
                timer.stop()
                cap.release()
                logger.info("Camera preview closed")

            preview_dialog.finished.connect(cleanup)

            logger.info(f"Showing camera preview for index {actual_index}")
            preview_dialog.exec()

        except Exception as e:
            logger.error(f"Failed to show camera preview: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to open camera preview: {str(e)}"
            )
    
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
        from PyQt6.QtWidgets import QInputDialog, QComboBox, QDialog, QLineEdit
        
        logger.info("Start session requested")
        
        # Show task input dialog with history
        task_name = self._show_task_input_dialog()
        if not task_name:  # User cancelled
            return
        
        # Update status with enhanced visual indicators
        self.session_status_icon.setText("🟢")  # Green active indicator
        self.session_status_label.setText("Session Active")
        self.session_status_label.setStyleSheet("font-size: 18px; color: #27ae60; font-weight: bold;")
        self.recording_indicators.setVisible(True)  # Show recording icons
        
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
        
        self.status_bar.showMessage("🟢 Focus session started - recording active")
        
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
            
            # Update status indicators for paused state
            self.session_status_icon.setText("🟡")  # Yellow paused indicator
            self.session_status_label.setText("Session Paused")
            self.session_status_label.setStyleSheet("font-size: 18px; color: #f39c12; font-weight: bold;")
            
            self.status_bar.showMessage("🟡 Session paused")
            
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
            
            # Update status indicators back to active
            self.session_status_icon.setText("🟢")  # Green active indicator
            self.session_status_label.setText("Session Active")
            self.session_status_label.setStyleSheet("font-size: 18px; color: #27ae60; font-weight: bold;")
            
            self.status_bar.showMessage("🟢 Session resumed")
            
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

            # Reset status indicators
            self.session_status_icon.setText("⚫")  # Gray idle indicator
            self.session_status_label.setText("No active session")
            self.session_status_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
            self.recording_indicators.setVisible(False)  # Hide recording icons
            
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

            # Stop session manager and get report
            try:
                stopped_session_id = self.session_manager.stop_session()
                logger.info(f"Session manager stopped: {stopped_session_id}")

                # Check if auto-upload is enabled
                if stopped_session_id:
                    hume_auto = self.config.is_hume_ai_auto_upload()
                    memories_auto = self.config.is_memories_ai_auto_upload()

                    if hume_auto or memories_auto:
                        # Auto-upload enabled - trigger upload with progress UI
                        logger.info("Auto-upload enabled, triggering cloud upload")
                        self._auto_upload_session(stopped_session_id, hume_auto, memories_auto)
                    else:
                        # No auto-upload - just show summary
                        self._show_session_summary(stopped_session_id)
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
        """Update session statistics display with enhanced visualizations."""
        if not self.session_active:
            return
        
        try:
            stats = self.session_manager.get_session_stats()
            
            # Update counters with icons and colors
            snapshots = stats['total_snapshots']
            distractions = stats['total_events']
            focus_ratio = stats['focus_ratio'] * 100
            
            self.snapshots_label.setText(f"📸 Snapshots: {snapshots}")
            self.distractions_label.setText(f"⚠️ Distractions: {distractions}")
            self.focus_ratio_label.setText(f"✓ Focus: {focus_ratio:.0f}%")
            
            # Update progress bar with color coding
            self.focus_progress_bar.setValue(int(focus_ratio))
            
            # Change progress bar color based on focus ratio
            if focus_ratio >= 80:
                color = "#27ae60"  # Green - excellent
            elif focus_ratio >= 60:
                color = "#f39c12"  # Orange - good
            else:
                color = "#e74c3c"  # Red - needs improvement
            
            self.focus_progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    height: 20px;
                    background-color: #ecf0f1;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            # Calculate estimated cost based on snapshots
            # Cost: ~$0.01 per snapshot (cam + screen) with gpt-5-nano high detail
            estimated_cost = snapshots * 2 * 0.055  # 2 images per snapshot, $0.055 each
            self.cost_label.setText(f"💰 Estimated cost: ${estimated_cost:.2f}")
            
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
        """Handle distraction alert with emotion-aware messaging."""
        logger.info(f"🔔 DISTRACTION ALERT RECEIVED: {alert_data}")
        
        # Get alert details
        distraction_type = alert_data.get("distraction_type", "Unknown")
        confidence = alert_data.get("confidence", 0.0)
        vision_votes = alert_data.get("vision_votes", {})
        duration_minutes = alert_data.get("duration_minutes", 0)
        
        # Get current task name
        task_name = self.task_label.text().replace('Task: ', '')
        
        # Detect emotion state (placeholder - will be enhanced with real Hume data)
        emotion_state = EmotionState.UNKNOWN  # TODO: Get from recent Hume data
        
        # Generate emotion-aware alert message
        alert_message = self.emotion_messenger.generate_distraction_alert(
            distraction_type=distraction_type,
            duration_minutes=duration_minutes,
            task_name=task_name,
            emotion_state=emotion_state
        )
        
        # Build detailed evidence section
        evidence = f"<b>Detection Confidence:</b> {confidence:.0%}<br><br>"
        
        if vision_votes:
            evidence += "<b>AI detected across multiple snapshots:</b><br>"
            for label, count in vision_votes.items():
                evidence += f"• {label}: {count}/3 snapshots<br>"
        
        # Create custom message box with rich formatting
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(alert_message["title"])
        msg_box.setIcon(QMessageBox.Icon.Information)  # Less alarming than Warning
        
        # Format message with HTML
        formatted_message = f"""<div style="color: #2c3e50; line-height: 1.5;">
<p>{alert_message['message']}</p>
<hr style="margin: 15px 0;">
<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px;">
{evidence}
</div>
</div>"""
        
        msg_box.setText(formatted_message)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Add custom buttons based on emotion state if available
        if "actions" in alert_message and alert_message["actions"]:
            # Could add custom buttons here for actions
            pass
        
        msg_box.exec()
        
        logger.info(f"Emotion-aware alert shown (tone: {alert_message.get('tone', 'neutral')})")
    
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
    
    def _show_session_summary(self, session_id: str, auto_upload_success: bool = None, auto_upload_error: str = None):
        """
        Show AI-enhanced session summary report after session ends.

        Args:
            session_id: Session ID to show summary for
            auto_upload_success: If auto-upload was triggered, whether it succeeded (None = not triggered)
            auto_upload_error: Error message if auto-upload failed
        """
        try:
            # Get report from database
            report_data = self.database.get_session_report(session_id)

            if not report_data:
                logger.warning("No report available for session")
                return

            # Get session object
            session = self.database.get_session(session_id)

            # Extract key metrics
            kpis = report_data.get("kpis", {})
            meta = report_data.get("meta", {})
            recommendations = report_data.get("recommendations", [])

            # Build summary message
            duration = meta.get("total_duration_minutes", 0)
            focus_ratio = kpis.get("focus_ratio", 0)
            focus_pct = focus_ratio * 100
            num_alerts = kpis.get("num_alerts", 0)
            avg_focus = kpis.get("avg_focus_bout_min", 0)

            # Generate AI-powered summary if available
            ai_summaries = None
            if self.ai_summary_generator:
                try:
                    logger.info("Generating AI-powered session summary...")
                    ai_summaries = self.ai_summary_generator.generate_session_summary(
                        session=session,
                        report_data=report_data,
                        emotion_data=None,  # Will be enhanced later
                        include_history=True
                    )
                except Exception as e:
                    logger.error(f"Failed to generate AI summary: {e}")

            # Build enhanced summary with AI insights
            summary = f"""<div style="color: #2c3e50; line-height: 1.6;">"""

            # AI Executive Summary (if available)
            if ai_summaries and ai_summaries.get("executive"):
                summary += f"""
<div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #27ae60; margin-bottom: 20px;">
    <p style="font-size: 16px; margin: 0; font-weight: 500;">✨ {ai_summaries['executive']}</p>
</div>"""

            # Session Statistics
            summary += f"""<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px;">📊 Session Statistics</h2>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0;">
    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 12px;">DURATION</p>
        <p style="margin: 5px 0 0 0; font-size: 20px; font-weight: bold; color: #3498db;">⏱️ {duration:.0f} min</p>
    </div>
    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 12px;">FOCUS RATIO</p>
        <p style="margin: 5px 0 0 0; font-size: 20px; font-weight: bold; color: {'#27ae60' if focus_pct >= 75 else '#f39c12' if focus_pct >= 50 else '#e74c3c'};">✓ {focus_pct:.0f}%</p>
    </div>
    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 12px;">DISTRACTIONS</p>
        <p style="margin: 5px 0 0 0; font-size: 20px; font-weight: bold; color: #e74c3c;">⚠️ {num_alerts}</p>
    </div>
    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 12px;">AVG FOCUS BOUT</p>
        <p style="margin: 5px 0 0 0; font-size: 20px; font-weight: bold; color: #9b59b6;">📈 {avg_focus:.0f} min</p>
    </div>
</div>"""

            # AI Highlights (if available)
            if ai_summaries and ai_summaries.get("highlights"):
                summary += f"""
<h3 style="color: #2c3e50; margin-top: 20px;">🌟 Session Highlights</h3>
<div style="background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 4px solid #f39c12;">
    {ai_summaries['highlights'].replace('- ', '<br>• ')}
</div>"""

            # Comparative Insight (if available)
            if self.ai_summary_generator:
                try:
                    comparative = self.ai_summary_generator.generate_comparative_insight(session, report_data)
                    if comparative:
                        summary += f"""
<div style="background-color: #e3f2fd; padding: 12px; border-radius: 6px; margin-top: 15px; border-left: 4px solid #3498db;">
    <p style="margin: 0; font-size: 14px;">📊 {comparative}</p>
</div>"""
                except Exception as e:
                    logger.error(f"Failed to generate comparative insight: {e}")

            # Top Triggers
            if kpis.get("top_triggers"):
                triggers = kpis["top_triggers"]
                summary += f"""
<h3 style="color: #2c3e50; margin-top: 20px;">🎯 Top Distractors</h3>
<p>{'<br>'.join(f'• {trigger}' for trigger in triggers[:3])}</p>"""

            # Add auto-upload status if triggered
            if auto_upload_success is not None:
                summary += "<hr style='margin: 20px 0;'><h3 style='color: #2c3e50;'>☁️ Cloud Upload Status</h3>"
                if auto_upload_success:
                    summary += '<div style="background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 4px solid #27ae60;">'
                    summary += '<p style="margin: 0; color: #155724;"><b>✓ Auto-uploaded to cloud successfully</b></p>'
                    summary += "<p style='margin: 8px 0 0 0; color: #155724;'>Videos are being processed. Check Reports tab for results in 5-10 minutes.</p>"
                    summary += '</div>'
                else:
                    summary += '<div style="background-color: #f8d7da; padding: 12px; border-radius: 6px; border-left: 4px solid #e74c3c;">'
                    summary += '<p style="margin: 0; color: #721c24;"><b>✗ Auto-upload failed</b></p>'
                    if auto_upload_error:
                        summary += f"<p style='margin: 8px 0 0 0; color: #721c24; font-size: 12px;'>Error: {auto_upload_error}</p>"
                    summary += "<p style='margin: 8px 0 0 0; color: #721c24;'>You can retry manually from the Reports tab.</p>"
                    summary += '</div>'

            # AI Encouragement (if available)
            if ai_summaries and ai_summaries.get("encouragement"):
                summary += f"""
<div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: center; border: 2px solid #9b59b6;">
    <p style="margin: 0; font-size: 15px; color: #6a1b9a; font-weight: 500;">💜 {ai_summaries['encouragement']}</p>
</div>"""

            if recommendations:
                summary += "<h3>Recommendations:</h3><ul>"
                for rec in recommendations[:3]:  # Show top 3
                    summary += f"<li>{rec.get('message', '')}</li>"
                summary += "</ul>"

            summary += "</div>"

            # Show dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Session Complete")
            msg_box.setText(summary)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.exec()

        except Exception as e:
            logger.error(f"Failed to show session summary: {e}", exc_info=True)
    
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
    
    def _on_cloud_features_toggled(self, state):
        """Handle cloud features master switch toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config.set_cloud_features_enabled(enabled)

        # Update dependent checkboxes
        self.hume_ai_checkbox.setEnabled(enabled)
        self.memories_ai_checkbox.setEnabled(enabled)

        # Disable auto-upload if master switch is off
        if not enabled:
            self.hume_auto_upload_checkbox.setEnabled(False)
            self.memories_auto_upload_checkbox.setEnabled(False)
        else:
            # Re-enable based on individual feature settings
            self.hume_auto_upload_checkbox.setEnabled(self.config.is_hume_ai_enabled())
            self.memories_auto_upload_checkbox.setEnabled(self.config.is_memories_ai_enabled())

        logger.info(f"Cloud features {'enabled' if enabled else 'disabled'}")

    def _on_hume_ai_toggled(self, state):
        """Handle Hume AI toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config.set_hume_ai_enabled(enabled)

        # Update auto-upload checkbox availability
        self.hume_auto_upload_checkbox.setEnabled(enabled and self.config.is_cloud_features_enabled())

        # Check if API key is configured
        if enabled and not self.config.get_hume_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Hume AI API key is not configured. Please set HUME_API_KEY in your .env file."
            )

        logger.info(f"Hume AI {'enabled' if enabled else 'disabled'}")

    def _on_hume_auto_upload_toggled(self, state):
        """Handle Hume AI auto-upload toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config.set_hume_ai_auto_upload(enabled)
        logger.info(f"Hume AI auto-upload {'enabled' if enabled else 'disabled'}")

    def _on_memories_ai_toggled(self, state):
        """Handle Memories.ai toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config.set_memories_ai_enabled(enabled)

        # Update auto-upload checkbox availability
        self.memories_auto_upload_checkbox.setEnabled(enabled and self.config.is_cloud_features_enabled())

        # Check if API key is configured
        if enabled and not self.config.get_memories_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Memories.ai API key is not configured. Please set MEM_AI_API_KEY in your .env file."
            )

        logger.info(f"Memories.ai {'enabled' if enabled else 'disabled'}")

    def _on_memories_auto_upload_toggled(self, state):
        """Handle Memories.ai auto-upload toggle."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config.set_memories_ai_auto_upload(enabled)
        logger.info(f"Memories.ai auto-upload {'enabled' if enabled else 'disabled'}")

    def _on_manage_cloud_storage(self):
        """Show cloud storage management dialog with API-queried data."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox
        from PyQt6.QtCore import QTimer
        import threading

        logger.info("Opening cloud storage management dialog")

        # Show loading dialog
        loading = QMessageBox(self)
        loading.setWindowTitle("Loading...")
        loading.setText("Querying cloud storage APIs...\n\nThis may take a few seconds.")
        loading.setStandardButtons(QMessageBox.StandardButton.NoButton)
        loading.show()
        QApplication.processEvents()

        # Query cloud APIs in background thread
        summary = {}
        error_msg = None

        def query_worker():
            nonlocal summary, error_msg
            try:
                summary = self.session_manager.cloud_analysis_manager.get_storage_summary()
            except Exception as e:
                logger.error(f"Failed to query cloud storage: {e}", exc_info=True)
                error_msg = str(e)

        thread = threading.Thread(target=query_worker, daemon=True)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout

        loading.close()

        # Check for errors
        if error_msg:
            QMessageBox.critical(
                self,
                "Query Failed",
                f"Failed to query cloud storage:\n\n{error_msg}"
            )
            return

        if not summary:
            QMessageBox.warning(
                self,
                "Query Timeout",
                "Cloud storage query timed out after 30 seconds.\n\nPlease try again."
            )
            return

        # Check if any videos found
        total_count = summary.get("total_count", 0)
        if total_count == 0:
            QMessageBox.information(
                self,
                "No Cloud Storage",
                "You have no videos currently stored in cloud.\n\n"
                "Videos are stored when you upload sessions for analysis."
            )
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Cloud Storage Management")
        dialog.setMinimumSize(900, 600)

        layout = QVBoxLayout(dialog)

        # Summary header
        summary_text = f"Storage Summary (queried from APIs):\n\n"
        summary_text += f"• Hume AI: {summary['hume_ai']['count']} jobs\n"
        summary_text += f"• Memories.ai: {summary['memories_ai']['count']} videos\n"
        summary_text += f"• Total: {total_count} items\n\n"
        summary_text += "Note: Hume AI jobs auto-expire after 30 days (no delete API)"

        if summary.get("error"):
            summary_text += f"\n\nWarning: {summary['error']}"

        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2c3e50;
                background-color: #ffffff;
                padding: 15px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
            }
        """)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        # Build unified list combining Hume AI jobs and Memories.ai videos
        storage_items = []

        # Add Hume AI jobs
        for job in summary['hume_ai'].get('jobs', []):
            storage_items.append({
                "provider": "hume_ai",
                "id": job.get("id"),
                "name": f"Job {job.get('id', 'Unknown')[:12]}...",
                "status": job.get("status", "UNKNOWN"),
                "created_timestamp_ms": job.get("created_timestamp_ms"),
                "session_id": None,  # Will try to match with database
                "raw_data": job
            })

        # Add Memories.ai videos
        for video in summary['memories_ai'].get('videos', []):
            storage_items.append({
                "provider": "memories_ai",
                "id": video.get("video_no"),
                "name": video.get("video_name", "Unknown"),
                "status": video.get("status", "UNKNOWN"),
                "created_timestamp_ms": int(video.get("create_time", 0)),
                "session_id": video.get("focus_guardian_session_id"),  # Added by get_storage_summary
                "unique_id": f"focus_session_{video.get('focus_guardian_session_id')}" if video.get('focus_guardian_session_id') else None,
                "raw_data": video
            })

        # Table widget
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Select", "Provider", "ID/Name", "Status", "Session", "Age (days)"])
        table.setRowCount(len(storage_items))
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Populate table
        from datetime import datetime
        for row, item in enumerate(storage_items):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            table.setItem(row, 0, checkbox_item)

            # Provider
            provider_name = "Hume AI" if item["provider"] == "hume_ai" else "Memories.ai"
            table.setItem(row, 1, QTableWidgetItem(provider_name))

            # ID/Name
            table.setItem(row, 2, QTableWidgetItem(item["name"]))

            # Status
            table.setItem(row, 3, QTableWidgetItem(item["status"]))

            # Session (try to match with database)
            session_name = "Unknown"
            if item["session_id"]:
                session = self.database.get_session(item["session_id"])
                if session:
                    session_name = session.task_name
            table.setItem(row, 4, QTableWidgetItem(session_name))

            # Age (days)
            if item["created_timestamp_ms"]:
                created_dt = datetime.fromtimestamp(item["created_timestamp_ms"] / 1000.0)
                age_days = (datetime.now() - created_dt).days
                table.setItem(row, 5, QTableWidgetItem(str(age_days)))
            else:
                table.setItem(row, 5, QTableWidgetItem("Unknown"))

        # Adjust column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(table)

        # Action buttons row
        action_layout = QHBoxLayout()

        # Select All button
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._toggle_all_checkboxes(table, True))
        action_layout.addWidget(select_all_btn)

        # Deselect All button
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self._toggle_all_checkboxes(table, False))
        action_layout.addWidget(deselect_all_btn)

        action_layout.addStretch()

        # Delete Selected button
        delete_btn = QPushButton("Delete Selected from Cloud")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_selected_cloud_videos(table, storage_items, dialog))
        action_layout.addWidget(delete_btn)

        layout.addLayout(action_layout)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _toggle_all_checkboxes(self, table: 'QTableWidget', checked: bool):
        """Toggle all checkboxes in table."""
        for row in range(table.rowCount()):
            checkbox_item = table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _delete_selected_cloud_videos(self, table: 'QTableWidget', storage_items: list, dialog: 'QDialog'):
        """
        Delete selected cloud videos from remote storage using APIs.

        Args:
            table: QTableWidget containing storage item checkboxes
            storage_items: List of storage item dicts (from API queries)
            dialog: Parent dialog to close after deletion
        """
        import threading
        import time
        from PyQt6.QtWidgets import QProgressDialog

        # Get list of selected items
        selected_items = []
        for row in range(table.rowCount()):
            checkbox_item = table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                if row < len(storage_items):
                    selected_items.append(storage_items[row])

        if not selected_items:
            QMessageBox.warning(
                dialog,
                "No Items Selected",
                "Please select at least one item to delete."
            )
            return

        # Count by provider
        hume_count = sum(1 for item in selected_items if item["provider"] == "hume_ai")
        memories_count = sum(1 for item in selected_items if item["provider"] == "memories_ai")

        # Check for Hume AI selections (cannot delete)
        if hume_count > 0:
            QMessageBox.warning(
                dialog,
                "Hume AI Jobs Cannot Be Deleted",
                f"You selected {hume_count} Hume AI job(s).\n\n"
                "Hume AI does not provide a delete API.\n"
                "Jobs auto-expire after 30 days.\n\n"
                "Only Memories.ai videos can be deleted."
            )
            # Continue with only Memories.ai items
            selected_items = [item for item in selected_items if item["provider"] == "memories_ai"]
            if not selected_items:
                return

        # Show confirmation dialog
        confirm = QMessageBox.question(
            dialog,
            "Confirm Deletion",
            f"Delete {len(selected_items)} Memories.ai video(s) from cloud storage?\n\n"
            "This action cannot be undone. Videos will be permanently removed.\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Create progress dialog
        progress = QProgressDialog(
            "Deleting videos from Memories.ai...",
            "Cancel",
            0,
            len(selected_items),
            dialog
        )
        progress.setWindowTitle("Deleting Cloud Videos")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        # Track deletion results
        deletion_results = {
            "success": [],
            "failed": []
        }

        def deletion_worker():
            """Background thread for cloud video deletion."""
            try:
                for idx, item in enumerate(selected_items):
                    # Check if cancelled
                    if progress.wasCanceled():
                        logger.info("Cloud video deletion cancelled by user")
                        break

                    # Update progress
                    progress.setLabelText(
                        f"Deleting {idx + 1}/{len(selected_items)}: {item['name']}..."
                    )
                    progress.setValue(idx)

                    try:
                        # Delete using Memories.ai client
                        video_no = item["id"]
                        unique_id = item.get("unique_id", "default")

                        success = self.session_manager.cloud_analysis_manager.memories_client.delete_video(
                            video_no=video_no,
                            unique_id=unique_id
                        )

                        if success:
                            deletion_results["success"].append(item["name"])
                            logger.info(f"Successfully deleted Memories.ai video: {video_no}")
                        else:
                            deletion_results["failed"].append((item["name"], "API returned failure"))

                        # Add delay to avoid rate limits (3 seconds between deletions)
                        if idx < len(selected_items) - 1:
                            time.sleep(3)

                    except Exception as e:
                        logger.error(f"Failed to delete video {item['name']}: {e}", exc_info=True)
                        deletion_results["failed"].append((item["name"], str(e)))

                # Update progress to complete
                progress.setValue(len(selected_items))

            except Exception as e:
                logger.error(f"Cloud video deletion worker error: {e}", exc_info=True)

            finally:
                # Close progress dialog and show results
                def on_deletion_complete():
                    progress.close()

                    # Show results summary
                    success_count = len(deletion_results["success"])
                    failed_count = len(deletion_results["failed"])

                    if failed_count == 0:
                        QMessageBox.information(
                            dialog,
                            "Deletion Complete",
                            f"Successfully deleted {success_count} video(s) from Memories.ai cloud storage."
                        )
                    else:
                        error_details = "\n".join([
                            f"• {name}: {error}"
                            for name, error in deletion_results["failed"]
                        ])
                        QMessageBox.warning(
                            dialog,
                            "Deletion Partially Complete",
                            f"Successfully deleted: {success_count} video(s)\n"
                            f"Failed to delete: {failed_count} video(s)\n\n"
                            f"Errors:\n{error_details}"
                        )

                    # Close and reopen dialog to refresh the table with new API query
                    dialog.close()
                    self._on_manage_cloud_storage()

                # Schedule UI update on main thread
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, on_deletion_complete)

        # Start deletion in background thread
        thread = threading.Thread(target=deletion_worker, daemon=True)
        thread.start()

    def _on_upload_to_cloud(self, session_id: str):
        """Upload session videos to cloud for analysis."""
        from pathlib import Path
        import threading

        # Check if cloud features enabled
        if not self.config.is_cloud_features_enabled():
            QMessageBox.critical(
                self,
                "Cloud Features Disabled",
                "Cloud analysis features are not enabled.\n\n"
                "Please enable them in Settings tab."
            )
            return

        # Check which providers are enabled
        run_hume = self.config.is_hume_ai_enabled()
        run_memories = self.config.is_memories_ai_enabled()

        if not run_hume and not run_memories:
            QMessageBox.critical(
                self,
                "No Providers Enabled",
                "No cloud analysis providers are enabled.\n\n"
                "Please enable Hume AI or Memories.ai in Settings tab."
            )
            return

        # Get session from database
        session = self.database.get_session(session_id)
        if not session:
            QMessageBox.critical(self, "Error", "Session not found in database")
            return

        # Check video files exist
        data_dir = self.config.get_data_dir()
        cam_video = data_dir / session.cam_mp4_path
        screen_video = data_dir / session.screen_mp4_path if session.screen_mp4_path else None

        if not cam_video.exists():
            QMessageBox.critical(
                self,
                "Video Not Found",
                f"Webcam video not found:\n{cam_video}\n\n"
                "The session video files may have been deleted."
            )
            return

        # Check for duplicate uploads (CRITICAL: Prevent creating duplicate jobs)
        # First check if there's already an active upload for this session
        if session_id in self.active_uploads:
            QMessageBox.warning(
                self,
                "Upload Already In Progress",
                f"Upload already in progress for this session.\n\n"
                f"Please wait for the current upload to complete before retrying.\n\n"
                f"Check the Reports tab to see upload status."
            )
            return

        # Also check database for already-created jobs
        from ..core.models import CloudJobStatus, CloudProvider
        cloud_jobs = self.database.get_cloud_jobs_for_session(session_id)

        # Check if there are already active jobs for the enabled providers
        active_statuses = {CloudJobStatus.PENDING, CloudJobStatus.UPLOADING, CloudJobStatus.PROCESSING}
        duplicate_providers = []

        for job in cloud_jobs:
            if job.status in active_statuses:
                # Check if this job's provider matches one we're trying to upload to
                if run_hume and job.provider == CloudProvider.HUME_AI:
                    duplicate_providers.append("Hume AI")
                if run_memories and job.provider == CloudProvider.MEMORIES_AI:
                    duplicate_providers.append("Memories.ai")

        if duplicate_providers:
            # Duplicate upload detected - show warning and abort
            providers_str = " and ".join(duplicate_providers)
            QMessageBox.warning(
                self,
                "Upload Already In Progress",
                f"Upload already in progress for:\n\n" +
                "\n".join(f"  • {p}" for p in duplicate_providers) +
                f"\n\nPlease wait for the current upload to complete before retrying.\n\n"
                f"Check the Reports tab to see upload status."
            )
            return

        # Build provider list
        providers = []
        if run_hume:
            providers.append("Hume AI (emotion analysis)")
        if run_memories:
            providers.append("Memories.ai (pattern analysis)")

        # Calculate estimated cost
        cost_estimate = self._calculate_cloud_cost(session, run_hume, run_memories)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Upload to Cloud",
            f"Upload session videos to:\n\n" +
            "\n".join(f"  • {p}" for p in providers) +
            f"\n\nEstimated cost: {cost_estimate}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show status bar message (non-blocking)
        providers_list = []
        if run_hume:
            providers_list.append("Hume AI")
        if run_memories:
            providers_list.append("Memories.ai")
        providers_str = " and ".join(providers_list)
        self.status_bar.showMessage(f"Uploading to {providers_str}...")

        # Track upload
        if session_id not in self.active_uploads:
            self.active_uploads[session_id] = []

        # Create progress dialog (non-modal so user can still interact with app)
        from PyQt6.QtWidgets import QProgressDialog
        progress_dialog = QProgressDialog(
            f"Uploading session videos to {providers_str}...\n\nThis may take 10-30 seconds depending on file size.",
            "Cancel",
            0,
            0,  # 0,0 = indeterminate progress
            self
        )
        progress_dialog.setWindowTitle("Cloud Upload In Progress")
        progress_dialog.setWindowModality(Qt.WindowModality.NonModal)  # Non-modal: user can still use app
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setCancelButton(None)  # No cancel button (upload cannot be cancelled mid-flight)
        progress_dialog.show()

        # Run upload in background thread
        def upload_worker():
            try:
                logger.info(f"Starting cloud upload for session {session_id}")

                # Upload to cloud
                hume_job_id, memories_job_id = self.session_manager.cloud_analysis_manager.upload_session_for_analysis(
                    session_id=session_id,
                    cam_video_path=cam_video,
                    screen_video_path=screen_video,
                    run_hume=run_hume,
                    run_memories=run_memories
                )

                # Track job IDs
                job_ids = []
                if hume_job_id:
                    job_ids.append(hume_job_id)
                if memories_job_id:
                    job_ids.append(memories_job_id)

                logger.info(f"Cloud upload completed: hume={hume_job_id}, memories={memories_job_id}")

                # Schedule UI updates on main thread (CRITICAL: Never modify Qt widgets from background thread!)
                def on_upload_complete():
                    # CRITICAL: Remove from active uploads FIRST (before showing dialogs)
                    if session_id in self.active_uploads:
                        del self.active_uploads[session_id]

                    # Close progress dialog and ensure it's destroyed
                    progress_dialog.close()
                    progress_dialog.deleteLater()  # Force garbage collection

                    # Update status bar
                    self.status_bar.showMessage("✓ Upload completed - processing started", 10000)  # Show for 10 seconds

                    # Reload sessions list to show new cloud jobs
                    self._load_sessions_list()

                    # Show success notification after dialog closes (delayed to allow event loop to process close)
                    def show_success_message():
                        success_msg = "<div style='color: #2c3e50;'><h3 style='color: #27ae60;'>✓ Upload Successful!</h3>"
                        if hume_job_id:
                            success_msg += "<p><b>• Hume AI:</b> Processing started</p>"
                        if memories_job_id:
                            success_msg += "<p><b>• Memories.ai:</b> Processing started</p>"
                        success_msg += "<hr><p><b>Processing time:</b> 5-10 minutes</p>"
                        success_msg += "<p>Check back using the 'Check Status' button in the Reports tab.</p></div>"

                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Upload Complete")
                        msg_box.setText(success_msg)
                        msg_box.setIcon(QMessageBox.Icon.Information)
                        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                        msg_box.setTextFormat(Qt.TextFormat.RichText)
                        msg_box.exec()

                    QTimer.singleShot(100, show_success_message)  # 100ms delay ensures progress dialog closes first

                QTimer.singleShot(0, on_upload_complete)

            except Exception as e:
                logger.error(f"Upload failed: {e}", exc_info=True)

                # Schedule error handling on main thread (CRITICAL: Never modify Qt widgets from background thread!)
                def on_upload_error():
                    # CRITICAL: Remove from active uploads FIRST (before showing dialogs)
                    if session_id in self.active_uploads:
                        del self.active_uploads[session_id]

                    # Close progress dialog and ensure it's destroyed
                    progress_dialog.close()
                    progress_dialog.deleteLater()  # Force garbage collection

                    # Update status bar
                    self.status_bar.showMessage("✗ Upload failed", 10000)

                    # Show error message after dialog closes (delayed to allow event loop to process close)
                    def show_error_message():
                        QMessageBox.critical(
                            self,
                            "Upload Failed",
                            f"Failed to upload videos to cloud:\n\n{str(e)}\n\n"
                            "Check your internet connection and API keys."
                        )

                    QTimer.singleShot(100, show_error_message)  # 100ms delay ensures progress dialog closes first

                QTimer.singleShot(0, on_upload_error)

        thread = threading.Thread(target=upload_worker, daemon=True)
        thread.start()

    def _auto_upload_session(self, session_id: str, run_hume: bool, run_memories: bool):
        """
        Auto-upload session videos to cloud after session ends.
        Shows status bar messages (non-blocking) and session summary after completion.

        Args:
            session_id: Session to upload
            run_hume: Whether to upload to Hume AI
            run_memories: Whether to upload to Memories.ai
        """
        from pathlib import Path
        import threading

        logger.info(f"Auto-uploading session {session_id}: hume={run_hume}, memories={run_memories}")

        # Get session from database
        session = self.database.get_session(session_id)
        if not session:
            logger.error("Session not found in database for auto-upload")
            self._show_session_summary(session_id)
            return

        # Check video files exist
        data_dir = self.config.get_data_dir()
        cam_video = data_dir / session.cam_mp4_path
        screen_video = data_dir / session.screen_mp4_path if session.screen_mp4_path else None

        if not cam_video.exists():
            logger.error(f"Webcam video not found for auto-upload: {cam_video}")
            QMessageBox.warning(
                self,
                "Auto-Upload Failed",
                f"Webcam video not found:\n{cam_video}\n\n"
                "Skipping cloud upload."
            )
            self._show_session_summary(session_id)
            return

        # Show status bar message (non-blocking)
        providers_list = []
        if run_hume:
            providers_list.append("Hume AI")
        if run_memories:
            providers_list.append("Memories.ai")
        providers_str = " and ".join(providers_list)
        self.status_bar.showMessage(f"Auto-uploading to {providers_str}...", 5000)

        # Track auto-upload in active_uploads (enables quit warning)
        if session_id not in self.active_uploads:
            self.active_uploads[session_id] = []

        # Run upload in background thread
        def upload_worker():
            try:
                logger.info(f"Starting auto-upload for session {session_id}")

                # Upload to cloud
                hume_job_id, memories_job_id = self.session_manager.cloud_analysis_manager.upload_session_for_analysis(
                    session_id=session_id,
                    cam_video_path=cam_video,
                    screen_video_path=screen_video,
                    run_hume=run_hume,
                    run_memories=run_memories
                )

                # Track job IDs
                job_ids = []
                if hume_job_id:
                    job_ids.append(hume_job_id)
                if memories_job_id:
                    job_ids.append(memories_job_id)

                logger.info(f"Auto-upload completed: hume={hume_job_id}, memories={memories_job_id}")

                # Schedule UI updates on main thread (CRITICAL: Never modify Qt widgets from background thread!)
                def on_upload_complete():
                    # CRITICAL: Remove from active uploads FIRST (before showing dialogs)
                    if session_id in self.active_uploads:
                        del self.active_uploads[session_id]

                    # Update status bar
                    self.status_bar.showMessage("✓ Auto-upload completed - processing started", 10000)

                    # Reload sessions list to show new cloud jobs
                    self._load_sessions_list()

                    # Show session summary with upload status
                    self._show_session_summary(session_id, auto_upload_success=True)

                QTimer.singleShot(0, on_upload_complete)

            except Exception as e:
                logger.error(f"Auto-upload failed: {e}", exc_info=True)
                upload_error = str(e)

                # Schedule error handling on main thread (CRITICAL: Never modify Qt widgets from background thread!)
                def on_upload_error():
                    # CRITICAL: Remove from active uploads FIRST (before showing dialogs)
                    if session_id in self.active_uploads:
                        del self.active_uploads[session_id]

                    # Update status bar
                    self.status_bar.showMessage("✗ Auto-upload failed", 10000)

                    # Show error message
                    QMessageBox.critical(
                        self,
                        "Auto-Upload Failed",
                        f"Failed to auto-upload videos to cloud:\n\n{str(e)}\n\n"
                        "You can retry manually from the Reports tab."
                    )

                    # Show session summary with failure status
                    self._show_session_summary(session_id, auto_upload_success=False, auto_upload_error=upload_error)

                QTimer.singleShot(0, on_upload_error)

        thread = threading.Thread(target=upload_worker, daemon=True)
        thread.start()

    def _on_show_files(self, session_id: str):
        """Open session folder in system file manager."""
        import subprocess
        import platform
        from pathlib import Path

        # Get session from database
        session = self.database.get_session(session_id)
        if not session:
            QMessageBox.critical(self, "Error", "Session not found in database")
            return

        # Get session folder path
        data_dir = self.config.get_data_dir()
        session_folder = data_dir / f"sessions/{session_id}"

        if not session_folder.exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Session folder not found:\n{session_folder}\n\n"
                "The session files may have been deleted."
            )
            return

        # Open folder in system file manager
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(session_folder)])
            elif system == "Windows":
                subprocess.run(["explorer", str(session_folder)])
            else:  # Linux
                subprocess.run(["xdg-open", str(session_folder)])

            logger.info(f"Opened session folder: {session_folder}")

        except Exception as e:
            logger.error(f"Failed to open folder: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open session folder:\n\n{str(e)}"
            )

    def _on_delete_session(self, session_id: str):
        """Delete session with user confirmation."""
        from PyQt6.QtWidgets import QRadioButton, QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QButtonGroup
        from pathlib import Path
        import shutil

        # Get session from database
        session = self.database.get_session(session_id)
        if not session:
            QMessageBox.critical(self, "Error", "Session not found in database")
            return

        # Check if cloud jobs are processing
        cloud_jobs = self.database.get_cloud_jobs_for_session(session_id)
        processing_jobs = [j for j in cloud_jobs if j.status.value == "processing"]
        if processing_jobs:
            reply = QMessageBox.warning(
                self,
                "Cloud Jobs Processing",
                f"{len(processing_jobs)} cloud job(s) are still processing.\n\n"
                "If you delete this session, you may lose the cloud analysis results.\n\n"
                "Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Calculate folder size
        data_dir = self.config.get_data_dir()
        session_folder = data_dir / f"sessions/{session_id}"
        folder_size_mb = 0
        if session_folder.exists():
            folder_size_mb = sum(f.stat().st_size for f in session_folder.rglob('*') if f.is_file()) / (1024 * 1024)

        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Session")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Header
        header = QLabel(f"<b>Delete session \"{session.task_name}\"?</b>")
        header.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header)

        # Session info
        duration = self._format_duration(session)
        info = QLabel(
            f"Date: {session.started_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Duration: {duration}\n"
            f"Files: {folder_size_mb:.1f} MB"
        )
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(info)

        # Radio buttons for deletion options
        button_group = QButtonGroup(dialog)

        record_only_radio = QRadioButton("Delete record only (keep video files)")
        record_only_radio.setStyleSheet("margin-bottom: 5px;")
        button_group.addButton(record_only_radio, 1)
        layout.addWidget(record_only_radio)

        delete_all_radio = QRadioButton("Delete record + all files (cam.mp4, screen.mp4, snapshots)")
        delete_all_radio.setStyleSheet("margin-bottom: 15px;")
        delete_all_radio.setChecked(True)  # Default to delete all
        button_group.addButton(delete_all_radio, 2)
        layout.addWidget(delete_all_radio)

        # Warning
        warning = QLabel("⚠️ This action cannot be undone!")
        warning.setStyleSheet("color: #e74c3c; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(warning)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Delete")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog
        result = dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            return

        # Get selected option
        delete_files = (button_group.checkedId() == 2)

        # Perform deletion
        try:
            # Delete from database
            self.database.delete_session(session_id)
            logger.info(f"Deleted session {session_id} from database")

            # Delete files if requested
            if delete_files and session_folder.exists():
                shutil.rmtree(session_folder)
                logger.info(f"Deleted session folder: {session_folder}")

            # Reload sessions list
            self._load_sessions_list()

            # Show success message
            msg = "Session deleted successfully!"
            if delete_files:
                msg += f"\n\nFreed {folder_size_mb:.1f} MB of disk space."
            else:
                msg += f"\n\nVideo files kept in:\n{session_folder}"

            QMessageBox.information(self, "Session Deleted", msg)

        except Exception as e:
            logger.error(f"Failed to delete session: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Delete Failed",
                f"Failed to delete session:\n\n{str(e)}"
            )

    def _load_sessions_list(self):
        """Load all sessions from database and display in Reports tab with filtering."""
        from ..core.models import CloudJobStatus
        from datetime import datetime, timedelta

        # Clear existing session cards
        while self.sessions_layout.count():
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get all sessions from database (most recent first)
        all_sessions = self.database.get_all_sessions(limit=50)

        if not all_sessions:
            placeholder = QLabel("No sessions found. Complete a focus session to see reports here.")
            placeholder.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sessions_layout.addWidget(placeholder)
            return

        # Apply search filter
        search_text = self.search_box.text().strip().lower()
        if search_text:
            all_sessions = [s for s in all_sessions if search_text in s.task_name.lower()]

        # Apply date/status filter
        filter_type = self.filter_combo.currentText()
        filtered_sessions = self._apply_session_filter(all_sessions, filter_type)

        if not filtered_sessions:
            placeholder = QLabel(f"No sessions match the current filters.\n\nTry adjusting your search or filter settings.")
            placeholder.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setWordWrap(True)
            self.sessions_layout.addWidget(placeholder)
            return

        # Create card for each session
        for session in filtered_sessions:
            # Get cloud jobs for this session
            cloud_jobs = self.database.get_cloud_jobs_for_session(session.session_id)

            # Create session card
            card = self._create_session_card(session, cloud_jobs)
            self.sessions_layout.addWidget(card)
    
    def _apply_session_filter(self, sessions: list, filter_type: str) -> list:
        """Apply date/status filter to sessions list."""
        from datetime import datetime, timedelta
        
        if filter_type == "All Sessions":
            return sessions
        
        elif filter_type == "Today":
            today = datetime.now().date()
            return [s for s in sessions if s.started_at.date() == today]
        
        elif filter_type == "This Week":
            week_ago = datetime.now() - timedelta(days=7)
            return [s for s in sessions if s.started_at >= week_ago]
        
        elif filter_type == "This Month":
            month_ago = datetime.now() - timedelta(days=30)
            return [s for s in sessions if s.started_at >= month_ago]
        
        elif filter_type == "With Cloud Analysis":
            return [s for s in sessions if self.database.get_cloud_jobs_for_session(s.session_id)]
        
        elif filter_type == "Without Cloud Analysis":
            return [s for s in sessions if not self.database.get_cloud_jobs_for_session(s.session_id)]
        
        elif filter_type == "Upload Failed":
            from ..core.models import CloudJobStatus
            failed_sessions = []
            for s in sessions:
                cloud_jobs = self.database.get_cloud_jobs_for_session(s.session_id)
                if any(job.status == CloudJobStatus.FAILED for job in cloud_jobs):
                    failed_sessions.append(s)
            return failed_sessions
        
        return sessions
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        # Reload sessions with search filter applied
        self._load_sessions_list()
    
    def _on_filter_changed(self, filter_text: str):
        """Handle filter change."""
        # Reload sessions with filter applied
        self._load_sessions_list()
    
    def _on_batch_upload_sessions(self):
        """Upload all completed sessions without cloud analysis."""
        from PyQt6.QtWidgets import QProgressDialog
        from ..core.models import CloudJobStatus
        import threading
        
        # Find sessions that can be uploaded
        all_sessions = self.database.get_all_sessions(limit=50)
        uploadable_sessions = []
        
        for session in all_sessions:
            # Only include completed sessions
            if not session.ended_at:
                continue
            
            # Check if already has cloud jobs
            cloud_jobs = self.database.get_cloud_jobs_for_session(session.session_id)
            if not cloud_jobs:
                uploadable_sessions.append(session)
        
        if not uploadable_sessions:
            QMessageBox.information(
                self,
                "No Sessions to Upload",
                "All completed sessions have already been uploaded for cloud analysis."
            )
            return
        
        # Show confirmation
        cost_per_session = 0.15  # Rough estimate
        total_cost = len(uploadable_sessions) * cost_per_session
        
        reply = QMessageBox.question(
            self,
            "Batch Upload Sessions",
            f"Upload {len(uploadable_sessions)} session(s) to cloud for analysis?\n\n"
            f"Estimated total cost: ${total_cost:.2f}\n"
            f"Processing time: 5-10 minutes per session\n\n"
            "This will upload to all enabled providers (Hume AI and/or Memories.ai).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Show progress dialog
        progress = QProgressDialog(
            "Uploading sessions...",
            "Cancel",
            0,
            len(uploadable_sessions),
            self
        )
        progress.setWindowTitle("Batch Upload In Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)  # No cancel for simplicity
        progress.show()
        
        # Upload in background
        def batch_upload_worker():
            for i, session in enumerate(uploadable_sessions):
                if progress.wasCanceled():
                    break
                
                # Update progress
                def update_progress(index=i, task=session.task_name):
                    progress.setValue(index)
                    progress.setLabelText(f"Uploading session {index + 1} of {len(uploadable_sessions)}:\n{task}")
                
                QTimer.singleShot(0, update_progress)
                
                # Upload session
                try:
                    self.session_manager.cloud_analysis_manager.upload_session_for_analysis(
                        session_id=session.session_id,
                        cam_video_path=self.config.get_data_dir() / session.cam_mp4_path,
                        screen_video_path=self.config.get_data_dir() / session.screen_mp4_path if session.screen_mp4_path else None,
                        run_hume=self.config.is_hume_ai_enabled(),
                        run_memories=self.config.is_memories_ai_enabled()
                    )
                except Exception as e:
                    logger.error(f"Failed to upload session {session.session_id}: {e}")
            
            # Complete
            def on_complete():
                progress.close()
                progress.deleteLater()
                self._load_sessions_list()
                
                QMessageBox.information(
                    self,
                    "Batch Upload Complete",
                    f"Successfully uploaded {len(uploadable_sessions)} session(s).\n\n"
                    "Cloud processing started. Check back in 5-10 minutes."
                )
            
            QTimer.singleShot(0, on_complete)
        
        thread = threading.Thread(target=batch_upload_worker, daemon=True)
        thread.start()
    
    def _show_snapshot_details(self):
        """Show detailed snapshot analysis panel."""
        if not self.current_session_id:
            QMessageBox.information(
                self,
                "No Active Session",
                "Start a session to see snapshot details."
            )
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        # Get snapshots from database
        snapshots = self.database.get_snapshots_for_session(self.current_session_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📸 Snapshot Analysis Details")
        dialog.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Header summary
        summary = QLabel(f"<h2>Snapshot Analysis</h2><p>Total snapshots: <b>{len(snapshots)}</b></p>")
        summary.setStyleSheet("color: #2c3e50;")
        layout.addWidget(summary)
        
        # Create table for snapshot details
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Time", "Type", "Status", "Labels", "Confidence", "Latency"
        ])
        table.setRowCount(len(snapshots))
        
        for row, snapshot in enumerate(snapshots):
            # Time
            time_str = snapshot.captured_at.strftime("%H:%M:%S") if snapshot.captured_at else "N/A"
            table.setItem(row, 0, QTableWidgetItem(time_str))
            
            # Type
            snap_type = "📷 Camera" if "cam" in snapshot.jpeg_path else "🖥️ Screen"
            table.setItem(row, 1, QTableWidgetItem(snap_type))
            
            # Status
            status_map = {
                "pending": "⏳ Pending",
                "uploading": "⬆️ Uploading",
                "completed": "✅ Done",
                "failed": "❌ Failed"
            }
            status = status_map.get(snapshot.upload_status, snapshot.upload_status)
            table.setItem(row, 2, QTableWidgetItem(status))
            
            # Labels
            if snapshot.vision_labels:
                labels_str = ", ".join([f"{k}:{v:.0%}" for k, v in list(snapshot.vision_labels.items())[:2]])
                table.setItem(row, 3, QTableWidgetItem(labels_str))
            else:
                table.setItem(row, 3, QTableWidgetItem("Analyzing..."))
            
            # Confidence
            if snapshot.vision_labels:
                max_conf = max(snapshot.vision_labels.values()) if snapshot.vision_labels else 0
                table.setItem(row, 4, QTableWidgetItem(f"{max_conf:.0%}"))
            else:
                table.setItem(row, 4, QTableWidgetItem("-"))
            
            # Latency
            table.setItem(row, 5, QTableWidgetItem("-"))
        
        # Adjust columns
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(table)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def _show_distraction_details(self):
        """Show detailed distraction analysis with hysteresis voting details."""
        if not self.current_session_id:
            QMessageBox.information(
                self,
                "No Active Session",
                "Start a session to see distraction details."
            )
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QScrollArea, QFrame
        
        # Get events and snapshots from database
        events = self.database.get_session_events(self.current_session_id)
        snapshots = self.database.get_snapshots_for_session(self.current_session_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Distraction Analysis Details")
        dialog.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Build detailed report inline
        html = self._build_distraction_report(events, snapshots)
        
        text_display = QTextEdit()
        text_display.setReadOnly(True)
        text_display.setHtml(html)
        text_display.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                color: #2c3e50;
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 15px;
                line-height: 1.5;
            }
        """)
        content_layout.addWidget(text_display)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def _show_focus_details(self):
        """Show detailed focus analysis."""
        if not self.current_session_id:
            QMessageBox.information(
                self,
                "No Active Session",
                "Start a session to see focus details."
            )
            return
        
        # For now, show a simple summary - can be enhanced later
        try:
            stats = self.session_manager.get_session_stats()
            
            QMessageBox.information(
                self,
                "✓ Focus Analysis",
                f"Current Focus Statistics:\n\n"
                f"• Focus Ratio: {stats['focus_ratio']*100:.1f}%\n"
                f"• Total Snapshots: {stats['total_snapshots']}\n"
                f"• Distraction Events: {stats['total_events']}\n\n"
                f"The hysteresis voting engine (K=3) analyzes patterns across "
                f"multiple snapshots to confirm distractions before alerting."
            )
        except Exception as e:
            logger.error(f"Failed to show focus details: {e}")
    
    def _build_distraction_report(self, events: list, snapshots: list) -> str:
        """Build detailed HTML report for distraction analysis."""
        
        html = """<div style="color: #2c3e50; line-height: 1.6;">"""
        
        # Header
        html += """<h1 style="color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px;">
        ⚠️ Distraction Analysis Report</h1>"""
        
        # Summary stats
        distraction_events = [e for e in events if e.event_type == "distraction"]
        total_snapshots = len(snapshots)
        
        html += f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3>Overview</h3>
        <p><b>Total Snapshots Analyzed:</b> {total_snapshots}</p>
        <p><b>Distraction Events Detected:</b> {len(distraction_events)}</p>
        <p><b>Hysteresis Voting:</b> K=3 (requires pattern across 3+ consecutive snapshots)</p>
        <p><b>Minimum Span:</b> 3.5 minutes (prevents false positives from brief glances)</p>
        </div>"""
        
        # Hysteresis Voting Explanation
        html += """<h2 style="color: #3498db; margin-top: 25px;">🔬 How the Voting Engine Works</h2>
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 6px; border-left: 4px solid #3498db;">
        <p><b>Pattern-Confirmed Detection:</b> The system uses K=3 hysteresis voting to eliminate false positives.</p>
        <ul>
            <li>Each snapshot is analyzed by AI (webcam + screen)</li>
            <li>Results are accumulated in a rolling buffer (last 3 snapshots)</li>
            <li>A distraction is only flagged if ≥2 of 3 snapshots show the same pattern</li>
            <li>Minimum 3.5 minute span required across snapshots (debounce)</li>
            <li>This ensures brief glances don't trigger false alerts</li>
        </ul>
        </div>"""
        
        # Distraction Events with Voting Details
        if distraction_events:
            html += f"""<h2 style="color: #e74c3c; margin-top: 25px;">📋 Detected Distraction Events ({len(distraction_events)})</h2>"""
            
            for i, event in enumerate(distraction_events, 1):
                # Parse event data
                event_data = event.event_data if isinstance(event.event_data, dict) else {}
                distraction_type = event_data.get("distraction_type", "Unknown")
                confidence = event_data.get("confidence", 0) * 100
                duration = event_data.get("duration_sec", 0) / 60
                vision_votes = event_data.get("vision_votes", {})
                
                html += f"""<div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #f39c12;">
                <h3 style="margin-top: 0;">Event #{i}: {distraction_type}</h3>
                <p><b>Time:</b> {event.timestamp.strftime('%H:%M:%S') if event.timestamp else 'N/A'}</p>
                <p><b>Duration:</b> {duration:.1f} minutes</p>
                <p><b>Confidence:</b> {confidence:.0f}%</p>"""
                
                # Show voting breakdown
                if vision_votes:
                    html += """<h4 style="color: #3498db; margin-top: 15px;">🗳️ Voting Breakdown (K=3 Hysteresis)</h4>
                    <div style="background-color: white; padding: 10px; border-radius: 4px;">
                    <p style="font-size: 12px; color: #7f8c8d; margin-bottom: 8px;">
                    AI classifications across 3 consecutive snapshots:</p>"""
                    
                    for label, count in vision_votes.items():
                        percentage = (count / 3) * 100
                        bar_width = int(percentage)
                        
                        # Color code based on label type
                        if any(word in label.lower() for word in ["away", "off", "absent", "sleep", "phone"]):
                            color = "#e74c3c"  # Red for distraction
                        elif "video" in label.lower() or "social" in label.lower() or "game" in label.lower():
                            color = "#f39c12"  # Orange for screen distraction
                        else:
                            color = "#3498db"  # Blue for neutral
                        
                        html += f"""<div style="margin: 5px 0;">
                        <span style="font-weight: bold; width: 150px; display: inline-block;">{label}:</span>
                        <span style="display: inline-block; background-color: #ecf0f1; width: 200px; height: 20px; border-radius: 3px; position: relative; overflow: hidden; vertical-align: middle;">
                            <span style="display: block; background-color: {color}; width: {bar_width}%; height: 100%;"></span>
                        </span>
                        <span style="margin-left: 10px; color: {color}; font-weight: bold;">{count}/3 snapshots ({percentage:.0f}%)</span>
                        </div>"""
                    
                    html += "</div>"
                
                html += "</div>"
        else:
            html += """<div style="background-color: #d4edda; padding: 15px; border-radius: 6px; margin-top: 20px;">
            <p style="color: #155724; font-size: 16px; margin: 0;">
            <b>✅ No distractions detected so far!</b><br>
            Keep up the great focus! 🎯
            </p>
            </div>"""
        
        # Snapshot Timeline
        html += """<h2 style="color: #3498db; margin-top: 25px;">📊 Snapshot Timeline</h2>
        <p style="font-size: 13px; color: #7f8c8d;">Real-time AI analysis results for each snapshot captured:</p>"""
        
        # Group snapshots by timestamp (cam + screen pairs)
        from collections import defaultdict
        from datetime import datetime
        
        snapshot_pairs = defaultdict(list)
        for snap in snapshots:
            time_key = snap.captured_at.replace(second=0, microsecond=0) if snap.captured_at else datetime.now()
            snapshot_pairs[time_key].append(snap)
        
        for time_key in sorted(snapshot_pairs.keys(), reverse=True):
            pair = snapshot_pairs[time_key]
            html += f"""<div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #3498db;">
            <p style="margin: 0; font-weight: bold;">⏱️ {time_key.strftime('%H:%M:%S')}</p>"""
            
            for snap in pair:
                snap_type = "📷 Camera" if "cam" in snap.jpeg_path else "🖥️ Screen"
                
                if snap.vision_labels:
                    labels_display = "<br>".join([
                        f"&nbsp;&nbsp;• <b>{k}</b>: {v:.0%}"
                        for k, v in sorted(snap.vision_labels.items(), key=lambda x: x[1], reverse=True)[:3]
                    ])
                    html += f"""<p style="margin: 5px 0 5px 15px; font-size: 12px;">
                    {snap_type}: <span style="color: #27ae60;">✓ Analyzed</span><br>
                    {labels_display}
                    </p>"""
                else:
                    html += f"""<p style="margin: 5px 0 5px 15px; font-size: 12px; color: #95a5a6;">
                    {snap_type}: Pending analysis...
                    </p>"""
            
            html += "</div>"
        
        html += "</div>"
        
        text_display.setHtml(html)
        
        layout.addWidget(text_display)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def _build_distraction_report(self, events: list, snapshots: list) -> str:
        """Build detailed HTML report for distraction analysis."""
        
        html = """<div style="color: #2c3e50; line-height: 1.6;">"""
        
        # Header
        html += """<h1 style="color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px;">
        ⚠️ Distraction Analysis Report</h1>"""
        
        # Summary stats
        distraction_events = [e for e in events if e.event_type == "distraction"]
        total_snapshots = len(snapshots)
        
        html += f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3>Overview</h3>
        <p><b>Total Snapshots Analyzed:</b> {total_snapshots}</p>
        <p><b>Distraction Events Detected:</b> {len(distraction_events)}</p>
        <p><b>Hysteresis Voting:</b> K=3 (requires pattern across 3+ consecutive snapshots)</p>
        <p><b>Minimum Span:</b> 3.5 minutes (prevents false positives from brief glances)</p>
        </div>"""
        
        # Hysteresis Voting Explanation
        html += """<h2 style="color: #3498db; margin-top: 25px;">🔬 How the Voting Engine Works</h2>
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 6px; border-left: 4px solid #3498db;">
        <p><b>Pattern-Confirmed Detection:</b> The system uses K=3 hysteresis voting to eliminate false positives.</p>
        <ul>
            <li>Each snapshot is analyzed by AI (webcam + screen)</li>
            <li>Results are accumulated in a rolling buffer (last 3 snapshots)</li>
            <li>A distraction is only flagged if ≥2 of 3 snapshots show the same pattern</li>
            <li>Minimum 3.5 minute span required across snapshots (debounce)</li>
            <li>This ensures brief glances don't trigger false alerts</li>
        </ul>
        </div>"""
        
        # Distraction Events with Voting Details
        if distraction_events:
            html += f"""<h2 style="color: #e74c3c; margin-top: 25px;">📋 Detected Distraction Events ({len(distraction_events)})</h2>"""
            
            for i, event in enumerate(distraction_events, 1):
                # Parse event data
                event_data = event.event_data if isinstance(event.event_data, dict) else {}
                distraction_type = event_data.get("distraction_type", "Unknown")
                confidence = event_data.get("confidence", 0) * 100
                duration = event_data.get("duration_sec", 0) / 60
                vision_votes = event_data.get("vision_votes", {})
                
                html += f"""<div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #f39c12;">
                <h3 style="margin-top: 0;">Event #{i}: {distraction_type}</h3>
                <p><b>Time:</b> {event.timestamp.strftime('%H:%M:%S') if event.timestamp else 'N/A'}</p>
                <p><b>Duration:</b> {duration:.1f} minutes</p>
                <p><b>Confidence:</b> {confidence:.0f}%</p>"""
                
                # Show voting breakdown
                if vision_votes:
                    html += """<h4 style="color: #3498db; margin-top: 15px;">🗳️ Voting Breakdown (K=3 Hysteresis)</h4>
                    <div style="background-color: white; padding: 10px; border-radius: 4px;">
                    <p style="font-size: 12px; color: #7f8c8d; margin-bottom: 8px;">
                    AI classifications across 3 consecutive snapshots:</p>"""
                    
                    for label, count in vision_votes.items():
                        percentage = (count / 3) * 100
                        bar_width = int(percentage)
                        
                        # Color code based on label type
                        if any(word in label.lower() for word in ["away", "off", "absent", "sleep", "phone"]):
                            color = "#e74c3c"  # Red for distraction
                        elif "video" in label.lower() or "social" in label.lower() or "game" in label.lower():
                            color = "#f39c12"  # Orange for screen distraction
                        else:
                            color = "#3498db"  # Blue for neutral
                        
                        html += f"""<div style="margin: 5px 0;">
                        <span style="font-weight: bold; width: 150px; display: inline-block;">{label}:</span>
                        <span style="display: inline-block; background-color: #ecf0f1; width: 200px; height: 20px; border-radius: 3px; position: relative; overflow: hidden; vertical-align: middle;">
                            <span style="display: block; background-color: {color}; width: {bar_width}%; height: 100%;"></span>
                        </span>
                        <span style="margin-left: 10px; color: {color}; font-weight: bold;">{count}/3 snapshots ({percentage:.0f}%)</span>
                        </div>"""
                    
                    html += "</div>"
                
                html += "</div>"
        else:
            html += """<div style="background-color: #d4edda; padding: 15px; border-radius: 6px; margin-top: 20px;">
            <p style="color: #155724; font-size: 16px; margin: 0;">
            <b>✅ No distractions detected so far!</b><br>
            Keep up the great focus! 🎯
            </p>
            </div>"""
        
        # Snapshot Timeline
        html += """<h2 style="color: #3498db; margin-top: 25px;">📊 Snapshot Timeline</h2>
        <p style="font-size: 13px; color: #7f8c8d;">Real-time AI analysis results for each snapshot captured:</p>"""
        
        # Group snapshots by timestamp (cam + screen pairs)
        from collections import defaultdict
        from datetime import datetime
        
        snapshot_pairs = defaultdict(list)
        for snap in snapshots:
            time_key = snap.captured_at.replace(second=0, microsecond=0) if snap.captured_at else datetime.now()
            snapshot_pairs[time_key].append(snap)
        
        for time_key in sorted(snapshot_pairs.keys(), reverse=True):
            pair = snapshot_pairs[time_key]
            html += f"""<div style="background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #3498db;">
            <p style="margin: 0; font-weight: bold;">⏱️ {time_key.strftime('%H:%M:%S')}</p>"""
            
            for snap in pair:
                snap_type = "📷 Camera" if "cam" in snap.jpeg_path else "🖥️ Screen"
                
                if snap.vision_labels:
                    labels_display = "<br>".join([
                        f"&nbsp;&nbsp;• <b>{k}</b>: {v:.0%}"
                        for k, v in sorted(snap.vision_labels.items(), key=lambda x: x[1], reverse=True)[:3]
                    ])
                    html += f"""<p style="margin: 5px 0 5px 15px; font-size: 12px;">
                    {snap_type}: <span style="color: #27ae60;">✓ Analyzed</span><br>
                    {labels_display}
                    </p>"""
                else:
                    html += f"""<p style="margin: 5px 0 5px 15px; font-size: 12px; color: #95a5a6;">
                    {snap_type}: Pending analysis...
                    </p>"""
            
            html += "</div>"
        
        html += "</div>"
        
        return html

    def _create_session_card(self, session, cloud_jobs):
        """
        Create a card widget for a session.

        Args:
            session: Session object
            cloud_jobs: List of CloudAnalysisJob objects for this session
        """
        from PyQt6.QtWidgets import QFrame, QGridLayout
        from ..core.models import CloudJobStatus, CloudProvider

        card = QFrame()
        card.setFrameShape(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: #ecf0f1;
                padding: 15px;
            }
        """)

        layout = QGridLayout(card)

        # Session info
        row = 0
        task_label = QLabel(f"<b>{session.task_name}</b>")
        task_label.setStyleSheet("font-size: 16px; color: #2c3e50;")
        layout.addWidget(task_label, row, 0, 1, 2)

        row += 1
        date_label = QLabel(f"Date: {session.started_at.strftime('%Y-%m-%d %H:%M')}")
        date_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
        layout.addWidget(date_label, row, 0)

        duration_label = QLabel(f"Duration: {self._format_duration(session)}")
        duration_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
        layout.addWidget(duration_label, row, 1)

        # Cloud analysis section
        row += 1

        if not cloud_jobs:
            # No cloud jobs - show upload button if session is complete
            if session.ended_at:
                # Check if upload is in progress for this session
                is_uploading = session.session_id in self.active_uploads

                # Enhanced upload button with progress indicator
                btn_text = "⬆️ Uploading..." if is_uploading else "☁️ Upload to Cloud for Analysis"
                upload_btn = QPushButton(btn_text)
                upload_btn.setEnabled(not is_uploading)  # Disable if uploading
                upload_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9b59b6;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 12px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #8e44ad;
                    }
                    QPushButton:disabled {
                        background-color: #95a5a6;
                        color: #ecf0f1;
                    }
                """)
                
                # Add tooltip with cost estimate
                duration_sec = (session.ended_at - session.started_at).total_seconds() if session.ended_at else 0
                cost_estimate = (duration_sec / 120) * 2 * 0.055  # Rough estimate
                upload_btn.setToolTip(
                    f"Upload videos for cloud analysis\n"
                    f"Estimated cost: ${cost_estimate:.2f}\n"
                    f"Processing time: 5-10 minutes"
                )
                
                upload_btn.clicked.connect(lambda: self._on_upload_to_cloud(session.session_id))
                layout.addWidget(upload_btn, row, 0, 1, 2)
                row += 1
        else:
            # Has cloud jobs - show status for each
            for job in cloud_jobs:
                status_label = QLabel(f"{job.provider.value}: {self._get_status_badge(job.status)}")
                status_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
                layout.addWidget(status_label, row, 0)

                # Only show check status button for PROCESSING jobs
                if job.status == CloudJobStatus.PROCESSING:
                    # Check if this job is currently being refreshed
                    is_refreshing = job.job_id in self.active_refresh_jobs

                    # Create button with spinner icon when checking
                    btn_text = "🔄 Checking..." if is_refreshing else "🔍 Check Status"
                    
                    # Add last checked timestamp if available
                    if job.job_id in self.job_last_checked:
                        from datetime import datetime
                        last_check = self.job_last_checked[job.job_id]
                        elapsed = (datetime.now() - last_check).total_seconds()
                        
                        if elapsed < 60:
                            time_str = f"{int(elapsed)}s ago"
                        elif elapsed < 3600:
                            time_str = f"{int(elapsed / 60)}m ago"
                        else:
                            time_str = f"{int(elapsed / 3600)}h ago"
                        
                        btn_text += f" ({time_str})" if not is_refreshing else ""
                    
                    refresh_btn = QPushButton(btn_text)
                    refresh_btn.setEnabled(not is_refreshing)  # Disable if refreshing
                    refresh_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #2980b9;
                        }
                        QPushButton:disabled {
                            background-color: #95a5a6;
                            color: #ecf0f1;
                        }
                    """)
                    
                    tooltip_text = "Check if cloud processing is complete and retrieve results"
                    if job.job_id in self.job_auto_refresh_timers:
                        tooltip_text += "\n\nAuto-refresh: Will check automatically every 60 seconds"
                    
                    refresh_btn.setToolTip(tooltip_text)
                    refresh_btn.clicked.connect(lambda checked, jid=job.job_id: self._on_refresh_job(jid))
                    layout.addWidget(refresh_btn, row, 1)

                # Show retry button for FAILED jobs
                elif job.status == CloudJobStatus.FAILED:
                    # Check if upload is in progress for this session
                    is_uploading = session.session_id in self.active_uploads

                    retry_btn = QPushButton("Uploading..." if is_uploading else "Retry Upload")
                    retry_btn.setEnabled(not is_uploading)  # Disable if uploading
                    retry_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e67e22;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #d35400;
                        }
                        QPushButton:disabled {
                            background-color: #95a5a6;
                            color: #ecf0f1;
                        }
                    """)
                    retry_btn.clicked.connect(lambda checked, sid=session.session_id: self._on_upload_to_cloud(sid))
                    layout.addWidget(retry_btn, row, 1)

                # Show details button for COMPLETED jobs
                elif job.status == CloudJobStatus.COMPLETED:
                    details_btn = QPushButton("Show Details")
                    details_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #27ae60;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #229954;
                        }
                    """)
                    details_btn.clicked.connect(lambda checked, jid=job.job_id: self._on_show_cloud_details(jid))
                    layout.addWidget(details_btn, row, 1)

                row += 1

        # Action buttons row
        row += 1
        action_layout = QHBoxLayout()

        # Show Files button
        show_files_btn = QPushButton("📁 Show Files")
        show_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        show_files_btn.clicked.connect(lambda: self._on_show_files(session.session_id))
        action_layout.addWidget(show_files_btn)

        # Delete Session button
        delete_btn = QPushButton("🗑️ Delete Session")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(lambda: self._on_delete_session(session.session_id))
        action_layout.addWidget(delete_btn)

        action_layout.addStretch()

        # Add action layout to grid (span 2 columns)
        layout.addLayout(action_layout, row, 0, 1, 2)

        return card

    def _format_duration(self, session) -> str:
        """Format session duration."""
        if not session.ended_at:
            return "In progress"

        duration = session.ended_at - session.started_at
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} min"

    def _calculate_cloud_cost(self, session, run_hume: bool, run_memories: bool) -> str:
        """
        Calculate estimated cloud analysis cost based on session duration.

        Args:
            session: Session object
            run_hume: Whether Hume AI will be used
            run_memories: Whether Memories.ai will be used

        Returns:
            Cost estimate string (e.g., "$1.50-$3.00")
        """
        if not session.ended_at:
            return "~$0.50+"  # In-progress session

        # Calculate duration in minutes
        duration = session.ended_at - session.started_at
        minutes = duration.total_seconds() / 60

        # Pricing per minute (estimated)
        HUME_COST_PER_MIN = 0.20
        MEMORIES_COST_PER_MIN = 0.40
        MINIMUM_COST = 0.50

        # Calculate base costs
        hume_cost = (minutes * HUME_COST_PER_MIN) if run_hume else 0
        memories_cost = (minutes * MEMORIES_COST_PER_MIN) if run_memories else 0
        total_cost = hume_cost + memories_cost

        # Apply minimum
        total_cost = max(total_cost, MINIMUM_COST)

        # Format cost string
        if minutes < 2:
            # Very short session - show flat minimum
            return f"~${MINIMUM_COST:.2f}"
        elif minutes < 5:
            # Short session - show approximate cost
            return f"~${total_cost:.2f}"
        else:
            # Longer session - show range (±20%)
            low_estimate = total_cost * 0.8
            high_estimate = total_cost * 1.2
            return f"${low_estimate:.2f}-${high_estimate:.2f}"

    def _get_status_badge(self, status) -> str:
        """Get enhanced status badge with icons and colors."""
        from ..core.models import CloudJobStatus

        badges = {
            CloudJobStatus.PENDING: ('⏸️', '#95a5a6', 'PENDING'),
            CloudJobStatus.UPLOADING: ('⬆️', '#f39c12', 'UPLOADING'),
            CloudJobStatus.PROCESSING: ('🔄', '#3498db', 'PROCESSING'),
            CloudJobStatus.COMPLETED: ('✅', '#27ae60', 'COMPLETED'),
            CloudJobStatus.FAILED: ('❌', '#e74c3c', 'FAILED')
        }

        icon, color, text = badges.get(status, ('❓', '#95a5a6', 'UNKNOWN'))
        return f'<span style="color: {color}; font-weight: bold;">{icon} {text}</span>'

    def _on_refresh_all_sessions(self):
        """Refresh all sessions with processing cloud jobs."""
        logger.info("Refreshing all cloud analysis jobs...")
        # TODO: Implement refresh all logic
        self._load_sessions_list()

    def _on_refresh_job(self, job_id: str):
        """
        Refresh a specific cloud analysis job.

        Polls the cloud provider to check if processing is complete.
        If complete, retrieves results and deletes cloud videos.
        """
        import threading
        from ..core.models import CloudJobStatus

        logger.info(f"Refreshing cloud job: {job_id}")

        # Check if this job is already being refreshed
        if job_id in self.active_refresh_jobs:
            logger.warning(f"Job {job_id} is already being refreshed, skipping duplicate request")
            return

        # Track active refresh
        self.active_refresh_jobs.add(job_id)

        # Reload sessions list immediately to show button as disabled
        self._load_sessions_list()

        # Run in background thread to avoid blocking UI
        def refresh_worker():
            try:
                # Check status
                if not self.session_manager.cloud_analysis_manager:
                    logger.error("Cloud analysis manager not available")
                    return

                status = self.session_manager.cloud_analysis_manager.check_job_status(job_id)

                if status == CloudJobStatus.COMPLETED:
                    # Job completed - retrieve results
                    logger.info(f"Job {job_id} completed, retrieving results...")
                    results_path = self.session_manager.cloud_analysis_manager.retrieve_and_store_results(job_id)

                    if results_path:
                        # Delete cloud videos
                        self.session_manager.cloud_analysis_manager.delete_cloud_videos(job_id)

                        # Notify user
                        self.ui_queue.put({
                            "type": "cloud_job_complete",
                            "job_id": job_id,
                            "results_path": str(results_path)
                        })
                    else:
                        logger.error(f"Failed to retrieve results for job {job_id}")

                elif status == CloudJobStatus.PROCESSING:
                    # Job still processing - schedule another check in 30 seconds
                    logger.info(f"Job {job_id} still processing, will check again in 30 seconds")

                    def retry_check():
                        if job_id in self.active_refresh_jobs:
                            self._on_refresh_job(job_id)

                    QTimer.singleShot(30000, retry_check)  # 30 second delay
                    return  # Don't complete the refresh yet

                elif status == CloudJobStatus.FAILED:
                    # Job failed - log error but don't retry automatically
                    logger.error(f"Job {job_id} failed permanently")

                else:
                    # Unknown status - log warning
                    logger.warning(f"Job {job_id} has unknown status: {status}")

                # CRITICAL: Schedule UI update on main thread (CANNOT modify Qt widgets from background thread!)
                def on_refresh_complete():
                    # Update last checked timestamp
                    from datetime import datetime
                    self.job_last_checked[job_id] = datetime.now()
                    
                    # Remove from active refreshes
                    if job_id in self.active_refresh_jobs:
                        self.active_refresh_jobs.remove(job_id)
                    
                    # Setup auto-refresh timer for PROCESSING jobs
                    if status == CloudJobStatus.PROCESSING:
                        self._setup_auto_refresh_timer(job_id)
                    else:
                        # Job completed or failed, stop auto-refresh
                        self._cancel_auto_refresh_timer(job_id)
                    
                    # Reload sessions list to update button state
                    self._load_sessions_list()

                QTimer.singleShot(0, on_refresh_complete)

            except Exception as e:
                logger.error(f"Error refreshing job {job_id}: {e}", exc_info=True)

                # Remove from active refreshes even on error
                def on_refresh_error():
                    if job_id in self.active_refresh_jobs:
                        self.active_refresh_jobs.remove(job_id)
                    self._load_sessions_list()

                QTimer.singleShot(0, on_refresh_error)

        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()
    
    def _setup_auto_refresh_timer(self, job_id: str) -> None:
        """Setup auto-refresh timer for PROCESSING cloud job."""
        # Cancel existing timer if any
        self._cancel_auto_refresh_timer(job_id)
        
        # Create new timer (60 second interval)
        timer = QTimer()
        timer.timeout.connect(lambda: self._auto_refresh_job(job_id))
        timer.start(60000)  # 60 seconds
        
        self.job_auto_refresh_timers[job_id] = timer
        logger.info(f"Auto-refresh timer started for job {job_id} (60s interval)")
    
    def _cancel_auto_refresh_timer(self, job_id: str) -> None:
        """Cancel auto-refresh timer for a job."""
        if job_id in self.job_auto_refresh_timers:
            timer = self.job_auto_refresh_timers[job_id]
            timer.stop()
            del self.job_auto_refresh_timers[job_id]
            logger.info(f"Auto-refresh timer cancelled for job {job_id}")
    
    def _auto_refresh_job(self, job_id: str) -> None:
        """Auto-refresh a job (called by timer)."""
        # Check if job still exists and is still processing
        job = self.database.get_cloud_job(job_id)
        if not job:
            self._cancel_auto_refresh_timer(job_id)
            return
        
        from ..core.models import CloudJobStatus
        if job.status != CloudJobStatus.PROCESSING:
            # Job no longer processing, cancel auto-refresh
            self._cancel_auto_refresh_timer(job_id)
            self._load_sessions_list()  # Refresh UI
            return
        
        # Trigger manual refresh
        logger.info(f"Auto-refreshing job {job_id}...")
        self._on_refresh_job(job_id)

    def _on_show_cloud_details(self, job_id: str):
        """
        Display cloud analysis results for a completed job.

        Args:
            job_id: Cloud analysis job ID
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QSizePolicy, QScrollArea, QFrame
        from pathlib import Path
        import json
        from ..core.models import CloudProvider

        logger.info(f"Showing cloud details for job: {job_id}")

        try:
            # Get job from database
            job = self.database.get_cloud_job(job_id)
            if not job:
                QMessageBox.critical(self, "Error", "Cloud job not found in database")
                return

            # Check if results are available
            if not job.results_file_path:
                QMessageBox.warning(
                    self,
                    "Results Not Available",
                    "Cloud analysis results have not been retrieved yet.\n\n"
                    "Click 'Check Status' to fetch results."
                )
                return

            # Read results JSON file
            results_path = Path(job.results_file_path)
            if not results_path.exists():
                QMessageBox.critical(
                    self,
                    "Results File Missing",
                    f"Results file not found:\n{results_path}\n\n"
                    "The results file may have been deleted."
                )
                return

            with open(results_path, 'r') as f:
                results = json.load(f)

            # Format results based on provider
            if job.provider == CloudProvider.HUME_AI:
                title = "Hume AI - Emotion Analysis Results"
                formatted_text = self._format_hume_results(results)
            elif job.provider == CloudProvider.MEMORIES_AI:
                title = "Memories.ai - Pattern Analysis Results"
                formatted_text = self._format_memories_results(results)
            else:
                QMessageBox.critical(self, "Error", f"Unknown provider: {job.provider}")
                return

            # Create dialog to display results
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setMinimumSize(800, 600)  # Increased size for better readability
            dialog.resize(900, 700)  # Default size

            layout = QVBoxLayout(dialog)

            # Create scroll area for the text content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Text display with results
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            text_display.setMarkdown(formatted_text)
            text_display.setStyleSheet("""
                QTextEdit {
                    font-size: 13px;
                    color: #000000;
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 10px;
                    line-height: 1.4;
                }
            """)

            # Set the text display as the scroll area's widget
            scroll_area.setWidget(text_display)
            layout.addWidget(scroll_area)

            # Close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.exec()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse results JSON: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Invalid Results",
                f"Failed to parse results file:\n\n{str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to show cloud details: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load cloud analysis results:\n\n{str(e)}"
            )

    def _calculate_emotion_percentages(self, timeline: list) -> dict:
        """
        Calculate percentage of time spent in each emotion state.

        Args:
            timeline: List of frame dicts with emotions

        Returns:
            Dict mapping emotion -> percentage (0.0-100.0)
        """
        if not timeline:
            return {}

        # Count frames where each emotion is dominant (highest value)
        emotion_counts = {}
        total_frames = len(timeline)

        for frame in timeline:
            emotions = frame.get("emotions", {})
            if not emotions:
                continue

            # Find dominant emotion for this frame
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            emotion_counts[dominant_emotion] = emotion_counts.get(dominant_emotion, 0) + 1

        # Convert counts to percentages
        percentages = {
            emotion: (count / total_frames) * 100
            for emotion, count in emotion_counts.items()
        }

        return percentages

    def _identify_primary_emotion(self, emotion_percentages: dict) -> str:
        """
        Identify the primary (most frequent) emotion and provide interpretation.

        Args:
            emotion_percentages: Dict from _calculate_emotion_percentages

        Returns:
            Human-readable string describing primary emotion and interpretation
        """
        if not emotion_percentages:
            return "No dominant emotion detected"

        # Find emotion with highest percentage
        primary_emotion, percentage = max(emotion_percentages.items(), key=lambda x: x[1])

        # Emotion interpretations for productivity context
        interpretations = {
            "concentration": "high engagement and focus on task",
            "confusion": "cognitive load or difficulty understanding material",
            "boredom": "disengagement or lack of challenge",
            "frustration": "obstacles or technical difficulties",
            "stress": "time pressure or overwhelming complexity",
            "tiredness": "fatigue or need for break",
            "interest": "curiosity and active learning",
            "determination": "persistence despite challenges",
            "satisfaction": "accomplishment and progress",
            "distraction": "wandering attention or external interruptions"
        }

        interpretation = interpretations.get(primary_emotion.lower(), "emotional state detected")

        return f"**{primary_emotion.title()}** ({percentage:.1f}%) - suggests {interpretation}"

    def _create_emotion_timeline_ascii(self, timeline: list, width: int = 60) -> str:
        """
        Create ASCII visualization of emotion timeline.

        Args:
            timeline: List of frame dicts with emotions
            width: Character width of timeline (default 60)

        Returns:
            Multi-line ASCII art string
        """
        if not timeline:
            return "No timeline data available"

        # Get top 3 most frequent emotions
        emotion_percentages = self._calculate_emotion_percentages(timeline)
        top_emotions = sorted(emotion_percentages.items(), key=lambda x: x[1], reverse=True)[:3]

        if not top_emotions:
            return "No emotion data available"

        # Create timeline for each top emotion
        lines = []

        for emotion, percentage in top_emotions:
            # Build timeline string
            timeline_str = emotion.title().ljust(15) + " | "

            # Calculate segments (each char represents ~2% of timeline)
            segments_per_char = len(timeline) / width

            for i in range(width):
                # Find frames in this segment
                start_idx = int(i * segments_per_char)
                end_idx = int((i + 1) * segments_per_char)
                segment_frames = timeline[start_idx:end_idx]

                # Check if this emotion is dominant in this segment
                dominant_count = 0
                for frame in segment_frames:
                    emotions = frame.get("emotions", {})
                    if emotions:
                        dominant = max(emotions.items(), key=lambda x: x[1])[0]
                        if dominant == emotion:
                            dominant_count += 1

                # Use different symbols based on dominance strength
                if not segment_frames:
                    timeline_str += " "
                elif dominant_count / len(segment_frames) > 0.7:
                    timeline_str += "█"  # Strong presence
                elif dominant_count / len(segment_frames) > 0.4:
                    timeline_str += "▓"  # Moderate presence
                elif dominant_count / len(segment_frames) > 0.2:
                    timeline_str += "▒"  # Weak presence
                else:
                    timeline_str += "░"  # Very weak presence

            timeline_str += f" | {percentage:.1f}%"
            lines.append(timeline_str)

        # Add time markers
        time_markers = " " * 15 + " | " + "0%".ljust(width-4) + "100% |"
        lines.append(time_markers)

        return "\n".join(lines)

    def _analyze_emotion_transitions(self, timeline: list) -> list:
        """
        Analyze significant emotion transitions in timeline.

        Args:
            timeline: List of frame dicts with emotions

        Returns:
            List of dicts describing significant transitions
        """
        if len(timeline) < 2:
            return []

        transitions = []
        prev_dominant = None
        transition_count = 0

        for i, frame in enumerate(timeline):
            emotions = frame.get("emotions", {})
            if not emotions:
                continue

            # Get dominant emotion for this frame
            dominant = max(emotions.items(), key=lambda x: x[1])[0]

            # Check if dominant emotion changed
            if prev_dominant and dominant != prev_dominant:
                # Calculate timestamp (assuming evenly spaced frames)
                timestamp_sec = (i / len(timeline)) * (timeline[-1].get("timestamp", 0))

                transitions.append({
                    "from": prev_dominant,
                    "to": dominant,
                    "timestamp": timestamp_sec,
                    "frame_index": i
                })

                transition_count += 1

            prev_dominant = dominant

        # Calculate transition frequency
        if timeline:
            duration_min = timeline[-1].get("timestamp", 0) / 60.0
            transitions_per_min = transition_count / duration_min if duration_min > 0 else 0
        else:
            transitions_per_min = 0

        return {
            "transitions": transitions[:10],  # Return top 10 transitions
            "total_count": transition_count,
            "frequency_per_min": transitions_per_min
        }

    def _format_hume_results(self, results: dict) -> str:
        """Format Hume AI results as markdown with comprehensive emotion analytics."""
        # Extract key metrics
        job_id = results.get("job_id", "Unknown")
        frame_count = results.get("frame_count", 0)
        summary = results.get("summary", {})
        timeline = results.get("timeline", [])

        # Build formatted text
        text = f"# Hume AI Emotion Analysis\n\n"
        text += f"**Job ID:** {job_id}\n\n"
        text += f"**Frames Analyzed:** {frame_count}\n\n"

        if frame_count == 0:
            text += "**Note:** No faces detected in video. This typically means the camera was not showing your face during the session.\n\n"
            text += "See documentation/HUME_VIDEO_REQUIREMENTS.md for details.\n\n"
            return text

        # Section 1: Emotion Distribution
        text += "## Emotion Distribution\n\n"
        emotion_percentages = self._calculate_emotion_percentages(timeline)

        if emotion_percentages:
            # Show percentages sorted by frequency
            sorted_emotions = sorted(emotion_percentages.items(), key=lambda x: x[1], reverse=True)
            for emotion, percentage in sorted_emotions:
                text += f"- **{emotion.title()}:** {percentage:.1f}%\n"
            text += "\n"

            # Primary emotion interpretation
            text += "### Primary Emotion\n\n"
            primary_text = self._identify_primary_emotion(emotion_percentages)
            text += f"{primary_text}\n\n"

        # Section 2: Emotion Timeline Visualization
        text += "## Emotion Timeline\n\n"
        ascii_timeline = self._create_emotion_timeline_ascii(timeline, width=50)
        text += "```\n"
        text += ascii_timeline
        text += "\n```\n\n"
        text += "*Legend: █ = strong presence, ▓ = moderate, ▒ = weak, ░ = very weak*\n\n"

        # Section 3: Emotion Transitions
        text += "## Emotion Transitions\n\n"
        transition_analysis = self._analyze_emotion_transitions(timeline)

        if transition_analysis:
            total_transitions = transition_analysis.get("total_count", 0)
            freq_per_min = transition_analysis.get("frequency_per_min", 0)
            transitions_list = transition_analysis.get("transitions", [])

            text += f"**Total Transitions:** {total_transitions}\n\n"
            text += f"**Frequency:** {freq_per_min:.1f} transitions/minute\n\n"

            if transitions_list:
                text += "**Notable Transitions:**\n\n"
                for trans in transitions_list[:5]:  # Show top 5
                    timestamp_min = int(trans["timestamp"] // 60)
                    timestamp_sec = int(trans["timestamp"] % 60)
                    text += f"- {timestamp_min}:{timestamp_sec:02d} - {trans['from'].title()} → {trans['to'].title()}\n"
                text += "\n"

            # Interpretation
            if freq_per_min > 2.0:
                text += "*High transition frequency suggests emotional volatility or task switching.*\n\n"
            elif freq_per_min < 0.5:
                text += "*Low transition frequency suggests stable emotional state.*\n\n"

        # Section 4: Summary Statistics (original data)
        text += "## Detailed Statistics\n\n"
        if summary:
            for emotion, stats in summary.items():
                if isinstance(stats, dict):
                    mean = stats.get("mean", 0.0)
                    max_val = stats.get("max", 0.0)
                    text += f"**{emotion.title()}:**\n"
                    text += f"  - Average: {mean:.2f}\n"
                    text += f"  - Peak: {max_val:.2f}\n\n"

        # Section 5: Raw Data Summary
        text += "## Raw Data Summary\n\n"
        text += f"**Total Frames:** {frame_count}\n\n"
        text += f"**Timeline Length:** {len(timeline)} data points\n\n"
        if emotion_percentages:
            text += "**Emotion Distribution Summary:**\n\n"
            for emotion, percentage in sorted(emotion_percentages.items(), key=lambda x: x[1], reverse=True):
                text += f"- {emotion.title()}: {percentage:.1f}%\n"
            text += "\n"

        text += "---\n\n"
        text += "*Report generated by Focus Guardian*\n"

        logger.info(f"Hume AI report generated: {len(text)} characters")
        return text

    def _format_memories_results(self, results: dict) -> str:
        """Display Memories.ai Markdown report directly without post-processing."""
        # Get raw Markdown report from results
        markdown_report = results.get("markdown_report", "")

        if markdown_report:
            # Return the VLM-generated Markdown report as-is
            return markdown_report
        else:
            # Fallback for missing or empty report
            return "# Memories.ai Pattern Analysis\n\nNo analysis report available."

    def closeEvent(self, event):
        """Handle window close event."""
        # Check for active uploads first
        if self.active_uploads:
            # Double-check that uploads are actually still active
            # (they might have completed but not been cleared yet)
            active_sessions = []
            for session_id, job_ids in self.active_uploads.items():
                if job_ids:  # Only count sessions that have active job IDs
                    active_sessions.append(session_id)

            if active_sessions:
                num_uploads = len(active_sessions)
                reply = QMessageBox.warning(
                    self,
                    "Uploads In Progress",
                    f"{num_uploads} cloud upload(s) in progress.\n\n"
                    "If you quit now, the uploads will be cancelled and you'll need to restart them.\n\n"
                    "Are you sure you want to quit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

        # Check for active session
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

