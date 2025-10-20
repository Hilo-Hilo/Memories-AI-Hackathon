# Quick Fix Reference Card

**Use this for rapid bug fixing during development**

---

## 🔥 CRITICAL - FIX THESE FIRST

### 1. Missing Database Method
**File**: `src/focus_guardian/core/database.py`  
**Add after line 611**:
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

### 2. Fix None Handling in Cloud Manager
**File**: `src/focus_guardian/session/cloud_analysis_manager.py`  
**Replace lines 194-207** with:
```python
cam_status = self.memories_client.get_video_status(cam_video_no, unique_id)
screen_status = None
if screen_video_no:
    time.sleep(1.0)
    screen_status = self.memories_client.get_video_status(screen_video_no, unique_id)

# Check if videos exist
cam_exists = cam_status is not None
screen_exists = (screen_status is not None) if screen_video_no else True

if cam_exists and screen_exists:
    cam_processed = cam_status.get('status') == 'PARSE' if cam_status else False
    screen_processed = (screen_status.get('status') == 'PARSE') if screen_status else True
    
    if cam_processed and screen_processed:
        logger.info(f"Reusing existing processed videos")
        return existing_memories_job.job_id
```

---

### 3. Catch Queue Full Exception
**File**: `src/focus_guardian/capture/snapshot_scheduler.py`  
**Replace line 262** with:
```python
try:
    self.upload_queue.put(snapshot_pair, block=False)
except queue.Full:
    logger.error("Upload queue full, dropping snapshot pair")
```

**Also fix in**: `src/focus_guardian/analysis/distraction_detector.py`  
**Lines 395-402** and **Lines 437-444** - wrap with try-except

---

### 4. Add Camera Failure Counter
**File**: `src/focus_guardian/capture/recorder.py`  
**Replace lines 164-180** with:
```python
# Recording loop
frame_interval = 1.0 / self.fps
consecutive_failures = 0
MAX_FAILURES = 30

while not self._stop_event.is_set():
    start_time = time.time()
    
    ret, frame = self._camera.read()
    if not ret or frame is None:
        consecutive_failures += 1
        logger.warning(f"Failed to read frame ({consecutive_failures}/{MAX_FAILURES})")
        
        if consecutive_failures >= MAX_FAILURES:
            logger.error("Camera failure threshold exceeded")
            break
            
        time.sleep(0.1)
        continue
    
    consecutive_failures = 0  # Reset on success
    self._writer.write(frame)
    
    elapsed = time.time() - start_time
    if elapsed < frame_interval:
        time.sleep(frame_interval - elapsed)
```

---

### 5. Add Timestamp Microseconds
**File**: `src/focus_guardian/capture/snapshot_scheduler.py`  
**Replace line 212** with:
```python
timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
```

---

## ⚡ HIGH PRIORITY - FIX SOON

### 6. Wrap Component Cleanup
**File**: `src/focus_guardian/session/session_manager.py`  
**Replace lines 383-390** with:
```python
if self.webcam_recorder:
    try:
        self.webcam_recorder.stop()
        logger.info("Webcam recorder stopped")
    except Exception as e:
        logger.error(f"Error stopping webcam: {e}", exc_info=True)

if self.screen_recorder:
    try:
        self.screen_recorder.stop()
        logger.info("Screen recorder stopped")
    except Exception as e:
        logger.error(f"Error stopping screen: {e}", exc_info=True)
```

---

### 7. Fix Monitor Index
**File**: `src/focus_guardian/capture/screen_capture.py`  
**Replace lines 40-42** with:
```python
elif 0 <= monitor_index + 1 < len(monitors):
    self.monitor = monitors[monitor_index + 1]
```

---

### 8. Add Camera Validation
**File**: `src/focus_guardian/session/session_manager.py`  
**Add before line 137**:
```python
def _validate_camera_index(self, camera_index: int) -> bool:
    """Validate camera is accessible."""
    test_cap = cv2.VideoCapture(camera_index)
    if test_cap.isOpened():
        test_cap.release()
        return True
    return False

# In _initialize_components, before creating webcam_recorder:
camera_index = self.config.get_camera_index()
if not self._validate_camera_index(camera_index):
    raise RuntimeError(f"Camera {camera_index} not accessible")
```

---

### 9. Add Transaction Rollback
**File**: `src/focus_guardian/core/database.py`  
**Replace lines 247-266** with:
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
            logger.error(f"Failed to delete session: {e}")
            raise
```

---

## 🧪 QUICK SMOKE TEST

After applying fixes, run these quick tests:

```bash
# 1. Start app
python -m src.focus_guardian.main

# 2. Start a session
# 3. Wait for 2+ snapshots
# 4. Stop session
# 5. Check logs for errors

# 6. Upload to cloud (if configured)
# 7. Upload same session again (test reuse)

# Test camera failure
# 8. Unplug camera mid-session
# 9. Verify graceful handling

# Test queue saturation
# 10. Set snapshot_interval_sec to 1 in config
# 11. Run session for 1 minute
# 12. Check no queue full errors
```

---

## 📋 CHECKLIST BEFORE COMMITTING

- [ ] Fixed critical bugs (#1-5)
- [ ] Added unit tests for fixes
- [ ] Ran smoke tests
- [ ] Updated CHANGELOG
- [ ] No new linter errors
- [ ] Verified on macOS
- [ ] Checked logs for errors

---

## 🆘 IF THINGS BREAK

### Application Won't Start
1. Check database file exists: `data/focus_guardian.db`
2. Check schema file exists: `config/schema.sql`
3. Delete database file to reset
4. Check Python dependencies installed

### No Snapshots Being Captured
1. Check camera permissions in System Preferences
2. Test camera manually: `python -c "import cv2; print(cv2.VideoCapture(0).read())"`
3. Check upload queue not full: Look for "queue full" in logs
4. Verify snapshot directory created

### Cloud Upload Fails
1. Check API keys configured correctly
2. Test API key: `curl -H "Authorization: YOUR_KEY" https://api.memories.ai/serve/api/v1/list_videos`
3. Check rate limits: Look for "429" or "rate limit" in logs
4. Verify video files exist and are not corrupt

### Crashes During Cleanup
1. Check all component stop() methods wrapped in try-except
2. Look for "stop" or "cleanup" in error logs
3. Increase timeout values if needed

---

## 📞 QUICK HELP

- **Full Details**: See `BUG_REPORT.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Test Guide**: See `tests/TEST_GUIDE.md`
- **Logs**: `data/logs/*.log`

**Last Updated**: 2025-10-20



