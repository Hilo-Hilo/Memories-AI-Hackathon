"""
Focus Guardian - Application Entry Point

ADHD distraction analysis desktop application with snapshot-based
cloud vision AI for pattern-confirmed distraction detection.
"""

import sys
import signal
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .core.config import Config
from .core.database import Database
from .ui.main_window import MainWindow
from .utils.logger import setup_logger, get_logger

# Setup logging
logger = setup_logger("focus_guardian")


def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    QApplication.quit()


def main():
    """Main application entry point."""
    logger.info("="*60)
    logger.info("FOCUS GUARDIAN - Starting Application")
    logger.info("="*60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize configuration
        config = Config()
        logger.info(f"Configuration loaded from {config.root_dir}")
        
        # Initialize database
        db_path = config.get_data_dir() / "focus_guardian.db"
        schema_path = config.root_dir / "config" / "schema.sql"
        database = Database(db_path, schema_path)
        logger.info(f"Database initialized at {db_path}")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Focus Guardian")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("Focus Guardian")
        
        # Set application-wide style
        app.setStyle("Fusion")  # Modern cross-platform style
        
        # Create main window
        main_window = MainWindow(config, database)
        main_window.show()
        
        # Connect cleanup handler for Ctrl+C and app quit
        def cleanup_on_quit():
            """Cleanup handler for application quit."""
            logger.info("Application quit signal received")
            # The closeEvent will handle session cleanup
        
        app.aboutToQuit.connect(cleanup_on_quit)
        
        logger.info("Main window created, entering event loop")
        
        # Run application
        exit_code = app.exec()
        
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

