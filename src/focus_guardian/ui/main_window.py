"""
Main application window for Focus Guardian.

PyQt6-based window with menu bar, status bar, system tray integration,
and tabbed interface for dashboard, reports, and settings.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication,
    QCheckBox, QTableWidget, QDialog, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import json

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget, QDialog

from ..core.config import Config
from ..core.database import Database
from ..core.models import QualityProfile, CAM_LABELS, SCREEN_LABELS
from ..session.session_manager import SessionManager
from ..utils.logger import get_logger
from ..ai.summary_generator import AISummaryGenerator
from ..ai.emotion_aware_messaging import EmotionAwareMessenger, EmotionState
from ..ai.comprehensive_report_generator import ComprehensiveReportGenerator

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
        
        # Theme mode (light/dark)
        self.dark_mode = False
        
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
        self.generating_reports = set()  # Set[session_id] - Track sessions generating comprehensive reports
        self.regenerating_hume = set()  # Set[session_id] - Track Hume regenerations
        self.regenerating_memories = set()  # Set[session_id] - Track Memories regenerations

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_system_tray()
        self._setup_timers()

        # Set minimum window size to prevent layout issues
        self.setMinimumSize(1000, 700)
        
        # Apply initial theme
        self._apply_theme()
        
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
        self.comprehensive_report_generator = None
        
        # Initialize AI generators if API key available
        openai_key = self.config.get_openai_api_key()
        if openai_key:
            try:
                self.ai_summary_generator = AISummaryGenerator(openai_key, self.database)
                self.comprehensive_report_generator = ComprehensiveReportGenerator(openai_key, self.database, self.config)
                logger.info("AI report generators initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AI generators: {e}")
        
        logger.info("Main window initialized")
    
    def _get_colors(self):
        """Get color palette based on current theme mode."""
        if self.dark_mode:
            return {
                'bg_primary': '#1C1C1E',
                'bg_secondary': '#2C2C2E',
                'bg_tertiary': '#3A3A3C',
                'card_bg': '#2C2C2E',
                'accent_blue': '#0A84FF',
                'accent_green': '#30D158',
                'accent_orange': '#FF9F0A',
                'accent_red': '#FF453A',
                'text_primary': '#FFFFFF',
                'text_secondary': '#98989D',
                'text_tertiary': '#636366',
                'border': '#48484A',
                'hover_bg': 'rgba(10, 132, 255, 0.12)',
                'shadow': 'rgba(0, 0, 0, 0.5)',
            }
        else:
            return {
                'bg_primary': '#F5F5F7',
                'bg_secondary': '#FFFFFF',
                'bg_tertiary': '#FAFAFA',
                'card_bg': '#FFFFFF',
                'accent_blue': '#007AFF',
                'accent_green': '#34C759',
                'accent_orange': '#FF9500',
                'accent_red': '#FF3B30',
                'text_primary': '#1C1C1E',
                'text_secondary': '#8E8E93',
                'text_tertiary': '#AEAEB2',
                'border': '#D1D1D6',
                'hover_bg': 'rgba(0, 122, 255, 0.08)',
                'shadow': 'rgba(0, 0, 0, 0.08)',
            }
    
    def _apply_theme(self):
        """Apply theme to entire application."""
        colors = self._get_colors()
        
        # Global application stylesheet
        global_style = f"""
            QMainWindow {{
                background-color: {colors['bg_primary']};
            }}
            
            QWidget {{
                color: {colors['text_primary']};
                font-size: 14px;
            }}
            
            QTabWidget::pane {{
                border: none;
                background-color: {colors['bg_primary']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_secondary']};
                padding: 12px 24px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 500;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {colors['bg_secondary']};
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                selection-background-color: {colors['accent_blue']};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 2px solid {colors['accent_blue']};
            }}
            
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                min-height: 24px;
            }}
            
            QComboBox:focus {{
                border: 2px solid {colors['accent_blue']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {colors['text_secondary']};
                margin-right: 8px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 4px;
                selection-background-color: {colors['hover_bg']};
            }}
            
            QScrollBar:vertical {{
                background-color: {colors['bg_primary']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors['text_tertiary']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['text_secondary']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {colors['bg_primary']};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {colors['text_tertiary']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors['text_secondary']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QCheckBox {{
                spacing: 8px;
                color: {colors['text_primary']};
            }}
            
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid {colors['border']};
                background-color: {colors['card_bg']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors['accent_blue']};
                border-color: {colors['accent_blue']};
                image: none;
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {colors['accent_blue']};
            }}
            
            QGroupBox {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                margin-top: 12px;
                padding: 20px;
                font-weight: 600;
                font-size: 16px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {colors['text_primary']};
            }}
            
            QLabel {{
                color: {colors['text_primary']};
            }}
            
            QMessageBox {{
                background-color: {colors['card_bg']};
            }}
            
            QDialog {{
                background-color: {colors['card_bg']};
            }}
        """
        
        self.setStyleSheet(global_style)
        
        # Re-apply component-specific styles
        if hasattr(self, 'tabs'):
            self._refresh_component_styles()
    
    def _refresh_component_styles(self):
        """Refresh styles for all components after theme change."""
        # This method is called during initial theme application
        # The full refresh happens in _toggle_theme() which recreates all tabs
        
        # Apply button styles to ensure they're properly themed
        self._apply_button_styles()
    
    def _apply_button_styles(self):
        """Apply modern button styles based on current theme."""
        colors = self._get_colors()
        
        # Dashboard buttons
        if hasattr(self, 'start_button'):
            self.start_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_green']};
                    color: white;
                    font-size: 15px;
                    font-weight: 600;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 24px;
                }}
                QPushButton:hover {{
                    background-color: #30B350;
                }}
                QPushButton:pressed {{
                    background-color: #2BA048;
                }}
                QPushButton:disabled {{
                    background-color: {colors['bg_tertiary']};
                    color: {colors['text_tertiary']};
                    opacity: 0.6;
                    cursor: not-allowed;
                }}
            """)
        
        if hasattr(self, 'pause_button'):
            self.pause_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_orange']};
                    color: white;
                    font-size: 15px;
                    font-weight: 600;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 24px;
                }}
                QPushButton:hover {{
                    background-color: #E68600;
                }}
                QPushButton:pressed {{
                    background-color: #CC7700;
                }}
                QPushButton:disabled {{
                    background-color: {colors['bg_tertiary']};
                    color: {colors['text_tertiary']};
                    opacity: 0.6;
                    cursor: not-allowed;
                }}
            """)
        
        if hasattr(self, 'stop_button'):
            self.stop_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_red']};
                    color: white;
                    font-size: 15px;
                    font-weight: 600;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 24px;
                }}
                QPushButton:hover {{
                    background-color: #E6342B;
                }}
                QPushButton:pressed {{
                    background-color: #CC2E26;
                }}
                QPushButton:disabled {{
                    background-color: {colors['bg_tertiary']};
                    color: {colors['text_tertiary']};
                    opacity: 0.6;
                    cursor: not-allowed;
                }}
            """)
    
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
        
        colors = self._get_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Start Focus Session")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['card_bg']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Instructions
        instruction_label = QLabel("What task are you working on?")
        instruction_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: 600; 
            color: {colors['text_primary']};
            margin-bottom: 4px;
        """)
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
        layout.addWidget(task_input)
        
        # Hint label
        hint_label = QLabel("Tip: Press Enter to start quickly")
        hint_label.setStyleSheet(f"""
            font-size: 12px; 
            color: {colors['text_secondary']}; 
            font-style: italic;
        """)
        layout.addWidget(hint_label)
        
        # Label profile selector
        profile_label = QLabel("Label Profile:")
        profile_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {colors['text_primary']};
            margin-top: 16px;
        """)
        layout.addWidget(profile_label)
        
        profile_combo = QComboBox()
        try:
            # Load available profiles
            profile_manager = self.config.get_label_profiles_manager()
            available_profiles = profile_manager.list_profiles()
            profile_combo.addItems(available_profiles)
            
            # Set to active profile
            active_profile = self.config.get_active_profile_name()
            if active_profile in available_profiles:
                profile_combo.setCurrentText(active_profile)
            
        except Exception as e:
            logger.error(f"Failed to load label profiles: {e}")
            profile_combo.addItem("Default")
        
        layout.addWidget(profile_combo)
        
        # Profile hint
        profile_hint = QLabel("Different profiles detect different behaviors (configure in Settings)")
        profile_hint.setStyleSheet(f"""
            font-size: 11px;
            color: {colors['text_secondary']};
            font-style: italic;
            margin-bottom: 8px;
        """)
        layout.addWidget(profile_hint)
        
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
            selected_profile = profile_combo.currentText()
            
            if task_name:
                # Save to history
                self._save_task_to_history(task_name)
                
                # Save selected profile as active
                self.config.set_active_profile_name(selected_profile)
                
                # Store selected profile for session start
                self._selected_profile_name = selected_profile
                
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
        colors = self._get_colors()
        
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {colors['bg_primary']};")
        layout = QVBoxLayout(widget)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_label = QLabel("Focus Session")
        header_label.setStyleSheet(f"""
            font-size: 28px; 
            font-weight: 700; 
            color: {colors['text_primary']};
            letter-spacing: -0.5px;
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Session info card
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(16)
        info_layout.setContentsMargins(32, 32, 32, 32)
        info_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['card_bg']};
                border-radius: 16px;
            }}
        """)
        
        # Enhanced session status with colored indicator
        status_container = QWidget()
        status_container.setStyleSheet("background: transparent;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.setSpacing(12)
        
        self.session_status_icon = QLabel("●")
        self.session_status_icon.setStyleSheet(f"""
            font-size: 16px;
            color: {colors['text_tertiary']};
        """)
        status_layout.addWidget(self.session_status_icon)
        
        self.session_status_label = QLabel("No active session")
        self.session_status_label.setStyleSheet(f"""
            font-size: 16px; 
            color: {colors['text_secondary']};
            font-weight: 500;
        """)
        status_layout.addWidget(self.session_status_label)
        
        # Recording indicators (hidden by default)
        self.recording_indicators = QLabel("📷 🖥️")
        self.recording_indicators.setStyleSheet("font-size: 14px; margin-left: 8px;")
        self.recording_indicators.setVisible(False)
        status_layout.addWidget(self.recording_indicators)
        
        info_layout.addWidget(status_container)
        
        self.session_timer_label = QLabel("00:00:00")
        self.session_timer_label.setStyleSheet(f"""
            font-size: 64px; 
            font-weight: 700; 
            color: {colors['accent_blue']};
            letter-spacing: -1px;
        """)
        self.session_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.session_timer_label)
        
        self.task_label = QLabel("Task: None")
        self.task_label.setStyleSheet(f"""
            font-size: 16px; 
            color: {colors['text_secondary']};
            font-weight: 500;
        """)
        self.task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.task_label)
        
        layout.addWidget(info_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.start_button = QPushButton("Start Focus Session")
        self.start_button.setMinimumHeight(44)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.clicked.connect(self._on_start_session)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumHeight(44)
        self.pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_button.clicked.connect(self._on_pause_session)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop Session")
        self.stop_button.setMinimumHeight(44)
        self.stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_button.clicked.connect(self._on_stop_session)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Enhanced stats display with visual indicators
        stats_label = QLabel("Statistics")
        stats_label.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: 600;
            color: {colors['text_primary']};
            margin-top: 8px;
        """)
        layout.addWidget(stats_label)
        
        stats_widget = QWidget()
        stats_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['card_bg']};
                border-radius: 12px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(16)
        stats_layout.setContentsMargins(24, 24, 24, 24)
        
        # First row: Counters (clickable for details)
        counters_layout = QHBoxLayout()
        counters_layout.setSpacing(16)
        
        # Make labels clickable buttons for detailed view
        self.snapshots_label = QPushButton("📸 Snapshots: 0")
        self.snapshots_label.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                color: {colors['accent_blue']};
                font-weight: 600;
                background: transparent;
                border: none;
                text-align: left;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
                border-radius: 8px;
            }}
        """)
        self.snapshots_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snapshots_label.setToolTip("Click to see detailed snapshot analysis")
        self.snapshots_label.clicked.connect(self._show_snapshot_details)
        counters_layout.addWidget(self.snapshots_label)
        
        self.distractions_label = QPushButton("⚠️ Distractions: 0")
        self.distractions_label.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                color: {colors['accent_red']};
                font-weight: 600;
                background: transparent;
                border: none;
                text-align: left;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
                border-radius: 8px;
            }}
        """)
        self.distractions_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.distractions_label.setToolTip("Click to see distraction breakdown and voting details")
        self.distractions_label.clicked.connect(self._show_distraction_details)
        counters_layout.addWidget(self.distractions_label)
        
        self.focus_ratio_label = QPushButton("✓ Focus: 100%")
        self.focus_ratio_label.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                color: {colors['accent_green']};
                font-weight: 600;
                background: transparent;
                border: none;
                text-align: left;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
                border-radius: 8px;
            }}
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
        self.focus_progress_bar.setFixedHeight(8)
        self.focus_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {colors['bg_tertiary']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['accent_green']}, 
                    stop:1 #32de84);
                border-radius: 4px;
            }}
        """)
        stats_layout.addWidget(self.focus_progress_bar)
        
        
        layout.addWidget(stats_widget)
        
        # Stretch to push everything to top
        layout.addStretch()
        
        return widget
    
    def _create_reports_tab(self) -> QWidget:
        """Create reports tab for session history."""
        from PyQt6.QtWidgets import QScrollArea, QFrame
        
        colors = self._get_colors()

        widget = QWidget()
        widget.setStyleSheet(f"background-color: {colors['bg_primary']};")
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header_layout = QHBoxLayout()
        label = QLabel("Session Reports")
        label.setStyleSheet(f"""
            font-size: 24px; 
            font-weight: 700;
            color: {colors['text_primary']};
            letter-spacing: -0.5px;
        """)
        header_layout.addWidget(label)

        header_layout.addStretch()

        # Refresh all button
        self.refresh_all_btn = QPushButton("🔄 Refresh All")
        self.refresh_all_btn.setMinimumHeight(36)
        self.refresh_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
            }}
        """)
        self.refresh_all_btn.setToolTip("Refresh status of all processing cloud jobs")
        self.refresh_all_btn.clicked.connect(self._on_refresh_all_sessions)
        header_layout.addWidget(self.refresh_all_btn)
        
        # Batch Upload All button
        self.batch_upload_btn = QPushButton("☁️ Upload All Completed")
        self.batch_upload_btn.setMinimumHeight(36)
        self.batch_upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #AF52DE;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #9F42CE;
            }}
        """)
        self.batch_upload_btn.setToolTip("Upload all completed sessions that haven't been uploaded yet")
        self.batch_upload_btn.clicked.connect(self._on_batch_upload_sessions)
        header_layout.addWidget(self.batch_upload_btn)
        
        header_layout.addStretch()

        layout.addLayout(header_layout)
        
        # Search and filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        # Search box
        from PyQt6.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search sessions by task name...")
        self.search_box.setMinimumHeight(36)
        self.search_box.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_box, 2)
        
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
        self.filter_combo.setMinimumHeight(36)
        self.filter_combo.setMinimumWidth(180)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo, 1)
        
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
        """Create settings tab with General and Developer Options subtabs."""
        from PyQt6.QtWidgets import QComboBox, QGroupBox, QFormLayout, QScrollArea, QFrame, QTabWidget
        from ..capture.screen_capture import WebcamCapture

        colors = self._get_colors()

        # Create main widget
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {colors['bg_primary']};")
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header with theme and developer mode toggles
        header_layout = QHBoxLayout()

        label = QLabel("Settings")
        label.setStyleSheet(f"""
            font-size: 24px; 
            font-weight: 700;
            color: {colors['text_primary']};
            letter-spacing: -0.5px;
        """)
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        # Theme toggle button
        self.theme_toggle_btn = QPushButton("🌙 Dark Mode" if not self.dark_mode else "☀️ Light Mode")
        self.theme_toggle_btn.setMinimumHeight(36)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
            }}
        """)
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_toggle_btn)
        
        # Developer mode toggle
        self.developer_mode_checkbox = QCheckBox("🔧 Developer Options")
        self.developer_mode_checkbox.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {colors['accent_orange']};
        """)
        self.developer_mode_checkbox.stateChanged.connect(self._toggle_developer_mode)
        header_layout.addWidget(self.developer_mode_checkbox)
        
        main_layout.addLayout(header_layout)

        # Create tab widget for General vs Developer settings
        self.settings_tabs = QTabWidget()
        main_layout.addWidget(self.settings_tabs)

        # General Settings tab (existing settings)
        general_tab = self._create_general_settings_widget()
        self.settings_tabs.addTab(general_tab, "General Settings")

        # Developer Options tab (new)
        self.developer_tab = self._create_developer_options_widget()
        self.settings_tabs.addTab(self.developer_tab, "Developer Options")
        self.settings_tabs.setTabEnabled(1, False)  # Hidden by default

        return widget
    
    def _create_general_settings_widget(self) -> QWidget:
        """Create the general settings widget (existing settings content)."""
        from PyQt6.QtWidgets import QComboBox, QGroupBox, QFormLayout, QScrollArea, QFrame
        from ..capture.screen_capture import WebcamCapture

        # Get colors for theme
        colors = self._get_colors()

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

        # Camera dropdown - will be populated on first refresh
        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        camera_layout.addRow("Camera:", self.camera_combo)

        # Instruction label
        instruction_label = QLabel(
            "Detecting available cameras..."
        )
        instruction_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px; font-style: italic;")
        camera_layout.addRow("", instruction_label)

        # Camera status label
        self.camera_status_label = QLabel(
            f"✓ Current: {self.config.get_camera_name()}"
        )
        self.camera_status_label.setStyleSheet(f"color: {colors['accent_green']}; font-size: 13px; font-weight: 500;")
        camera_layout.addRow("Status:", self.camera_status_label)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()

        # Preview button
        preview_btn = QPushButton("Show Live Preview")
        preview_btn.setMinimumHeight(36)
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(self._show_camera_preview)
        preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_green']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #30B350;
            }}
        """)
        button_layout.addWidget(preview_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_camera_list)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
            }}
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
        cloud_desc.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px; margin-left: 20px;")
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
        hume_info.setStyleSheet(f"color: {colors['text_tertiary']}; font-size: 10px; margin-left: 40px;")
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
        memories_info.setStyleSheet(f"color: {colors['text_tertiary']}; font-size: 10px; margin-left: 40px;")
        memories_info.setWordWrap(True)
        memories_layout.addWidget(memories_info)

        cloud_layout.addWidget(memories_container)

        # Privacy notice
        privacy_notice = QLabel(
            "Privacy: Full videos stay local by default. They are only uploaded to cloud services "
            "when you enable auto-upload or manually request cloud analysis."
        )
        privacy_notice.setStyleSheet(f"color: {colors['accent_orange']}; font-size: 11px; margin-top: 10px; font-style: italic;")
        privacy_notice.setWordWrap(True)
        cloud_layout.addWidget(privacy_notice)

        # Cloud Storage Management button
        storage_mgmt_btn = QPushButton("🗄️ Manage Cloud Storage")
        storage_mgmt_btn.setMinimumHeight(36)
        storage_mgmt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        storage_mgmt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                margin-top: 15px;
            }}
            QPushButton:hover {{
                background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
            }}
        """)
        storage_mgmt_btn.clicked.connect(self._on_manage_cloud_storage)
        cloud_layout.addWidget(storage_mgmt_btn)

        layout.addWidget(cloud_group)

        layout.addStretch()

        # Set the scroll widget as the scroll area's widget
        scroll_area.setWidget(scroll_widget)

        # Auto-refresh camera list on startup to detect available cameras
        # This ensures we never use -1 (auto-detect) and always have real camera indices
        QTimer.singleShot(500, self._refresh_camera_list_silent)

        return scroll_area
    
    def _create_developer_options_widget(self) -> QWidget:
        """Create developer options widget for prompt editing."""
        from PyQt6.QtWidgets import QScrollArea, QFrame, QGroupBox, QTextEdit, QFormLayout
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Scrollable content
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(20)
        
        # Warning banner
        warning_label = QLabel(
            "⚠️ Developer Options - Advanced Settings\n\n"
            "Modifying prompts changes how AI analyzes your sessions. "
            "Changes take effect immediately for new operations."
        )
        colors = self._get_colors()
        warning_bg = '#FFF3CD' if not self.dark_mode else '#3A3420'
        warning_text = '#856404' if not self.dark_mode else '#FFD700'
        warning_border = '#FFC107' if not self.dark_mode else '#B8860B'
        warning_label.setStyleSheet(f"""
            QLabel {{
                background-color: {warning_bg};
                color: {warning_text};
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {warning_border};
                font-size: 12px;
            }}
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Section 1: Label Profiles (NEW)
        label_profiles_group = self._create_label_profiles_section()
        layout.addWidget(label_profiles_group)
        
        # Section 2: Snapshot Vision Prompts
        vision_group = self._create_snapshot_prompts_section()
        layout.addWidget(vision_group)
        
        # Section 3: Memories.ai Prompt
        memories_group = self._create_memories_prompt_section()
        layout.addWidget(memories_group)
        
        # Section 4: Comprehensive Report Template
        comprehensive_group = self._create_comprehensive_prompt_section()
        layout.addWidget(comprehensive_group)
        
        # Section 5: Snapshot Debugging
        debug_group = self._create_snapshot_debug_section()
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        return scroll_area
    
    def _toggle_theme(self):
        """Toggle between light and dark mode."""
        self.dark_mode = not self.dark_mode
        
        # Apply new theme
        self._apply_theme()
        
        # Force recreation of all tabs to apply new theme
        if hasattr(self, 'tabs'):
            # Store current tab index
            current_index = self.tabs.currentIndex()
            
            # Clear and recreate tabs
            self.tabs.clear()
            
            # Recreate dashboard tab
            self.dashboard_tab = self._create_dashboard_tab()
            self.tabs.addTab(self.dashboard_tab, "Dashboard")
            
            # Recreate reports tab
            self.reports_tab = self._create_reports_tab()
            self.tabs.addTab(self.reports_tab, "Reports")
            
            # Recreate settings tab
            self.settings_tab = self._create_settings_tab()
            self.tabs.addTab(self.settings_tab, "Settings")
            
            # Restore tab index
            self.tabs.setCurrentIndex(current_index)
        
        logger.info(f"Theme switched to {'dark' if self.dark_mode else 'light'} mode")
    
    def _toggle_developer_mode(self, state):
        """Toggle developer options tab visibility."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.settings_tabs.setTabEnabled(1, enabled)
        
        if enabled:
            self.settings_tabs.setCurrentIndex(1)  # Switch to developer tab
            logger.info("Developer options enabled")
        else:
            self.settings_tabs.setCurrentIndex(0)  # Switch back to general
            logger.info("Developer options disabled")
    
    def _create_label_profiles_section(self) -> QWidget:
        """Create label profiles editor section."""
        from PyQt6.QtWidgets import (
            QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
            QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QLabel,
            QDialog, QLineEdit, QTextEdit, QDoubleSpinBox, QMessageBox
        )
        
        colors = self._get_colors()
        
        group = QGroupBox("🏷️ Label Profiles")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {colors['text_primary']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout(group)
        
        # Description
        desc_label = QLabel(
            "Customize detection labels for different session types. "
            "Each profile defines what behaviors to detect (HeadAway, VideoOnScreen, etc.) "
            "and how to classify them (distraction vs focus)."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {colors['text_secondary']}; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Profile selector and management buttons
        profile_controls = QHBoxLayout()
        
        profile_select_label = QLabel("Profile:")
        profile_select_label.setStyleSheet(f"color: {colors['text_primary']}; font-weight: 600;")
        profile_controls.addWidget(profile_select_label)
        
        self.profile_selector = QComboBox()
        self.profile_selector.setMinimumWidth(200)
        self.profile_selector.currentTextChanged.connect(self._on_profile_selected)
        profile_controls.addWidget(self.profile_selector)
        
        new_profile_btn = QPushButton("+ New Profile")
        new_profile_btn.clicked.connect(self._on_new_profile)
        new_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_green']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_green']};
                opacity: 0.9;
            }}
        """)
        profile_controls.addWidget(new_profile_btn)
        
        delete_profile_btn = QPushButton("Delete Profile")
        delete_profile_btn.clicked.connect(self._on_delete_profile)
        delete_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_red']};
                opacity: 0.9;
            }}
        """)
        profile_controls.addWidget(delete_profile_btn)
        
        profile_controls.addStretch()
        layout.addLayout(profile_controls)
        
        # Profile description display
        self.profile_desc_label = QLabel("")
        self.profile_desc_label.setWordWrap(True)
        self.profile_desc_label.setStyleSheet(f"""
            color: {colors['text_secondary']};
            font-style: italic;
            padding: 8px;
            background-color: {colors['bg_tertiary']};
            border-radius: 4px;
            margin: 8px 0;
        """)
        layout.addWidget(self.profile_desc_label)
        
        # Camera labels table
        cam_label = QLabel("📷 Camera Labels")
        cam_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {colors['text_primary']}; margin-top: 12px;")
        layout.addWidget(cam_label)
        
        self.cam_labels_table = QTableWidget()
        self.cam_labels_table.setColumnCount(4)
        self.cam_labels_table.setHorizontalHeaderLabels(["Label", "Category", "Threshold", "Description"])
        self.cam_labels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.cam_labels_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cam_labels_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cam_labels_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.cam_labels_table.setMaximumHeight(200)
        self.cam_labels_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                padding: 6px;
                border: none;
                font-weight: 600;
            }}
        """)
        layout.addWidget(self.cam_labels_table)
        
        # Camera labels buttons
        cam_btn_layout = QHBoxLayout()
        add_cam_label_btn = QPushButton("+ Add Camera Label")
        add_cam_label_btn.clicked.connect(lambda: self._on_add_label("cam"))
        add_cam_label_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
        cam_btn_layout.addWidget(add_cam_label_btn)
        
        edit_cam_label_btn = QPushButton("Edit Selected")
        edit_cam_label_btn.clicked.connect(lambda: self._on_edit_label("cam"))
        cam_btn_layout.addWidget(edit_cam_label_btn)
        
        remove_cam_label_btn = QPushButton("Remove Selected")
        remove_cam_label_btn.clicked.connect(lambda: self._on_remove_label("cam"))
        remove_cam_label_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
        cam_btn_layout.addWidget(remove_cam_label_btn)
        cam_btn_layout.addStretch()
        layout.addLayout(cam_btn_layout)
        
        # Screen labels table
        screen_label = QLabel("🖥️ Screen Labels")
        screen_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {colors['text_primary']}; margin-top: 16px;")
        layout.addWidget(screen_label)
        
        self.screen_labels_table = QTableWidget()
        self.screen_labels_table.setColumnCount(4)
        self.screen_labels_table.setHorizontalHeaderLabels(["Label", "Category", "Threshold", "Description"])
        self.screen_labels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.screen_labels_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.screen_labels_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.screen_labels_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.screen_labels_table.setMaximumHeight(200)
        self.screen_labels_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                padding: 6px;
                border: none;
                font-weight: 600;
            }}
        """)
        layout.addWidget(self.screen_labels_table)
        
        # Screen labels buttons
        screen_btn_layout = QHBoxLayout()
        add_screen_label_btn = QPushButton("+ Add Screen Label")
        add_screen_label_btn.clicked.connect(lambda: self._on_add_label("screen"))
        add_screen_label_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
        screen_btn_layout.addWidget(add_screen_label_btn)
        
        edit_screen_label_btn = QPushButton("Edit Selected")
        edit_screen_label_btn.clicked.connect(lambda: self._on_edit_label("screen"))
        screen_btn_layout.addWidget(edit_screen_label_btn)
        
        remove_screen_label_btn = QPushButton("Remove Selected")
        remove_screen_label_btn.clicked.connect(lambda: self._on_remove_label("screen"))
        remove_screen_label_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
        screen_btn_layout.addWidget(remove_screen_label_btn)
        screen_btn_layout.addStretch()
        layout.addLayout(screen_btn_layout)
        
        # Load initial profile
        self._load_profile_list()
        
        return group
    
    def _load_profile_list(self):
        """Load available profiles into selector dropdown."""
        try:
            profile_manager = self.config.get_label_profiles_manager()
            profiles = profile_manager.list_profiles()
            
            current = self.profile_selector.currentText()
            self.profile_selector.clear()
            self.profile_selector.addItems(profiles)
            
            # Restore selection or use active profile
            if current and current in profiles:
                self.profile_selector.setCurrentText(current)
            else:
                active = self.config.get_active_profile_name()
                if active in profiles:
                    self.profile_selector.setCurrentText(active)
                    
            logger.info(f"Loaded {len(profiles)} label profiles")
            
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
    
    def _on_profile_selected(self, profile_name: str):
        """Handle profile selection change."""
        from PyQt6.QtWidgets import QTableWidgetItem
        
        if not profile_name:
            return
        
        try:
            profile_manager = self.config.get_label_profiles_manager()
            profile = profile_manager.get_profile(profile_name)
            
            if not profile:
                return
            
            # Update description
            self.profile_desc_label.setText(f"Description: {profile.description}")
            
            # Load camera labels into table
            self.cam_labels_table.setRowCount(0)
            for row, (label_name, label_def) in enumerate(sorted(profile.cam_labels.items())):
                self.cam_labels_table.insertRow(row)
                self.cam_labels_table.setItem(row, 0, QTableWidgetItem(label_name))
                self.cam_labels_table.setItem(row, 1, QTableWidgetItem(label_def.category))
                self.cam_labels_table.setItem(row, 2, QTableWidgetItem(f"{label_def.threshold:.2f}"))
                self.cam_labels_table.setItem(row, 3, QTableWidgetItem(label_def.description))
            
            # Load screen labels into table
            self.screen_labels_table.setRowCount(0)
            for row, (label_name, label_def) in enumerate(sorted(profile.screen_labels.items())):
                self.screen_labels_table.insertRow(row)
                self.screen_labels_table.setItem(row, 0, QTableWidgetItem(label_name))
                self.screen_labels_table.setItem(row, 1, QTableWidgetItem(label_def.category))
                self.screen_labels_table.setItem(row, 2, QTableWidgetItem(f"{label_def.threshold:.2f}"))
                self.screen_labels_table.setItem(row, 3, QTableWidgetItem(label_def.description))
            
            logger.info(f"Loaded profile '{profile_name}': {len(profile.cam_labels)} cam labels, {len(profile.screen_labels)} screen labels")
            
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
    
    def _on_new_profile(self):
        """Create new label profile."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QDialogButtonBox, QLabel, QComboBox
        
        colors = self._get_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Label Profile")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Profile name
        name_label = QLabel("Profile Name:")
        name_label.setStyleSheet(f"font-weight: 600; color: {colors['text_primary']};")
        layout.addWidget(name_label)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., Coding_Focus, Writing_Mode, Deep_Work")
        layout.addWidget(name_input)
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet(f"font-weight: 600; color: {colors['text_primary']}; margin-top: 12px;")
        layout.addWidget(desc_label)
        
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Describe what this profile is for...")
        desc_input.setMaximumHeight(80)
        layout.addWidget(desc_input)
        
        # Clone from existing
        clone_label = QLabel("Clone from existing profile:")
        clone_label.setStyleSheet(f"font-weight: 600; color: {colors['text_primary']}; margin-top: 12px;")
        layout.addWidget(clone_label)
        
        clone_combo = QComboBox()
        clone_combo.addItem("(Start empty)")
        try:
            profile_manager = self.config.get_label_profiles_manager()
            clone_combo.addItems(profile_manager.list_profiles())
        except:
            pass
        layout.addWidget(clone_combo)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile_name = name_input.text().strip()
            description = desc_input.toPlainText().strip()
            clone_from = clone_combo.currentText() if clone_combo.currentIndex() > 0 else None
            
            if not profile_name:
                QMessageBox.warning(self, "Invalid Name", "Please enter a profile name")
                return
            
            try:
                profile_manager = self.config.get_label_profiles_manager()
                profile_manager.create_profile(profile_name, description, clone_from)
                
                # Reload and select new profile
                self._load_profile_list()
                self.profile_selector.setCurrentText(profile_name)
                
                QMessageBox.information(
                    self,
                    "Profile Created",
                    f"Label profile '{profile_name}' created successfully!"
                )
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                logger.error(f"Failed to create profile: {e}")
                QMessageBox.critical(self, "Error", f"Failed to create profile:\n{e}")
    
    def _on_delete_profile(self):
        """Delete current profile."""
        profile_name = self.profile_selector.currentText()
        
        if profile_name == "Default":
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "The Default profile cannot be deleted."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete the profile '{profile_name}'?\n\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                profile_manager = self.config.get_label_profiles_manager()
                success = profile_manager.delete_profile(profile_name)
                
                if success:
                    self._load_profile_list()
                    QMessageBox.information(self, "Deleted", f"Profile '{profile_name}' deleted")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete profile")
                    
            except Exception as e:
                logger.error(f"Failed to delete profile: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete profile:\n{e}")
    
    def _on_add_label(self, label_type: str):
        """Add new label to current profile."""
        profile_name = self.profile_selector.currentText()
        
        if not profile_name:
            return
        
        # Show label editor dialog
        label_def = self._show_label_editor_dialog(None, label_type)
        
        if label_def:
            try:
                profile_manager = self.config.get_label_profiles_manager()
                profile_manager.add_label_to_profile(profile_name, label_type, label_def)
                
                # Reload profile display
                self._on_profile_selected(profile_name)
                
                self.status_bar.showMessage(f"✅ Added {label_type} label '{label_def.name}'", 3000)
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                logger.error(f"Failed to add label: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add label:\n{e}")
    
    def _on_edit_label(self, label_type: str):
        """Edit selected label."""
        table = self.cam_labels_table if label_type == "cam" else self.screen_labels_table
        selected_rows = table.selectedItems()
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a label to edit")
            return
        
        row = selected_rows[0].row()
        label_name = table.item(row, 0).text()
        category = table.item(row, 1).text()
        threshold = float(table.item(row, 2).text())
        description = table.item(row, 3).text()
        
        # Create current label def for editing
        from ..core.label_profiles import LabelDefinition
        current_label = LabelDefinition(label_name, category, threshold, description)
        
        # Show editor
        updated_label = self._show_label_editor_dialog(current_label, label_type)
        
        if updated_label:
            profile_name = self.profile_selector.currentText()
            
            try:
                profile_manager = self.config.get_label_profiles_manager()
                profile = profile_manager.get_profile(profile_name)
                
                # Update the label in the profile
                if label_type == "cam":
                    profile.cam_labels[label_name] = updated_label
                else:
                    profile.screen_labels[label_name] = updated_label
                
                profile_manager.update_profile(profile)
                
                # Reload display
                self._on_profile_selected(profile_name)
                
                self.status_bar.showMessage(f"✅ Updated label '{label_name}'", 3000)
                
            except Exception as e:
                logger.error(f"Failed to edit label: {e}")
                QMessageBox.critical(self, "Error", f"Failed to edit label:\n{e}")
    
    def _on_remove_label(self, label_type: str):
        """Remove selected label from profile."""
        table = self.cam_labels_table if label_type == "cam" else self.screen_labels_table
        selected_rows = table.selectedItems()
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a label to remove")
            return
        
        row = selected_rows[0].row()
        label_name = table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Remove Label",
            f"Remove label '{label_name}' from this profile?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            profile_name = self.profile_selector.currentText()
            
            try:
                profile_manager = self.config.get_label_profiles_manager()
                profile_manager.remove_label_from_profile(profile_name, label_type, label_name)
                
                # Reload display
                self._on_profile_selected(profile_name)
                
                self.status_bar.showMessage(f"✅ Removed label '{label_name}'", 3000)
                
            except Exception as e:
                logger.error(f"Failed to remove label: {e}")
                QMessageBox.critical(self, "Error", f"Failed to remove label:\n{e}")
    
    def _show_label_editor_dialog(self, current_label, label_type: str):
        """
        Show dialog to create/edit a label.
        
        Args:
            current_label: LabelDefinition to edit (None for new label)
            label_type: "cam" or "screen"
            
        Returns:
            LabelDefinition if saved, None if cancelled
        """
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
            QComboBox, QDoubleSpinBox, QDialogButtonBox, QLabel
        )
        from ..core.label_profiles import LabelDefinition
        
        colors = self._get_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Label" if current_label else "Add New Label")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Label name
        name_input = QLineEdit()
        if current_label:
            name_input.setText(current_label.name)
            name_input.setReadOnly(True)  # Can't change name when editing
        else:
            name_input.setPlaceholderText("e.g., HeadAway, StandingUp, VideoOnScreen")
        form.addRow("Label Name:", name_input)
        
        # Category
        category_combo = QComboBox()
        category_combo.addItems(["distraction", "focus", "absence", "borderline", "neutral"])
        if current_label:
            category_combo.setCurrentText(current_label.category)
        form.addRow("Category:", category_combo)
        
        # Threshold
        threshold_spin = QDoubleSpinBox()
        threshold_spin.setRange(0.0, 1.0)
        threshold_spin.setSingleStep(0.05)
        threshold_spin.setDecimals(2)
        if current_label:
            threshold_spin.setValue(current_label.threshold)
        else:
            threshold_spin.setValue(0.70)
        form.addRow("Confidence Threshold:", threshold_spin)
        
        # Description
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(80)
        if current_label:
            desc_input.setPlainText(current_label.description)
        else:
            desc_input.setPlaceholderText("Describe what this label detects...")
        form.addRow("Description:", desc_input)
        
        layout.addLayout(form)
        
        # Help text
        help_text = QLabel(
            "• Category determines how this label affects focus detection\n"
            "• Threshold is minimum confidence (0.0-1.0) required to trigger\n"
            "• Higher thresholds = fewer false positives, may miss some events"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px; margin-top: 8px;")
        layout.addWidget(help_text)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            label_name = name_input.text().strip()
            category = category_combo.currentText()
            threshold = threshold_spin.value()
            description = desc_input.toPlainText().strip()
            
            if not label_name:
                QMessageBox.warning(self, "Invalid Input", "Label name is required")
                return None
            
            return LabelDefinition(
                name=label_name,
                category=category,
                threshold=threshold,
                description=description or f"{label_name} detection"
            )
        
        return None
    
    def _create_snapshot_prompts_section(self) -> QWidget:
        """Create snapshot vision prompts editing section."""
        from PyQt6.QtWidgets import QGroupBox, QTextEdit, QFormLayout
        
        group = QGroupBox("Snapshot Vision Prompts")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Camera prompt editor
        cam_label = QLabel("Camera Snapshot Prompt:")
        cam_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(cam_label)
        
        self.cam_prompt_edit = QTextEdit()
        self.cam_prompt_edit.setPlainText(self.config.get_custom_prompt("cam_snapshot") or self._get_default_cam_prompt())
        self.cam_prompt_edit.setMinimumHeight(200)
        self.cam_prompt_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11px;")
        layout.addWidget(self.cam_prompt_edit)
        
        cam_btn_layout = QHBoxLayout()
        save_cam_btn = QPushButton("💾 Save Camera Prompt")
        save_cam_btn.clicked.connect(self._save_cam_prompt)
        cam_btn_layout.addWidget(save_cam_btn)
        
        reset_cam_btn = QPushButton("🔄 Reset to Default")
        reset_cam_btn.clicked.connect(self._reset_cam_prompt)
        cam_btn_layout.addWidget(reset_cam_btn)
        cam_btn_layout.addStretch()
        layout.addLayout(cam_btn_layout)
        
        # Screen prompt editor
        screen_label = QLabel("Screen Snapshot Prompt:")
        screen_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(screen_label)
        
        self.screen_prompt_edit = QTextEdit()
        self.screen_prompt_edit.setPlainText(self.config.get_custom_prompt("screen_snapshot") or self._get_default_screen_prompt())
        self.screen_prompt_edit.setMinimumHeight(250)
        self.screen_prompt_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11px;")
        layout.addWidget(self.screen_prompt_edit)
        
        screen_btn_layout = QHBoxLayout()
        save_screen_btn = QPushButton("💾 Save Screen Prompt")
        save_screen_btn.clicked.connect(self._save_screen_prompt)
        screen_btn_layout.addWidget(save_screen_btn)
        
        reset_screen_btn = QPushButton("🔄 Reset to Default")
        reset_screen_btn.clicked.connect(self._reset_screen_prompt)
        screen_btn_layout.addWidget(reset_screen_btn)
        screen_btn_layout.addStretch()
        layout.addLayout(screen_btn_layout)
        
        return group
    
    def _create_memories_prompt_section(self) -> QWidget:
        """Create Memories.ai prompt editing section."""
        from PyQt6.QtWidgets import QGroupBox, QTextEdit
        
        group = QGroupBox("Memories.ai Analysis Prompt")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        colors = self._get_colors()
        desc_label = QLabel("This prompt is sent to Memories.ai for video analysis:")
        desc_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px;")
        layout.addWidget(desc_label)
        
        self.memories_prompt_edit = QTextEdit()
        self.memories_prompt_edit.setPlainText(self.config.get_custom_prompt("memories_analysis") or self._get_default_memories_prompt())
        self.memories_prompt_edit.setMinimumHeight(300)
        self.memories_prompt_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11px;")
        layout.addWidget(self.memories_prompt_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Memories.ai Prompt")
        save_btn.clicked.connect(self._save_memories_prompt)
        btn_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.clicked.connect(self._reset_memories_prompt)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_comprehensive_prompt_section(self) -> QWidget:
        """Create comprehensive report template editing section."""
        from PyQt6.QtWidgets import QGroupBox, QTextEdit
        
        group = QGroupBox("Comprehensive AI Report Template")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        colors = self._get_colors()
        desc_label = QLabel("Template for generating comprehensive reports (uses GPT-4):")
        desc_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px;")
        layout.addWidget(desc_label)
        
        self.comprehensive_prompt_edit = QTextEdit()
        self.comprehensive_prompt_edit.setPlainText(self.config.get_custom_prompt("comprehensive_report") or self._get_default_comprehensive_prompt())
        self.comprehensive_prompt_edit.setMinimumHeight(300)
        self.comprehensive_prompt_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11px;")
        layout.addWidget(self.comprehensive_prompt_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Report Template")
        save_btn.clicked.connect(self._save_comprehensive_prompt)
        btn_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.clicked.connect(self._reset_comprehensive_prompt)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_snapshot_debug_section(self) -> QWidget:
        """Create snapshot debugging section."""
        from PyQt6.QtWidgets import QGroupBox
        
        group = QGroupBox("Snapshot Debugging")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #95a5a6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        colors = self._get_colors()
        desc_label = QLabel("View raw snapshot analysis data and JSON schemas:")
        desc_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 11px;")
        layout.addWidget(desc_label)
        
        btn_layout = QHBoxLayout()
        
        view_snapshot_btn = QPushButton("🔍 View Last Snapshot Analysis")
        view_snapshot_btn.clicked.connect(self._view_last_snapshot_analysis)
        btn_layout.addWidget(view_snapshot_btn)
        
        export_schema_btn = QPushButton("📄 Export JSON Schema")
        export_schema_btn.clicked.connect(self._export_snapshot_schema)
        btn_layout.addWidget(export_schema_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    # Default prompt getters (extract from actual implementation)
    def _get_default_cam_prompt(self) -> str:
        """Get default camera snapshot prompt."""
        return """Analyze this webcam image and classify the user's attention state.

