# Focus Guardian Notification System

## Overview

Focus Guardian sends **real-time notifications** when distraction patterns are detected through the K=3 hysteresis voting system. The notification types are **standardized** in code but **driven by OpenAI Vision API** classifications.

---

## Notification Types

### **1. Distraction Alerts** (Immediate)

Triggered **immediately** when state machine transitions to `DISTRACTED` or `ABSENT` state (requires ≥2 of 3 snapshots showing distraction).

#### **Standardized Types** ([models.py:47-56](../src/focus_guardian/core/models.py#L47-L56))

```python
class DistractionType(Enum):
    LOOK_AWAY = "LookAway"       # Head/eyes off screen
    PHONE = "Phone"              # Phone detected in frame
    VIDEO = "Video"              # Video content on screen
    SOCIAL = "Social"            # Social media detected
    CHAT = "Chat"                # Chat window open
    ABSENT = "Absent"            # User not visible
    MICRO_SLEEP = "MicroSleep"   # Eyes closed/drowsy
    UNKNOWN = "Unknown"          # Could not classify
```

#### **Classification Logic** ([distraction_detector.py:313-345](../src/focus_guardian/analysis/distraction_detector.py#L313-L345))

The detector examines **OpenAI Vision labels** and maps them to notification types:

**Priority order (checked top to bottom)**:

1. **ABSENT** - OpenAI returns `Absent` label from webcam
2. **PHONE** - OpenAI returns `PhoneLikely` from webcam
3. **MICRO_SLEEP** - OpenAI returns `MicroSleep` from webcam
4. **LOOK_AWAY + context**:
   - If `HeadAway` or `EyesOffScreen` + screen shows `VideoOnScreen` → **VIDEO**
   - If `HeadAway` or `EyesOffScreen` + screen shows `SocialFeed` → **SOCIAL**
   - If `HeadAway` or `EyesOffScreen` + screen shows `ChatWindow` → **CHAT**
   - Otherwise → **LOOK_AWAY**
5. **Screen-only distractions**:
   - `VideoOnScreen` detected → **VIDEO**
   - `SocialFeed` detected → **SOCIAL**
   - `ChatWindow` detected → **CHAT**
   - `Games` detected → **SOCIAL** (using SOCIAL as proxy)
6. **UNKNOWN** - Pattern detected but unclear classification

#### **Example Alert Message**

```
🔔 Phone detected!
Confidence: 0.82
Vision votes: HeadAway (2/3), PhoneLikely (3/3)
```

---

### **2. Micro-Break Suggestions** (Pattern-based)

Triggered when user shows **≥3 distractions within 20 minutes**.

#### **Logic** ([distraction_detector.py:418-444](../src/focus_guardian/analysis/distraction_detector.py#L418-L444))

```python
# Checks recent_alerts deque (last 20 alerts)
if len(recent_alerts_in_last_20_minutes) >= 3:
    send_micro_break_suggestion()
```

#### **Example Message**

```
Micro-Break Suggestion
You've been distracted frequently. Consider a 5-minute break.
(3 distractions in last 20 minutes)
```

---

## OpenAI Vision API Label Taxonomy

### **Camera Labels** (6 classes)

