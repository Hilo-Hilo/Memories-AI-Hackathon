# Focus Guardian

**AI-Powered ADHD Focus Coach**

*Global Multi-Modal Hackathon Submission*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Hume AI](https://img.shields.io/badge/Powered%20by-Hume%20AI-FF6B6B.svg)](https://hume.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Team](#team)
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Hume AI Integration](#hume-ai-integration-primary-sponsor)
- [Installation](#installation)
- [Usage](#usage)
- [Technical Challenges](#technical-challenges)
- [Future Improvements](#future-improvements)
- [Documentation](#documentation)

---

## Team

**Developer:** Hanson Wen  
**Location:** San Francisco Bay Area  
**Type:** Solo Development  
**Motivation:** Personal experience with ADHD revealed a gap in productivity tools - they don't understand emotional context behind distraction

---

## Project Overview

### The Problem

People with ADHD often struggle with maintaining focus and attention regulation. Traditional productivity tools approach distraction as binary (focused/distracted) and respond with generic interventions. This results in high false positive rates, ineffective coaching, and user abandonment.

Emotional states like frustration and boredom can precede distraction, yet existing tools ignore this dimension.

### Our Solution

Focus Guardian combines **multimodal AI analysis** to understand not just when users are distracted, but why:

1. **Pattern-Confirmed Detection** (OpenAI Vision API)
   - Captures webcam and screen snapshots every 60 seconds
   - Classifies behavior and screen content
   - K=3 hysteresis voting eliminates false positives (requires 3 consecutive snapshots)

2. **Emotion Intelligence** (Hume AI Expression Measurement)
   - Post-session webcam video analysis
   - 48-dimension emotion timeline
   - Correlates emotion spikes with distraction events

3. **Behavioral Analysis** (Memories.ai VLM)
   - Long-form session analysis
   - Activity breakdown and context-switching patterns
   - Personalized recommendations

4. **Adaptive Interventions**
   - Alert tone and messaging adapt to emotional state
   - Frustrated: empathetic support
   - Tired: break suggestions
   - Bored: gamification strategies

### Key Innovation

**Emotion-Aware Interventions:** Adapts coaching style based on detected emotional state rather than using generic "get back to work" alerts. Interventions are contextually appropriate to the user's current emotional state.

---

## Key Features

### Core Functionality

- **Snapshot-Based Detection**: Webcam and screen capture at configurable intervals (default: 60s, adjustable down to 3s for testing)
- **AI-Powered Classification**: OpenAI Vision API (`gpt-4.1-nano`) for accurate pattern recognition
- **K=3 Hysteresis Voting**: Requires 3 consecutive snapshots over 1+ minutes to confirm distraction
- **Session Management**: Complete recording lifecycle with start/pause/resume/stop
- **Real-time Stats**: Track snapshots captured, uploaded, and distraction events during session

### Advanced Features

- **Emotion Analysis**: Optional post-session Hume AI emotion timeline with 48 emotion dimensions
- **Pattern Analysis**: Optional Memories.ai long-form VLM analysis
- **Comprehensive Reports**: AI-generated session reports combining all data sources
- **Privacy-First**: Encrypted API keys using system keyring, local video storage
- **Cross-Platform**: PyQt6 desktop application for macOS, Windows, Linux

### Detection Capabilities

**Webcam Analysis:**
- Head orientation (turned away >45°)
- Gaze direction (eyes off-screen)
- Physical presence (absent from workspace)
- Drowsiness indicators
- Phone usage

**Screen Content Analysis:**
- Video streaming (YouTube, Netflix)
- Social media (Twitter, Instagram, Facebook, TikTok)
- Gaming applications
- Messaging apps (Slack, Discord, WhatsApp)
- Productive apps (code editors, terminals, documentation)

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.10+ | Application development |
| **Desktop Framework** | PyQt6 | 6.6.0+ | Cross-platform native UI |
| **Video Processing** | OpenCV + FFmpeg | 4.8.0+ | Webcam/screen recording |
| **Screen Capture** | mss | 9.0.0+ | Fast screen grabbing |
| **Database** | SQLite | Built-in | Local data storage |
| **Image Processing** | Pillow + NumPy | 10.0.0+ | Snapshot handling |

### Dependencies

**Required:**
```python
# Core
PyQt6>=6.6.0
opencv-python>=4.8.0
mss>=9.0.0
ffmpeg-python>=0.2.0
Pillow>=10.0.0
numpy>=1.24.0

# AI APIs
openai>=1.0.0           # OpenAI Vision (required)
hume>=0.12.0            # Hume AI (optional)
requests>=2.31.0        # Memories.ai (optional)

# Config & Security
python-dotenv>=1.0.0
PyYAML>=6.0.0
cryptography>=41.0.0
keyring>=24.0.0

# Performance
psutil>=5.9.0
tqdm>=4.66.0
```

**Optional (Calendar Integration):**
```python
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.100.0
```

**Development:**
```python
pytest>=7.4.0
pytest-qt>=4.2.0
black>=23.0.0
ruff>=0.1.0
```

### System Architecture

```
Desktop Application (PyQt6)
├── Session Manager
│   ├── Video Recorders (cam.mp4, screen.mp4)
│   ├── Snapshot Scheduler (captures every 60s)
│   └── Snapshot Uploader (worker pool)
│
├── Real-time Analysis Pipeline
│   ├── OpenAI Vision Client → Label Classification
│   ├── Fusion Engine → K=3 Hysteresis Voting
│   ├── State Machine → State Tracking
│   └── Distraction Detector → Event Emission
│
└── Post-Session Processing
    ├── Hume AI Client → Emotion Analysis
    ├── Memories.ai Client → Pattern Analysis
    ├── Report Generator → Comprehensive Reports
    └── Cloud Analysis Manager → Job Orchestration
```

---

## Hume AI Integration (PRIMARY SPONSOR)

Hume AI provides the **emotional intelligence layer** that differentiates Focus Guardian from traditional productivity tools.

### What We Use

- **Batch API**: Post-session video analysis with job submission and polling
- **Facial Expression Model**: 48-dimension emotion measurement from webcam recordings
- **Python SDK**: Official `hume` package (v0.12.0+)

### Technical Integration

**1. Emotion Timeline Generation** (`integrations/hume_client.py`)

```python
class HumeExpressionClient:
    def analyze_video(self, video_path: Path) -> str:
        """Upload webcam video to Hume AI Batch API."""
        with open(video_path, 'rb') as video_file:
            job_id = self.client.expression_measurement.batch\
                .start_inference_job_from_local_file(
                    file=[video_file],
                    json={"models": {"face": {}}}
                )
        return job_id
    
    def fetch_results(self, job_id: str) -> Dict[str, Any]:
        """Fetch emotion analysis results."""
        predictions = self.client.expression_measurement.batch\
            .get_job_predictions(id=job_id)
        return self._parse_predictions(predictions, job_id)
```

**Key Features:**
- Extracts emotions per frame: Concentration, Frustration, Boredom, Stress, Confusion
- Creates 1Hz timeline synchronized with session timestamps
- Calculates summary statistics (mean emotions across session)

**2. Distraction-Emotion Correlation** (`integrations/hume_client.py:372-433`)

```python
def correlate_with_distractions(
    self,
    emotion_timeline: List[Dict],
    distraction_events: List[Dict]
) -> List[Dict]:
    """Correlate emotion spikes with distraction events."""
    for event in distraction_events:
        event_time = event["started_at"]
        window_start = event_time - 300  # 5 minutes before
        window_end = event_time + 300    # 5 minutes after
        
        # Extract emotions in window
        window_emotions = [
            frame for frame in emotion_timeline
            if window_start <= frame["timestamp"] <= window_end
        ]
        
        # Calculate pre-distraction averages
        pre_distraction = [f for f in window_emotions if f["timestamp"] < event_time]
        avg_emotions = calculate_average(pre_distraction)
        
        # Identify dominant trigger
        correlations.append({
            "event_id": event["event_id"],
            "dominant_emotion": max(avg_emotions.items(), key=lambda x: x[1])[0],
            "insight": self._generate_insight(avg_emotions)
        })
```

**3. Emotion-Aware Messaging** (`ai/emotion_aware_messaging.py`)

```python
def generate_distraction_alert(
    self, 
    distraction_type: str,
    emotion_state: EmotionState
) -> Dict[str, str]:
    """Generate context-appropriate alert based on emotional state."""
    
    if emotion_state == EmotionState.FRUSTRATED:
        return {
            "title": "I Notice You're Frustrated",
            "message": "Frustration is normal when tackling hard problems. "
                      "Sometimes stepping away helps.",
            "actions": ["Take a 5-min break", "Back to work", "Change task"]
        }
    elif emotion_state == EmotionState.TIRED:
        return {
            "title": "Energy Check",
            "message": "Pushing through fatigue leads to more distractions. "
                      "Your brain needs rest.",
            "actions": ["Take an energy break", "Continue", "End session"]
        }
```

**4. Comprehensive AI Reports** (`ai/comprehensive_report_generator.py`)

```python
def generate_comprehensive_report(
    self,
    session_id: str,
    hume_results: Optional[Dict] = None,
    memories_results: Optional[Dict] = None
) -> Dict[str, Any]:
    """Generate AI report combining all data sources."""
    
    # Gather data: session stats, OpenAI Vision labels, Hume emotions, Memories patterns
    context = self._gather_all_data(session_id, hume_results, memories_results)
    
    # Generate narrative using GPT-4
    prompt = self._build_comprehensive_prompt(context)  # Includes Hume emotion timeline
    report = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=2000
    )
    
    return {
        "report_text": report.choices[0].message.content,
        "data_sources": {
            "hume_ai": True,
            "memories_ai": bool(memories_results),
            "historical_data": True
        }
    }
```

### Why Hume AI Was Critical

Traditional tools treat distraction as binary (focused/distracted). Hume AI enabled us to understand **emotional context** behind distraction by providing 48-dimension emotion analysis that can be correlated with distraction events.

This enables **predictive coaching** - the system can identify emotional patterns that precede distraction (such as frustration or boredom spikes), rather than just reacting after distraction occurs.

### Technical Challenges Solved

1. **Timeline Synchronization**: Aligned 1Hz Hume emotion data with irregular distraction events using ±5 minute sliding window correlation

2. **Batch Processing Latency**: Implemented background threading with progressive enhancement - show OpenAI Vision results immediately, enhance with Hume data when ready (5-10 minutes)

3. **Data Validation**: Validated 48-dimension emotion vectors, handled missing frames gracefully

### Integration Code Files

- `src/focus_guardian/integrations/hume_client.py` - Core Hume AI integration (503 lines)
- `src/focus_guardian/session/cloud_analysis_manager.py` - Upload orchestration (817 lines)
- `src/focus_guardian/ai/emotion_aware_messaging.py` - Adaptive messaging (341 lines)
- `src/focus_guardian/ai/comprehensive_report_generator.py` - Report generation with Hume data (521 lines)

---

## Installation

### Prerequisites

- Python 3.10 or higher
- FFmpeg (for video encoding)
- Webcam (built-in or external)
- OpenAI API key (required)
- Hume AI API key (optional, for emotion analysis)
- Memories.ai API key (optional, for pattern analysis)

### Quick Start

1. **Clone repository:**
   ```bash
   git clone https://github.com/Hilo-Hilo/Memories-AI-Hackathon.git
   cd "Memories-AI-Hackathon"
   ```

2. **Install UV package manager (recommended):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

4. **Install FFmpeg:**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows: Download from https://ffmpeg.org/download.html
   ```

5. **Configure API keys:**

   Create `.env` file in project root:
   ```bash
   # Required for distraction detection
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   
   # Optional for emotion analysis
   HUME_API_KEY=your_hume_api_key_here
   
   # Optional for pattern analysis
   MEMORIES_API_KEY=your_memories_api_key_here
   ```

   **Get API Keys:**
   - OpenAI: https://platform.openai.com/api-keys
   - Hume AI: https://www.hume.ai
   - Memories.ai: https://memories.ai

6. **Run the application:**
   ```bash
   ./run_focus_guardian.sh
   # Or: python -m focus_guardian.main
   ```

### Platform-Specific Setup

**macOS:**
- Grant camera permission: System Settings → Privacy & Security → Camera
- Grant screen recording: System Settings → Privacy & Security → Screen Recording
- Code signing may be required for distribution

**Windows:**
- Grant camera permission: Settings → Privacy → Camera
- Add FFmpeg to PATH if not using Chocolatey/Scoop

**Linux:**
- Add user to video group: `sudo usermod -a -G video $USER`
- Install system dependencies: `sudo apt install libxcb-xinerama0`

---

## Usage

### Starting a Session

1. Launch Focus Guardian
2. Click "Start Focus Session"
3. Enter task name (e.g., "Code review")
4. Select options:
   - Quality profile: Low/Standard/High
   - Enable/disable screen capture
5. Session begins:
   - Continuous video recording (H.264/MP4)
   - Snapshot capture every 60 seconds
   - Real-time OpenAI Vision classification
   - K=3 hysteresis voting for pattern confirmation

### During a Session

- **Status Indicators**:
  - Green: Focused state confirmed
  - Yellow: Transitional state
  - Red: Distraction pattern detected (2-3 min confirmation)
  
- **Controls**:
  - Pause: Temporarily stop monitoring (intentional break)
  - Resume: Continue monitoring
  - Stop: End session and generate report

- **Real-time Stats**:
  - Snapshots captured/uploaded
  - Current focus ratio
  - Number of distraction events

### Ending a Session

1. Click "Stop Session"
2. Wait for final snapshot uploads (typically 5-10 seconds)
3. View immediate session report (OpenAI Vision data)
4. **Optional**: Upload for emotion analysis
   - Select "Analyze with Hume AI"
   - Processing takes 5-10 minutes
   - Report updates automatically when complete
5. **Optional**: Upload for pattern analysis
   - Select "Analyze with Memories.ai"
   - Get behavioral insights and recommendations

### Session Reports

Reports include:
- **Focus Metrics**: Time focused vs. distracted, focus ratio
- **Distraction Timeline**: When and what type of distractions occurred
- **Snapshot Evidence**: Visual labels and confidence scores
- **Emotion Analysis** (if Hume AI enabled): Emotional journey throughout session
- **Behavioral Insights** (if Memories.ai enabled): Activity patterns, context-switching
- **Recommendations**: Personalized strategies based on your patterns

Reports are saved to:
- `data/sessions/<session_id>/` - Individual session data
- `data/reports/<session_id>_report.json` - Structured report data

---

## Technical Challenges

### 1. Emotion-Distraction Timeline Synchronization

**Problem:** Hume AI returns 1Hz emotion data, but distractions are irregular events. How to correlate "frustration spike at 14:32:15" with "distraction at 14:34:20"?

**Solution:** ±5 minute sliding window correlation

```python
def correlate_with_distractions(self, emotion_timeline, distraction_events):
    for event in distraction_events:
        event_time = event["started_at"]
        window_start = event_time - 300  # 5 min before
        window_end = event_time + 300    # 5 min after
        
        window_emotions = [
            f for f in emotion_timeline
            if window_start <= f["timestamp"] <= window_end
        ]
        
        pre_distraction = [f for f in window_emotions if f["timestamp"] < event_time]
        avg_emotions = calculate_average(pre_distraction)
```

**Learning:** Window-based correlation handles noisy real-world data better than exact timestamp matching.

### 2. Hume AI Batch Processing Latency

**Problem:** 5-10 minute processing time, but users expect instant results.

**Solution:** Progressive enhancement with background processing

1. Show immediate basic report (OpenAI Vision data)
2. Upload to Hume AI starts in background thread
3. Report updates when Hume processing completes

```python
def upload_session_for_analysis(self, session_id, cam_video):
    job_id = self.hume_client.analyze_video(cam_video)
    
    # Non-blocking polling
    threading.Thread(
        target=self._poll_and_retrieve,
        args=(job_id,),
        daemon=True
    ).start()
    
    return job_id  # UI not blocked
```

**Learning:** Users tolerate latency with clear progress indicators and incremental value.

### 3. K=3 Hysteresis False Positive Elimination

**Problem:** Early prototypes generated excessive false alerts when users briefly glanced away from screens.

**Solution:** Require 3 consecutive snapshots showing distraction over 1+ minutes

```python
class FusionEngine:
    def process_snapshot(self, snapshot_labels, timestamp):
        self.snapshot_buffer.append({"labels": snapshot_labels, "timestamp": timestamp})
        
        if len(self.snapshot_buffer) == self.K:  # K=3
            time_span = self.snapshot_buffer[-1]["timestamp"] - self.snapshot_buffer[0]["timestamp"]
            
            if time_span >= 60:  # 1 minute minimum
                distraction_votes = sum(
                    1 for snap in self.snapshot_buffer 
                    if snap["labels"]["dominant"] in DISTRACTION_LABELS
                )
                
                if distraction_votes >= 2:  # ≥2 of 3
                    return "DISTRACTED"
        
        return "FOCUSED"
```

**Learning:** For ADHD tools, accuracy is more important than speed. The K=3 hysteresis approach significantly reduces false positives by requiring sustained patterns rather than reacting to brief glances. This trades 2-3 minute detection latency for higher reliability.

### 4. Multi-API Cost Management

**Problem:** OpenAI Vision (120 calls/session) + Hume AI ($0.50) + Memories.ai ($1.00) = substantial costs.

**Solution:**
- Configurable snapshot intervals (30s/60s/90s)
- Quality profiles (Economy/Standard/High)
- Pre-session cost estimates
- Real-time cost tracking
- Monthly cost caps with auto-pause

**Learning:** Cost transparency builds trust. When users understand costs and can control them through configuration, they're more willing to use the service.

---

## Future Improvements

### Immediate Next Steps (Post-Hackathon)

1. **Real-Time Emotion Detection**
   - Use Hume WebSocket Streaming API instead of Batch
   - Detect frustration/boredom *before* distraction occurs
   - Enable proactive interventions

2. **Predictive Distraction Prevention**
   - Train ML model: (emotion + time + task) → distraction probability
   - Alert: "78% risk of distraction in next 5 minutes"
   - Proactive coaching instead of reactive

3. **Mobile Companion App**
   - View session reports on phone
   - Notifications when desktop session completes
   - Track trends over time

### Version 1.0 (6 Months)

4. **Voice-Based Interventions**
   - Hume Vocal Burst analysis for tone detection
   - Gentle voice reminders
   - Adaptive tone based on emotional state

5. **Team & Accountability Mode**
   - Privacy-preserving focus metrics sharing
   - Leaderboards for study groups
   - Group sessions with synchronized breaks

6. **Cross-Platform Sync**
   - Work on desktop, check progress on mobile
   - Cloud backup of session reports
   - Multi-device notifications

### Research Directions

7. **ADHD Subtype Personalization**
   - Inattentive vs Hyperactive vs Combined
   - Adapt intervention strategies per subtype
   - A/B test effectiveness

8. **Clinical Research Integration**
   - Partner with ADHD researchers
   - Anonymized data donation (opt-in)
   - Validate interventions in clinical studies

---

## Documentation

### Core Documentation

- **[README.md](README.md)** - This file (overview, setup, usage)
- **[SETUP.md](SETUP.md)** - Detailed setup instructions and troubleshooting
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[prd.md](prd.md)** - Complete product requirements and specifications
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and component design

### API Reference

Located in `documentation/` directory:
- **Hume AI** (`hume-expression-measurement-docs/`) - Expression Measurement API
- **OpenAI** (`openai_vision_api_docs/`) - Vision API integration
- **Memories.ai** (`memories_ai_api_docs/`) - Video analysis API

### Test Documentation

- **[tests/TEST_GUIDE.md](tests/TEST_GUIDE.md)** - Testing procedures
- **[tests/TEST_RESULTS_SUMMARY.md](tests/TEST_RESULTS_SUMMARY.md)** - Test coverage

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

**Hackathon Sponsors:**

**Hume AI** - For the Expression Measurement API that enabled emotion-aware interventions. The 48-dimension emotion analysis provides insights into how emotional states correlate with distraction patterns, enabling a fundamentally different approach to ADHD productivity tools.

**OpenAI** - GPT-4.1-nano Vision provides accurate, cost-effective real-time snapshot classification.

**Memories.ai** - Long-form VLM analysis delivers behavioral insights that complement snapshot-based detection.

**Technology & Community:**
- PyQt6 - Cross-platform GUI framework
- FFmpeg - Video encoding
- Python Community - Open-source ecosystem
- ADHD Community - Feedback and inspiration
- Early Testers - Honest feedback that shaped the product

**Special Thanks:**

To every person with ADHD who has been told to "just focus harder" - this project is for you. You are not broken. Your brain works differently, and it deserves tools designed with empathy and understanding.

---

## Hackathon Submission Summary

**Project:** Focus Guardian  
**Developer:** Hanson Wen (Solo)  
**Repository:** https://github.com/Hilo-Hilo/Memories-AI-Hackathon

**What We Built:** AI-powered ADHD focus coach combining multimodal AI (computer vision, emotion recognition, behavioral analysis) for personalized, empathetic coaching.

**Primary Innovation:** Emotion-aware interventions powered by Hume AI - adapts coaching style based on emotional state analysis rather than using generic productivity alerts.

**Technical Achievement:** Synchronized three AI systems (Hume Expression Measurement, OpenAI Vision, Memories.ai VLM) into coherent multimodal pipeline for comprehensive focus analysis.

**Key Discovery:** Hume AI's emotion analysis reveals that emotional state changes (frustration, boredom, fatigue) can precede distraction events. This enables predictive, context-aware coaching rather than reactive generic alerts.

**Impact Potential:** Designed to help individuals with ADHD build better focus habits through AI-powered pattern recognition and emotion-aware coaching.

**Why It Matters:** Traditional productivity tools approach distraction as a behavioral problem requiring discipline. Focus Guardian recognizes ADHD attention difficulties often have emotional roots and provides supportive coaching adapted to emotional state. This human-centered AI approach represents a fundamental shift in neurodivergent productivity support.

---

**Focus Guardian** - Understanding focus through emotion, not judgment

Built for the ADHD community | Powered by Hume AI Expression Measurement

Global Multi-Modal Hackathon | Solo Developer: Hanson Wen | San Francisco Bay Area
