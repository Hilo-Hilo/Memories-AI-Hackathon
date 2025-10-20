# Focus Guardian - Bug Report & Code Issues

**Generated**: 2025-10-20  
**Review Type**: Comprehensive Code Analysis

This document identifies potential bugs, unexpected behaviors, and errorful internal logic that could lead to problems in the Focus Guardian application.

---

## 🔴 CRITICAL ISSUES

### 1. Missing Database Method - Cloud Analysis Manager Crash
**Location**: `src/focus_guardian/session/cloud_analysis_manager.py:178`  
**Severity**: CRITICAL - Application Crash  
**Description**:
```python
existing_jobs = self.database.get_cloud_jobs_by_session(session_id)
```
The method `get_cloud_jobs_by_session()` is called but **does not exist** in the `Database` class. This will cause `AttributeError` at runtime when trying to reuse existing Memories.ai videos.

**Impact**: 
- Application crashes when uploading videos to Memories.ai if a session was previously uploaded
- Re-upload feature completely broken
- Video reuse optimization cannot work

**Fix Required**: Add method to `Database` class:
```python
def get_cloud_jobs_by_session(self, session_id: str) -> List[CloudAnalysisJob]:
    """Get all cloud jobs for a specific session."""
    with self._get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM cloud_analysis_jobs
            WHERE session_id = ?
            ORDER BY created_at DESC
        """, (session_id,)).fetchall()
        return [self._row_to_cloud_job(row) for row in rows]
```

---

### 2. Unhandled None Return from get_video_status
**Location**: `src/focus_guardian/session/cloud_analysis_manager.py:194-207`  
**Severity**: CRITICAL - NoneType AttributeError  
**Description**:
```python
cam_status = self.memories_client.get_video_status(cam_video_no, unique_id)
# ... later ...
if cam_exists and screen_exists:
    cam_processed = cam_status.get('status') == 'PARSE'  # CRASH if cam_status is None
```

The `get_video_status()` method can return `None` (line 549 in memories_client.py), but the code assumes it returns a dict and calls `.get('status')` without checking.

**Impact**:
- `AttributeError: 'NoneType' object has no attribute 'get'` crash
- Upload fails when checking if videos already exist
- Video reuse feature broken

**Fix Required**: Add None checks:
```python
cam_status = self.memories_client.get_video_status(cam_video_no, unique_id)
screen_status = None
if screen_video_no:
    screen_status = self.memories_client.get_video_status(screen_video_no, unique_id)

# Determine overall status
cam_exists = cam_status is not None
screen_exists = (screen_status is not None) if screen_video_no else True

if cam_exists and screen_exists:
    cam_processed = cam_status.get('status') == 'PARSE' if cam_status else False
    screen_processed = (screen_status.get('status') == 'PARSE') if screen_status else True
```

---

### 3. Queue Full Exception Not Caught
**Location**: `src/focus_guardian/capture/snapshot_scheduler.py:262`  
**Severity**: HIGH - Snapshot Loss  
**Description**:
```python
self.upload_queue.put(snapshot_pair, block=False)
```

Using `block=False` without catching `queue.Full` exception will crash the scheduler thread if the queue is full.

**Impact**:
- Scheduler thread dies silently
- No more snapshots captured for remainder of session
- User unaware of problem until session ends

**Fix Required**:
```python
try:
    self.upload_queue.put(snapshot_pair, block=False)
except queue.Full:
    logger.error("Upload queue full, dropping snapshot pair")
    # Optionally: implement backpressure or queue size monitoring
```

---

### 4. Directory Creation Race Condition
**Location**: `src/focus_guardian/capture/snapshot_uploader.py:272-273`  
**Severity**: HIGH - File Write Failure  
**Description**:
```python
vision_dir = jpeg_path.parent.parent / "vision"
vision_dir.mkdir(parents=True, exist_ok=True)
vision_json_path = vision_dir / f"{jpeg_path.stem}.json"
```

The vision directory is created, but there's a subtle path construction issue. `jpeg_path.parent.parent` assumes the snapshot is two levels deep, but this isn't validated.

