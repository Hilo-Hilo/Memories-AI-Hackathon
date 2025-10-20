# Cloud Analysis Implementation Summary

This document describes the complete cloud video analysis workflow implementation for Focus Guardian.

## Architecture Overview

The implementation follows your specification:

1. **Upload Phase**: User stops session → Warning dialog (blocking) → Upload videos to cloud
2. **Post-Upload**: User can quit app (processing happens server-side)
3. **Reports Tab**: Shows all sessions with cloud analysis status badges
4. **Refresh Button**: Per-session polling to check if processing complete
5. **Result Retrieval**: When complete → Fetch structured data → Validate → Delete cloud videos → Store locally

## Components

### 1. Data Models ([src/focus_guardian/core/models.py](src/focus_guardian/core/models.py))

**CloudAnalysisJob** - Tracks full lifecycle of cloud analysis jobs:
- `job_id` - UUID for local tracking
- `provider` - CloudProvider.HUME_AI | CloudProvider.MEMORIES_AI
- `provider_job_id` - External job ID from cloud service
- `status` - PENDING → UPLOADING → PROCESSING → COMPLETED | FAILED
- `video_type` - WEBCAM | SCREEN | BOTH
- `results_fetched` - Boolean flag for retrieval completion
- `can_delete_remote` - Safety flag (only delete after local storage confirmed)
- `remote_deleted_at` - Timestamp when cloud videos deleted

### 2. Database Layer ([src/focus_guardian/core/database.py](src/focus_guardian/core/database.py))

**Schema** ([config/schema.sql](config/schema.sql)):
- `cloud_analysis_jobs` table with full lifecycle tracking
- Indexes on `session_id`, `status`, `provider`, `can_delete_remote`
- Foreign key constraint on `sessions` table with CASCADE delete

**New Methods**:
- `create_cloud_job()` - Create new cloud job record
- `get_cloud_job()` - Get job by job_id
- `get_cloud_jobs_for_session()` - Get all jobs for a session
- `get_cloud_jobs_by_status()` - Query by status
- `update_cloud_job_status()` - Update status with automatic timestamps
- `mark_cloud_job_upload_complete()` - Mark upload phase done
- `mark_cloud_job_results_fetched()` - Mark results retrieved and stored
- `mark_cloud_video_deleted()` - Mark cloud videos deleted
- `increment_cloud_job_retry()` - Increment retry counter
- `get_all_sessions()` - Get all sessions sorted by date (for Reports tab)

### 3. Cloud Analysis Manager ([src/focus_guardian/session/cloud_analysis_manager.py](src/focus_guardian/session/cloud_analysis_manager.py))

**Core Orchestrator** for cloud analysis lifecycle:

**`upload_session_for_analysis()`** - BLOCKING method:
- Uploads videos to Hume AI and/or Memories.ai
- Creates database records with status=UPLOADING
- Updates status to PROCESSING after successful upload
- Returns tuple of (hume_job_id, memories_job_id)
- Caller should show progress dialog during this operation

**`check_job_status()`** - NON-BLOCKING poll:
- Polls cloud provider API to check if processing complete
- Single check, no waiting (timeout=1s)
- Updates database with current status
- Returns CloudJobStatus

**`retrieve_and_store_results()`**:
- Fetches results from cloud provider
- Validates structure (different schema for Hume vs Memories.ai)
- Stores results locally in `data/cloud_results/{session_id}/`
- Marks `can_delete_remote=True` in database
- Returns path to stored results JSON

**`delete_cloud_videos()`**:
- Safety check: only deletes if `can_delete_remote=True`
- Hume AI: No delete API (jobs expire automatically)
- Memories.ai: Calls `delete_video()` for each video_no
- Marks `remote_deleted_at` in database

**Memories.ai Structured Output**:
- Uses custom prompt requesting strict JSON response
- Schema includes: `time_segmentation`, `app_usage`, `distraction_analysis`, `insights`
- Parsing handles markdown code blocks (```json ... ```)
- Validation checks for required fields
- Falls back to minimal valid structure if parsing fails