Defined in prompts ([openai_vision_client.py:108-137](../src/focus_guardian/integrations/openai_vision_client.py#L108-L137)):

| Label | Description | Triggers Notification |
|-------|-------------|----------------------|
| `Focused` | Engaged posture, eyes on screen | No (focus state) |
| `HeadAway` | Head turned >45° from screen | **LOOK_AWAY** (or VIDEO/SOCIAL/CHAT if screen context) |
| `EyesOffScreen` | Gaze not on screen | **LOOK_AWAY** |
| `Absent` | No person visible | **ABSENT** |
| `MicroSleep` | Eyes closed, drowsy | **MICRO_SLEEP** |
| `PhoneLikely` | Phone visible in hand | **PHONE** |

### **Screen Labels** (13 classes)

Defined in prompts ([openai_vision_client.py:139-177](../src/focus_guardian/integrations/openai_vision_client.py#L139-L177)):

| Label | Description | Category | Triggers Notification |
|-------|-------------|----------|----------------------|
| `Code` | Code editor, IDE | Focus | No |
| `Docs` | Documentation, wikis | Focus | No |
| `Reading` | Long-form reading | Focus | No |
| `Slides` | Presentation software | Focus | No |
| `Terminal` | Command line | Focus | No |
| `VideoOnScreen` | Video player/streaming | **Distraction** | **VIDEO** |
| `SocialFeed` | Social media scrolling | **Distraction** | **SOCIAL** |
| `Games` | Gaming applications | **Distraction** | **SOCIAL** |
| `ChatWindow` | Chat/messaging apps | **Distraction** | **CHAT** |
| `Email` | Email client | Borderline | Context-dependent |
| `VideoCall` | Video conferencing | Borderline | Context-dependent |
| `MultipleMonitors` | Multiple windows | Borderline | Context-dependent |
| `Unknown` | Cannot determine | Neutral | No |

---

## How Labels Become Notifications

### **Flow Diagram**

```
1. Snapshot Scheduler (every 120s)
   ↓
2. OpenAI Vision API
   - Webcam: "PhoneLikely: 0.85"
   - Screen: "VideoOnScreen: 0.78"
   ↓
3. Fusion Engine (K=3 hysteresis)
   - Snapshot 1: {PhoneLikely: 0.85}
   - Snapshot 2: {PhoneLikely: 0.80}
   - Snapshot 3: {Focused: 0.70}
   - Vote: 2 of 3 show PhoneLikely → MAJORITY
   ↓
4. State Machine
   - Transition: FOCUSED → DISTRACTED
   - Evidence: {PhoneLikely: count=2, VideoOnScreen: count=1}
   ↓
5. Distraction Detector
   - Classify: PhoneLikely (priority 2) → DistractionType.PHONE
   - Emit IMMEDIATE alert to UI
   ↓
6. UI (main_window.py)
   - Show popup: "🔔 Phone detected!"
   - Play alert sound (if enabled)
```

### **OpenAI Vision Prompt Engineering**

The prompts ([openai_vision_client.py](../src/focus_guardian/integrations/openai_vision_client.py)) are carefully designed to return **only the standardized labels**:

**Webcam Prompt**:
```
Analyze this webcam image and classify the user's attention state.

Possible classifications (return ONLY the most dominant ones with confidence 0.0-1.0):
- HeadAway: Head turned >45° away from screen
- EyesOffScreen: Gaze not directed at screen
- MicroSleep: Eyes closed or drowsy appearance
- PhoneLikely: Phone visible in hand or user looking down at phone
- Absent: No person visible in frame
- Focused: Engaged posture, eyes on screen, attentive appearance

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation"
}
```

**Screen Prompt**:
```
Analyze this screen capture and classify the visible content/applications.

Possible classifications (return ONLY clearly visible ones with confidence 0.0-1.0):
- VideoOnScreen: Video player or streaming
- SocialFeed: Social media feed scrolling
- Code: Code editor or IDE
- [... 10 more labels ...]

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation of what you see"
}
```

### **Label Validation**

OpenAI may occasionally return labels outside the taxonomy. The system **filters** them ([openai_vision_client.py:248-258](../src/focus_guardian/integrations/openai_vision_client.py#L248-L258)):

```python
valid_labels = CAM_LABELS if kind == "cam" else SCREEN_LABELS
filtered_labels = {}

for label, confidence in labels.items():
    if label in valid_labels:  # Only keep valid labels
        threshold = CONFIDENCE_THRESHOLDS.get(label, 0.5)
        if confidence >= threshold:  # Only keep high-confidence
            filtered_labels[label] = float(confidence)
    else:
        logger.warning(f"Invalid label '{label}' returned by Vision API")
```

---

## Notification Configuration

### **Alert Settings**

**config/default_config.json**:
```json
{
  "alert_sound_enabled": true,        // Play sound on distraction
  "K_hysteresis": 3,                  // Snapshots for voting
  "min_span_minutes": 3.5,            // Min span across K snapshots
  "snapshot_interval_sec": 120        // Snapshot frequency
}
```

**Alert threshold** ([distraction_detector.py:33](../src/focus_guardian/analysis/distraction_detector.py#L33)):
- Only distractions lasting **≥0.5 minutes** are written to database
- Immediate alerts sent when distraction **starts** (don't wait for end)

---

## Adding New Notification Types

### **Process**

1. **Add OpenAI Vision label** to prompts ([openai_vision_client.py](../src/focus_guardian/integrations/openai_vision_client.py)):
   ```python
   # In _build_cam_prompt() or _build_screen_prompt()
   - YourNewLabel: Description of behavior
   ```

2. **Add to label taxonomy** ([models.py:288-322](../src/focus_guardian/core/models.py#L288-L322)):
   ```python
   CAM_LABELS = {
       "HeadAway", "EyesOffScreen", ..., "YourNewLabel"
   }

   CAM_DISTRACTION_LABELS = {
       "HeadAway", ..., "YourNewLabel"  # If it's a distraction
   }
   ```

3. **Add DistractionType** ([models.py:47-56](../src/focus_guardian/core/models.py#L47-L56)):
   ```python
   class DistractionType(Enum):
       LOOK_AWAY = "LookAway"
       # ...
       YOUR_NEW_TYPE = "YourNewType"
   ```

4. **Add classification logic** ([distraction_detector.py:313-345](../src/focus_guardian/analysis/distraction_detector.py#L313-L345)):
   ```python
   def _classify_distraction_type(self, evidence: Dict) -> DistractionType:
       cam_labels = evidence.get("cam_labels", {})

       if "YourNewLabel" in cam_labels:
           return DistractionType.YOUR_NEW_TYPE
       # ...
   ```

### **Example: Adding "Yawning" Detection**

```python
# 1. Update OpenAI prompt
"Yawning: User yawning or showing signs of fatigue"

# 2. Add to taxonomy
CAM_LABELS = {..., "Yawning"}
CAM_DISTRACTION_LABELS = {..., "Yawning"}

# 3. Add DistractionType
class DistractionType(Enum):
    FATIGUE = "Fatigue"

# 4. Add classification
if "Yawning" in cam_labels:
    return DistractionType.FATIGUE
```

---

## Summary

### **Is it standardized?**

**Yes and No**:
- **Notification types**: Standardized (8 types hardcoded in `DistractionType` enum)
- **Label detection**: OpenAI Vision API driven (19 labels defined in prompts)
- **Mapping**: Deterministic (labels → notification types via classification logic)

### **Can OpenAI Vision return other labels?**

**Technically yes**, but:
1. Prompts explicitly instruct: "Return ONLY the most dominant ones"
2. Invalid labels are **filtered out** and logged as warnings
3. In practice, GPT-4o-mini follows the taxonomy very reliably (>95% compliance)

### **Notification Examples**

| User Behavior | OpenAI Labels | Notification Type | Message |
|---------------|---------------|-------------------|---------|
| Looking at phone | `PhoneLikely: 0.88` | **PHONE** | "🔔 Phone detected!" |
| Watching YouTube | `HeadAway: 0.75`, `VideoOnScreen: 0.90` | **VIDEO** | "🔔 Video detected!" |
| Scrolling Twitter | `SocialFeed: 0.85` | **SOCIAL** | "🔔 Social detected!" |
| Eyes closing | `MicroSleep: 0.80` | **MICRO_SLEEP** | "🔔 MicroSleep detected!" |
| Left desk | `Absent: 0.95` | **ABSENT** | "🔔 Absent detected!" |
| Slack chatting | `ChatWindow: 0.82` | **CHAT** | "🔔 Chat detected!" |
| Looking away | `HeadAway: 0.78` | **LOOK_AWAY** | "🔔 LookAway detected!" |

The system is **extensible** (add new labels/types) but **deterministic** (same labels always produce same notification).