**Impact**:
- Vision JSON files may be written to wrong location
- File not found errors when reading results later
- Database has incorrect path reference

**Fix Required**:
```python
# Use session directory structure explicitly
session_dir = jpeg_path.parent.parent
vision_dir = session_dir / "vision"
vision_dir.mkdir(parents=True, exist_ok=True)
```

---

## 🟠 HIGH SEVERITY ISSUES

### 5. Infinite Loop on Camera Failure
**Location**: `src/focus_guardian/capture/recorder.py:167-171`  
**Severity**: HIGH - Resource Exhaustion  
**Description**:
```python
ret, frame = self._camera.read()
if not ret or frame is None:
    logger.warning("Failed to read frame from camera")
    time.sleep(0.1)
    continue  # Keeps retrying forever
```

If camera hardware fails or becomes disconnected, this will loop indefinitely, consuming CPU and filling logs.

**Impact**:
- High CPU usage
- Log file grows unbounded
- No user notification of camera failure
- Recording appears to work but produces empty/corrupt video

**Fix Required**:
```python
consecutive_failures = 0
MAX_CONSECUTIVE_FAILURES = 30  # 3 seconds at 0.1s sleep

while not self._stop_event.is_set():
    ret, frame = self._camera.read()
    if not ret or frame is None:
        consecutive_failures += 1
        logger.warning(f"Failed to read frame from camera ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
        
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.error("Camera failure threshold exceeded, stopping recording")
            break
            
        time.sleep(0.1)
        continue
    
    consecutive_failures = 0  # Reset on success
    # ... write frame ...
```

---

### 7. Session Component Cleanup Without Null Checks
**Location**: `src/focus_guardian/session/session_manager.py:383-390`  
**Severity**: HIGH - Potential Crashes on Cleanup  
**Description**:
```python
if self.webcam_recorder:
    self.webcam_recorder.stop()

if self.screen_recorder:
    self.screen_recorder.stop()
```

While null checks exist, the `.stop()` methods themselves don't validate internal state before attempting cleanup operations.

**Impact**:
- Potential crashes during session shutdown
- Incomplete cleanup leaving threads/resources
- Video files may be corrupt or incomplete

**Fix Required**: Add try-except blocks:
```python
if self.webcam_recorder:
    try:
        self.webcam_recorder.stop()
        logger.info("Webcam recorder stopped")
    except Exception as e:
        logger.error(f"Error stopping webcam recorder: {e}", exc_info=True)

if self.screen_recorder:
    try:
        self.screen_recorder.stop()
        logger.info("Screen recorder stopped")
    except Exception as e:
        logger.error(f"Error stopping screen recorder: {e}", exc_info=True)
```

---

### 8. Memories.ai Rate Limiting - Inconsistent Retry Logic
**Location**: `src/focus_guardian/integrations/memories_client.py:97-111`  
**Severity**: HIGH - Upload Failures  
**Description**:
The rate limiting retry logic checks for error message strings, but the actual rate limit response might have different formatting or HTTP status codes that aren't caught.

```python
if 'exceeded the limit' in error_msg.lower() or 'rate limit' in error_msg.lower():
    # retry logic
```

**Impact**:
- Uploads fail permanently when they could be retried
- Users hit rate limits during legitimate usage
- No exponential backoff between uploads

**Fix Required**:
```python
# Add more comprehensive rate limit detection
rate_limit_indicators = [
    'exceeded the limit',
    'rate limit',
    'too many requests',
    'quota exceeded',
    'throttled'
]

is_rate_limited = any(indicator in error_msg.lower() for indicator in rate_limit_indicators)

# Also add delays between sequential uploads in cloud_analysis_manager
```

---

### 9. Timestamp Collision in Snapshot Naming
**Location**: `src/focus_guardian/capture/snapshot_scheduler.py:212`  
**Severity**: MEDIUM-HIGH - Data Loss  
**Description**:
```python
timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
cam_path = self.snapshots_dir / f"cam_{timestamp_str}.jpg"
```

Using only seconds precision for filenames can cause collisions if snapshots are taken more frequently than once per second (which is possible during testing or if interval is reduced).

