# Agentic Feature Fix Summary

## Problem
The application was not closing the frontmost app after two consecutive distractions, even though the feature was implemented.

## Root Causes Found and Fixed

### 1. Missing Call to `_process_ui_messages()`
**Issue**: The `_process_ui_messages()` method in `session_manager.py` was defined but never called, so agent events from the distraction detector were never processed.

**Fix**: Added a call to `self._process_ui_messages()` at the start of `_update_session_stats()`, which is called periodically during active sessions.

```python
def _update_session_stats(self) -> None:
    """Update session statistics in database from live components."""
    if not self.current_session_id:
        return
    
    # Process UI queue messages (e.g., agent events)
    self._process_ui_messages()  # <- Added this
    # ... rest of stats update
```

### 2. Missing Null Check
**Issue**: The `_process_ui_messages()` method could crash if `queue_manager` was not initialized yet.

**Fix**: Added a guard check for `queue_manager`:

```python
def _process_ui_messages(self) -> None:
    """Non-blocking drain of UI queue for agent triggers and alerts."""
    if not self.queue_manager:  # <- Added this
        return
    try:
        while True:
            # ... process messages
```

### 3. Settings Not Persisting
**Issue**: The "Close frontmost app" checkbox in Settings was only writing to an environment variable, not persisting to the encrypted user config.

**Fix**: 
- Added `set_agent_close_app_enabled()` method to `config.py` to save the setting
- Updated the UI callback to use this method

```python
def _on_agent_close_toggled(self, state):
    enabled = state == Qt.CheckState.Checked
    try:
        self.config.set_agent_close_app_enabled(enabled)  # <- Persists to config
    except Exception as e:
        self.logger.warning(f"Failed to save agent close app setting: {e}")
```

## How to Test

1. Launch the application
2. Enable the feature in Settings: Check "Close frontmost app after two distractions in a row"
3. Start a session
4. Create two distractions within 60 seconds
   - The second distraction must end within 60 seconds of the first ending
5. The frontmost application should close automatically

## Technical Details

The agentic feature works as follows:
1. **Detection**: When a distraction ends (state machine confirms return to FOCUSED), the end timestamp is tracked
2. **Triggering**: If two distraction end times are within 60 seconds, an `agent_consecutive_distractions` event is emitted to the UI queue
3. **Action**: `SessionManager._handle_agent_consecutive()` checks if the feature is enabled, gets the frontmost app, and calls `app_control.quit_app()` to close it
4. **Safeguards**: Critical apps (Focus Guardian, Terminal, Python, iTerm) are whitelisted

## Files Modified

### Round 1 (Initial Fix):
- `src/focus_guardian/session/session_manager.py`: Added call to `_process_ui_messages()` in `_update_session_stats()`
- `src/focus_guardian/core/config.py`: Added `set_agent_close_app_enabled()` method
- `src/focus_guardian/ui/main_window.py`: Updated settings toggle to persist config

### Round 2 (Logging Improvements):
- `src/focus_guardian/session/session_manager.py`: 
  - Added detailed logging in `_process_ui_messages()` to track message processing
  - Added detailed logging in `_handle_agent_consecutive()` to track the close flow
  - Properly handle `Empty` exception from queue
- `src/focus_guardian/analysis/distraction_detector.py`:
  - Added debug logging in `_check_consecutive_distractions()` to track timing calculations
  - Shows when distractions are too far apart vs when trigger is sent

## Expected Log Output

When the feature is working, you should see these logs in sequence:
1. From `distraction_detector.py`: `"Checking consecutive distractions: delta=X.Xs, window=60s"`
2. From `distraction_detector.py`: `"Agent trigger: two distractions within X.Xs"`
3. From `session_manager.py`: `"Processing UI message: agent_consecutive_distractions"`
4. From `session_manager.py`: `"Triggering agent close app feature"`
5. From `session_manager.py`: `"Closing frontmost app: <AppName>"`
6. From `session_manager.py`: `"Agentic close issued for frontmost app: <AppName>"`

**If you see an error about "not allowed assistive" or "Accessibility permissions required"**: You need to grant macOS Accessibility permissions (see `ACCESSIBILITY_PERMISSIONS.md`).

## Round 3 (Critical Fix): macOS Permissions

**Issue Found**: macOS requires Accessibility permissions for the app-close feature to work!

### Changes Made:
- **`src/focus_guardian/utils/app_control.py`**:
  - Better error handling in `_run_osascript()` - catches permission errors specifically
  - Added `check_accessibility_permissions()` function to detect if permissions are granted
  - Added detailed logging in `get_frontmost_app()` to warn about missing permissions
  
- **`src/focus_guardian/session/session_manager.py`**:
  - Added permission check at the start of `_handle_agent_consecutive()`
  - Shows clear error message: "macOS Accessibility permissions required!"
  - Attempts to notify UI if permissions are missing

### New File:
- **`ACCESSIBILITY_PERMISSIONS.md`**: Complete guide on how to grant macOS Accessibility permissions

### To Fix:
Follow the instructions in `ACCESSIBILITY_PERMISSIONS.md` to grant permissions in System Settings > Privacy & Security > Accessibility.

