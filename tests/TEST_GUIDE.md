# Focus Guardian - Complete Test Guide

## 🎯 What to Expect - Step by Step

### **Phase 1: Launch (You Should See Now)**

**Window Appears:**
```
╔════════════════════════════════════════════╗
║  Focus Guardian - ADHD Distraction Analysis ║
╠════════════════════════════════════════════╣
║  [Dashboard] [Reports] [Settings]          ║
║                                             ║
║      Focus Session Dashboard                ║
║  ┌──────────────────────────────────────┐  ║
║  │    No active session                 │  ║
║  │       00:00:00                       │  ║
║  │      Task: None                      │  ║
║  └──────────────────────────────────────┘  ║
║                                             ║
║  [Start Focus Session] [Pause] [Stop]      ║
║     (green, enabled)   (gray)  (gray)      ║
║                                             ║
║  Snapshots: 0 | Distractions: 0 | Focus: 0%║
╚════════════════════════════════════════════╝
```

**Terminal Logs:**
```
23:XX:XX | INFO | FOCUS GUARDIAN - Starting Application
23:XX:XX | INFO | Configuration loaded
23:XX:XX | INFO | Database initialized
23:XX:XX | INFO | Hume AI client initialized      ← Using your API key!
23:XX:XX | INFO | Memories.ai client initialized  ← Using your API key!
23:XX:XX | INFO | Main window created
```

---

### **Phase 2: Start a Session (Click Green Button)**

**What Happens Immediately:**
1. **UI Changes:**
   - Status: "Session Active"
   - Task: "Focus Work"
   - Timer starts: 00:00:01, 00:00:02, 00:00:03...
   - Start button → gray (disabled)
   - Pause button → orange (enabled)
   - Stop button → red (enabled)

2. **Terminal Logs (All in 1 second):**
   ```
   23:XX:XX | INFO | Starting new session: Focus Work
   23:XX:XX | INFO | Session record created: <uuid>
   23:XX:XX | INFO | Initializing session components...
   23:XX:XX | INFO | OpenAI Vision client initialized
   23:XX:XX | INFO | Webcam capture initialized: 1280x720 at index 0
   23:XX:XX | INFO | Screen capture initialized
   23:XX:XX | INFO | Snapshot scheduler initialized: interval=5s
   23:XX:XX | INFO | Snapshot uploader initialized with 3 workers
   23:XX:XX | INFO | State machine initialized (K=3)
   23:XX:XX | INFO | Fusion engine initialized
   23:XX:XX | INFO | Distraction detector initialized
   23:XX:XX | INFO | All components initialized
   23:XX:XX | INFO | Webcam recorder started
   23:XX:XX | INFO | Screen recorder started
   23:XX:XX | INFO | Snapshot uploader started
   23:XX:XX | INFO | Fusion engine started
   23:XX:XX | INFO | Distraction detector started
   23:XX:XX | INFO | Snapshot scheduler started
   23:XX:XX | INFO | Session started successfully
   ```

3. **What's Running in Background:**
   - 📹 Webcam recording to `cam.mp4` (continuous)
   - 🖥️ Screen recording to `screen.mp4` (continuous)
   - ⏱️ Snapshot scheduler (will trigger in 5 seconds)
   - 👷 3 upload workers (waiting for snapshots)
   - 🤖 Fusion engine (waiting for results)
   - 🔔 Distraction detector (waiting for patterns)

---

### **Phase 3: First Snapshot (After 5 Seconds)**

**At 00:00:05 on the timer:**

**Terminal Logs:**
```
23:XX:05 | INFO | Captured snapshot pair #1 (cam: 50,021 bytes, screen: 157,280)
23:XX:05 | DEBUG | Worker 0 uploading cam snapshot...
23:XX:05 | DEBUG | Worker 1 uploading screen snapshot...
23:XX:08 | DEBUG | Vision API (cam): {"Focused": 0.9} (latency: 3200ms)
23:XX:08 | DEBUG | Vision API (screen): {"Code": 0.9, "Terminal": 0.8}
23:XX:08 | DEBUG | Worker 0 uploaded cam snapshot (latency: 3200ms)
23:XX:08 | DEBUG | Worker 1 uploaded screen snapshot (latency: 3100ms)
```