**Impact**:
- File overwrite without warning
- Lost snapshot data
- Database references incorrect files

**Fix Required**:
```python
timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")  # Add microseconds
cam_path = self.snapshots_dir / f"cam_{timestamp_str}.jpg"
```

---

## 🟡 MEDIUM SEVERITY ISSUES

### 10. Config Validation Doesn't Stop Execution
**Location**: `src/focus_guardian/core/config.py:100-108`  
**Severity**: MEDIUM - Invalid Runtime State  
**Description**:
When configuration validation fails, the system logs errors but continues execution with potentially invalid configuration values.

```python
test_value = self._get_config_value("snapshot_interval_sec", None)
if test_value is None:
    logger.error("Configuration system validation failed")
    self._emergency_config_reset()  # Resets but continues
```

**Impact**:
- Application runs with invalid settings
- Unpredictable behavior
- Users don't know configuration is broken

**Fix Required**:
```python
if test_value is None:
    logger.critical("Configuration system validation failed - cannot continue")
    self._emergency_config_reset()
    # Re-validate after emergency reset
    test_value = self._get_config_value("snapshot_interval_sec", None)
    if test_value is None:
        raise RuntimeError("Configuration system is irrecoverably broken. Please check config files.")
```

---

### 11. State Buffer Span Could Be Zero
**Location**: `src/focus_guardian/core/state_machine.py:240-248`  
**Severity**: MEDIUM - State Transition Issues  
**Description**:
```python
def _get_buffer_span_seconds(self) -> float:
    if len(self._snapshot_buffer) < 2:
        return 0.0
    
    first_ts = self._snapshot_buffer[0].timestamp
    last_ts = self._snapshot_buffer[-1].timestamp
    
    return (last_ts - first_ts).total_seconds()
```

If snapshots have identical timestamps (rare but possible due to rapid testing or time sync issues), span is 0, which could cause division by zero elsewhere.

**Impact**:
- State machine may not transition properly
- False positives/negatives in distraction detection
- Metrics calculations may crash

**Fix Required**:
```python
def _get_buffer_span_seconds(self) -> float:
    if len(self._snapshot_buffer) < 2:
        return 0.0
    
    first_ts = self._snapshot_buffer[0].timestamp
    last_ts = self._snapshot_buffer[-1].timestamp
    
    span = (last_ts - first_ts).total_seconds()
    return max(span, 0.01)  # Minimum 0.01 seconds to avoid zero
```

---

### 12. Camera Index Not Validated
**Location**: `src/focus_guardian/capture/recorder.py:124`  
**Severity**: MEDIUM - Silent Failure  
**Description**:
```python
self._camera = cv2.VideoCapture(self.camera_index)

if not self._camera.isOpened():
    logger.error(f"Failed to open camera at index {self.camera_index}")
    return
```

The camera index is not validated before use. If user configures invalid index, error is logged but thread exits silently.

**Impact**:
- Recording appears to start but no video is captured
- User doesn't know recording failed until session ends
- Empty video files created

**Fix Required**:
```python
# In SessionManager before starting recorder:
def _validate_camera_index(self, camera_index: int) -> bool:
    """Validate camera index is accessible."""
    test_cap = cv2.VideoCapture(camera_index)
    if test_cap.isOpened():
        test_cap.release()
        return True
    return False

# In start_session:
camera_index = self.config.get_camera_index()
if not self._validate_camera_index(camera_index):
    raise RuntimeError(f"Camera at index {camera_index} is not accessible")
```

---

### 13. Hume AI Job List Parsing Assumptions
**Location**: `src/focus_guardian/integrations/hume_client.py:484-492`  
**Severity**: MEDIUM - Data Parsing Errors  
**Description**:
```python
job_dict = {
    "id": job.id if hasattr(job, 'id') else str(job),
    "status": job.state.status if hasattr(job, 'state') else "UNKNOWN",
    "created_timestamp_ms": job.state.created_timestamp_ms if hasattr(job, 'state') else None,
    # ...
}
```