### 4. Session Manager Integration ([src/focus_guardian/session/session_manager.py](src/focus_guardian/session/session_manager.py))

**Initialization**:
- Creates `CloudAnalysisManager` instance
- Passes config, database, and cloud clients (Hume + Memories)

**New Method**: `upload_session_for_cloud_analysis(session_id)`
- BLOCKING upload method
- Checks which services enabled (`is_hume_ai_enabled()`, `is_memories_ai_enabled()`)
- Calls `cloud_analysis_manager.upload_session_for_analysis()`
- Sends `cloud_upload_complete` message to UI queue
- Returns tuple of job IDs

**Removed**:
- Old `_run_cloud_analysis_background()` method (replaced with new workflow)
- Background daemon thread that blocked for 10-15 minutes
- `generate_with_cloud_analysis()` from report_generator (no longer used)

### 5. UI - Reports Tab ([src/focus_guardian/ui/main_window.py](src/focus_guardian/ui/main_window.py))

**New Components**:

**Reports Tab Layout**:
- Header with "Session Reports" title + "Refresh All" button
- Scrollable container for session cards
- Auto-loads on tab creation

**Session Card** (`_create_session_card()`):
- Displays: Task name, date, duration
- Shows cloud analysis status badges (color-coded by status)
- Per-provider "Refresh" button
- Statuses: PENDING (gray), UPLOADING (orange), PROCESSING (blue), COMPLETED (green), FAILED (red)

**Refresh Logic** (`_on_refresh_job()`):
- Runs in background thread (non-blocking UI)
- Calls `cloud_analysis_manager.check_job_status(job_id)`
- If COMPLETED:
  - Retrieves results via `retrieve_and_store_results()`
  - Deletes cloud videos via `delete_cloud_videos()`
  - Sends `cloud_job_complete` notification to UI queue
- Reloads sessions list to update status badges

**Refresh All** (`_on_refresh_all_sessions()`):
- TODO: Iterate through all PROCESSING jobs and refresh each
- Current implementation just reloads the list

### 6. Hume AI Integration ([src/focus_guardian/integrations/hume_client.py](src/focus_guardian/integrations/hume_client.py))

**Existing Methods** (no changes needed):
- `analyze_video()` - Submit video to Batch API, returns job_id
- `poll_job()` - Check status with exponential backoff
- `fetch_results()` - Download emotion timeline
- `analyze_video_sync()` - Convenience wrapper (submit → poll → fetch)

**Result Structure**:
```json
{
  "job_id": "...",
  "timeline": [{"timestamp": 0.0, "frame": 0, "emotions": {...}}],
  "summary": {"avg_concentration": 0.6, "avg_frustration": 0.4, ...},
  "frame_count": 120
}
```

### 7. Memories.ai Integration ([src/focus_guardian/integrations/memories_client.py](src/focus_guardian/integrations/memories_client.py))

**Existing Methods** (no changes needed):
- `upload_video()` - Upload MP4, returns video_no
- `wait_for_processing()` - Poll until status=PARSE
- `chat_with_video()` - Send prompt, get analysis (streaming)
- `delete_video()` - Delete video from cloud storage

**New Usage Pattern** (in CloudAnalysisManager):
- Upload both cam + screen videos with same `unique_id`
- Wait for both to process
- Chat with both videos for comprehensive analysis
- Parse JSON response into structured format
- Delete both videos after local storage

## Workflow Sequence Diagram