**GUI Updates:**
- Snapshots: 0 → **1**
- (Nothing else changes yet - need 3 snapshots for K=3)

**Files Created:**
```
data/sessions/<session_id>/
├── cam.mp4 (recording in progress)
├── screen.mp4 (recording in progress)
├── snapshots/
│   ├── cam_20251011_233005.jpg  ← New!
│   └── screen_20251011_233005.jpg  ← New!
└── vision/
    ├── cam_20251011_233005.json  ← OpenAI response!
    └── screen_20251011_233005.json  ← OpenAI response!
```

---

### **Phase 4: Second Snapshot (After 10 Seconds)**

**At 00:00:10:**

**Terminal:**
```
23:XX:10 | INFO | Captured snapshot pair #2
23:XX:13 | DEBUG | Vision API results received
```

**GUI:**
- Snapshots: 1 → **2**
- (Still need one more for K=3 voting)

---

### **Phase 5: Third Snapshot - Pattern Detection! (After 15 Seconds)**

**At 00:00:15:**

**Terminal:**
```
23:XX:15 | INFO | Captured snapshot pair #3
23:XX:18 | DEBUG | Vision API results received
23:XX:18 | INFO | State machine has 3 snapshots, span: 10.1s
```

**Now the magic happens - K=3 Voting:**

**If you're FOCUSED (looking at screen, coding):**
```
23:XX:18 | INFO | State: FOCUSED (confidence: 0.85)
23:XX:18 | DEBUG | No transition (already focused)
```
- No alert
- GUI shows: Distractions: 0, Focus: 100%

**If you're DISTRACTED (looking away, watching video, on social media):**
```
23:XX:18 | INFO | State transition: focused → distracted (confidence: 0.52)
23:XX:18 | INFO | Started tracking distraction: distracted
23:XX:18 | INFO | 🔔 IMMEDIATE ALERT: LookAway detected!
23:XX:18 | INFO | Alert sent to UI queue
23:XX:18 | INFO | 🔔 DISTRACTION ALERT RECEIVED
```

**Then a DIALOG POPS UP:**
```
╔═══════════════════════════════════════╗
║ 🔔 Focus Alert - Distraction Detected ║
╠═══════════════════════════════════════╣
║ 🔔 LookAway detected!                 ║
║                                        ║
║ Type: LookAway                        ║
║ Confidence: 52%                       ║
║                                        ║
║ Detected patterns:                    ║
║   • HeadAway: 2/3 snapshots           ║
║   • EyesOffScreen: 2/3 snapshots      ║
║                                        ║
║ Refocus on your task: Focus Work      ║
║                                        ║
║              [ OK ]                    ║
╚═══════════════════════════════════════╝
```

**GUI Updates:**
- Distractions: 0 → **1**
- Focus: 100% → **~70%**

---

### **Phase 6: Continuing the Session (Every 5 Seconds)**

**Pattern continues:**
- Every 5s: New snapshot captured
- Every 5s: Sent to OpenAI Vision API
- Rolling K=3 buffer updates
- If distraction pattern continues: More alerts
- If you refocus: State returns to FOCUSED

**Snapshots keep counting up:**
- 00:00:20 → Snapshots: **4**
- 00:00:25 → Snapshots: **5**
- 00:00:30 → Snapshots: **6**
- etc.

---

### **Phase 7: Stop the Session**

**Click Red "Stop Session" Button:**

**Confirmation Dialog:**
```
╔═══════════════════════════════════╗
║         Stop Session              ║
╠═══════════════════════════════════╣
║ Are you sure you want to stop     ║
║ the current session?              ║
║                                   ║
║        [ Yes ]    [ No ]          ║
╚═══════════════════════════════════╝
```

**Click "Yes":**