Possible classifications (return ONLY the most dominant ones with confidence 0.0-1.0):

**Distraction Indicators:**
- HeadAway: Head turned >45° away from screen (looking elsewhere)
- EyesOffScreen: Gaze not directed at screen (looking down, away, or unfocused)
- MicroSleep: Eyes closed or drowsy appearance (tired, nodding off)
- PhoneLikely: Phone visible in hand or user looking down at phone

**Absence Indicators:**
- Absent: No person visible in frame (empty chair, person left desk)

**Focus Indicators:**
- Focused: Engaged posture, eyes on screen, attentive appearance

**Instructions:**
1. Look carefully at head orientation, eye gaze, and body language
2. Return ONLY labels that are clearly present (confidence ≥ 0.6)
3. Multiple labels can apply (e.g., HeadAway + PhoneLikely)
4. If person is attentive and looking at screen, return Focused
5. If no person visible, return Absent

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation"
}"""
    
    def _get_default_screen_prompt(self) -> str:
        """Get default screen snapshot prompt."""
        return """Analyze this screen capture and classify the visible content/applications.

Possible classifications (return ONLY clearly visible ones with confidence 0.0-1.0):

**HIGH-RISK DISTRACTION Content (Always flag these):**
- VideoOnScreen: Video player showing entertainment/non-work content (YouTube, Netflix, TikTok, Twitch)
  * Look for: play buttons, video timelines, thumbnails, entertainment titles
  * Even if paused, flag if video content is visible
  * Exception: Tutorial/educational videos WITH code/terminal visible = WorkRelatedVideo instead
