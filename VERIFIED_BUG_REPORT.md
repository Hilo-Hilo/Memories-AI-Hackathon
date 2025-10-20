# VERIFIED Bug Report - Focus Guardian

**Generated**: 2025-10-20  
**Status**: All bugs verified against actual code  

This report contains ONLY verified bugs after careful code review.

---

## 🔴 CRITICAL ISSUES (Verified)

### 1. ⚠️ Method Name Mismatch - get_cloud_jobs_by_session vs get_cloud_jobs_for_session
**Location**: `src/focus_guardian/session/cloud_analysis_manager.py:178`  
**Severity**: CRITICAL - AttributeError crash  
**Status**: ✅ VERIFIED  

**Code calls**:
```python
existing_jobs = self.database.get_cloud_jobs_by_session(session_id)
```

**Database class has**:
```python
def get_cloud_jobs_for_session(self, session_id: str) -> List[CloudAnalysisJob]:
```

**Impact**: Immediate `AttributeError` when trying to reuse videos  
**Verification**: Confirmed via grep - method called doesn't exist with that name  

**Fix**: Rename the method in Database OR fix the caller:
```python
# Option 1: Fix the caller
existing_jobs = self.database.get_cloud_jobs_for_session(session_id)

# Option 2: Add alias in Database class
def get_cloud_jobs_by_session(self, session_id: str) -> List[CloudAnalysisJob]:
    return self.get_cloud_jobs_for_session(session_id)
```

---

## 🟠 HIGH SEVERITY ISSUES (Verified)

### 2. ⚠️ Camera Failure Retry Without Limit
**Location**: `src/focus_guardian/capture/recorder.py:164-171`  
**Severity**: HIGH - Resource waste, log spam  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
while not self._stop_event.is_set():
    ret, frame = self._camera.read()
    if not ret or frame is None:
        logger.warning("Failed to read frame from camera")
        time.sleep(0.1)
        continue  # Loops forever if camera fails
```

**Impact**: 
- Continuous CPU usage on camera failure
- Log file grows rapidly (warning every 0.1 seconds)
- Only exits when session manually stopped
- User has no indication camera failed

**Verification**: Confirmed code continues indefinitely on camera failure  

**Severity Correction**: Not as critical as initially reported (exits on stop), but still wasteful  

**Fix**: Add failure counter:
```python
consecutive_failures = 0
MAX_CONSECUTIVE_FAILURES = 300  # 30 seconds at 0.1s intervals

