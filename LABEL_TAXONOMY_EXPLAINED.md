# Label Taxonomy - How Detection Labels Work in Focus Guardian

**Question**: Are the labels like "HeadAway", "VideoOnScreen" etc. hardcoded into the voting engine?

**Answer**: **YES - They are hardcoded**, but with some flexibility. Here's the complete picture:

---

## 🏗️ Architecture Overview

```
┌─────────────────┐
│  OpenAI Vision  │  Prompts describe labels
│   API Prompt    │  (Can be customized!)
└────────┬────────┘
         │ Returns: {"HeadAway": 0.8, "Focused": 0.3}
         ↓
┌─────────────────┐
│  Label Filter   │  Validates against HARDCODED taxonomy
│  (Client)       │  Rejects invalid labels
└────────┬────────┘
         │ Only valid labels pass through
         ↓
┌─────────────────┐
│  State Machine  │  Uses HARDCODED label categories
│  (Voting Engine)│  to determine state
└────────┬────────┘
         │ FOCUSED / DISTRACTED / ABSENT
         ↓
┌─────────────────┐
│  Distraction    │  Emits alerts
│  Detector       │
└─────────────────┘
```

---

## 📝 WHERE LABELS ARE DEFINED

### 1. Canonical Taxonomy (HARDCODED)

**File**: `src/focus_guardian/core/models.py` (lines 347-384)

```python
# Webcam Labels - HARDCODED SET
CAM_LABELS = {
    "HeadAway",        # Head turned >45° from screen
    "EyesOffScreen",   # Gaze not directed at screen
    "Absent",          # No person visible in frame
    "MicroSleep",      # Eyes closed, drowsy appearance
    "PhoneLikely",     # Phone visible in hand or being viewed
    "Focused"          # Engaged posture, eyes on screen (positive class)
}

# Screen Labels - HARDCODED SET
SCREEN_LABELS = {
    "VideoOnScreen",      # Video player or streaming content
    "WorkRelatedVideo",   # Tutorial/educational video with work context
    "SocialFeed",         # Social media feed scrolling
    "Code",               # Code editor or IDE
    "Docs",               # Documentation, technical reading
    "Email", "VideoCall", "Reading", "Slides", "Terminal",
    "ChatWindow", "WorkChat", "Browser", "Games",
    "MultipleMonitors", "Unknown"
}

# Category Mappings - HARDCODED CLASSIFICATION
CAM_DISTRACTION_LABELS = {"HeadAway", "EyesOffScreen", "MicroSleep", "PhoneLikely"}
CAM_FOCUS_LABELS = {"Focused"}
CAM_ABSENCE_LABELS = {"Absent"}

SCREEN_DISTRACTION_LABELS = {"VideoOnScreen", "SocialFeed", "Games", "ChatWindow"}
SCREEN_FOCUS_LABELS = {"Code", "Docs", "Reading", "Slides", "Terminal", "WorkRelatedVideo", "WorkChat"}
SCREEN_BORDERLINE_LABELS = {"Email", "VideoCall", "MultipleMonitors", "Browser"}
```

**Impact**: These sets define the ONLY valid labels the system recognizes.

---

## 🔒 WHERE LABELS ARE ENFORCED

### 2. OpenAI Vision Client - Label Validation

**File**: `src/focus_guardian/integrations/openai_vision_client.py` (lines 336-348)

```python
# After OpenAI returns labels, they are validated
valid_labels = CAM_LABELS if kind == "cam" else SCREEN_LABELS
filtered_labels = {}

for label, confidence in labels.items():
    if label in valid_labels:  # ← HARDCODED CHECK
        threshold = CONFIDENCE_THRESHOLDS.get(label, 0.5)
        if confidence >= threshold:
            filtered_labels[label] = float(confidence)
    else:
        # INVALID LABEL - REJECTED!
        logger.warning(f"Invalid label '{label}' returned by Vision API")
```

**Impact**: If OpenAI returns a label NOT in the hardcoded sets, it's **silently dropped** with a warning in the logs.

---

### 3. State Machine - Hardcoded Logic

**File**: `src/focus_guardian/core/state_machine.py` (lines 137-207)

```python
# Check for absence (HARDCODED label set)
if self._has_majority(cam_label_counts, CAM_ABSENCE_LABELS, threshold):
    return State.ABSENT

# Check for distraction (HARDCODED label sets)
cam_distracted = self._has_majority(cam_label_counts, CAM_DISTRACTION_LABELS, threshold)
screen_distracted = self._has_majority(screen_label_counts, SCREEN_DISTRACTION_LABELS, threshold)

# Check for focus (HARDCODED label sets)
cam_focused = self._has_majority(cam_label_counts, CAM_FOCUS_LABELS, threshold)
screen_focused = self._has_majority(screen_label_counts, SCREEN_FOCUS_LABELS, threshold)
```

**Impact**: The voting engine ONLY knows about the hardcoded label categories. It doesn't process any other labels.