```
USER                     UI                      SESSION_MANAGER              CLOUD_ANALYSIS_MANAGER        CLOUD_APIS
 |                        |                              |                              |                         |
 | Stop Session           |                              |                              |                         |
 |----------------------->|                              |                              |                         |
 |                        | stop_session()               |                              |                         |
 |                        |----------------------------->|                              |                         |
 |                        |                              | (cleanup components)         |                         |
 |                        |                              |--                            |                         |
 |                        |                              |  |                           |                         |
 |                        |                              |<-                            |                         |
 |                        |                              |                              |                         |
 |                        |<--(session_id)---------------|                              |                         |
 |                        |                              |                              |                         |
 | [Optional] Upload?     |                              |                              |                         |
 |<-----------------------|                              |                              |                         |
 | Yes                    |                              |                              |                         |
 |----------------------->|                              |                              |                         |
 |                        | upload_session_for_cloud_analysis()                         |                         |
 |                        |----------------------------->|                              |                         |
 |                        |                              | upload_session_for_analysis()|                         |
 |                        |                              |----------------------------->|                         |
 |                        |                              |                              | _upload_to_hume()       |
 |                        |                              |                              |------------------------>|
 |  SHOW PROGRESS DIALOG  |                              |                              | analyze_video()         |
 |  (Uploading to Hume)   |                              |                              |------------------------>|
 |                        |                              |                              |<------(job_id)----------|
 |                        |                              |                              | DB: status=PROCESSING   |
 |                        |                              |                              |------------------------>|
 |                        |                              |                              |                         |
 |                        |                              |                              | _upload_to_memories()   |
 |                        |                              |                              |------------------------>|
 |  (Uploading to Mem.ai) |                              |                              | upload_video(cam)       |
 |                        |                              |                              |------------------------>|
 |                        |                              |                              |<----(cam_video_no)------|
 |                        |                              |                              | upload_video(screen)    |
 |                        |                              |                              |------------------------>|
 |                        |                              |                              |<---(screen_video_no)----|
 |                        |                              |                              | DB: status=PROCESSING   |
 |                        |                              |                              |------------------------>|
 |                        |                              |<--(hume_id, memories_id)-----|                         |
 |                        |<--(job_ids)------------------|                              |                         |
 |  CLOSE DIALOG          |                              |                              |                         |
 |  "Upload complete"     |                              |                              |                         |
 |                        |                              |                              |                         |
 | [User can quit app now - processing happens server-side]                            |                         |
 |                        |                              |                              |                         |
 | Open Reports Tab       |                              |                              |                         |
 |----------------------->|                              |                              |                         |
 |                        | _load_sessions_list()        |                              |                         |
 |                        |--                            |                              |                         |
 |                        |  | get_all_sessions()        |                              |                         |
 |                        |  | get_cloud_jobs_for_session()                             |                         |
 |                        |<-                            |                              |                         |
 |  See session cards     |                              |                              |                         |
 |  with status badges    |                              |                              |                         |
 |                        |                              |                              |                         |
 | Click "Refresh"        |                              |                              |                         |
 |----------------------->|                              |                              |                         |
 |                        | _on_refresh_job(job_id)      |                              |                         |
 |                        |--                            |                              |                         |
 |                        |  | (background thread)       |                              |                         |
 |                        |  | check_job_status()        |                              |                         |
 |                        |  |--------------------------------------------->|                         |
 |                        |  |                           |                              | poll_job(job_id)        |
 |                        |  |                           |                              |------------------------>|
 |                        |  |                           |                              |<-----(status)-----------|
 |                        |  |                           |                              | DB: update status       |
 |                        |  |<-----(status)--------------------------------|                         |
 |                        |  |                           |                              |                         |
 |                        |  | IF COMPLETED:             |                              |                         |
 |                        |  | retrieve_and_store_results()                              |                         |
 |                        |  |--------------------------------------------->|                         |
 |                        |  |                           |                              | fetch_results(job_id)   |
 |                        |  |                           |                              |------------------------>|
 |                        |  |                           |                              |<----(results)-----------|
 |                        |  |                           |                              | _validate_results()     |
 |                        |  |                           |                              | Save to local JSON      |
 |                        |  |                           |                              | DB: mark fetched        |
 |                        |  |<--(results_path)-----------------------------|                         |
 |                        |  |                           |                              |                         |
 |                        |  | delete_cloud_videos()     |                              |                         |
 |                        |  |--------------------------------------------->|                         |
 |                        |  |                           |                              | delete_video()          |
 |                        |  |                           |                              |------------------------>|
 |                        |  |                           |                              |<-----(success)----------|
 |                        |  |                           |                              | DB: mark deleted        |
 |                        |  |<--(success)----------------------------------|                         |
 |                        |  |                           |                              |                         |
 |                        |  | _load_sessions_list()     |                              |                         |
 |                        |  | (update UI)               |                              |                         |
 |                        |<-                            |                              |                         |
 |  See COMPLETED status  |                              |                              |                         |
 |  (green badge)         |                              |                         |
```

