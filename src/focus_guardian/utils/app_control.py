"""
macOS app control utilities: get frontmost app and quit it.

Local-only implementation using AppleScript with safe fallbacks.
"""

from __future__ import annotations

import subprocess
from typing import Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


WHITELIST = {
    "Focus Guardian",
    "Python",
    "Terminal",
    "iTerm",
}


def _run_osascript(script: str) -> str:
    try:
        out = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"osascript failed with error {e.returncode}: {e.stderr}")
        if "not allowed assistive" in e.stderr.lower() or "not authorized" in e.stderr.lower():
            logger.error("macOS Accessibility permissions required! Please grant permissions in System Settings > Privacy & Security > Accessibility")
        return ""
    except Exception as e:
        logger.error(f"osascript failed: {e}")
        return ""


def check_accessibility_permissions() -> bool:
    """Check if this app has accessibility permissions.
    
    Returns:
        True if permissions are granted, False otherwise
    """
    result = _run_osascript(
        'tell application "System Events" to get name of every process'
    )
    return bool(result)


def get_frontmost_app() -> Optional[Tuple[str, str]]:
    """Return (name, name) for frontmost app. Bundle id resolution optional.

    Returns None if unavailable or if permissions are not granted.
    """
    name = _run_osascript(
        'tell application "System Events" to get name of first process whose frontmost is true'
    )
    if not name:
        logger.warning("Could not get frontmost app - may need Accessibility permissions")
        return None
    logger.debug(f"Frontmost app: {name}")
    return (name, name)


def quit_app(name: str) -> bool:
    """Attempt to quit app by name. Returns True if command issued.

    Uses AppleScript quit; falls back to pkill -x.
    """
    if not name or name in WHITELIST:
        logger.info(f"Skipping quit for whitelisted or empty app name: {name}")
        return False

    # Try polite quit first
    script = f'tell application "{name}" to quit'
    out = _run_osascript(script)
    if out is not None:
        logger.info(f"Sent quit to '{name}' via AppleScript")
        return True

    # Fallback to pkill
    try:
        subprocess.run(["pkill", "-x", name], check=False)
        logger.info(f"Issued pkill for '{name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to pkill '{name}': {e}")
        return False