- SocialFeed: Social media feed scrolling (Twitter, Instagram, Facebook, Reddit, LinkedIn feed)
- Games: Gaming applications or entertainment software
- ChatWindow: Personal chat/messaging apps (Discord, WhatsApp, iMessage - NOT work Slack)

**WORK-RELATED Video (Educational/Tutorial):**
- WorkRelatedVideo: Tutorial, coding video, educational content WITH evidence of work context
  * Must see: Code editor, terminal, or technical content alongside video
  * Or: Video shows coding, technical tutorial, documentation walkthrough
  
**Focus Content:**
- Code: Code editor or IDE (VS Code, PyCharm, Sublime, JetBrains, Vim)
- Docs: Documentation, technical reading, wikis, API docs, Stack Overflow
- Reading: Long-form reading (ebooks, PDFs, research papers)
- Slides: Presentation software (PowerPoint, Google Slides, Keynote)
- Terminal: Command line terminal or shell

**Work Communication:**
- Email: Email client (Gmail, Outlook, Apple Mail)
- VideoCall: Video conferencing UI (Zoom, Meet, Teams, FaceTime)
- WorkChat: Work messaging (Slack, Teams chat, work Discord server)

**Borderline Content:**
- MultipleMonitors: Multiple windows visible, potential context switching
- Browser: Generic browser without clear content type