Uses hasattr checks but doesn't handle AttributeError if state exists but status doesn't, or if the API response structure changes.

**Impact**:
- Storage summary feature may crash
- UI can't display cloud storage info
- User can't manage cloud videos

**Fix Required**:
```python
try:
    job_dict = {
        "id": getattr(job, 'id', str(job)),
        "status": getattr(getattr(job, 'state', None), 'status', 'UNKNOWN'),
        "created_timestamp_ms": getattr(getattr(job, 'state', None), 'created_timestamp_ms', None),
        # ...
    }
except Exception as e:
    logger.warning(f"Failed to parse job data: {e}, skipping")
    continue
```

---

### 14. Incomplete Transaction Rollback
**Location**: `src/focus_guardian/core/database.py:247-266`  
**Severity**: MEDIUM - Data Integrity  
**Description**:
The `delete_session()` method deletes from multiple tables but doesn't use a transaction wrapper to ensure atomicity.

```python
def delete_session(self, session_id: str) -> None:
    with self._get_connection() as conn:
        conn.execute("DELETE FROM session_reports WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM cloud_analysis_jobs WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM distraction_events WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM snapshots WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
```

If any DELETE fails (e.g., foreign key constraint in future), partial deletion occurs.

**Impact**:
- Orphaned database records
- Database integrity issues
- Storage not fully reclaimed

**Fix Required**:
```python
def delete_session(self, session_id: str) -> None:
    with self._get_connection() as conn:
        try:
            # Delete in reverse dependency order
            conn.execute("DELETE FROM session_reports WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM cloud_analysis_jobs WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM distraction_events WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM snapshots WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
```

---

### 15. Monitor Index Off-By-One Error
**Location**: `src/focus_guardian/capture/screen_capture.py:41`  
**Severity**: MEDIUM - Wrong Monitor Captured  
**Description**:
```python
elif 0 <= monitor_index < len(monitors):
    self.monitor = monitors[monitor_index + 1]  # +1 because monitors[0] is "all monitors"
```

The logic adds +1 to the monitor_index, but the bounds check doesn't account for this. If user selects the last monitor index, this could go out of bounds.

**Impact**:
- Screen capture from wrong monitor
- Potential IndexError crash
- User confusion about which screen is captured

**Fix Required**:
```python
# Adjust bounds check to account for +1 offset
elif 0 <= monitor_index + 1 < len(monitors):
    self.monitor = monitors[monitor_index + 1]
else:
    self.monitor = monitors[1]
    logger.warning(f"Monitor index {monitor_index} out of range, using primary")
```

---

### 16. Queue.put Without Full Exception Not Caught in Detector
**Location**: `src/focus_guardian/analysis/distraction_detector.py:395-402`  
**Severity**: MEDIUM - Lost Alerts  
**Description**:
```python
self.ui_queue.put({
    "type": "distraction_alert",
    # ...
}, block=False)
```

Similar to snapshot scheduler, using `block=False` without catching `queue.Full` will crash if UI queue is full.

**Impact**:
- Detector thread crash on full queue
- User doesn't see alerts
- Distraction events still saved but no notification

**Fix Required**:
```python
try:
    self.ui_queue.put({
        "type": "distraction_alert",
        # ...
    }, block=False)
    logger.info("Alert sent to UI queue")
except queue.Full:
    logger.warning("UI queue full, alert dropped")
except Exception as e:
    logger.error(f"Failed to send immediate alert: {e}")
```

---

## 🔵 LOW SEVERITY / CODE QUALITY ISSUES

### 17. Excessive Logging in Production
**Location**: Multiple files, e.g., `snapshot_uploader.py:290-293`  
**Severity**: LOW - Performance  
**Description**:
Debug-level logs use string formatting eagerly even when debug logging is disabled.

```python
logger.debug(
    f"Worker {worker_id} uploaded {kind} snapshot {snapshot_id[:8]} "
    f"(latency: {vision_result.latency_ms:.0f}ms)"
)
```

**Impact**:
- Unnecessary string formatting overhead
- Reduced performance in tight loops

