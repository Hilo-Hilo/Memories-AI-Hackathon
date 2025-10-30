# Focus Guardian - ADHD Distraction Analysis Desktop Application

[![Watch Demo](https://img.shields.io/badge/YouTube-Watch%20Demo-red?style=for-the-badge&logo=youtube)](https://youtu.be/hQMT0d7uPpw)

## Project Overview

**Focus Guardian** is a desktop application designed to help individuals with ADHD monitor and reduce distraction episodes in real-time. Unlike traditional productivity tools that block websites or track time, Focus Guardian actively monitors your attention state through webcam and screen analysis, detecting when you lose focus and providing gentle interventions to refocus.

### The Problem We're Solving

People with ADHD often struggle to maintain focus, especially in unstructured or remote work environments. Moments of distraction—whether daydreaming, fidgeting, or being pulled into unrelated activities—can significantly reduce productivity and increase frustration. Traditional tools like site blockers or timers address external distractions but **do not actively monitor the person's attention state**.

Focus Guardian solves this by:
- **Recognizing distraction in real-time** through behavioral cues (gaze aversion, screen content patterns)
- **Gentle intervention** via alerts when sustained distraction is detected (2-3 minute latency for accuracy)
- **Learning your patterns** to provide personalized strategies over time
- **Privacy-conscious** - snapshots for AI analysis, full video recordings stay local
- **Easy to use** - native desktop app with minimal setup

### Why It Matters

For people with ADHD, external structure and feedback are crucial for maintaining productivity. Constant human coaching is impractical, but an automated, intelligent assistant that understands your goals and patterns can fill this gap. Focus Guardian acts as a **digital "coach"** that:

- Detects when you drift away from your task
- Helps you understand your distraction patterns (when, why, how)
- Provides emotion-aware feedback (recognizes frustration, boredom, stress)
- Learns from your behavior to deliver increasingly personalized guidance
- Tracks long-term progress and suggests habit improvements

## Team Introduction

**James Gui** | *Los Angeles, CA - USC*
- Contribution: Core development, video editing, Vibe coding
- Background: University student passionate about building tools that make a difference

**Hanson Wen** | *Berkeley, CA - UC Berkeley*
- Contribution: Core development, video editing, Vibe coding  
- Background: University student with expertise in AI/ML applications

**Fun Facts:**
- James is lactose intolerant but drinks a lot of milk anyway—his digestive system pays the price daily 😅
- Hanson holds a Guinness World Record for flying around the world in the fastest time! 🌍✈️

*We've been high school friends for a long time, giving us great team chemistry and seamless collaboration.*

## Key Features & Tech Stack

### Core Features

1. **Real-Time Distraction Detection**
   - Webcam monitoring for attention state (head position, eye gaze, presence)
   - Screen content analysis (detects social feeds, videos, games vs. productive work)
   - K=3 hysteresis voting for 2-3 minute pattern confirmation (eliminates false positives)
   - Configurable snapshot intervals (default: 60 seconds, range: 10-120s)

2. **Personalized Coaching**
   - **Optimal Focus Duration Analyzer**: Analyzes your past sessions to recommend ideal focus block durations
   - Tracks when you typically get your first distraction
   - Suggests personalized focus durations based on your historical patterns
   - Example: "Based on your past sessions, you typically get distracted after 20 minutes. We recommend 15-minute focus blocks."

3. **Emotion-Aware Insights** (Hume AI Integration)
   - Post-session emotion analysis from webcam video
   - Timeline visualization of frustration, boredom, stress, engagement
   - Correlates emotions with distraction events
   - Example: "Your frustration increased 5 minutes before each distraction—try taking a 2-minute break when you feel frustrated"

4. **AI-Powered Session Reports**
   - Comprehensive session summaries with KPIs (focus ratio, distraction frequency)
   - Pattern analysis (when you get distracted, what triggers it)
   - Long-term trend tracking
   - Actionable recommendations

5. **Privacy-First Architecture**
   - Periodic snapshots uploaded to OpenAI Vision API for analysis
   - Full video recordings stored locally
   - Optional post-session cloud analysis (user chooses)
   - Complete data transparency

### Tech Stack

**Frontend & GUI:**
- PyQt6 - Native desktop GUI framework
- Modern dark theme with smooth animations
- System tray integration for macOS/Windows

**Core Technologies:**
- Python 3.13+ - Primary language
- SQLite - Local data storage (sessions, events, reports)
- OpenCV (cv2) - Image processing and camera capture
- MSS - Fast screen capture
- ffmpeg-python - Continuous video recording

**AI & Cloud Services:**
- **OpenAI Vision API** - Real-time snapshot classification
  - Detects: Head away, eyes off-screen, phone usage, screen content types
  - Snapshot-based analysis (not continuous video streams)
- **Hume AI Expression API** - Post-session emotion analysis
  - Detailed emotion timeline (frustration, boredom, engagement)
  - Correlates emotions with distraction patterns
- **Memories.ai** - Pattern analysis and semantic understanding
  - Long-term behavior tracking
  - Personalized insights over time

**Development & Packaging:**
- pyproject.toml - Modern Python project configuration
- UV - Fast package manager (supports dependency resolution)
- PyInstaller (planned) - Desktop app packaging

**Utilities:**
- python-dotenv - Configuration management
- cryptography - API key encryption
- logging - Structured application logging

## Sponsor Tools Used

### Hume AI - Emotional Intelligence Layer

**What it does:** Hume AI's Expression API analyzes video to detect "hundreds of dimensions of human expression" including facial expressions, vocal prosody, and gestural patterns.

**How we integrated it:**
- **Post-session analysis**: After a focus session ends, users can optionally upload their webcam video for emotion analysis
- **1Hz emotion timeline**: Hume processes the video and returns a detailed timeline showing how emotions fluctuated throughout the session
- **Correlation analysis**: We correlate emotion spikes with distraction events to identify triggers
  - Example: "Frustration peaks 5 minutes before distractions → try taking breaks when you feel frustrated"

**Why it matters:** Understanding *why* someone gets distracted (emotional triggers) is as important as detecting *when* it happens. Hume AI provides this emotional intelligence layer that makes our coaching adaptive and truly personalized.

**Implementation:**
```python
# Post-session upload to Hume AI
hume_job_id = self.hume_client.upload_video_for_analysis(
    session_id=session_id,
    video_path=cam_video_path
)

# Emotion timeline results
emotions = self.hume_client.get_emotion_timeline(
    job_id=hume_job_id
)
```

### Memories.ai - Pattern Intelligence

**What it does:** Memories.ai provides semantic understanding and video intelligence through their LLM + VLM (Vision Language Model) approach. It can analyze video content, detect patterns, and generate structured insights.

**How we integrated it:**
- **Post-session analysis**: Users can optionally upload session recordings for deep analysis
- **Semantic understanding**: Extracts high-level insights from video (what the user was doing, when distractions occurred, patterns)
- **Long-term memory**: Stores behavioral patterns to build a personalized model over time
- **Pattern detection**: Identifies unusual behavior and trends (e.g., "You're consistently distracted in late afternoon")

**Why it matters:** Memories.ai helps build a **semantic memory** of the user's behavior, enabling the app to learn patterns and provide increasingly personalized guidance. It transforms raw video data into actionable insights.

**Implementation:**
```python
# Upload session for analysis
memories_job_id = self.memories_client.upload_session(
    session_id=session_id,
    cam_video=cam_video_path,
    screen_video=screen_video_path,
    snapshots=snapshot_files
)

# Get semantic insights
insights = self.memories_client.get_session_insights(
    job_id=memories_job_id
)
```

## Challenges & Learnings

### Biggest Challenge: Tech Stack Decisions

Throughout this project, we learned that **choosing the right tech stack is critical** when building applications, especially when AI and video processing are involved.

**Lessons learned:**
- **PyQt6 vs CustomTkinter**: We initially considered CustomTkinter but found PyQt6 offered better performance and native feel for a desktop application
- **Snapshot-based vs Full video streaming**: We chose snapshot-based analysis (60s intervals) over continuous video streaming for privacy, bandwidth, and cost reasons—critical decision
- **Local-first vs Cloud-first**: We designed a hybrid approach—snapshots to cloud for analysis, full video local—which balanced privacy with AI capabilities
- **Performance optimization**: Using OpenCV, MSS, and ffmpeg-python together requires careful threading to avoid blocking the UI

### Strategy Matters, Even in Vibe Coding

Despite AI coding assistants making it easy to generate code, we learned that **proper planning is still essential**:

- **PRD document was crucial**: Having a detailed product requirements document helped us make consistent decisions and avoid scope creep
- **Architecture first**: We spent time on architecture before coding—defining data models, API structure, and component boundaries
- **Phased development**: Breaking the project into phases (Core → Capture → AI → GUI → Post-processing) prevented chaos
- **Deep planning pays off**: Going in-depth on specifications (e.g., snapshot cadence, privacy model, cost structure) saved us from expensive pivots

## Future Improvements / Next Steps

Based on our PRD and current implementation, here are the planned enhancements:

### Phase 8: Google Calendar Integration
- **OAuth flow** for Google Calendar access
- **Auto-session start** based on calendar events
- **Task import** from calendar to know what user "should" be working on
- **Smart scheduling**: App learns optimal times for different types of tasks

### Phase 9: Packaging & Distribution
- **PyInstaller configuration** for macOS, Windows, Linux
- **Code signing**: Apple Developer Certificate (macOS), Authenticode (Windows)
- **Platform-specific installers**:
  - macOS: DMG with drag-and-drop install
  - Windows: MSI installer with Start Menu integration
  - Linux: AppImage or DEB package

### Phase 10: Testing & Refinement
- **Unit tests** for core components (state machine, fusion engine, database)
- **Integration tests** for session lifecycle and AI workflows
- **UI tests** using pytest-qt for GUI interactions
- **Performance tuning**: CPU/RAM optimization, battery efficiency

### Beyond MVP

**Enhanced Agentic Features:**
- **Smart break scheduling**: Automatically suggest breaks based on detected patterns (e.g., "You usually get distracted after 20 minutes—try 15-minute Pomodoros")
- **Proactive interventions**: Detect frustration spikes and suggest pre-distraction interventions
- **Calendar auto-scheduling**: If user consistently needs more time for tasks, app adjusts calendar estimates

**Advanced Personalization:**
- **Day-of-week patterns**: "You're 73% more focused on Mondays"
- **Task-type patterns**: "You maintain focus best during coding vs. documentation"
- **Environmental factors**: Correlate distraction with time of day, day of week, task type

**Community & Social Features:**
- **Anonymous pattern sharing**: Compare your patterns with others (privacy-preserving)
- **Focus leaderboards**: Gamification for sustained focus
- **Shared strategies**: "Users with similar patterns found X strategy helpful"

## Getting Started

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd focus-guardian

# 2. Set up Python environment (requires Python 3.13+)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Set up API keys in .env
cp .env.example .env
# Edit .env with your OpenAI, Hume AI, and Memories.ai API keys

# 5. Run the application
python -m focus_guardian.main
```

### Usage

1. **Start a Focus Session**: Click "Start Focus Session" in the app
2. **Work Normally**: The app captures periodic snapshots (every 60 seconds by default)
3. **Get Alerts**: If you're distracted for 2+ minutes, you'll receive a gentle notification
4. **Review Insights**: After session ends, view your focus ratio, distraction patterns, and recommendations

### Configuration

See `config/default_config.json` for customizable settings:
- Snapshot interval (default: 60 seconds, range: 10-120s)
- Video quality profiles (Low/Std/High)
- Alert sensitivity
- Focus analyzer settings

## Architecture Highlights

- **Snapshot-based detection**: Takes periodic images (60s intervals) and analyzes with OpenAI Vision API
- **K=3 hysteresis**: Requires 3 consecutive snapshots over 2+ minutes to confirm distraction (eliminates false positives)
- **Hybrid storage**: Snapshots uploaded for analysis, full video stays local
- **Modular design**: Separation of concerns (capture → analysis → state machine → UI)
- **Threading architecture**: UI thread stays responsive, background workers handle heavy processing

## License

[Your license here]

## Contact

**James Gui** - Los Angeles, CA  
**Hanson Wen** - Berkeley, CA

---

*Built with ❤️ for the ADHD community*