**Terminal Shows Cleanup:**
```
23:XX:XX | INFO | Stopping session: <uuid>
23:XX:XX | INFO | Snapshot scheduler stopped
23:XX:XX | INFO | Waiting for uploads to complete...
23:XX:XX | INFO | Snapshot uploader stopped
23:XX:XX | INFO | Fusion engine stopped
23:XX:XX | INFO | Distraction detector stopped
23:XX:XX | INFO | Webcam recorder stopped
23:XX:XX | INFO | Screen recorder stopped
23:XX:XX | INFO | Session ended: 8 snapshots, 2 distractions
23:XX:XX | INFO | Generating session report...
23:XX:XX | INFO | Session report generated
```

**Then a SUMMARY DIALOG appears:**
```
╔═══════════════════════════════════════╗
║        Session Complete               ║
╠═══════════════════════════════════════╗
║        Session Summary                ║
║                                        ║
║ Duration: 2.5 minutes                 ║
║ Focus Ratio: 67%                      ║
║ Distractions Detected: 2              ║
║ Average Focus Bout: 1.2 minutes       ║
║ Top Distractors: LookAway             ║
║                                        ║
║ Recommendations:                      ║
║ • Your focus ratio is 67%. Try        ║
║   scheduling regular 5-minute breaks  ║
║   every 25 minutes (Pomodoro).        ║
║ • You had 2 distraction alerts.       ║
║   Consider breaking your task into    ║
║   smaller chunks.                     ║
║                                        ║
║              [ OK ]                    ║
╚═══════════════════════════════════════╝
```

**Files Created:**
```
data/
├── focus_guardian.db (updated with session data)
├── sessions/<session_id>/
│   ├── cam.mp4 (complete video)
│   ├── screen.mp4 (complete video)
│   ├── snapshots/ (all JPEG files)
│   └── vision/ (all JSON results)
└── reports/
    └── <session_id>_report.json  ← NEW! Full report
```

---

## 🧪 **Your Test Scenario:**

### **Test 1: Normal Focus Session (No Distractions)**
1. **Start session**
2. **Stay focused** - keep looking at screen, working normally
3. **Run for 30-60 seconds**
4. **Stop session**
5. **Expected**: 
   - 0 distraction alerts
   - Focus ratio: 100%
   - Summary shows great focus

### **Test 2: Distraction Detection**
1. **Start session**
2. **Wait 5 seconds** (first snapshot)
3. **Look away from screen** or **open YouTube**
4. **Wait 15 seconds** (3 snapshots captured while distracted)
5. **Expected at ~15-20 seconds**:
   - 🔔 **Alert dialog pops up!**
   - Shows what distraction was detected
   - GUI shows Distractions: 1
6. **Click OK on alert**
7. **Refocus on screen**
8. **Wait another 15 seconds**
9. **Should return to FOCUSED state**
10. **Stop session**
11. **See summary** with focus ratio ~50-70%

### **Test 3: Multiple Distractions**
1. **Start session**
2. **Alternate**: 30s focused, 30s distracted, 30s focused, 30s distracted
3. **Stop after 2 minutes**
4. **Expected**:
   - Multiple alerts
   - Focus ratio ~50%
   - Recommendations about frequent distractions

---

## 📊 **What to Watch in Terminal:**

Monitor `/tmp/focus_guardian_debug.log` for:
- ✅ All components start successfully
- ✅ Snapshots captured every 5 seconds
- ✅ OpenAI Vision API responses (3-4 second latency)
- ✅ State transitions when K=3 pattern detected
- ✅ Alerts sent to UI queue
- ✅ Report generation at end

---

## 🔍 **How to Monitor Progress:**

Run this in a separate terminal to watch logs live:
```bash
tail -f /tmp/focus_guardian_debug.log
```

Or check session data:
```bash
ls -la data/sessions/
```

---

## 🎬 **Ready to Test!**

The GUI should be visible now. Try **Test 2** (Distraction Detection) to see the full pipeline in action:

1. Start session
2. Look away or browse social media
3. Wait ~15-20 seconds
4. **ALERT SHOULD POP UP!** 🔔
5. Refocus
6. Stop session
7. See summary report

Let me know what happens! Does the alert appear when you're distracted?