---

## 🎨 WHAT CAN BE CUSTOMIZED

### Prompts (Customizable ✅)

**File**: `src/focus_guardian/integrations/openai_vision_client.py` (lines 136-142, 174-180)

```python
def _build_cam_prompt(self) -> str:
    # Check for custom prompt first
    if self.config:
        custom = self.config.get_custom_prompt("cam_snapshot")
        if custom:
            return custom  # ← CUSTOM PROMPT USED
    
    # Default prompt (describes hardcoded labels)
    return """Analyze this webcam image..."""
```

**You CAN customize**:
- The prompt text sent to OpenAI
- How labels are described
- Instructions and context

**BUT you CANNOT**:
- Add new label names (they'll be filtered out)
- Change which labels = distraction vs focus
- Modify the voting logic

---

## ⚠️ THE LIMITATION

### Example Scenario:

**What you want**: Add a new label called "StandingUp" to detect when user stands up

**What happens**:
1. ✅ You can add "StandingUp" to your custom prompt
2. ✅ OpenAI Vision will return `{"StandingUp": 0.9}`
3. ❌ Label validation rejects it (not in `CAM_LABELS`)
4. ⚠️ Warning logged: `"Invalid label 'StandingUp' returned"`
5. ❌ State machine never sees it
6. ❌ No effect on voting

**The label is thrown away because it's not in the hardcoded set!**

---

## 🔓 HOW TO ADD NEW LABELS

If you want to add custom labels, you need to modify 3 files:

### Step 1: Add to Taxonomy (`models.py`)
```python
# Add to the hardcoded set
CAM_LABELS = {
    "HeadAway",
    "EyesOffScreen",
    "Absent",
    "MicroSleep",
    "PhoneLikely",
    "Focused",
    "StandingUp"  # ← NEW LABEL
}

# Categorize it
CAM_DISTRACTION_LABELS = {
    "HeadAway", "EyesOffScreen", "MicroSleep", 
    "PhoneLikely", "StandingUp"  # ← ADD TO CATEGORY
}

# Add confidence threshold
CONFIDENCE_THRESHOLDS = {
    # ... existing thresholds
    "StandingUp": 0.75  # ← SET THRESHOLD
}
```

### Step 2: Update Prompt (`openai_vision_client.py`)
```python
def _build_cam_prompt(self) -> str:
    return """Analyze this webcam image...
    
    Possible classifications:
    - HeadAway: ...
    - StandingUp: User is standing or not seated  # ← DESCRIBE NEW LABEL
    ...
    """
```

### Step 3: No Changes Needed!
- State machine automatically picks up new label
- Voting engine uses it for distraction detection
- UI displays it in reports

---

## 📊 CURRENT HARDCODED STRUCTURE

### Camera Labels (6 total)
| Label | Category | Purpose |
|-------|----------|---------|
| HeadAway | Distraction | Head >45° from screen |
| EyesOffScreen | Distraction | Gaze not on screen |
| MicroSleep | Distraction | Eyes closed/drowsy |
| PhoneLikely | Distraction | Phone in hand |
| Absent | Absence | No person visible |
| Focused | Focus | Attentive posture |

### Screen Labels (15 total)
| Label | Category | Purpose |
|-------|----------|---------|
| VideoOnScreen | Distraction | Entertainment video |
| SocialFeed | Distraction | Social media |
| Games | Distraction | Gaming |
| ChatWindow | Distraction | Personal chat |
| Code | Focus | Code editor |
| Docs | Focus | Documentation |
| Reading | Focus | Long-form reading |
| Slides | Focus | Presentations |
| Terminal | Focus | Command line |
| WorkRelatedVideo | Focus | Tutorial videos |
| WorkChat | Focus | Work messaging |
| Email | Borderline | Context-dependent |
| VideoCall | Borderline | Context-dependent |
| MultipleMonitors | Borderline | Context switching |
| Browser | Neutral | Generic browser |
| Unknown | Neutral | Can't determine |

---

## 🎯 CUSTOMIZATION OPTIONS (Current System)

### What You CAN Customize ✅
1. **Prompt wording** - Via `config.save_custom_prompt("cam_snapshot", custom_text)`
2. **Label descriptions** - How you describe labels to OpenAI
3. **Instructions** - How you tell OpenAI to classify
4. **Context and examples** - Additional guidance in prompts

### What You CANNOT Customize ❌
1. **Label names** - Must be exact matches from hardcoded sets
2. **Label categories** - Which labels = distraction vs focus
3. **Voting logic** - K=3 hysteresis, majority threshold
4. **State machine transitions** - Hardcoded priority: Absence > Distraction > Focus

---

## 💡 DESIGN RATIONALE

### Why Are Labels Hardcoded?

**Pro**:
- ✅ Consistent classification across all sessions
- ✅ Reliable state machine logic
- ✅ Prevents AI from inventing random labels
- ✅ Enables comparison across sessions
- ✅ Database schema stability

**Con**:
- ❌ Can't add new detection types without code changes
- ❌ Limited flexibility for user-specific needs
- ❌ Requires developer to modify code for new labels

---

## 🔧 MAKING IT MORE FLEXIBLE (Future Enhancement)

If you want to make labels configurable, here's what would need to change:

### Option 1: Configuration-Based Labels
```python
# In config.json
{
  "custom_labels": {
    "cam": {
      "StandingUp": {
        "category": "distraction",
        "threshold": 0.75,
        "description": "User is standing or not seated"
      }
    }
  }
}
```

### Option 2: Dynamic Label Registration
```python
class LabelRegistry:
    def register_label(self, name, category, threshold, description):
        # Dynamically add to valid labels
        # Update state machine categories
        # Regenerate prompts
```

### Option 3: Plugin System
```python
# Load custom detection modules
class CustomDetector:
    def get_labels(self) -> Set[str]:
        return {"StandingUp", "DrinkingWater"}
    
    def get_category(self, label: str) -> str:
        return "distraction" if label == "StandingUp" else "neutral"
```

---

## 📋 SUMMARY

### Current Reality

| Component | Hardcoded? | Can Customize? |
|-----------|------------|----------------|
| **Label names** | ✅ YES | ❌ NO (must match exactly) |
| **Label categories** | ✅ YES | ❌ NO (focus/distraction/absence) |
| **Confidence thresholds** | ✅ YES | ❌ NO (in code) |
| **Prompt text** | ❌ NO | ✅ YES (via config) |
| **Prompt descriptions** | ❌ NO | ✅ YES (via custom prompts) |
| **Voting logic (K=3)** | ✅ YES | ❌ NO (hardcoded) |
| **State priorities** | ✅ YES | ❌ NO (Absence > Distraction > Focus) |

### To Add a New Label

You must modify **source code** in 3 places:
1. `models.py` - Add to CAM_LABELS or SCREEN_LABELS sets
2. `models.py` - Add to appropriate category (distraction/focus/etc)
3. `models.py` - Add confidence threshold
4. `openai_vision_client.py` - Update default prompt (optional if using custom)

**Then restart the application** for changes to take effect.

---

## 🤔 SHOULD YOU MAKE IT CONFIGURABLE?

### Keep It Hardcoded If:
- ✅ Current labels cover all your use cases
- ✅ You want consistent, comparable data across all sessions
- ✅ You don't want users accidentally breaking the detection system
- ✅ Simplicity is more important than flexibility

### Make It Configurable If:
- ⚠️ Users need domain-specific detection (e.g., medical, education)
- ⚠️ Different users need different label sets
- ⚠️ You want to experiment with new detection types frequently
- ⚠️ You're building a platform for others to customize

---

## 💬 RECOMMENDATION

**For your hackathon/MVP**: Keep it hardcoded ✅

The current 6 camera + 15 screen labels cover 95% of distraction scenarios. Adding configuration would:
- Increase complexity significantly
- Introduce bugs (invalid label configurations)
- Make debugging harder
- Not add much value for most users

**For production v2.0**: Consider making it plugin-based for power users

---

## 🛠️ QUICK EXAMPLE: Adding "DrinkingCoffee" Label

```python
# 1. Edit: src/focus_guardian/core/models.py
CAM_LABELS = {
    "HeadAway", "EyesOffScreen", "Absent", "MicroSleep", 
    "PhoneLikely", "Focused",
    "DrinkingCoffee"  # ← ADD HERE
}

# 2. Categorize it (is it distraction, focus, or neutral?)
# Option A: Make it a distraction
CAM_DISTRACTION_LABELS = {
    "HeadAway", "EyesOffScreen", "MicroSleep", 
    "PhoneLikely", "DrinkingCoffee"  # ← ADD HERE
}

# Option B: Or make it neutral (ignored by voting)
CAM_NEUTRAL_LABELS = {"DrinkingCoffee"}  # ← NEW CATEGORY

# 3. Set threshold
CONFIDENCE_THRESHOLDS = {
    # ... existing
    "DrinkingCoffee": 0.7  # ← ADD THRESHOLD
}

# 4. Update prompt (optional - or use custom prompt in UI)
def _build_cam_prompt(self):
    return """...
    - DrinkingCoffee: User is drinking coffee or other beverage
    ..."""

# 5. Restart app - new label is now active!
```

---

## 📚 FILES TO CHECK

- **Label definitions**: `src/focus_guardian/core/models.py:347-411`
- **Prompt generation**: `src/focus_guardian/integrations/openai_vision_client.py:136-235`
- **Label validation**: `src/focus_guardian/integrations/openai_vision_client.py:336-347`
- **Voting logic**: `src/focus_guardian/core/state_machine.py:135-207`

---

**Bottom Line**: Yes, labels are hardcoded by design for consistency and reliability. You can customize prompts (how you describe labels), but not the label names or their categories without modifying source code.