## Configuration

**Environment Variables** (`.env`):
```bash
# Cloud features master switch
CLOUD_FEATURES_ENABLED=true

# Hume AI
HUME_AI_ENABLED=true
HUME_API_KEY=your_key_here

# Memories.ai
MEMORIES_AI_ENABLED=true
MEM_AI_API_KEY=your_key_here
```

**Config Methods**:
- `config.is_cloud_features_enabled()` - Master switch
- `config.is_hume_ai_enabled()` - Hume AI toggle
- `config.is_memories_ai_enabled()` - Memories.ai toggle
- `config.get_hume_api_key()` - Decrypted API key
- `config.get_memories_api_key()` - Decrypted API key

## Database Schema v1.4

**cloud_analysis_jobs** table:
```sql
CREATE TABLE cloud_analysis_jobs (
    job_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    provider TEXT NOT NULL,  -- 'memories_ai' | 'hume_ai'
    provider_job_id TEXT,

    status TEXT NOT NULL,  -- 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
    upload_started_at TEXT,
    upload_completed_at TEXT,
    processing_started_at TEXT,
    processing_completed_at TEXT,

    results_fetched INTEGER DEFAULT 0,
    results_stored_at TEXT,
    results_file_path TEXT,

    video_type TEXT NOT NULL,  -- 'webcam' | 'screen' | 'both'
    video_path TEXT NOT NULL,

    can_delete_remote INTEGER DEFAULT 0,  -- Safety flag
    remote_deleted_at TEXT,

    retry_count INTEGER DEFAULT 0,
    last_error TEXT,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
```

## Testing Checklist

- [ ] Stop session with cloud features disabled (should skip upload)
- [ ] Stop session with Hume AI only (should upload cam.mp4)
- [ ] Stop session with Memories.ai only (should upload both videos)
- [ ] Stop session with both enabled (should create 2 jobs)
- [ ] Upload progress dialog shows correct status
- [ ] User can quit app after upload completes
- [ ] Reports tab loads all sessions correctly
- [ ] Session cards show correct status badges
- [ ] Refresh button polls and updates status
- [ ] When processing complete, refresh retrieves results
- [ ] Results stored locally in `data/cloud_results/{session_id}/`
- [ ] Cloud videos deleted after successful retrieval
- [ ] Memories.ai JSON parsing handles code blocks
- [ ] Validation catches malformed responses
- [ ] Error handling for upload failures
- [ ] Error handling for processing failures
- [ ] Retry logic for transient errors
- [ ] Database integrity (foreign keys, indexes)

## Known Limitations

1. **No upload resume**: If upload fails, user must retry manually
2. **No progress tracking during upload**: Simple "Uploading..." dialog
3. **Memories.ai parsing**: Depends on LLM returning valid JSON
4. **Hume AI deletion**: No delete API (relies on automatic expiration)
5. **Refresh All**: Not yet implemented (TODO)

## Future Enhancements

1. **Upload progress bar**: Track bytes uploaded
2. **Auto-refresh**: Periodically poll PROCESSING jobs in background
3. **Notifications**: Desktop notifications when analysis complete
4. **Result preview**: Show analysis summary in Reports tab
5. **Bulk operations**: Upload multiple sessions, delete multiple jobs
6. **Cost tracking**: Display API usage and estimated costs
7. **Export results**: Download structured data as CSV/JSON