**Neutral:**
- Unknown: Cannot determine content type clearly

**CRITICAL Instructions for Video Detection:**
1. If you see a video player (YouTube, etc.), check the CONTEXT:
   - Is there code, terminal, or work tools visible? → WorkRelatedVideo (productive)
   - Is it just entertainment content? → VideoOnScreen (distraction)
   - Look at video title, thumbnails, related videos for clues
2. Entertainment videos are ALWAYS flagged as VideoOnScreen (distraction)
3. Tutorial/educational videos WITH work context → WorkRelatedVideo (not flagged)
4. Social media is ALWAYS a distraction (even LinkedIn feed browsing)
5. Return labels with confidence ≥ 0.6 only
6. Multiple labels can apply if multiple windows visible

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "detailed explanation of what you see and why you classified it this way"
}"""
    
    def _get_default_memories_prompt(self) -> str:
        """Get default Memories.ai analysis prompt."""
        return """Analyze this focus session by examining both the webcam and screen recordings.

Generate a comprehensive productivity report in Markdown format with the following sections:

# Focus Session Productivity Report

## Executive Summary
Provide a 2-3 sentence overview of the session quality, primary activities, and overall productivity assessment.

## Time-Based Activity Breakdown
Create a chronological timeline showing:
- Time segments with start/end timestamps (MM:SS format)
- Activity classification (Focus/Break/Distraction)
- Task hypothesis (what you observed the user doing)
- Confidence level and evidence from both webcam and screen

Use a table or structured list format for readability.

## Application Usage Analysis
Analyze screen content to identify:
- Applications/tools used with time spent in each
- Productivity classification (Productive/Neutral/Distraction)
- Context switches and multitasking patterns
- Percentage breakdown of time allocation

## Distraction Analysis
Detail distraction events including:
- Timestamp and duration of each distraction
- Distraction triggers (social media, phone, web browsing, etc.)
- Correlation between webcam behavior (head movement, gaze) and screen content
- Total distraction time and frequency

## Behavioral Insights
Correlate webcam and screen observations:
- Focus patterns (when user was most engaged)
- Attention quality indicators (posture, gaze consistency, head position)
- Break patterns and their relationship to productivity
- Signs of fatigue or frustration
- Phone usage detection and impact

## Productivity Metrics
Calculate and present:
- Focus ratio (focused time / total session time)
- Average focus bout duration
- Distraction frequency (events per hour)
- Overall productivity score (0-100)
- Context switch frequency

## Actionable Recommendations
Provide 3-5 specific, evidence-based recommendations to improve focus and productivity based on observed patterns.

---

**Instructions:**
- Use clear Markdown formatting with headers, lists, tables, and emphasis
- Include specific timestamps and evidence from the videos
- Be objective and analytical
- Provide quantitative metrics wherever possible
- Make recommendations actionable and personalized to observed behavior
- Do NOT wrap the output in code blocks - return raw Markdown text"""
    
    def _get_default_comprehensive_prompt(self) -> str:
        """Get default comprehensive report template."""
        return """You are an expert ADHD coach analyzing a focus session with comprehensive AI data.

Generate a comprehensive, long-form report (800-1200 words) that:

1. **Session Story** - Tell the narrative of this session
2. **Emotional Journey** (if Hume AI data available)
3. **Behavioral Patterns** (if Memories.ai data available)
4. **Historical Comparison** (vs past week/month)
5. **Deep Insights** - Non-obvious patterns
6. **Actionable Recommendations** - Specific to user's data
7. **Encouragement & Motivation**

**TONE & STYLE:**
- Personal: Use "you" and "your"
- Data-driven: Reference specific numbers
- Supportive: Encouraging, not judgmental
- Insightful: Go beyond surface-level
- Actionable: Every insight has a "what next"