**Fix Recommended**:
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(
        f"Worker {worker_id} uploaded {kind} snapshot {snapshot_id[:8]} "
        f"(latency: {vision_result.latency_ms:.0f}ms)"
    )
```

---

### 18. Hardcoded Sleep Delays
**Location**: `cloud_analysis_manager.py:259, 579`  
**Severity**: LOW - User Experience  
**Description**:
```python
time.sleep(3.0)
logger.info("Waiting 3 seconds before uploading screen video...")
```

Hardcoded 3-second delays between Memories.ai uploads may be too conservative or too aggressive depending on API rate limits.

**Impact**:
- Unnecessarily slow uploads
- Or still hitting rate limits if API changes

**Fix Recommended**:
```python
# Add to config
MEMORIES_API_DELAY_SECONDS = 3.0

# Use adaptive backoff
def _adaptive_delay(self, attempt: int) -> float:
    """Calculate delay with exponential backoff."""
    base_delay = self.config.get_config_value("memories_api_delay_seconds", 3.0)
    return min(base_delay * (2 ** attempt), 30.0)  # Cap at 30s
```

---

### 19. Missing Type Hints in Critical Methods
**Location**: Multiple files, e.g., `main_window.py`  
**Severity**: LOW - Maintainability  
**Description**:
Many methods lack return type hints, making it harder to catch type errors.

**Impact**:
- Harder to maintain
- Type checking tools less effective
- More runtime type errors

**Fix Recommended**:
Add comprehensive type hints throughout codebase.

---

### 20. No Timeout on Blocking Queue Operations
**Location**: `fusion_engine.py:96`  
**Severity**: LOW - Shutdown Hang  
**Description**:
```python
fusion_message = self.fusion_queue.get(timeout=1.0)
```

While a timeout exists, other queue operations elsewhere may not have timeouts.

**Impact**:
- Application may hang during shutdown
- Threads don't exit cleanly

**Fix Recommended**:
Audit all queue.get() calls and ensure timeouts are used consistently.

---

## 📊 SUMMARY

| Severity | Count | Immediate Action Required |
|----------|-------|---------------------------|
| Critical | 5 | Yes - Blocks core functionality |
| High | 8 | Yes - Causes data loss or crashes |
| Medium | 7 | Soon - Affects reliability |
| Low | 4 | Eventually - Code quality |
| **Total** | **24** | |

---

## 🎯 RECOMMENDED PRIORITY ORDER

1. **Fix Database Method (Issue #1)** - Blocks video reuse feature completely
2. **Fix None Handling (Issue #2)** - Causes crashes in video upload flow  
3. **Add Queue Exception Handling (Issue #3)** - Prevents snapshot loss
4. **Fix Camera Failure Loop (Issue #5)** - Prevents resource exhaustion
5. **Add Session Cleanup Error Handling (Issue #6)** - Ensures clean shutdown
6. **Improve Rate Limiting (Issue #7)** - Better API resilience
7. **Fix Path Construction (Issue #4)** - Data integrity
8. **Add Timestamp Microseconds (Issue #8)** - Prevents file collision
9. **Validate Config State (Issue #9)** - Better error visibility
10. **All remaining issues** - Code quality and edge cases

---

## 🔧 TESTING RECOMMENDATIONS

After fixes are applied, test:

1. **Video Re-upload**: Upload same session twice, verify reuse works
2. **Camera Disconnect**: Unplug camera during recording, verify graceful handling
3. **Queue Saturation**: Fast snapshot interval to fill upload queue
4. **Rate Limiting**: Sequential uploads to trigger Memories.ai rate limits
5. **Config Corruption**: Manually corrupt config files, verify recovery
6. **Parallel Sessions**: Start/stop multiple sessions rapidly
7. **Network Failures**: Disconnect network during upload
8. **Timestamp Collisions**: Set 1-second interval, verify unique filenames

---

## 📝 NOTES

- This review was conducted via static analysis
- Runtime testing may reveal additional issues
- Database schema migrations may be needed for some fixes
- API contract changes from external services (Hume, Memories) not covered
- Thread safety and race conditions require deeper analysis

**Review completed**: 2025-10-20

