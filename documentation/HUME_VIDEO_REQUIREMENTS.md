# Hume AI Video Compatibility Requirements

## Overview

Hume AI's facial expression analysis requires videos with **detectable human faces** to return emotion data. Videos without faces will complete processing successfully but return 0 frames.

## Investigation Summary

During testing, we discovered that Hume AI returns different results based on video content:

**Video 1 (ce08da15-986c-4c63-8788-bd851a94b130):**
- Duration: 522 seconds (8.7 minutes)
- Resolution: 1920x1080
- FPS: 15
- Size: 3.0 MB
- Result: **0 frames** (camera icon visible, no actual face)

**Video 2 (bb581b1b-bc22-43e8-abc8-606c8d87e59d):**
- Duration: 44 seconds
- Resolution: 1280x720
- FPS: 15
- Size: 6.7 MB
- Result: **119 frames** (clear human face visible)

## Root Cause

The first video shows a **camera app placeholder icon** (paused camera state) rather than an actual human face. Hume AI's face detection algorithm correctly identified no faces in this video.

The parsing code in `hume_client.py` is working correctly - the issue is video content, not code.

## Requirements for Valid Analysis

For Hume AI to detect emotions, videos MUST contain:

1. **Visible Human Faces**
   - At least one face clearly visible in frames
   - Face must be facing the camera (frontal or near-frontal)
   - Adequate lighting to detect facial features

2. **Video Quality**
   - Resolution: 720p or higher recommended
   - FPS: 10-30 fps
   - Codec: H.264, VP8, VP9, or similar
   - Format: MP4, AVI, MOV, WebM

3. **Face Characteristics**
   - Face size: At least 100x100 pixels in frame
   - Not occluded by objects, hands, or masks
   - Facial features (eyes, nose, mouth) clearly visible

## What Will Return 0 Frames

Videos with these characteristics will process successfully but return no emotion data:

- Camera paused/disabled screens
- App icons or placeholder graphics
- User absent from webcam view
- User facing away from camera
- Heavy occlusion (masks, hands covering face)
- Very dark/underexposed footage
- Very small face size (<100px)

## Validation Recommendations

### Before Upload

Check video content before uploading to Hume AI:
```python
# Extract sample frames and check for faces
ffmpeg -i cam.mp4 -vframes 5 -vf fps=1 frame_%d.jpg

# Manually inspect frames for visible faces
```

### After Processing

Always check frame_count in results:
```python
results = hume_client.fetch_results(job_id)

if results['frame_count'] == 0:
    logger.warning(f"No faces detected in video. Check webcam was active during session.")
    # Graceful degradation - use local CNN fallback or skip emotion analysis
```

### In Production

The Focus Guardian application should:

1. **Preview Check**: Show webcam preview before starting session to verify face is visible
2. **Frame Sampling**: Extract sample frames during recording and validate face detection
3. **Graceful Degradation**: If Hume returns 0 frames, log warning but don't fail the session
4. **User Feedback**: Notify user if webcam appears inactive during session

## Cost Implications

Empty videos (0 frames) still incur API costs for:
- Upload bandwidth
- Processing time (5-10 minutes)
- Storage (until deletion)

Cost: ~$0.50 per video regardless of frame count.

**Recommendation**: Validate face presence in first 10 seconds of recording before committing to full session upload.

## Testing Approach

When testing Hume AI integration:

1. Use test videos with **confirmed human faces** (like session bb581b1b-bc22-43e8-abc8-606c8d87e59d)
2. Don't use videos showing camera icons, paused states, or empty desks
3. Extract a sample frame first to visually verify face presence
4. Test graceful degradation with intentionally face-free videos

## Summary

- **Hume AI parsing code is correct** - no bugs found
- **Video content determines frame count** - faces required for emotion detection
- **0 frames is valid API behavior** - not an error condition
- **Graceful degradation implemented** - app continues even with 0 frames
- **Prevention is best** - validate webcam shows face before starting session