Return as markdown with clear sections and formatting."""
    
    # Save handlers
    def _save_cam_prompt(self):
        """Save custom camera prompt."""
        prompt_text = self.cam_prompt_edit.toPlainText()
        self.config.save_custom_prompt("cam_snapshot", prompt_text)
        self.status_bar.showMessage("✅ Camera prompt saved - applies to new snapshots", 5000)
        logger.info("Custom camera prompt saved")
    
    def _save_screen_prompt(self):
        """Save custom screen prompt."""
        prompt_text = self.screen_prompt_edit.toPlainText()
        self.config.save_custom_prompt("screen_snapshot", prompt_text)
        self.status_bar.showMessage("✅ Screen prompt saved - applies to new snapshots", 5000)
        logger.info("Custom screen prompt saved")
    
    def _save_memories_prompt(self):
        """Save custom Memories.ai prompt."""
        prompt_text = self.memories_prompt_edit.toPlainText()
        self.config.save_custom_prompt("memories_analysis", prompt_text)
        self.status_bar.showMessage("✅ Memories.ai prompt saved - applies to new uploads", 5000)
        logger.info("Custom Memories.ai prompt saved")
    
    def _save_comprehensive_prompt(self):
        """Save custom comprehensive report template."""
        prompt_text = self.comprehensive_prompt_edit.toPlainText()
        self.config.save_custom_prompt("comprehensive_report", prompt_text)
        self.status_bar.showMessage("✅ Report template saved - applies to new reports", 5000)
        logger.info("Custom comprehensive report template saved")
    
    # Reset handlers
    def _reset_cam_prompt(self):
        """Reset camera prompt to default."""
        self.cam_prompt_edit.setPlainText(self._get_default_cam_prompt())
        self.config.reset_prompt_to_default("cam_snapshot")
        self.status_bar.showMessage("✅ Camera prompt reset to default", 3000)
        logger.info("Camera prompt reset to default")
    
    def _reset_screen_prompt(self):
        """Reset screen prompt to default."""
        self.screen_prompt_edit.setPlainText(self._get_default_screen_prompt())
        self.config.reset_prompt_to_default("screen_snapshot")
        self.status_bar.showMessage("✅ Screen prompt reset to default", 3000)
        logger.info("Screen prompt reset to default")
    
    def _reset_memories_prompt(self):
        """Reset Memories.ai prompt to default."""
        self.memories_prompt_edit.setPlainText(self._get_default_memories_prompt())
        self.config.reset_prompt_to_default("memories_analysis")
        self.status_bar.showMessage("✅ Memories.ai prompt reset to default", 3000)
        logger.info("Memories.ai prompt reset to default")
    
    def _reset_comprehensive_prompt(self):
        """Reset comprehensive template to default."""
        self.comprehensive_prompt_edit.setPlainText(self._get_default_comprehensive_prompt())
        self.config.reset_prompt_to_default("comprehensive_report")
        self.status_bar.showMessage("✅ Report template reset to default", 3000)
        logger.info("Comprehensive template reset to default")
    
    # Snapshot debugging
    def _view_last_snapshot_analysis(self):
        """View the last snapshot's raw analysis data."""
        if not self.current_session_id:
            QMessageBox.information(
                self,
                "No Active Session",
                "Start a session to view snapshot analysis."
            )
            return
        
        # Get last snapshot from current session
        snapshots = self.database.get_snapshots_for_session(self.current_session_id)
        
        if not snapshots:
            QMessageBox.information(
                self,
                "No Snapshots",
                "No snapshots captured yet. Wait for the first snapshot (30 seconds)."
            )
            return
        
        # Get most recent snapshot with vision results
        last_snap = None
        for snap in reversed(snapshots):
            if snap.vision_labels and snap.vision_json_path:
                last_snap = snap
                break
        
        if not last_snap:
            QMessageBox.information(
                self,
                "No Analysis Yet",
                "Snapshots captured but not yet analyzed. Wait a few seconds."
            )
            return
        
        # Load raw vision JSON
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        import json
        
        try:
            vision_file = self.config.get_data_dir() / last_snap.vision_json_path
            with open(vision_file, 'r') as f:
                vision_data = json.load(f)
            
            # Get theme colors
            colors = self._get_colors()
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("🔍 Snapshot Analysis Details")
            dialog.setMinimumSize(700, 600)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['bg_primary']};
                }}
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Info header
            info = QLabel(f"Snapshot: {last_snap.timestamp.strftime('%H:%M:%S') if last_snap.timestamp else 'N/A'}")
            info.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {colors['text_primary']};")
            layout.addWidget(info)
            
            # JSON display
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(json.dumps(vision_data, indent=2))
            text_edit.setStyleSheet(f"""
                QTextEdit {{
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    background-color: {colors['card_bg']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border']};
                    border-radius: 4px;
                }}
            """)
            layout.addWidget(text_edit)
            
            # Parsed labels
            labels_text = "\n".join([f"• {k}: {v:.0%}" for k, v in last_snap.vision_labels.items()])
            parsed_label = QLabel(f"Parsed Labels:\n{labels_text}")
            parsed_label.setStyleSheet(f"""
                background-color: {colors['accent_green'] if self.dark_mode else '#e8f5e9'};
                color: {colors['text_primary']};
                padding: 10px;
                border-radius: 4px;
            """)
            layout.addWidget(parsed_label)
            
            # Close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_blue']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-width: 80px;
                }}
            """)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to view snapshot analysis: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load snapshot data:\n\n{str(e)}")
    
    def _export_snapshot_schema(self):
        """Export snapshot JSON schema to file."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        schema = {
            "title": "Snapshot Vision API Response Schema",
            "type": "object",
            "required": ["labels", "reasoning"],
            "properties": {
                "labels": {
                    "type": "object",
                    "description": "Classification labels with confidence scores",
                    "additionalProperties": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "examples": [
                        {"Focused": 0.9, "HeadAway": 0.1},
                        {"VideoOnScreen": 0.85, "Code": 0.75}
                    ]
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of classification"
                }
            },
            "camera_labels": list(CAM_LABELS),
            "screen_labels": list(SCREEN_LABELS)
        }
        
        # Save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON Schema",
            "snapshot_schema.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(schema, f, indent=2)
                QMessageBox.information(
                    self,
                    "Schema Exported",
                    f"JSON schema exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export schema:\n\n{str(e)}")

    def _on_camera_changed(self, index: int):
        """Handle camera selection change."""
        camera_index = self.camera_combo.itemData(index)
        camera_name = self.camera_combo.itemText(index)

        # Save to config
        self.config.set_camera_config(camera_index, camera_name)

        # Update status
        colors = self._get_colors()
        self.camera_status_label.setText(f"✓ Saved: {camera_name}")
        self.camera_status_label.setStyleSheet(f"color: {colors['accent_green']}; font-size: 13px;")

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
        colors = self._get_colors()
        self.camera_status_label.setText("⏳ Scanning for cameras...")
        self.camera_status_label.setStyleSheet(f"color: {colors['accent_orange']}; font-size: 13px;")
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
            for cam in cameras:
                self.camera_combo.addItem(cam["name"], cam["index"])

            # Restore current selection or default to last camera
            combo_index = self.camera_combo.findData(current_index)
            if combo_index >= 0 and current_index != -1:
                # Restore saved camera if valid and not -1
                self.camera_combo.setCurrentIndex(combo_index)
            else:
                # Default to last camera (highest index, typically built-in FaceTime)
                # Use len(cameras)-1 to get the last camera safely
                last_camera_combo_index = len(cameras) - 1 if cameras else 0
                self.camera_combo.setCurrentIndex(last_camera_combo_index)
                # Save the new default
                if cameras:
                    last_camera = cameras[-1]
                    self.config.set_camera_config(last_camera["index"], last_camera["name"])

            # Update status
            colors = self._get_colors()
            self.camera_status_label.setText(f"✓ Found {len(cameras)} camera(s)")
            self.camera_status_label.setStyleSheet(f"color: {colors['accent_green']}; font-size: 13px;")

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
            colors = self._get_colors()
            self.camera_status_label.setText("❌ Scan failed")
            self.camera_status_label.setStyleSheet(f"color: {colors['accent_red']}; font-size: 13px;")
            QMessageBox.warning(
                self,
                "Camera Refresh Failed",
                f"Could not scan for cameras: {str(e)}"
            )

    def _refresh_camera_list_silent(self):
        """
        Silently refresh camera list on startup without showing popup dialogs.
        Defaults to last camera (highest index, typically built-in FaceTime).
        """
        from ..capture.screen_capture import WebcamCapture

        # Show loading message
        colors = self._get_colors()
        self.camera_status_label.setText("⏳ Detecting cameras...")
        self.camera_status_label.setStyleSheet(f"color: {colors['accent_orange']}; font-size: 13px;")

        try:
            logger.info("Auto-detecting cameras on startup...")
            cameras = WebcamCapture.enumerate_cameras()

            logger.info(f"Found {len(cameras)} cameras on startup")
            for cam in cameras:
                logger.info(f"  Camera: index={cam['index']}, name={cam['name']}")

            if not cameras:
                colors = self._get_colors()
                self.camera_status_label.setText("❌ No cameras found")
                self.camera_status_label.setStyleSheet(f"color: {colors['accent_red']}; font-size: 13px;")
                return

            # Save current selection
            current_index = self.config.get_camera_index()

            # Clear and repopulate
            self.camera_combo.clear()
            for cam in cameras:
                self.camera_combo.addItem(cam["name"], cam["index"])

            # Restore current selection or default to last camera
            combo_index = self.camera_combo.findData(current_index)
            if combo_index >= 0 and current_index != -1:
                # Restore saved camera if valid and not -1
                self.camera_combo.setCurrentIndex(combo_index)
                logger.info(f"Restored saved camera: index={current_index}")
            else:
                # Default to last camera (highest index, typically built-in FaceTime)
                # Use len(cameras)-1 to get the last camera safely
                last_camera_combo_index = len(cameras) - 1 if cameras else 0
                self.camera_combo.setCurrentIndex(last_camera_combo_index)
                # Save the new default
                if cameras:
                    last_camera = cameras[-1]
                    self.config.set_camera_config(last_camera["index"], last_camera["name"])
                    logger.info(f"Defaulted to last camera: index={last_camera['index']}, name={last_camera['name']}")

            # Update status
            colors = self._get_colors()
            selected_camera = self.camera_combo.currentText()
            self.camera_status_label.setText(f"✓ {selected_camera}")
            self.camera_status_label.setStyleSheet(f"color: {colors['accent_green']}; font-size: 13px;")

            logger.info(f"Camera auto-detection complete: {len(cameras)} camera(s) found")

        except Exception as e:
            logger.error(f"Failed to auto-detect cameras: {e}", exc_info=True)
            colors = self._get_colors()
            self.camera_status_label.setText("❌ Detection failed")
            self.camera_status_label.setStyleSheet(f"color: {colors['accent_red']}; font-size: 13px;")

    def _show_camera_preview(self):
        """Show live camera preview window."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtCore import QTimer
        from PyQt6.QtGui import QImage, QPixmap
        import cv2
        import numpy as np

        camera_index = self.camera_combo.itemData(self.camera_combo.currentIndex())
        camera_name = self.camera_combo.currentText()

        # Get theme colors
        colors = self._get_colors()

        # Create preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"Camera Preview - {camera_name}")
        preview_dialog.setMinimumSize(640, 480)
        preview_dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)

        layout = QVBoxLayout(preview_dialog)

        # Video label
        video_label = QLabel()
        video_label.setStyleSheet(f"border: 2px solid {colors['border']};")
        layout.addWidget(video_label)

        # Status label
        status_label = QLabel(f"Camera: {camera_name} (Index: {camera_index})")
        status_label.setStyleSheet(f"font-size: 12px; color: {colors['text_secondary']};")
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
        colors = self._get_colors()
        self.session_status_icon.setText("●")
        self.session_status_icon.setStyleSheet(f"font-size: 16px; color: {colors['accent_green']};")
        self.session_status_label.setText("Session Active")
        self.session_status_label.setStyleSheet(f"""
            font-size: 16px; 
            color: {colors['accent_green']}; 
            font-weight: 600;
        """)
        self.recording_indicators.setVisible(True)  # Show recording icons
        
        self.task_label.setText(f"Task: {task_name}")
        self.task_label.setStyleSheet(f"""
            font-size: 16px; 
            color: {colors['text_primary']};
            font-weight: 600;
        """)
        
        # Start actual session FIRST before updating UI
        # This way if it fails, UI never changes
        try:
            logger.info("Starting session manager...")
            
            # Get selected profile name (stored when dialog accepted)
            profile_name = getattr(self, '_selected_profile_name', None)
            
            self.current_session_id = self.session_manager.start_session(
                task_name=task_name,
                quality_profile=QualityProfile.STD,
                screen_enabled=True,
                label_profile_name=profile_name
            )
            logger.info(f"✅ Session manager started successfully: {self.current_session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to start session: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error Starting Session",
                f"Failed to start session: {str(e)}\n\nCheck that your camera is available and not in use by another application."
            )
            # Don't change UI state since session didn't start
            return
        
        # Session started successfully - NOW update UI
        logger.info("Updating UI for active session...")
        
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        logger.info(f"Button states: start={self.start_button.isEnabled()}, pause={self.pause_button.isEnabled()}, stop={self.stop_button.isEnabled()}")
        logger.info(f"Session using label profile: {getattr(self, '_selected_profile_name', 'Default')}")
        
        self.session_active = True
        self.session_start_time = datetime.now()
        self.session_elapsed_seconds = 0
        self.session_paused_at = None
        self.session_total_paused_seconds = 0
        self.session_timer.start(1000)  # Update every second
        self.stats_timer.start(5000)     # Update every 5 seconds
        
        self.status_bar.showMessage("🟢 Focus session started - recording active")
        logger.info("✅ Session start complete")
    
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
            colors = self._get_colors()
            self.session_status_icon.setText("●")
            self.session_status_icon.setStyleSheet(f"font-size: 16px; color: {colors['accent_orange']};")
            self.session_status_label.setText("Session Paused")
            self.session_status_label.setStyleSheet(f"""
                font-size: 16px; 
                color: {colors['accent_orange']}; 
                font-weight: 600;
            """)
            
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
            colors = self._get_colors()
            self.session_status_icon.setText("●")
            self.session_status_icon.setStyleSheet(f"font-size: 16px; color: {colors['accent_green']};")
            self.session_status_label.setText("Session Active")
            self.session_status_label.setStyleSheet(f"""
                font-size: 16px; 
                color: {colors['accent_green']}; 
                font-weight: 600;
            """)
            
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
            colors = self._get_colors()
            self.session_status_icon.setText("●")
            self.session_status_icon.setStyleSheet(f"font-size: 16px; color: {colors['text_tertiary']};")
            self.session_status_label.setText("No active session")
            self.session_status_label.setStyleSheet(f"""
                font-size: 16px; 
                color: {colors['text_secondary']};
                font-weight: 500;
            """)
            self.recording_indicators.setVisible(False)  # Hide recording icons
            
            self.session_timer_label.setText("00:00:00")
            self.session_timer_label.setStyleSheet(f"""
                font-size: 64px; 
                font-weight: 700; 
                color: {colors['accent_blue']};
                letter-spacing: -1px;
            """)
            
            self.task_label.setText("Task: None")
            self.task_label.setStyleSheet(f"""
                font-size: 16px; 
                color: {colors['text_secondary']};
                font-weight: 500;
            """)
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
                    # Show upload prompt instead of immediate summary
                    self._prompt_for_cloud_upload(stopped_session_id)
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

            # Save AI summary to session folder
            if self.ai_summary_generator and ai_summaries:
                self._save_ai_summary_to_session(session_id, ai_summaries, summary)

            # Show resizable dialog instead of fixed-width QMessageBox
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QScrollArea, QFrame
            
            # Get theme colors
            colors = self._get_colors()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("✨ Session Complete - AI Summary")
            dialog.setMinimumSize(800, 600)
            dialog.resize(950, 750)  # Default comfortable size
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['bg_primary']};
                }}
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Create scroll area for content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {colors['bg_primary']};
                    border: none;
                }}
            """)
            
            # Text display
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            text_display.setHtml(summary)
            text_display.setStyleSheet(f"""
                QTextEdit {{
                    font-size: 13px;
                    color: {colors['text_primary']};
                    background-color: {colors['card_bg']};
                    border: none;
                    padding: 15px;
                    line-height: 1.6;
                }}
            """)
            
            scroll_area.setWidget(text_display)
            layout.addWidget(scroll_area)
            
            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            button_box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_blue']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-width: 80px;
                }}
            """)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec()

        except Exception as e:
            logger.error(f"Failed to show session summary: {e}", exc_info=True)
    
    def _save_ai_summary_to_session(self, session_id: str, ai_summaries: dict, full_html: str) -> None:
        """Save AI-generated summaries to session folder."""
        try:
            import json
            from pathlib import Path
            
            # Get session folder
            session = self.database.get_session(session_id)
            if not session:
                return
            
            session_dir = self.config.get_data_dir() / f"sessions/{session_id}"
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save AI summaries as JSON
            ai_summary_file = session_dir / "ai_summary.json"
            with open(ai_summary_file, 'w') as f:
                json.dump({
                    "generated_at": datetime.now().isoformat(),
                    "session_id": session_id,
                    "task_name": session.task_name,
                    "summaries": ai_summaries,
                    "full_html": full_html
                }, f, indent=2)
            
            logger.info(f"AI summary saved to {ai_summary_file}")
            
        except Exception as e:
            logger.error(f"Failed to save AI summary: {e}", exc_info=True)
    
    def _load_saved_ai_summary(self, session_id: str) -> Optional[dict]:
        """Load saved AI summary from session folder."""
        try:
            import json
            from pathlib import Path
            
            session_dir = self.config.get_data_dir() / f"sessions/{session_id}"
            ai_summary_file = session_dir / "ai_summary.json"
            
            if not ai_summary_file.exists():
                return None
            
            with open(ai_summary_file, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"Failed to load AI summary: {e}")
            return None
    
    def _on_view_saved_summary(self, session_id: str):
        """View saved AI summary for a session."""
        try:
            saved_summary = self._load_saved_ai_summary(session_id)
            
            if not saved_summary:
                QMessageBox.warning(
                    self,
                    "Summary Not Available",
                    "AI summary not found for this session.\n\n"
                    "Summaries are generated when AI features are enabled."
                )
                return
            
            # Get session info
            session = self.database.get_session(session_id)
            task_name = session.task_name if session else "Unknown"
            generated_at = saved_summary.get("generated_at", "Unknown")
            full_html = saved_summary.get("full_html", "")
            
            # Create resizable dialog
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QScrollArea, QFrame, QLabel
            
            # Get theme colors
            colors = self._get_colors()
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"✨ AI Summary - {task_name}")
            dialog.setMinimumSize(800, 600)
            dialog.resize(950, 750)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['bg_primary']};
                }}
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Header with metadata
            header = QLabel(f"<p style='color: #7f8c8d; font-size: 11px;'>Generated: {generated_at}</p>")
            layout.addWidget(header)
            
            # Scroll area for content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            
            # Text display
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            text_display.setHtml(full_html)
            text_display.setStyleSheet("""
                QTextEdit {
                    font-size: 13px;
                    color: #2c3e50;
                    background-color: white;
                    border: none;
                    padding: 15px;
                    line-height: 1.6;
                }
            """)
            
            scroll_area.setWidget(text_display)
            layout.addWidget(scroll_area)
            
            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to show saved summary: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load AI summary:\n\n{str(e)}"
            )
    
    def _prompt_for_cloud_upload(self, session_id: str):
        """Prompt user to upload session for AI analysis after session ends."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        
        # Get session
        session = self.database.get_session(session_id)
        if not session:
            return
        
        # Get theme colors
        colors = self._get_colors()
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Session Complete")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel(f"<h2>Session Complete: {session.task_name}</h2>")
        header.setStyleSheet(f"color: {colors['text_primary']};")
        layout.addWidget(header)
        
        # Basic stats
        duration = (session.ended_at - session.started_at).total_seconds() / 60 if session.ended_at else 0
        stats_label = QLabel(f"""<div style="color: #2c3e50; background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
<p><b>Duration:</b> {duration:.0f} minutes</p>
<p><b>Task:</b> {session.task_name}</p>
<p>Basic session report has been saved.</p>
</div>""")
        stats_label.setWordWrap(True)
        stats_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(stats_label)
        
        # Cloud upload offer
        if self.config.is_cloud_features_enabled():
            offer_label = QLabel("""<div style="background-color: #e8f5e9; padding: 15px; border-radius: 6px; margin-top: 15px;">
<h3 style="color: #27ae60; margin-top: 0;">✨ Want AI-Powered Insights?</h3>
<p style="color: #2c3e50;">Upload your session for comprehensive AI analysis:</p>
<ul style="color: #2c3e50;">
    <li><b>Hume AI:</b> Emotion timeline analysis</li>
    <li><b>Memories.ai:</b> Pattern detection & insights</li>
    <li><b>GPT-4:</b> Comprehensive report with historical trends</li>
</ul>
<p style="color: #7f8c8d; font-size: 12px;">Processing time: 5-10 minutes</p>
</div>""")
            offer_label.setWordWrap(True)
            offer_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(offer_label)
            
            # Upload button
            upload_btn = QPushButton("☁️ Yes, Upload for AI Analysis")
            upload_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            upload_btn.clicked.connect(lambda: self._handle_upload_and_close(dialog, session_id))
            layout.addWidget(upload_btn)
            
            # Skip button
            skip_btn = QPushButton("Skip - View Basic Report")
            skip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            skip_btn.clicked.connect(lambda: self._handle_skip_and_close(dialog, session_id))
            layout.addWidget(skip_btn)
        else:
            # Cloud features disabled
            close_btn = QPushButton("OK")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                }
            """)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _handle_upload_and_close(self, dialog, session_id: str):
        """Handle upload request and close dialog."""
        dialog.accept()
        
        # Trigger upload
        run_hume = self.config.is_hume_ai_enabled()
        run_memories = self.config.is_memories_ai_enabled()
        
        if run_hume or run_memories:
            self._on_upload_to_cloud(session_id)
            
            # Show info message
            QMessageBox.information(
                self,
                "Upload Started",
                "Session uploaded to cloud for AI analysis.\n\n"
                "Check the Reports tab in 5-10 minutes.\n"
                "A '🤖 Generate AI Report' button will appear when ready."
            )
        else:
            QMessageBox.warning(
                self,
                "No Providers Enabled",
                "Please enable Hume AI and/or Memories.ai in Settings first."
            )
    
    def _handle_skip_and_close(self, dialog, session_id: str):
        """Handle skip upload - just close dialog."""
        dialog.accept()
        # Don't show summary - user can access it from Reports tab
        logger.info("User skipped cloud upload")
    
    def _on_generate_comprehensive_report(self, session_id: str):
        """Generate comprehensive AI report in background (non-blocking)."""
        if not self.comprehensive_report_generator:
            QMessageBox.warning(
                self,
                "AI Not Available",
                "Comprehensive AI report generation requires an OpenAI API key."
            )
            return
        
        import threading
        
        # Mark as generating
        self.generating_reports.add(session_id)
        
        # Update UI immediately to show generating state
        self._load_sessions_list()
        
        # Show non-blocking status message
        self.status_bar.showMessage(f"🤖 Generating comprehensive AI report in background...", 5000)
        
        def generate_worker():
            import json  # Ensure json is available in nested function scope
            try:
                logger.info(f"Starting comprehensive report generation for {session_id}")
                
                # Load Hume AI results
                hume_results = None
                hume_jobs = [j for j in self.database.get_cloud_jobs_for_session(session_id) if j.provider.value == "hume_ai"]
                if hume_jobs and hume_jobs[0].results_file_path:
                    with open(hume_jobs[0].results_file_path, 'r') as f:
                        hume_results = json.load(f)
                
                # Load Memories.ai results
                memories_results = None
                memories_jobs = [j for j in self.database.get_cloud_jobs_for_session(session_id) if j.provider.value == "memories_ai"]
                if memories_jobs and memories_jobs[0].results_file_path:
                    with open(memories_jobs[0].results_file_path, 'r') as f:
                        memories_results = json.load(f)
                
                # Generate comprehensive report
                report = self.comprehensive_report_generator.generate_comprehensive_report(
                    session_id=session_id,
                    hume_results=hume_results,
                    memories_results=memories_results
                )
                
                # Save report
                self.comprehensive_report_generator.save_comprehensive_report(session_id, report)
                
                logger.info(f"Comprehensive report generated successfully for {session_id}")
                
                # Update UI on completion
                def on_complete():
                    # Remove from generating set
                    if session_id in self.generating_reports:
                        self.generating_reports.remove(session_id)
                    
                    # Refresh UI to show new button
                    self._load_sessions_list()
                    
                    # Show subtle notification
                    self.status_bar.showMessage("✅ Comprehensive AI report generated! Click to view.", 10000)
                    
                    # Desktop notification
                    self._show_desktop_notification(
                        "AI Report Ready",
                        "Comprehensive AI report generated! Click to view insights."
                    )
                    
                    # Auto-open the report after generation (with small delay to ensure file is written)
                    def delayed_open():
                        logger.info(f"Auto-opening comprehensive report for {session_id}")
                        try:
                            self._on_view_comprehensive_report(session_id)
                        except Exception as view_error:
                            logger.error(f"Failed to auto-open report: {view_error}", exc_info=True)
                            # Show fallback message if auto-open fails
                            QMessageBox.information(
                                self,
                                "Report Generated",
                                "Comprehensive AI report generated!\n\n"
                                "Click the purple '📊 View Comprehensive AI Report' button to see it."
                            )
                    
                    QTimer.singleShot(500, delayed_open)  # 500ms delay to ensure file is written
                
                QTimer.singleShot(0, on_complete)
                
            except Exception as e:
                logger.error(f"Failed to generate comprehensive report: {e}", exc_info=True)
                
                # Determine error type for better messaging
                error_msg = str(e)
                if "rate_limit" in error_msg.lower():
                    user_message = "Rate limit exceeded. Please wait a moment and try again."
                elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
                    user_message = "API quota exceeded. Please check your OpenAI account."
                elif "timeout" in error_msg.lower():
                    user_message = "Request timed out. Please try again."
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    user_message = "Network error. Please check your internet connection."
                else:
                    user_message = f"An error occurred: {str(e)[:100]}"
                
                def on_error():
                    # Remove from generating set
                    if session_id in self.generating_reports:
                        self.generating_reports.remove(session_id)
                    
                    # Refresh UI
                    self._load_sessions_list()
                    
                    # Show error in status bar (non-blocking)
                    self.status_bar.showMessage(f"❌ AI report generation failed: {user_message[:80]}", 15000)
                    
                    # Optionally show a dialog for critical errors
                    if "quota" in error_msg.lower() or "api" in error_msg.lower():
                        QMessageBox.warning(
                            self,
                            "AI Report Generation Failed",
                            f"{user_message}\n\n"
                            "You can try again later or view the basic Hume AI and Memories.ai results separately."
                        )
                
                QTimer.singleShot(0, on_error)
        
        thread = threading.Thread(target=generate_worker, daemon=True)
        thread.start()
    
    def _on_view_comprehensive_report(self, session_id: str):
        """View comprehensive AI report for a session."""
        try:
            import json
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QScrollArea, QFrame
            
            # Load report
            report_path = self.config.get_data_dir() / f"sessions/{session_id}/comprehensive_ai_report.json"
            
            if not report_path.exists():
                QMessageBox.warning(
                    self,
                    "Report Not Available",
                    "Comprehensive AI report has not been generated yet.\n\n"
                    "Click '🤖 Generate Comprehensive AI Report' to create it."
                )
                return
            
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            # Get session for title
            session = self.database.get_session(session_id)
            task_name = session.task_name if session else "Unknown"
            
            # Extract report text
            report_text = report_data.get('report_text', '')
            
            # Debug logging
            logger.info(f"Report data keys: {list(report_data.keys())}")
            logger.info(f"Report text length: {len(report_text)} characters")
            logger.info(f"Report text preview: {report_text[:200] if report_text else 'EMPTY!'}")
            
            # Check if report text is empty
            if not report_text or len(report_text.strip()) == 0:
                logger.error("Report text is empty!")
                QMessageBox.warning(
                    self,
                    "Empty Report",
                    f"The comprehensive report was generated but contains no text.\n\n"
                    f"Report data: {json.dumps(report_data, indent=2)[:500]}"
                )
                return
            
            # Get theme colors
            colors = self._get_colors()
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"📊 Comprehensive AI Report - {task_name}")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1000, 800)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['bg_primary']};
                }}
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Header
            header_text = f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
<p style="margin: 0; color: #7f8c8d; font-size: 12px;">Generated: {report_data.get('generated_at', 'Unknown')}</p>
<p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 12px;">
Data Sources: {'Hume AI, ' if report_data.get('data_sources', {}).get('hume_ai') else ''}
{'Memories.ai, ' if report_data.get('data_sources', {}).get('memories_ai') else ''}
Historical Trends, Snapshot Analysis</p>
</div>"""
            
            header = QLabel(header_text)
            header.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(header)
            
            # Scroll area
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            
            # Text display
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            
            # Try to set content as markdown, fallback to plain text
            try:
                text_display.setMarkdown(report_text)
            except Exception as e:
                logger.warning(f"Failed to set markdown, using plain text: {e}")
                text_display.setPlainText(report_text)
            
            text_display.setStyleSheet("""
                QTextEdit {
                    font-size: 14px;
                    color: #000000;
                    background-color: #ffffff;
                    border: none;
                    padding: 20px;
                    line-height: 1.8;
                }
                QTextEdit p, QTextEdit h1, QTextEdit h2, QTextEdit h3, QTextEdit h4, QTextEdit li {
                    color: #000000;
                }
            """)
            
            scroll_area.setWidget(text_display)
            layout.addWidget(scroll_area)
            
            # Close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to show comprehensive report: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load comprehensive AI report:\n\n{str(e)}"
            )
    
    
    def _show_desktop_notification(self, title: str, message: str):
        """Show desktop notification using system tray."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                5000  # Show for 5 seconds
            )
            logger.info(f"Desktop notification: {title} - {message}")
    
    def _on_regenerate_hume(self, session_id: str):
        """Regenerate Hume AI emotion analysis only."""
        import threading
        
        reply = QMessageBox.question(
            self,
            "Regenerate Hume AI",
            "Re-analyze emotions with Hume AI?\n\n"
            "Old analysis will be archived.\n"
            "Processing time: ~5 minutes\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        session = self.database.get_session(session_id)
        if not session:
            return
        
        # Mark as regenerating
        self.regenerating_hume.add(session_id)
        self._load_sessions_list()  # Update UI to show loading state
        self.status_bar.showMessage("🔄 Regenerating Hume AI analysis...", 3000)
        
        def worker():
            try:
                self._archive_old_cloud_results(session_id, hume_only=True)
                
                cam_video = self.config.get_data_dir() / session.cam_mp4_path
                hume_job_id, _ = self.session_manager.cloud_analysis_manager.upload_session_for_analysis(
                    session_id=session_id,
                    cam_video_path=cam_video,
                    screen_video_path=None,
                    run_hume=True,
                    run_memories=False
                )
                
                def done():
                    self.regenerating_hume.discard(session_id)
                    self._load_sessions_list()
                    self.status_bar.showMessage(f"✅ Hume AI regeneration started! Check status in ~5 minutes.", 10000)
                    
                    # Desktop notification
                    self._show_desktop_notification(
                        "Hume AI Regeneration Started",
                        "Emotion analysis regeneration in progress. Check status in ~5 minutes."
                    )
                
                QTimer.singleShot(0, done)
                
            except Exception as e:
                logger.error(f"Hume regeneration failed: {e}")
                def on_error():
                    self.regenerating_hume.discard(session_id)
                    self._load_sessions_list()
                    self.status_bar.showMessage(f"❌ Failed: {str(e)[:50]}", 10000)
                QTimer.singleShot(0, on_error)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_regenerate_memories(self, session_id: str):
        """Regenerate Memories.ai pattern analysis only."""
        import threading
        
        reply = QMessageBox.question(
            self,
            "Regenerate Memories.ai",
            "Re-analyze patterns with Memories.ai?\n\n"
            "Old analysis will be archived.\n"
            "Processing time: ~5 minutes\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        session = self.database.get_session(session_id)
        if not session:
            return
        
        # Mark as regenerating
        self.regenerating_memories.add(session_id)
        self._load_sessions_list()  # Update UI to show loading state
        self.status_bar.showMessage("🔄 Regenerating Memories.ai analysis...", 3000)
        
        def worker():
            try:
                self._archive_old_cloud_results(session_id, memories_only=True)
                
                cam_video = self.config.get_data_dir() / session.cam_mp4_path
                screen_video = self.config.get_data_dir() / session.screen_mp4_path if session.screen_mp4_path else None
                
                _, memories_job_id = self.session_manager.cloud_analysis_manager.upload_session_for_analysis(
                    session_id=session_id,
                    cam_video_path=cam_video,
                    screen_video_path=screen_video,
                    run_hume=False,
                    run_memories=True
                )
                
                def done():
                    self.regenerating_memories.discard(session_id)
                    self._load_sessions_list()
                    self.status_bar.showMessage(f"✅ Memories.ai regeneration started! Check status in ~5 minutes.", 10000)
                    
                    # Desktop notification
                    self._show_desktop_notification(
                        "Memories.ai Regeneration Started",
                        "Pattern analysis regeneration in progress. Check status in ~5 minutes."
                    )
                
                QTimer.singleShot(0, done)
                
            except Exception as e:
                logger.error(f"Memories regeneration failed: {e}")
                def on_error():
                    self.regenerating_memories.discard(session_id)
                    self._load_sessions_list()
                    self.status_bar.showMessage(f"❌ Failed: {str(e)[:50]}", 10000)
                QTimer.singleShot(0, on_error)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_regenerate_comprehensive_only(self, session_id: str):
        """Regenerate comprehensive AI report using latest Hume/Memories data."""
        # Just trigger normal generation - it will archive old and create new
        self._on_generate_comprehensive_report(session_id)
    
    
    def _archive_old_cloud_results(self, session_id: str, hume_only: bool = False, memories_only: bool = False):
        """Archive old Hume AI and Memories.ai results before regenerating."""
        import shutil
        from pathlib import Path
        from datetime import datetime
        
        try:
            session_dir = self.config.get_data_dir() / f"sessions/{session_id}"
            archive_dir = session_dir / "ai_reports_archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Find and archive old results
            cloud_results_dir = self.config.get_data_dir() / "cloud_results" / session_id
            if cloud_results_dir.exists():
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                
                if not memories_only:  # Archive Hume unless memories_only
                    for file in cloud_results_dir.glob("hume_*.json"):
                        archive_file = archive_dir / f"{file.stem}_{timestamp}.json"
                        shutil.copy2(file, archive_file)
                        logger.info(f"Archived {file.name}")
                
                if not hume_only:  # Archive Memories unless hume_only
                    for file in cloud_results_dir.glob("memories_*.json"):
                        archive_file = archive_dir / f"{file.stem}_{timestamp}.json"
                        shutil.copy2(file, archive_file)
                        logger.info(f"Archived {file.name}")
            
        except Exception as e:
            logger.error(f"Failed to archive old results: {e}")
    
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

        # Properly dismiss the loading dialog
        loading.hide()
        loading.deleteLater()

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

        # Get theme colors
        colors = self._get_colors()
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Cloud Storage Management")
        dialog.setMinimumSize(900, 600)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)

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
        summary_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {colors['text_primary']};
                background-color: {colors['card_bg']};
                padding: 15px;
                border: 1px solid {colors['border']};
                border-radius: 6px;
            }}
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

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Upload to Cloud",
            f"Upload session videos to:\n\n" +
            "\n".join(f"  • {p}" for p in providers) +
            f"\n\nProcessing time: 5-10 minutes\n\nProceed?",
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

        # Get theme colors
        colors = self._get_colors()
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Session")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)

        layout = QVBoxLayout(dialog)

        # Header
        header = QLabel(f"<b>Delete session \"{session.task_name}\"?</b>")
        header.setStyleSheet(f"font-size: 14px; margin-bottom: 10px; color: {colors['text_primary']};")
        layout.addWidget(header)

        # Session info
        duration = self._format_duration(session)
        info = QLabel(
            f"Date: {session.started_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Duration: {duration}\n"
            f"Files: {folder_size_mb:.1f} MB"
        )
        info.setStyleSheet(f"color: {colors['text_secondary']}; margin-bottom: 15px;")
        layout.addWidget(info)

        # Radio buttons for deletion options
        button_group = QButtonGroup(dialog)

        record_only_radio = QRadioButton("Delete record only (keep video files)")
        record_only_radio.setStyleSheet(f"margin-bottom: 5px; color: {colors['text_primary']};")
        button_group.addButton(record_only_radio, 1)
        layout.addWidget(record_only_radio)

        delete_all_radio = QRadioButton("Delete record + all files (cam.mp4, screen.mp4, snapshots)")
        delete_all_radio.setStyleSheet(f"margin-bottom: 15px; color: {colors['text_primary']};")
        delete_all_radio.setChecked(True)  # Default to delete all
        button_group.addButton(delete_all_radio, 2)
        layout.addWidget(delete_all_radio)

        # Warning
        warning = QLabel("⚠️ This action cannot be undone!")
        warning.setStyleSheet(f"color: {colors['accent_red']}; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(warning)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Delete")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_red']};
                opacity: 0.85;
            }}
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
            colors = self._get_colors()
            placeholder = QLabel("No sessions found. Complete a focus session to see reports here.")
            placeholder.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 14px; padding: 20px;")
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
            colors = self._get_colors()
            placeholder = QLabel(f"No sessions match the current filters.\n\nTry adjusting your search or filter settings.")
            placeholder.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 14px; padding: 20px;")
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
        reply = QMessageBox.question(
            self,
            "Batch Upload Sessions",
            f"Upload {len(uploadable_sessions)} session(s) to cloud for analysis?\n\n"
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
        
        # Get theme colors
        colors = self._get_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📸 Snapshot Analysis Details")
        dialog.setMinimumSize(900, 600)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Header summary
        summary = QLabel(f"<h2>Snapshot Analysis</h2><p>Total snapshots: <b>{len(snapshots)}</b></p>")
        summary.setStyleSheet(f"color: {colors['text_primary']};")
        layout.addWidget(summary)
        
        # Create table for snapshot details
        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                gridline-color: {colors['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {colors['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Time", "Type", "Status", "Labels", "Confidence", "Latency"
        ])
        table.setRowCount(len(snapshots))
        
        for row, snapshot in enumerate(snapshots):
            # Time
            time_str = snapshot.timestamp.strftime("%H:%M:%S") if snapshot.timestamp else "N/A"
            table.setItem(row, 0, QTableWidgetItem(time_str))
            
            # Type
            snap_type = "📷 Camera" if "cam" in snapshot.jpeg_path else "🖥️ Screen"
            table.setItem(row, 1, QTableWidgetItem(snap_type))
            
            # Status
            from ..core.models import UploadStatus
            status_map = {
                UploadStatus.PENDING: "⏳ Pending",
                UploadStatus.UPLOADING: "⬆️ Uploading",
                UploadStatus.SUCCESS: "✅ Done",
                UploadStatus.FAILED: "❌ Failed"
            }
            status_text = status_map.get(snapshot.upload_status, str(snapshot.upload_status.value if hasattr(snapshot.upload_status, 'value') else snapshot.upload_status))
            table.setItem(row, 2, QTableWidgetItem(status_text))
            
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
        button_box.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_blue']};
                opacity: 0.9;
            }}
        """)
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
        
        # Get theme colors
        colors = self._get_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Distraction Analysis Details")
        dialog.setMinimumSize(900, 700)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors['bg_primary']};
                border: none;
            }}
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['bg_primary']};
            }}
        """)
        content_layout = QVBoxLayout(content_widget)
        
        # Build detailed report inline
        html = self._build_distraction_report(events, snapshots)
        
        text_display = QTextEdit()
        text_display.setReadOnly(True)
        text_display.setHtml(html)
        text_display.setStyleSheet(f"""
            QTextEdit {{
                font-size: 13px;
                color: {colors['text_primary']};
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 15px;
                line-height: 1.5;
            }}
        """)
        content_layout.addWidget(text_display)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_blue']};
                opacity: 0.9;
            }}
        """)
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
            time_key = snap.timestamp.replace(second=0, microsecond=0) if snap.timestamp else datetime.now()
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
            time_key = snap.timestamp.replace(second=0, microsecond=0) if snap.timestamp else datetime.now()
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

        colors = self._get_colors()

        card = QFrame()
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        layout = QGridLayout(card)
        layout.setSpacing(12)

        # Session info
        row = 0
        task_label = QLabel(session.task_name)
        task_label.setStyleSheet(f"""
            font-size: 17px; 
            font-weight: 700;
            color: {colors['text_primary']};
        """)
        layout.addWidget(task_label, row, 0, 1, 2)

        row += 1
        date_label = QLabel(f"📅 {session.started_at.strftime('%b %d, %Y at %H:%M')}")
        date_label.setStyleSheet(f"""
            color: {colors['text_secondary']}; 
            font-size: 13px;
            font-weight: 500;
        """)
        layout.addWidget(date_label, row, 0)

        duration_label = QLabel(f"⏱️ {self._format_duration(session)}")
        duration_label.setStyleSheet(f"""
            color: {colors['text_secondary']}; 
            font-size: 13px;
            font-weight: 500;
        """)
        layout.addWidget(duration_label, row, 1)

        # Cloud analysis section
        row += 1

        if not cloud_jobs:
            # No cloud jobs - show upload button if session is complete
            if session.ended_at:
                # Check if upload is in progress for this session
                is_uploading = session.session_id in self.active_uploads

                # Enhanced upload button with progress indicator
                btn_text = "⬆️ Uploading..." if is_uploading else "☁️ Upload to Cloud"
                upload_btn = QPushButton(btn_text)
                upload_btn.setEnabled(not is_uploading)  # Disable if uploading
                upload_btn.setMinimumHeight(32)
                upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                upload_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #AF52DE;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #9F42CE;
                    }}
                    QPushButton:disabled {{
                        background-color: {colors['text_tertiary']};
                        opacity: 0.5;
                    }}
                """)
                
                # Add tooltip
                upload_btn.setToolTip(
                    "Upload videos for cloud analysis\n"
                    "Processing time: 5-10 minutes"
                )
                
                upload_btn.clicked.connect(lambda: self._on_upload_to_cloud(session.session_id))
                layout.addWidget(upload_btn, row, 0, 1, 2)
                row += 1
        else:
            # Has cloud jobs - show status for each
            for job in cloud_jobs:
                status_label = QLabel(f"{job.provider.value}: {self._get_status_badge(job.status)}")
                status_label.setStyleSheet(f"""
                    color: {colors['text_primary']}; 
                    font-size: 13px;
                    font-weight: 500;
                """)
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
                    refresh_btn.setMinimumHeight(28)
                    refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    refresh_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['accent_blue']};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 4px 12px;
                            font-size: 12px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
                        }}
                        QPushButton:disabled {{
                            background-color: {colors['text_tertiary']};
                            opacity: 0.5;
                        }}
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

                    retry_btn = QPushButton("Uploading..." if is_uploading else "🔄 Retry")
                    retry_btn.setEnabled(not is_uploading)  # Disable if uploading
                    retry_btn.setMinimumHeight(28)
                    retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    retry_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['accent_orange']};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 4px 12px;
                            font-size: 12px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: #E68600;
                        }}
                        QPushButton:disabled {{
                            background-color: {colors['text_tertiary']};
                            opacity: 0.5;
                        }}
                    """)
                    retry_btn.clicked.connect(lambda checked, sid=session.session_id: self._on_upload_to_cloud(sid))
                    layout.addWidget(retry_btn, row, 1)

                # Show details button for COMPLETED jobs
                elif job.status == CloudJobStatus.COMPLETED:
                    details_btn = QPushButton("📄 Details")
                    details_btn.setMinimumHeight(28)
                    details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    details_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['accent_green']};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 4px 12px;
                            font-size: 12px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: #30B350;
                        }}
                    """)
                    details_btn.clicked.connect(lambda checked, jid=job.job_id: self._on_show_cloud_details(jid))
                    layout.addWidget(details_btn, row, 1)

                row += 1

        # Check cloud analysis status
        hume_complete = any(job.provider.value == "hume_ai" and job.status == CloudJobStatus.COMPLETED for job in cloud_jobs)
        memories_complete = any(job.provider.value == "memories_ai" and job.status == CloudJobStatus.COMPLETED for job in cloud_jobs)
        has_any_cloud_jobs = len(cloud_jobs) > 0
        
        # Individual regenerate buttons (if analysis has been done)
        if has_any_cloud_jobs and (hume_complete or memories_complete):
            regen_layout = QHBoxLayout()
            
            # Hume AI regenerate button
            if hume_complete:
                is_regen_hume = session.session_id in self.regenerating_hume
                btn_text = "⏳ Regenerating..." if is_regen_hume else "🔄 Regen Hume AI"
                regen_hume_btn = QPushButton(btn_text)
                regen_hume_btn.setEnabled(not is_regen_hume)
                regen_hume_btn.setMinimumHeight(28)
                regen_hume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                regen_hume_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['accent_blue']};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
                    }}
                    QPushButton:disabled {{
                        background-color: {colors['text_tertiary']};
                        opacity: 0.5;
                    }}
                """)
                tooltip = "Regenerating in background..." if is_regen_hume else "Regenerate Hume AI emotion analysis (old archived)"
                regen_hume_btn.setToolTip(tooltip)
                regen_hume_btn.clicked.connect(lambda: self._on_regenerate_hume(session.session_id))
                regen_layout.addWidget(regen_hume_btn)
            
            # Memories.ai regenerate button
            if memories_complete:
                is_regen_memories = session.session_id in self.regenerating_memories
                btn_text = "⏳ Regenerating..." if is_regen_memories else "🔄 Regen Memories.ai"
                regen_memories_btn = QPushButton(btn_text)
                regen_memories_btn.setEnabled(not is_regen_memories)
                regen_memories_btn.setMinimumHeight(28)
                regen_memories_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                regen_memories_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #AF52DE;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #9F42CE;
                    }}
                    QPushButton:disabled {{
                        background-color: {colors['text_tertiary']};
                        opacity: 0.5;
                    }}
                """)
                tooltip = "Regenerating in background..." if is_regen_memories else "Regenerate Memories.ai pattern analysis (old archived)"
                regen_memories_btn.setToolTip(tooltip)
                regen_memories_btn.clicked.connect(lambda: self._on_regenerate_memories(session.session_id))
                regen_layout.addWidget(regen_memories_btn)
            
            regen_layout.addStretch()
            layout.addLayout(regen_layout, row, 0, 1, 2)
            row += 1
        
        if hume_complete and memories_complete:
            # Check if comprehensive report already generated
            comprehensive_report_path = self.config.get_data_dir() / f"sessions/{session.session_id}/comprehensive_ai_report.json"
            
            if comprehensive_report_path.exists():
                # Report already generated - show regenerate button above view button
                is_generating = session.session_id in self.generating_reports
                btn_text = "🔄 Regenerating..." if is_generating else "🔄 Regenerate AI Report"
                regen_btn = QPushButton(btn_text)
                regen_btn.setEnabled(not is_generating)
                regen_btn.setMinimumHeight(32)
                regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                regen_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['accent_orange']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #E68600;
                    }}
                    QPushButton:disabled {{
                        background-color: {colors['text_tertiary']};
                        opacity: 0.5;
                    }}
                """)
                regen_btn.setToolTip("Regenerate comprehensive report with latest data (old archived)")
                regen_btn.clicked.connect(lambda: self._on_regenerate_comprehensive_only(session.session_id))
                layout.addWidget(regen_btn, row, 0, 1, 2)
                row += 1
                
                # View button below regenerate
                view_comprehensive_btn = QPushButton("📊 View Comprehensive AI Report")
                view_comprehensive_btn.setMinimumHeight(36)
                view_comprehensive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                view_comprehensive_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #AF52DE;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #9F42CE;
                    }}
                """)
                view_comprehensive_btn.setToolTip("View full AI-generated report with historical trends")
                view_comprehensive_btn.clicked.connect(lambda: self._on_view_comprehensive_report(session.session_id))
                layout.addWidget(view_comprehensive_btn, row, 0, 1, 2)
                row += 1
            else:
                # Can generate report - show generate button
                is_generating = session.session_id in self.generating_reports
                
                btn_text = "🔄 Generating AI Report..." if is_generating else "🤖 Generate Comprehensive AI Report"
                generate_btn = QPushButton(btn_text)
                generate_btn.setEnabled(not is_generating)
                generate_btn.setMinimumHeight(36)
                generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                generate_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['accent_orange']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: #E68600;
                    }}
                    QPushButton:disabled {{
                        background-color: {colors['text_tertiary']};
                        opacity: 0.5;
                    }}
                """)
                tooltip = "Generating report in background..." if is_generating else "Generate long-form AI report using Hume AI, Memories.ai, and historical data"
                generate_btn.setToolTip(tooltip)
                generate_btn.clicked.connect(lambda: self._on_generate_comprehensive_report(session.session_id))
                layout.addWidget(generate_btn, row, 0, 1, 2)
                row += 1

        # Action buttons row
        row += 1
        action_layout = QHBoxLayout()

        # View AI Summary button (if available)
        if self._load_saved_ai_summary(session.session_id):
            view_summary_btn = QPushButton("✨ View AI Summary")
            view_summary_btn.setMinimumHeight(32)
            view_summary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_summary_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #AF52DE;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #9F42CE;
                }}
            """)
            view_summary_btn.setToolTip("View AI-generated session summary")
            view_summary_btn.clicked.connect(lambda: self._on_view_saved_summary(session.session_id))
            action_layout.addWidget(view_summary_btn)

        # Show Files button
        show_files_btn = QPushButton("📁 Show Files")
        show_files_btn.setMinimumHeight(32)
        show_files_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        show_files_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#0066CC' if not self.dark_mode else '#0F8FFF'};
            }}
        """)
        show_files_btn.clicked.connect(lambda: self._on_show_files(session.session_id))
        action_layout.addWidget(show_files_btn)

        # Delete Session button
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setMinimumHeight(32)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #E6342B;
            }}
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
                        # NOTE: Videos are kept on cloud for reuse during regeneration
                        # User can manually delete them via "Manage Cloud Storage"
                        # self.session_manager.cloud_analysis_manager.delete_cloud_videos(job_id)

                        # Notify user
                        self.ui_queue.put({
                            "type": "cloud_job_complete",
                            "job_id": job_id,
                            "results_path": str(results_path)
                        })
                    else:
                        logger.error(f"Failed to retrieve results for job {job_id}")

                elif status == CloudJobStatus.PROCESSING:
                    # Job still processing - will be handled by auto-refresh timer
                    logger.info(f"Job {job_id} still processing, auto-refresh will check again in 60s")

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

            # Get theme colors
            colors = self._get_colors()
            
            # Create dialog to display results
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setMinimumSize(800, 600)  # Increased size for better readability
            dialog.resize(900, 700)  # Default size
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['bg_primary']};
                }}
            """)

            layout = QVBoxLayout(dialog)

            # Create scroll area for the text content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {colors['bg_primary']};
                    border: none;
                }}
            """)

            # Text display with results
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            text_display.setMarkdown(formatted_text)
            text_display.setStyleSheet(f"""
                QTextEdit {{
                    font-size: 13px;
                    color: {colors['text_primary']};
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 4px;
                    padding: 10px;
                    line-height: 1.4;
                }}
            """)

            # Set the text display as the scroll area's widget
            scroll_area.setWidget(text_display)
            layout.addWidget(scroll_area)

            # Close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent_blue']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-width: 80px;
                }}
            """)
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
                "Active Session Detected",
                "A focus session is currently active.\n\n"
                "Do you want to stop and save the session before quitting?\n\n"
                "• Yes: Stop session and save data\n"
                "• No: Cancel quit and keep session running",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            # User chose Yes - stop the session before quitting
            logger.info("Auto-stopping active session before application close...")
            try:
                # Stop timers
                self.session_timer.stop()
                self.stats_timer.stop()
                
                # Stop session manager
                stopped_session_id = self.session_manager.stop_session()
                logger.info(f"✅ Session auto-stopped on quit: {stopped_session_id}")
                
                # Reset UI state
                self.session_active = False
                self.current_session_id = None
                
                # Show brief confirmation
                self.status_bar.showMessage("✅ Session saved successfully", 2000)
                
            except Exception as e:
                logger.error(f"❌ Failed to auto-stop session: {e}", exc_info=True)
                
                # Ask if user still wants to quit despite error
                error_reply = QMessageBox.critical(
                    self,
                    "Error Stopping Session",
                    f"Failed to properly stop the session:\n\n{str(e)}\n\n"
                    "Quit anyway? (Session data may be incomplete)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if error_reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

        logger.info("Application closing gracefully")
        event.accept()

