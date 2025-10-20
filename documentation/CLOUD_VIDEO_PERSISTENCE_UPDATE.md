# Cloud Video Persistence Update

## Overview
This update changes the behavior of cloud video management to keep videos on Memories.ai after upload, enabling video reuse during regeneration and reducing upload times and costs.

## Changes Made

### 1. **Added Video Status Check Method** (`memories_client.py`)
- **New Method**: `get_video_status(video_no, unique_id)`
- **Purpose**: Check if a video exists in the cloud and get its processing status
- **Returns**: Video info dict with status (PARSE, UNPARSE, PROCESSING, FAIL) or None if not found

### 2. **Removed Automatic Video Deletion** (`main_window.py`)
- **Location**: Line 5641-5643 in `_on_refresh_job()`
- **Change**: Commented out automatic deletion after retrieving results
- **Reason**: Videos are now kept on cloud for reuse
- **Note**: Users can still manually delete videos via "Manage Cloud Storage"

### 3. **Smart Upload Logic with Video Reuse** (`cloud_analysis_manager.py`)
- **Modified Method**: `_upload_to_memories()`
- **New Behavior**:
  1. **Check for existing videos**: Before uploading, checks if videos for this session already exist in cloud
  2. **Reuse if processed**: If videos exist and status is PARSE (processed), reuses them without re-uploading
  3. **Wait if processing**: If videos exist but still processing (UNPARSE, PROCESSING), returns existing job
  4. **Upload if missing**: If videos don't exist (deleted), uploads new videos

### Detailed Flow

#### Scenario 1: Videos Already Processed
```
User clicks "Regenerate Memories.ai"
  ↓
_upload_to_memories() checks for existing videos
  ↓
Videos found with status = PARSE (processed)
  ↓
Returns existing job_id (no upload needed!)
  ↓
retrieve_and_store_results() called
  ↓
chat_with_video() queries chat API again with prompt
  ↓
New analysis generated and stored
```

**Result**: Fast regeneration (~30 seconds) without re-uploading videos

#### Scenario 2: Videos Still Processing
```
User clicks "Regenerate Memories.ai"
  ↓
_upload_to_memories() checks for existing videos
  ↓
Videos found with status = UNPARSE or PROCESSING
  ↓
Returns existing job_id
  ↓
Job status remains PROCESSING
  ↓
UI shows "Processing" status badge
  ↓
User can check back later when processing completes
```

**Result**: User informed that videos are still processing

#### Scenario 3: Videos Not Found (Deleted)
```
User clicks "Regenerate Memories.ai"
  ↓
_upload_to_memories() checks for existing videos
  ↓
Videos not found in cloud
  ↓
Creates new job and uploads videos
  ↓
Normal upload flow
```

**Result**: Videos uploaded as usual

## Benefits

### 1. **Faster Regeneration**
- No need to re-upload videos (saves ~1-2 minutes for 2-hour session)
- Only queries chat API again (~30 seconds)

### 2. **Cost Savings**
- Avoids redundant uploads
- Reduces bandwidth usage
- No additional storage costs (Memories.ai already stores videos)

### 3. **Better User Experience**
- Regeneration feels instant for already-processed videos
- Clear status messaging for processing videos
- Manual control over deletion via "Manage Cloud Storage"

### 4. **More Reliable**
- Handles network interruptions better
- Can retry regeneration without re-uploading
- Videos persist across app restarts

## Video Status Values

The Memories.ai API returns these status values:

- `PARSE` - Video fully processed and ready for chat queries
- `UNPARSE` - Video uploaded but not yet processed
- `PROCESSING` - Video currently being processed
- `FAIL` - Video processing failed

## Migration Notes

### Existing Sessions
- Sessions with already-deleted videos will upload new videos as usual
- Sessions with videos still in cloud will benefit immediately from reuse

### Manual Deletion
- Users can still delete videos via "Manage Cloud Storage" dialog
- Deletion is now a manual action, not automatic
- Deleting videos will cause next regeneration to re-upload

## Testing Recommendations

### Test Case 1: Regenerate with Existing Processed Videos
1. Upload session for cloud analysis
2. Wait for processing to complete (~5 minutes)
3. Click "Regenerate Memories.ai"
4. **Expected**: Fast regeneration without upload progress
5. **Verify**: New analysis results generated

### Test Case 2: Regenerate with Processing Videos
1. Upload session for cloud analysis
2. Immediately click "Regenerate Memories.ai" (before processing completes)
3. **Expected**: Message about videos still processing
4. **Verify**: No new upload, job status shows PROCESSING

### Test Case 3: Regenerate After Manual Deletion
1. Upload session for cloud analysis
2. Wait for processing to complete
3. Manually delete videos via "Manage Cloud Storage"
4. Click "Regenerate Memories.ai"
5. **Expected**: Videos re-uploaded
6. **Verify**: Upload progress shown, new videos in cloud

### Test Case 4: Multiple Regenerations
1. Complete cloud analysis for a session
2. Click "Regenerate Memories.ai" 3 times
3. **Expected**: All three regenerations use same cloud videos
4. **Verify**: 3 different analysis results, but same video_nos

## Files Modified

1. `src/focus_guardian/integrations/memories_client.py`
   - Added `get_video_status()` method

2. `src/focus_guardian/session/cloud_analysis_manager.py`
   - Updated `_upload_to_memories()` with video reuse logic

3. `src/focus_guardian/ui/main_window.py`
   - Commented out automatic video deletion in `_on_refresh_job()`

## API Usage

### Checking Video Status
```python
# Check if video exists and get status
video_info = memories_client.get_video_status(
    video_no="VI123456789",
    unique_id="focus_session_abc123"
)

if video_info:
    status = video_info.get('status')
    if status == 'PARSE':
        # Video is processed and ready
        pass
    elif status in ['UNPARSE', 'PROCESSING']:
        # Video still processing
        pass
else:
    # Video not found (deleted or never uploaded)
    pass
```

## Future Enhancements

### Potential Improvements
1. **Cache status checks** - Avoid repeated API calls for same video
2. **Progress indicators** - Show different UI for reuse vs upload
3. **Expiration tracking** - Warn users before videos expire (if applicable)
4. **Batch status checks** - Check multiple videos in one API call
5. **Smart cleanup** - Auto-delete videos older than X days

### Configuration Options
Consider adding settings for:
- Auto-delete after X days
- Max videos to keep per session
- Notification before deletion