while not self._stop_event.is_set():
    ret, frame = self._camera.read()
    if not ret or frame is None:
        consecutive_failures += 1
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.error("Camera failure threshold exceeded, stopping recording")
            break
        logger.warning(f"Failed to read frame ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
        time.sleep(0.1)
        continue
    
    consecutive_failures = 0  # Reset on success
    # ... rest of code
```

---

### 3. ⚠️ Timestamp Collision Risk
**Location**: `src/focus_guardian/capture/snapshot_scheduler.py:212`  
**Severity**: MEDIUM-HIGH - File overwrite  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
cam_path = self.snapshots_dir / f"cam_{timestamp_str}.jpg"
```

**Impact**: 
- Only second-precision in filenames
- If interval < 1 second or rapid testing, files overwrite
- Silent data loss

**Verification**: Confirmed format string lacks microseconds  

**Fix**:
```python
timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
```

---

### 4. ⚠️ SQL Injection via F-String
**Location**: `src/focus_guardian/core/database.py:633-640`  
**Severity**: HIGH - SQL injection vulnerability  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
if timestamp_field:
    conn.execute(f"""
        UPDATE cloud_analysis_jobs
        SET status = ?,
            provider_job_id = COALESCE(?, provider_job_id),
            {timestamp_field} = ?,  # <-- UNESCAPED F-STRING
            last_error = ?
        WHERE job_id = ?
    """, (status.value, provider_job_id, timestamp_value, error_message, job_id))
```

**Impact**: 
- SQL injection if `timestamp_field` is controlled by attacker
- Currently safe because values are hardcoded, but bad pattern

**Verification**: Confirmed f-string interpolation in SQL  

**Risk Level**: Low immediate risk (values hardcoded) but dangerous pattern  

**Fix**: Use parameterization or validate field name:
```python
ALLOWED_TIMESTAMP_FIELDS = {"upload_started_at", "processing_started_at", "processing_completed_at"}

if timestamp_field:
    if timestamp_field not in ALLOWED_TIMESTAMP_FIELDS:
        raise ValueError(f"Invalid timestamp field: {timestamp_field}")
    
    # Now safe to use
    conn.execute(f"""
        UPDATE cloud_analysis_jobs
        SET status = ?,
            provider_job_id = COALESCE(?, provider_job_id),
            {timestamp_field} = ?,
            last_error = ?
        WHERE job_id = ?
    """, (status.value, provider_job_id, timestamp_value, error_message, job_id))
```

---

## 🟡 MEDIUM SEVERITY ISSUES (Verified)

### 5. ⚠️ Monitor Index Bounds Check
**Location**: `src/focus_guardian/capture/screen_capture.py:40-46`  
**Severity**: MEDIUM - Potential IndexError  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
elif 0 <= monitor_index < len(monitors):
    self.monitor = monitors[monitor_index + 1]  # +1 offset
else:
    self.monitor = monitors[1]
```

**Impact**: 
- Bounds check doesn't account for +1 offset
- If `monitor_index == len(monitors) - 1`, then `monitors[monitor_index + 1]` is out of bounds

**Verification**: Confirmed bounds check vs actual access mismatch  

**Fix**:
```python
elif 0 <= monitor_index + 1 < len(monitors):
    self.monitor = monitors[monitor_index + 1]
else:
    self.monitor = monitors[1]
    logger.warning(f"Monitor index {monitor_index} out of range")
```

---

### 6. ⚠️ Transaction Rollback Not Implemented
**Location**: `src/focus_guardian/core/database.py:247-266`  
**Severity**: MEDIUM - Data integrity  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
def delete_session(self, session_id: str) -> None:
    with self._get_connection() as conn:
        # Multiple DELETE statements
        conn.execute("DELETE FROM session_reports WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM cloud_analysis_jobs WHERE session_id = ?", (session_id,))
        # ... more deletes
        conn.commit()  # No rollback on error
```

**Impact**: 
- If one DELETE fails, previous ones are committed
- Partial deletion leaves orphaned records
- Database integrity violated

**Verification**: Confirmed no try-except with rollback  

**Fix**:
```python
def delete_session(self, session_id: str) -> None:
    with self._get_connection() as conn:
        try:
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

### 7. ⚠️ State Buffer Span Can Be Zero
**Location**: `src/focus_guardian/core/state_machine.py:240-248`  
**Severity**: MEDIUM - Division by zero potential  
**Status**: ✅ VERIFIED  

**Actual code**:
```python
def _get_buffer_span_seconds(self) -> float:
    if len(self._snapshot_buffer) < 2:
        return 0.0
    
    first_ts = self._snapshot_buffer[0].timestamp
    last_ts = self._snapshot_buffer[-1].timestamp
    
    return (last_ts - first_ts).total_seconds()  # Can be 0.0
```

**Impact**: 
- If timestamps are identical (clock skew, rapid testing), span is 0.0
- Could cause division by zero elsewhere
- State machine may not transition properly

**Verification**: Confirmed no minimum value enforced  

**Fix**:
```python
def _get_buffer_span_seconds(self) -> float:
    if len(self._snapshot_buffer) < 2:
        return 0.0
    
    first_ts = self._snapshot_buffer[0].timestamp
    last_ts = self._snapshot_buffer[-1].timestamp
    span = (last_ts - first_ts).total_seconds()
    
    return max(span, 0.01)  # Minimum 0.01 seconds
```

---

## ✅ FALSE POSITIVES (Not Actually Bugs)

### ❌ None Handling in Cloud Analysis Manager
**Originally Reported**: Line 206 calls `cam_status.get('status')` without None check  
**Actual Status**: NOT A BUG - Protected by if statement  

**Why it's safe**:
```python
# Line 202-203
cam_exists = cam_status is not None
screen_exists = (screen_status is not None) if screen_video_no else True

# Line 205 - Only enter if not None
if cam_exists and screen_exists:
    # Line 206 - Safe because we're inside the if block
    cam_processed = cam_status.get('status') == 'PARSE'
```

The code properly checks `is not None` before accessing `.get()`. ✅

---

### ❌ Queue Full Exception Not Caught
**Originally Reported**: Line 262 doesn't catch queue.Full  
**Actual Status**: NOT A CRITICAL BUG - Caught by general exception handler  

**Why it's handled**:
```python
try:
    # Line 262
    self.upload_queue.put(snapshot_pair, block=False)
    # ... more code
except Exception as e:  # Line 273 - Catches queue.Full
    logger.error(f"Error capturing snapshots: {e}", exc_info=True)
```

The queue.Full exception IS caught, just not with a specific handler. This is a **code quality issue**, not a critical bug. Could be improved with specific handling for better error messages.

---

### ❌ Database Initialization Poor Error Handling
**Originally Reported**: Database init failures not handled  
**Actual Status**: NOT A BUG - Errors are caught  

**Why it's handled**:
```python
try:
    database = Database(db_path, schema_path)  # Line 47
    # ... rest of init
except Exception as e:  # Line 71 - Catches everything
    logger.error(f"Fatal error: {e}", exc_info=True)
    return 1
```

Errors ARE handled, just with generic messages. This is a **UX issue**, not a critical bug.

---

## 📊 VERIFIED BUG SUMMARY

| Severity | Count | Actual Bugs |
|----------|-------|-------------|
| Critical | 1 | Method name mismatch |
| High | 3 | Camera retry, Timestamp, SQL pattern |
| Medium | 3 | Monitor bounds, Transactions, Buffer span |
| **Total** | **7** | **Real bugs verified** |

**False Positives**: 3 (None handling, Queue exception, DB errors - all handled)

---

## 🎯 PRIORITY FIX ORDER

1. **Method name mismatch** (5 min) - Causes immediate crash
2. **SQL injection pattern** (10 min) - Security best practice
3. **Timestamp collision** (2 min) - Prevents data loss
4. **Camera retry limit** (10 min) - Improves reliability
5. **Monitor bounds** (5 min) - Prevents potential crash
6. **Transaction rollback** (10 min) - Data integrity
7. **Buffer span minimum** (2 min) - Edge case protection

**Total estimated fix time**: ~45 minutes

---

## 🧪 TESTING CHECKLIST

After fixes:

- [ ] Test video reuse (upload same session twice)
- [ ] Unplug camera during recording
- [ ] Set 1-second snapshot interval (test timestamp collision)
- [ ] Test with 3+ monitors
- [ ] Force database error during session delete
- [ ] Rapid session start/stop (test identical timestamps)

---

## 📝 NOTES

- Original report had 24 issues, 7 verified as real bugs
- 3 were false positives (code actually handles them)
- 14 were code quality issues (not critical bugs)
- All critical functionality is actually working, just with potential edge case failures

**Conclusion**: The codebase is generally solid. The one critical bug (method name) should be fixed immediately. Other bugs are edge cases or quality improvements.

