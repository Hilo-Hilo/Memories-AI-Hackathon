# Product Requirements Document: ADHD Distraction Analysis Desktop Application

## Document Information

- **Product Name:** Focus Guardian - ADHD Distraction Analysis Desktop Application
- **Version:** 1.2 (Draft)
- **Date:** October 5, 2025
- **Author:** Hanson Wen

## Executive Summary

Focus Guardian is a **desktop application** designed to help individuals with ADHD monitor and reduce distraction episodes in real time. Using a device's camera, the app detects when a user loses focus or becomes distracted and provides gentle interventions to refocus attention. The system uses periodic snapshot analysis via OpenAI Vision API to detect distraction patterns, with full video recordings stored locally. Snapshot images (webcam and screen) are sent to OpenAI for classification during sessions. Post-session, users can optionally upload recordings to Hume AI for emotion analysis or Memories.ai for pattern analysis to personalize feedback and track progress over time. Optional integrations with calendar and email can enrich the app's understanding of the user's schedule and tasks, enabling proactive focus assistance. The ultimate goal is to create an **autonomous digital "coach"** that not only detects distractions but also helps users self-correct and build better focus habits, all through a minimally intrusive, battery-efficient **native desktop application** packaged with PyInstaller for easy distribution.

## Problem Statement

People with ADHD often struggle to maintain focus, especially in unstructured or remote work environments. Moments of distraction-whether daydreaming, fidgeting, or getting pulled into unrelated activities-can significantly reduce productivity and increase frustration. Traditional solutions like site blockers or timers address external distractions but **do not actively monitor the person's attention state**. There is a need for a personalized tool that can **recognize distraction as it happens** through behavioral cues (e.g. gaze aversion, screen content patterns) and gently guide the user back on track. Moreover, ADHD individuals benefit from external structure and feedback; however, constant human coaching is impractical. An automated, intelligent assistant that understands the user's goals and patterns could fill this gap. The solution must be privacy-conscious (many users are uncomfortable recording sensitive video/audio to the cloud) and easy to use (minimal setup, simple installation), running as a **native desktop application** on laptops and desktop computers people already use daily.

## Objectives & Success Metrics

**Primary Objectives:**
1\. **Pattern-Based Distraction Detection:** Accurately detect episodes of inattention or distraction via webcam video and screen content analysis, with 2-3 minute latency for high-accuracy pattern recognition.  
2\. **Timely Intervention:** Prompt the user with a subtle alert or cue when a distraction is detected, enabling them to self-correct quickly.  
3\. **Goal Alignment:** Assist the user in staying on task by importing their goals/calendar and breaking down tasks into manageable steps with automated tracking.  
4\. **Personalization:** Adapt to each user over time by storing **semantic and episodic memories** of their behavior (when they get distracted, emotional states, effective interventions) to provide personalized strategies.  
5\. **Emotion-Aware Feedback:** Leverage emotion recognition (via Hume AI) to gauge user frustration, stress, or boredom, and adjust interventions accordingly (e.g. if the user appears frustrated, the app might suggest a short break or a calming technique).  
6\. **Minimize Burden:** Ensure the solution is easy to set up (no complex configuration), runs as a native desktop application without significant impact on device battery or performance, and keeps all sensitive raw data local to alleviate privacy concerns.

**Success Metrics (KPIs):**
\- _Detection Accuracy:_ ≥90% of clear distraction events (e.g. user visibly looking away or leaving desk) are correctly identified, with minimal false alerts.
\- _User Focus Improvement:_ 25% reduction in average daily "off-task" time after 1 month of use (measured by length of detected distraction episodes).
\- _User Engagement:_ At least 70% of users continue using the app daily after 4 weeks, indicating sustained value.
\- _Personalization Efficacy:_ >80% of users report that the feedback/interventions feel "helpful and tailored" in post-use surveys.
\- _Performance:_ The app maintains snapshot analysis (60-second intervals with 2-3 minute pattern detection) on a typical laptop without exceeding 30% CPU usage on average, and with negligible impact on battery life (target <5% per hour).

## User Personas

**Persona 1 - "The Distracted Student":** _Alex, 20 years old,_ is a university student with ADHD. Alex struggles to stay focused during online lectures and self-study sessions. They often find themselves scrolling social media or staring off into space without realizing it. Alex needs a tool that can **alert them when they drift off-task** and help break study goals into smaller chunks. Privacy is a concern - they prefer not to have their webcam footage sent to cloud servers. Alex would use the app on their laptop while studying at home.

**Persona 2 - "The Busy Professional":** _Jordan, 35 years old,_ is a software developer with ADHD working remotely. Jordan juggles multiple projects and often gets **sidetracked by emails and notifications**. They want an assistant that integrates with their calendar to know what they _should_ be working on, and that can detect if they've gotten distracted (e.g. watching videos or getting up from the desk). Jordan appreciates data-driven insights, so an end-of-day report on when and why distractions happened would be valuable. They need the solution to be lightweight because they run many apps simultaneously and can't afford a performance drag.

## Use Cases & User Stories

- **Real-Time Focus Alert:** _As a user with ADHD, I want the app to alert me immediately when I lose focus (e.g. staring off or looking at my phone) so that I can quickly return to my task._
- **Goal/Task Management:** _As a user, I want to import my tasks or calendar events into the app so it knows what I intend to work on and can remind me of my goal if I get distracted._
- **Personalized Guidance:** _As a user, I want the app to learn my patterns (e.g. I often get distracted in mid-afternoon) and suggest proactive strategies (like scheduling a break or using the Focus mode at those times)._
- **Emotion-Sensitive Response:** _As a user, if I become frustrated or anxious, I want the app to recognize that and respond supportively (for example, not just telling me "get back to work" if I appear very upset, but perhaps suggesting a brief relaxation exercise)._
- **Privacy Transparency:** _As a user, I want clear information about what data is sent to cloud services (periodic snapshots to OpenAI) and what stays on my device (full video recordings), so I can make informed decisions about using the app._

## Functional Requirements

### FR1. Distraction Detection (Snapshot-Based Vision Analysis)

The system shall **detect distraction patterns** using periodic snapshots from the user's webcam and screen. The detection approach uses K=3 hysteresis (analyzing 3 consecutive snapshots spanning 2 minutes) to ensure high accuracy and avoid false alarms from brief glances. Key behaviors to detect include:

- **Visual Inattention:** If the user's gaze or head turns away from the screen across multiple snapshots (sustained pattern over 2-3 minutes), the app flags a loss of focus. OpenAI Vision API analyzes webcam snapshots to detect: head orientation changes (>45° away from screen), eyes off-screen, or "absent" states where no face is visible.
- **Physical Absence:** Detect if the user leaves their workspace consistently across snapshots (e.g., no face detected in multiple consecutive frames spanning 2 minutes).
- **Phone Usage:** Identify when a user is holding or looking at a phone/mobile device in the webcam frame, confirmed across multiple snapshots.
- **Screen Content Distractors:** Analyze screen snapshots to detect distracting content: video streaming, social media feeds, gaming, or chat applications. The system differentiates between focus activities (code editors, documentation, terminals) and distraction activities (social feeds, videos, games).
- **Drowsiness/Fatigue:** If video analysis shows signs of drowsiness (e.g. eyes closed, drowsy expression) across multiple snapshots, the app flags this since fatigue leads to distraction. This serves as an early warning that the user is no longer effectively focusing.

**Detection Latency:** The hysteresis approach (K=3 snapshots with 60-second intervals) means confirmed distraction alerts appear 2-3 minutes after distraction begins. This is a deliberate design choice to eliminate false positives - brief glances or momentary distractions don't trigger alerts, only sustained pattern changes.

When a distraction pattern is detected, the app timestamps the event and classifies it with specific labels (e.g., "HeadAway", "SocialFeed", "VideoOnScreen"). **Snapshot images are uploaded to OpenAI Vision API for analysis; full video recordings stay local** unless the user enables optional post-session cloud processing.

**Alert Mechanism:** Upon detecting a likely distraction that lasts more than a brief threshold (configurable, e.g. >5-10 seconds to avoid false alarms), the app provides feedback. This could be a gentle audio chime or a desktop notification saying "Refocus on task X". The alert should be configurable (some users may prefer a subtle visual nudge vs. a sound). The app should also allow a short grace period; for example, if the user quickly regains focus, an alert might be skipped to avoid annoyance. Additionally, if the user explicitly _pauses_ the monitoring (say they intentionally take a break), alerts are suppressed.

### FR2. Goal Management and Agentic Assistance

The system shall incorporate features of an **intelligent productivity assistant** to help users set goals and stay on track:

- **Task/Calendar Import:** Users can connect their calendar (Google Calendar, Outlook, etc.) or task management tool to the app (optional integration). This allows the app to know the user's schedule and current tasks. For instance, if the user's calendar says "9:00-11:00 Project Work on Report", the app will treat "Report project" as the focus goal during that window. Calendar integration is optional, but when enabled, the app can automatically start a focus session when a calendar event labeled as work/study is active. Similarly, importing tasks (via an API or file) can help the user select a task or goal for an ad-hoc focus session. _(If integration is not set up, the user can manually input or select their current task within the app UI.)_
- **Goal Decomposition:** The app should assist users in breaking down big goals into smaller sub-tasks. For example, if Alex sets a goal "Finish writing essay", the system (optionally using an AI agent) can suggest sub-tasks like "1) Outline the essay, 2) Write introduction, 3) Draft main sections, 4) Proofread final draft". Research indicates that AI (like ChatGPT) can effectively help break tasks into manageable steps and provide real-time feedback[\[2\]](https://link.springer.com/article/10.1007/s44230-025-00099-1#:~:text=In%20the%20same%20line%2C%20Medghalchi,55). The app may utilize a prompt-based approach (leveraging an LLM via API) to decompose a user's goal when asked. These steps can then appear in the UI as a checklist, and the distraction monitoring can track progress (e.g., if a step is expected to take 30 minutes, and the user is on step 1 but repeatedly distracted, the system knows to possibly extend the focus time or suggest splitting further).
- **Agentic Self-Correction:** The assistant should exhibit _agentic behavior_ in helping the user stay on course. This means beyond just alerting, it can take initiative to adjust the plan. For instance, if repeated distractions are detected on a particular task, the system might ask: "Is this task too difficult or causing stress? Should we break it down or schedule a short break?" If a user runs over the allocated time for a task (from calendar or user input), the system might automatically reorganize the schedule (with user permission), pushing meetings or sending a notification that the current task needs more time. This essentially makes the app a smart coach that not only tracks tasks but can suggest corrections: **auto-rescheduling, reminders to return to task after break, or recommending focus techniques** (like the Pomodoro technique if the user is consistently distracted after ~20 minutes).
- **Progress Tracking:** The app will automatically log time spent on each task vs. distracted, giving the user a real-time view of progress. For example, "Writing Report - focused 40 min, distracted 5 min" might be displayed. If integrated with a task manager, the app can mark tasks complete or update progress status once finished (with user confirmation). The user can also manually correct or annotate sessions (e.g., "I was interrupted by a phone call here"). This data feeds into the personal Memory (FR4).

### FR3. Post-Session Emotion Intelligence (Hume AI Integration)

To better understand emotional patterns that drive distraction, the app offers **optional post-session emotion analysis**. After a focus session ends, the recorded webcam video can be uploaded to **Hume AI's Expression API** for detailed emotion timeline analysis. Hume AI's models measure "hundreds of dimensions of human expression" across facial expressions[\[3\]](https://dev.hume.ai/intro#:~:text=Hume%E2%80%99s%20state,in%20audio%2C%20video%2C%20and%20images), detecting nuanced emotional states like frustration, confusion, boredom, and engagement level.

**Functionality:**
\- **Post-Session Upload:** After a session ends, the user can choose to upload the webcam recording (cam.mp4) to Hume AI for emotion analysis. This is entirely optional and requires explicit user consent each time.
\- **Emotion Timeline Generation:** Hume AI processes the video and returns a 1Hz emotion timeline showing how emotions like frustration, boredom, stress, and concentration fluctuated throughout the session.
\- **Correlation Analysis:** The system correlates emotion spikes with distraction events. For example: "Your frustration increased 5 minutes before each distraction event" or "Boredom levels peaked during documentation tasks".
\- **Actionable Insights:** The final session report includes emotion-aware recommendations like: "Frustration often precedes distraction for you. Try scheduling 2-minute breaks when you feel frustrated" or "Boredom detected during repetitive tasks - consider using the Pomodoro technique for these".

**Privacy and Control:**
\- Users maintain full control - they can review each session and decide whether to upload for emotion analysis
\- Video is only sent to Hume if explicitly approved
\- Raw emotion data is stored securely and only the user can access it
\- Users can delete any uploaded emotion analysis data at any time

**Performance Consideration:** Since emotion analysis happens post-session, there's no real-time bandwidth consumption or latency impact during focus sessions. The Hume AI processing typically completes within 5-10 minutes after upload, generating comprehensive insights without interrupting the user's workflow. All calls to Hume use the desktop application with Hume's Python SDK and API keys stored encrypted in local configuration files.

### FR4. Semantic & Episodic Memory (Personalization via Memories AI)

The application shall maintain a **long-term memory** of user behavior to enable personalization. This includes recording _episodic data_ (timestamped events like distractions, focus sessions, task completions) and _semantic data_ (general knowledge about user's preferences, patterns, and effective strategies). The integration with **Memories AI** (or a similarly purposed "memory" service) will be used to store and analyze these behavior logs over time:

- **Data Stored:** Only **high-level analytic results** and metadata are stored in the cloud memory. This includes entries like: "10/5/2025 2:30pm - Distracted for 3 minutes (looked away, emotion: bored)" or "10/6/2025 9:00am-10:00am - Focus session on Project X, 2 alerts issued, user stayed on task 85% of time". Raw video or audio is **never stored** in this memory database; the focus is on the _what, when, how long,_ and _possible why_ of distraction events. Additional context such as the task in focus, time of day, and user's emotional state (from FR3) at the time are included to enrich the data.
- **Memories AI Platform:** The Memories AI integration provides a scalable **behavioral data lake** to accumulate these events. Over time, this yields a timeline of the user's focus patterns. The system can run analysis to find patterns - e.g., "The user is frequently distracted in the late afternoon" or "When working on coding tasks, the user rarely gets distracted, but when writing documentation, distractions spike." The platform's semantic layer can help cluster similar episodes or triggers. (If using the Memories.ai service, it might offer built-in analytics for unusual behavior detection or trend analysis[\[4\]](https://memories.ai/solution#:~:text=solution%20,layer%20makes%20all%20video)[\[5\]](https://memories.ai/solution#:~:text=It%20can%20detect%20unusual%20behavior%2C,layer%20makes%20all%20video), which we can leverage for pattern mining).
- **Personalized Insights:** Using the stored data, the app will periodically (say weekly) generate a summary for the user: _e.g., "This week, your average focus duration was 25 minutes, after which you tended to get distracted. Distractions often happened when you were doing Task A, typically around 3 PM. You seemed most focused during 10-12 AM. Compared to last week, you improved your focus time by 15%. Triggers for distraction noted: incoming emails (3 times), phone notifications (2 times)."_ These insights help the user adjust their habits (maybe scheduling tougher work in the morning, or turning off notifications in the afternoon).
- **Adaptive System Behavior:** The app uses the memory data to adjust its own behavior. For example, if it "knows" a user usually struggles on Mondays, it might proactively activate a stricter focus mode on Mondays (with more frequent check-ins). If a user responds poorly to a certain type of alert (e.g., they always dismiss it and remain distracted), the system can try a different approach (perhaps a different alert style or message). Essentially, the app treats past interactions as training data to refine its coaching strategy per individual.

All personal data in this memory is stored securely (likely under the user's account with encryption). If using a third-party service (Memories.ai), we will use their API to store/retrieve data, ensuring compliance with privacy (the data stored is already abstracted, but even so, it should be protected and only accessible to the user). The user may be given controls to view and delete their recorded "memories" at any time, maintaining transparency.

### FR5. Minimal Setup & Desktop Application UX

The product is delivered as a **native desktop application** packaged with PyInstaller - meaning the user can download and install it like any standard application, with **no special hardware or complicated configuration**. Key requirements for the UX and setup include:

- **Onboarding:** The first time user experience will guide the user through granting camera access permissions. It will clearly explain how the system works: "We capture periodic snapshots (every 60 seconds) from your camera and screen to detect distraction patterns. **Snapshot images are sent to OpenAI Vision API for analysis**. Full video recordings stay on your device unless you choose to upload them for optional post-session emotion analysis." The onboarding also asks if the user wants to connect their calendar or task manager (optional, can be skipped). If they choose to, a secure OAuth flow to Google, Microsoft, etc., is provided. The goal is to make initial setup doable in minutes. Default settings will work out-of-the-box (e.g., some default alert settings and working hours), which the user can later customize. On macOS, the app will request necessary permissions through system dialogs.
- **UI Design:** The interface will be clean and minimal to avoid being a distraction itself. Likely there will be a **dashboard screen** that shows: current focus session or task, a timer or progress indicator, and maybe an icon indicating monitoring is ON. There may be a small status like "🔵 Focus mode active" or "🟡 Break (monitoring paused)". When an alert triggers, it might display as a system notification or small overlay window rather than a jarring popup. The color scheme and visuals should be calming (avoiding bright reds or alarming designs, as the aim is supportive). Battery and CPU efficiency considerations mean using native UI frameworks (CustomTkinter, PyQt, or Tkinter) with minimal animations and efficient rendering.
- **Cross-Platform Support:** The desktop application will support macOS, Windows, and Linux through PyInstaller packaging. The primary use case is desktop/laptop computers where users typically do their focus work. Each platform will have a native installer (DMG for macOS, MSI/EXE for Windows, AppImage/DEB for Linux). Platform-specific features (like system tray integration or native notifications) will be implemented using conditional imports and platform detection.
- **Battery/CPU Optimizations:** The app will implement numerous optimizations to remain lightweight:
- Utilizing **optimized Python libraries** for video processing to leverage native performance. Critical algorithms (face landmark detection via MediaPipe, eye gaze estimation) run as compiled C++ extensions through libraries like OpenCV and MediaPipe, achieving real-time performance without excessive CPU usage.
- Adaptive frame rate processing: if the app detects high CPU or battery drain, it can reduce how often it samples video frames (e.g., processing 1 frame per second when idle, ramping up to 5 fps during active focus sessions). Many distraction cues don't require 30fps full motion analysis - a lower frequency can suffice to catch most issues, thereby saving power.
- Use of Threading: all heavy computations (video frame analysis, emotion API calls) will run in background threads using Python's threading or multiprocessing modules, so the UI thread remains free and the application stays responsive.
- Graceful degradation: On older devices that cannot handle local video analysis well, the app could detect this and offer an alternative (such as more reliance on cloud analysis, if the user permits, or limiting features like turning off emotion analysis).
- **Security & Privacy UX:** Clearly communicate privacy features in the UI. For example, have an indicator showing when snapshots are being captured and uploaded (like a small camera icon that the user can click to see "Snapshot captured and sent to OpenAI Vision API for analysis. Full video recording stored locally."). Also allow users to easily pause or stop monitoring at any time (maybe a big "Pause" button), giving them control. This transparency will build trust, which is crucial for an app that has camera access.

### FR6. Optional Integrations (Calendar, Email, etc.)

While not core to the MVP, the system may support additional integrations to enhance functionality:

- **Calendar Integration:** (Optional) As described in FR2, connecting a calendar helps the app contextualize the user's focus sessions. In addition to import, if given write access, the app could automatically create calendar entries for focus sessions or distraction logs (e.g., log "Focus Session - 45 min" on the calendar for self-tracking). This integration should use standard APIs (Google Calendar API, Microsoft Graph for Outlook) and adhere to least privilege (only reading events and writing focus logs if user enables that feature). The PRD treats this as an enhancement: it's highly useful but the app should still function without it (user manually inputs their current goal).
- **Email Integration:** (Optional) An idea is to integrate with email (e.g., Gmail or Outlook) to both manage distractions and gather context. For example, the desktop app could detect when the user alt-tabs to check email during a focus session and count that as a distraction (using cross-platform window monitoring libraries like pygetwindow or platform-specific APIs). On the other hand, email could be a source of tasks: the app might parse flagged emails or to-dos from email content to suggest tasks to focus on. Due to complexity, email integration is considered a future enhancement and would need careful privacy handling (accessing email content might be sensitive).
- **Other Productivity Tools:** (Future Consideration) Integration with project management tools (Trello, Asana, etc.) or note-taking apps could deepen the system's knowledge of what the user should be doing. These are beyond the current scope but can be kept in mind for extensibility. The architecture should allow adding new integrations without major overhaul (perhaps via plugin-like modules that feed the goal/task system).

**Note:** Both calendar and email integrations require user authentication into third-party services and should use industry-standard OAuth flows. They are optional - the app's core loop (monitor distraction, alert user, log data) does not depend on them. If not connected, the user can manually specify their focus periods or rely on default work hour settings.

## Non-Functional Requirements (NFRs)

- **NFR1: Privacy & Data Security:** The system transmits **periodic snapshot images** (webcam and screen) to OpenAI Vision API for analysis during focus sessions. Full video recordings remain on the local device unless explicitly uploaded by the user for optional post-session emotion analysis (Hume AI) or pattern analysis (Memories.ai). All cloud-stored data will be limited to processed results, snapshot images, and metadata. Data in transit to cloud (e.g., snapshot uploads, emotion analysis calls) must be encrypted (HTTPS). In storage (databases), user data must be encrypted at rest. The user will have unique access to their data (protected by account login). We will comply with relevant privacy laws (e.g., GDPR) giving users rights to their data (export, deletion).
- **NFR2: Performance:** The distraction detection uses pattern-confirmed analysis with 2-3 minute latency (K=3 snapshots spanning 60+ seconds). This deliberate design choice eliminates false positives from brief glances. Individual snapshot processing should complete within 5 seconds (p95 latency for OpenAI Vision API call + analysis). The app should be optimized to use <500MB RAM and keep CPU usage low (target <30% on a typical 4-core CPU during active analysis). It should not noticeably slow down other applications. To maintain system health, if the app detects it is using too many resources (via performance APIs), it may auto-throttle or warn the user.
- **NFR3: Battery Efficiency:** Especially for laptop users on battery, the app should be thrifty. Utilizing device resources like GPU for video processing can be more power-efficient than pegging CPU. OpenCV and MediaPipe can leverage GPU acceleration when available. The app shall avoid continuous high-resolution processing; for example, analyzing a downsampled video stream (e.g., 320x240 px frames) is often sufficient for face detection and significantly reduces CPU load. If available, the app can make use of any OS-level optimizations or platform-specific ML accelerators (like CoreML on macOS, DirectML on Windows). The aim is that running the app for an hour uses only a small percentage of battery - achieving this will likely require tuning and possibly dynamic adjustment of processing intensity.
- **NFR4: Compatibility:** The desktop app must be compatible with modern operating systems (macOS 10.14+, Windows 10+, Ubuntu 20.04+). It should degrade gracefully if certain features aren't available. For instance, if GPU acceleration isn't available, the app might use CPU-only processing (with a possible hit to performance, but still functional). The app will detect platform capabilities at startup and adjust processing accordingly.
- **NFR5: Reliability:** The system should handle long-running sessions (e.g., 8+ hours of monitoring) without memory leaks or crashes. **Internet connectivity is required during focus sessions** for OpenAI Vision API snapshot analysis. The system should be resilient to brief connectivity issues: if the connection drops temporarily (<5 minutes), snapshots are queued locally and uploaded when connectivity restores. If connectivity is lost for extended periods (>5 minutes), the session should pause automatically and notify the user. The user interface should clearly show connectivity status and queue depth. Optional cloud features (Hume emotion analysis, Memories.ai uploads, calendar sync) can be deferred until connectivity is available.
- **NFR6: Security:** Follow best practices for desktop application security. All libraries used for the app should be well-audited to prevent vulnerabilities, especially since we are dealing with camera access. Store sensitive data (API keys, session recordings) using encrypted storage. The backend APIs will authenticate requests (the user will likely log in to the app, possibly using OAuth or our own account system, to tie their data to them). The system must also ensure that no one else can access the user's data - e.g., memory data is scoped per user account with proper auth checks. The PyInstaller bundle will be code-signed on macOS and Windows to ensure authenticity.
- **NFR7: Usability:** The app's interventions must be supportive, not punitive or overly distracting themselves. We will follow UX guidelines for assistive tech - for example, allow the user to adjust alert frequency or turn off certain types of nudges. The user retains ultimate control (they can snooze the assistant if needed). The interface will be simple to navigate, with clear terminology (avoid technical jargon in user-facing text). We will gather some user feedback in testing to ensure the prompts and summaries are actually helpful and not guilt-inducing.
- **NFR8: Extensibility:** The architecture should allow adding new detection methods or integrations. For example, if later we want to incorporate keystroke or mouse activity as additional signals of distraction, the system's modular design should accommodate plugging in another module (using libraries like pynput for cross-platform input monitoring). Similarly, if alternative emotion recognition or memory services are to be supported, it should be relatively easy to swap those in (abstract the API calls behind interfaces).
- **NFR9: Cost Transparency:** The system uses cloud AI services with associated costs that users should understand upfront. The application will provide cost estimates before starting sessions and track actual spending throughout use.

### Cost Model

The system uses three main cloud services, each with distinct cost structures:

**OpenAI Vision API (Required During Sessions):**
- Cost per snapshot: ~$0.01 (using "low" detail mode)
- Snapshots per session: (duration_minutes × 60 / interval_seconds) × 2 (cam + screen)
- Standard 2-hour session (60s intervals): 120 snapshots × 2 × $0.01 = $2.40

**Hume AI Expression Analysis (Optional Post-Session):**
- Cost: ~$0.50 per 2-hour video analysis
- User chooses whether to upload after each session
- Estimated monthly (20 sessions with emotion analysis): $10

**Memories.ai Video Analysis (Optional Post-Session):**
- Cost: ~$1.00 per 2-hour session (video upload + VLM analysis)
- User chooses whether to upload after each session
- Estimated monthly (20 sessions with full analysis): $20

**Quality Profile Cost Trade-offs:**

| Profile | Interval | Snapshots/2hr | Cost/2hr | Accuracy | Use Case |
|---------|----------|---------------|----------|----------|----------|
| High Frequency | 30s | 240 | $4.80 | Highest | Critical focus sessions |
| Standard | 60s | 120 | $2.40 | Balanced | Daily work sessions |
| Economy | 90s | 80 | $1.60 | Good | Long sessions, budget-conscious |

**Monthly Cost Estimates (20 work sessions @ 2hr each):**
- Minimum (Standard quality, no optional features): $48/month
- Typical (Standard quality + occasional emotion analysis): $58/month
- Maximum (High frequency + all features): $144/month

**Cost Control Features:**
- Adjustable snapshot frequency (30s - 120s)
- Session-based estimates before starting
- Real-time cost tracking in UI
- Monthly spending reports
- Optional cost caps with auto-pause

## Detection Label Taxonomy

To ensure consistency across all system components, this section defines the canonical set of detection labels used throughout the application. All documentation, code, and API integrations reference these exact labels.

### Webcam Labels (Camera Snapshot Analysis)

| Label | Description | Confidence Threshold | Category |
|-------|-------------|---------------------|----------|
| `HeadAway` | Head turned >45° from screen | 0.7 | Distraction |
| `EyesOffScreen` | Gaze not directed at screen | 0.7 | Distraction |
| `Absent` | No person visible in frame | 0.8 | Absence |
| `MicroSleep` | Eyes closed, drowsy appearance | 0.7 | Distraction |
| `PhoneLikely` | Phone visible in hand or being viewed | 0.75 | Distraction |
| `Focused` | Engaged posture, eyes on screen | 0.6 | Focus |

### Screen Labels (Screen Content Analysis)

| Label | Description | Confidence Threshold | Category |
|-------|-------------|---------------------|----------|
| `VideoOnScreen` | Video player or streaming content (YouTube, Netflix, etc.) | 0.7 | Distraction |
| `SocialFeed` | Social media feed scrolling (Twitter, Instagram, Facebook, LinkedIn, TikTok) | 0.75 | Distraction |
| `Code` | Code editor or IDE (VS Code, PyCharm, Sublime, JetBrains, Vim) | 0.7 | Focus |
| `Docs` | Documentation, technical reading, wikis, API docs | 0.65 | Focus |
| `Email` | Email client (Gmail, Outlook, Apple Mail) | 0.6 | Borderline* |
| `VideoCall` | Video conferencing UI (Zoom, Meet, Teams, FaceTime) | 0.7 | Borderline* |
| `Reading` | Long-form reading (ebooks, PDFs, news articles, NOT code docs) | 0.65 | Focus |
| `Slides` | Presentation software (PowerPoint, Google Slides, Keynote) | 0.7 | Focus |
| `Terminal` | Command line terminal or shell | 0.75 | Focus |
| `ChatWindow` | Chat/messaging applications (Slack, Discord, WhatsApp, iMessage) | 0.7 | Distraction |
| `Games` | Gaming applications or entertainment software | 0.8 | Distraction |
| `MultipleMonitors` | Multiple windows visible, context switching | 0.6 | Borderline* |
| `Unknown` | Cannot determine content type | 0.5 | Neutral |

**Note on Borderline Categories:**
- `Email`: Context-dependent - inbox processing = focus, frequent checking = distraction
- `VideoCall`: Work meeting = focus, social call = distraction (requires additional context)
- `MultipleMonitors`: Single focus window = acceptable, rapid switching = distraction

### Label Hierarchy and Precedence

When multiple labels are detected in a single snapshot:

1. **Camera labels take precedence for attention state:**
   - If `Absent` or `MicroSleep` detected → ABSENT state (highest priority)
   - If `HeadAway`, `EyesOffScreen`, or `PhoneLikely` detected → DISTRACTED state
   - If `Focused` detected → proceed to screen analysis

2. **Screen labels provide distraction type specificity:**
   - Combined with camera distraction → specific distraction type (e.g., "HeadAway + VideoOnScreen" → "Distracted watching video")
   - Standalone screen distraction → lower confidence distraction
   - Focus labels + focused camera → FOCUSED state

3. **Confidence aggregation:**
   - Multiple distraction labels increase overall distraction confidence
   - Conflicting labels (e.g., "Focused" + "VideoOnScreen") → use hysteresis voting across K=3 snapshots

### Usage Throughout System

- **OpenAI Vision API prompts:** Use these exact label names in classification prompts
- **Database schema:** Store as enum types matching these labels
- **State machine:** Reference these labels for transition logic
- **UI display:** Show user-friendly versions (e.g., "Head turned away" for `HeadAway`)
- **Reports:** Use these labels for distraction type classification
- **Analytics:** Aggregate statistics by these label categories

## Technical Architecture

The system uses a **snapshot-based cloud vision API approach** with local video recording. The architecture prioritizes pattern-confirmed accuracy over instantaneous detection, using K=3 hysteresis voting to eliminate false positives. **Session Report Schema:** v1.3 (includes vision_votes and snapshot_refs fields for post-session analysis reconciliation).

### Runtime Topology

**Realtime (On-Device + Network Active):**
- Session start immediately initiates two continuous recordings: cam.mp4 (webcam) and screen.mp4 (screen), running end-to-end for the entire session
- Snapshot scheduler captures still images at developer-configurable cadence (default: every 60s) from both sources:
  - cam_snapshot_YYYYmmdd_HHMMSS.jpg
  - screen_snapshot_YYYYmmdd_HHMMSS.jpg
- Each snapshot uploads in realtime to OpenAI Vision API for image-only inference (no audio). Results are cached locally and used for live nudges
- Network activity is continuous per snapshot cadence
- All media and inferences are written to per-session folders

**Post-Processing (End of Session, Cloud Jobs):**
- Inputs: cam.mp4, screen.mp4, and all snapshots
- Upload targets: Hume AI (video expression tracks over cam.mp4) and Memories.ai (session assets for segmentation/LLM+VLM analysis)
- Outputs: merged session_report.json persisted in SQLite and optionally synced

### Local Folder Layout (Per Session)

```
sessions/<session_id>/
  cam.mp4
  screen.mp4
  snapshots/
    cam_*.jpg
    screen_*.jpg
  vision/
    cam_*.json
    screen_*.json
  logs/
    runtime.log
    uploads.log
```

### Snapshot-Based Detection Pipeline

**Sources:** Webcam frames, screen frames. Audio is disabled.

**Continuous Recording:** MP4/H.264 for cam and screen from t0→t1 without gaps.

**Snapshot Cadence:** Developer-tunable SNAPSHOT_INTERVAL_SEC (default 60; min 10). Implementation uses wall-clock scheduler independent of frame rate.

**Inference:** Each snapshot → OpenAI Vision API → JSON result saved to vision/ and inserted into SQLite.

**Detection Classes (Image-Only):** {HeadAway, EyesOffScreen, Absent, MicroSleep, PhoneLikely, VideoOnScreen, SocialFeed, Code, Docs, Slides, Terminal, ChatWindow, Games, Unknown}

**Fusion:** Hysteresis over last K snapshots (default K=3) with ≥1 minute span debounce → emits focus_event/distract_event with reason codes. No audio heuristics.

**Performance Budgets:** CPU avg <30%; RAM <500 MB; snapshot upload rate bounded by SNAPSHOT_INTERVAL_SEC and backoff on 429/5xx.

### Storage, Privacy, and Controls

**Privacy Model:** No raw frames leave device except snapshots explicitly uploaded to OpenAI Vision API by design. Full video recordings remain local unless user chooses post-session upload.

**Developer Settings (Protected Panel or .env/yaml):**
- SNAPSHOT_INTERVAL_SEC
- VIDEO_BITRATE_KBPS_CAM, VIDEO_BITRATE_KBPS_SCREEN
- VIDEO_RES_PROFILE ∈ {Low, Std, High}
- OPENAI_VISION_ENABLED (default: true, developer-only toggle)
  - If enabled: Snapshots sent to OpenAI Vision API (normal operation, required for distraction detection)
  - If disabled: System falls back to local CNN classifier (reduced accuracy, no cloud dependency during sessions)
  - Note: Fallback mode must be implemented for graceful degradation when OpenAI Vision is unavailable
- MAX_PARALLEL_UPLOADS

**User-Visible Controls:** Pause monitoring; Sensitivity slider; Screen-capture toggle. No user toggle for OpenAI Vision (developer settings only).

### Tech Stack

**Desktop Application:**
- **GUI Framework:** CustomTkinter or PyQt6 for cross-platform UI
- **Recording:** ffmpeg-python or OpenCV VideoWriter with H.264 codec; developer-settable bitrates via env/yaml (VIDEO_BITRATE_KBPS_*)
- **Realtime Inference:** OpenAI Vision API (image classification) per snapshot; retry with exponential backoff; local JSON cache
- **Screen Capture:** mss (Python MSS) for fast screen grabbing
- **Threading:** Uploader worker pool (MAX_PARALLEL_UPLOADS) separate from capture threads to avoid blocking
- **Config:** .env or config.yaml; developer mode reveals advanced toggles in UI
- **Local Storage:** SQLite for structured data (sessions, events, KPIs) and filesystem for recordings

**Optional Cloud Features:**
- **Memories.ai:** Upload assets + snapshots via requests library; invoke Chat API with schema prompt; poll job status; fetch JSON response
- **Hume AI:** Video expression endpoint via Hume Python SDK; poll job status; fetch 1 Hz emotion tracks
- **Backend API:** Python with FastAPI for optional cloud sync features

**Packaging & Distribution:**
- PyInstaller for creating standalone executables
- Platform-specific installers: create-dmg (macOS), Inno Setup/WiX (Windows), AppImage/fpm (Linux)
- Code signing: Apple Developer Certificate (macOS), Authenticode certificate (Windows)

### Network and Bandwidth

**Network During Sessions:** Required for snapshot uploads to OpenAI Vision; sustained outbound traffic at interval cadence.

**Encryption:** HTTPS/TLS for all snapshot uploads; signed URLs for post-processing artifact transfers.

**Bandwidth Caps:** Enforce per-session cap; pre-flight estimate based on snapshot count × JPEG avg + video bitrate × duration; adaptive JPEG quality to remain within cap.

**Retention:** Raw cam.mp4/screen.mp4 and snapshots deleted after successful Memories/Hume merge if Auto-delete enabled; retention window configurable (0/24h/7d).

## Risks & Open Issues

- **Accuracy vs. False Alarms:** Tuning the distraction detection to be sensitive enough but not overly sensitive will be challenging. If the app misidentifies normal behavior (e.g., briefly glancing at notes or looking away in thought) as a distraction too often, users will get annoyed and may quit using it. We will need to refine algorithms and possibly allow user calibration (maybe an initial calibration session to learn what "focused" looks like for that user, or adjustable sensitivity sliders). Using proven models (like eye gaze tracking) should help, but individual differences exist. We might mitigate this by starting with conservative alerts (only alert on clear-cut cases) and then gradually getting more proactive as trust is built.
- **User Comfort and Consent:** Having a camera watch you can itself _feel_ distracting or intrusive for some. Even though we handle privacy well, some users might be uncomfortable knowing they are being recorded (even locally). Clear communication and the ability to **turn off the camera at any time** is essential. We also ensure that if camera is off, the app gracefully degrades (perhaps just doing audio-based limited monitoring or only tracking tasks without live feedback). User workshops or testing could inform how to make the experience more comfortable (maybe using avatars or animations to indicate the AI "coach" presence instead of a feeling of being surveilled).
- **Integration Complexity:** Calendar and email integrations, if enabled, have to handle various user contexts and errors (auth tokens expiring, conflicting events, etc.). Since these are optional, it's acceptable if initially they are somewhat basic (e.g., only Google Calendar supported in MVP). We note the risk that these can consume development time without being core to the prototype; hence they are scoped as stretch goals.
- **Performance on Different Devices:** There's variability in user hardware. On a high-end PC, everything might run smoothly, but on an older laptop or a budget tablet, real-time video analysis could lag. We plan to test on a range of devices and provide settings to reduce load. If necessary, we may use a simpler detection method for low-end devices (e.g., just detect face presence and large movements, skipping fine gaze tracking). Ensuring wide compatibility is a risk but manageable with feature scaling.
- **Third-Party Dependency Reliability:** Our solution relies on Hume AI and possibly Memories AI. If these services have downtime or change their API, it could affect our app. To mitigate, we will implement graceful fallbacks - e.g., if Hume is unreachable, the app continues without emotion input (and maybe informs the user that emotion features are temporarily unavailable). For Memories AI, if not using it, we can rely on our own DB. Essentially, the core loop doesn't break if those services fail; only some enhanced features do. We also should consider cost: Hume API calls might incur cost per request, which could become expensive if done too frequently. We will limit usage to stay within a free tier or a predictable budget.
- **Recording Compatibility:** Ensuring MP4/H.264 codec support across all platforms via OpenCV and ffmpeg-python is critical. We will implement fallback mechanisms to platform-specific codecs if the default encoding fails, ensuring sessions can always be recorded even on systems with limited codec support.
- **Upload Size/Time:** Long focus sessions can produce large video files (potentially GBs for multi-hour sessions), which may take significant time to upload. We will enforce per-session file size caps, implement chunked uploads with resumable transport to handle network interruptions, and expose upload progress with estimated time remaining (ETA) to manage user expectations.
- **OpenAI Vision / Memories / Hume API Quotas:** All external APIs have rate limits and quotas. We will enforce sampling rates and quality profile presets to stay within limits, implement exponential backoff when receiving 429 (rate limit) responses, and queue jobs when quotas are temporarily exhausted to ensure graceful degradation rather than hard failures.
- **LLM Hallucination in Post-Processing:** When using Memories.ai Chat API or other LLM-based analysis for generating session reports, there's risk of hallucinated or inaccurate inferences. We will constrain outputs with strict JSON schema validation, add confidence scoring per field, and surface uncertainty indicators to users when the system's confidence is low, preventing misleading recommendations.

## Hackathon Demo Script

This section provides a tested 5-minute demo narrative that showcases the product's key features and emotional impact for hackathon judges.

### Demo Narrative (5 Minutes)

**Minute 0-1: The Problem (Personal & Relatable)**

"Hi, I'm [name], and I have ADHD. When I sit down to work, I start with great intentions. But 20 minutes later, I realize I've been scrolling Twitter without even noticing the transition. By the time I catch myself, my focus is gone and my productivity is shot.

Traditional tools like website blockers don't work because they don't understand *me* - they don't know when I'm actually focused vs. when I'm vulnerable to distraction. I need something that watches my patterns and catches me before I fall down the rabbit hole.

That's why we built Focus Guardian."

**Minute 1-2: The Solution (Live Demo)**

"Let me show you how it works. I'm going to start a focus session - my goal is to work on this presentation."

[Start session in app]
[UI shows: "Focus mode active - Working on presentation"]

"For the next 2 minutes, watch what happens..."

[30 seconds: Actually work on slides, typing, focused]
[Then casually switch to Twitter, scroll for ~90 seconds]

[Alert notification appears]: "**Distraction Detected:** Social feed - 3 minutes"

"See that? The system detected I switched from focused work to distraction. It took 2-3 minutes to confirm this wasn't just a brief glance - it's a real distraction pattern. That's deliberate - we use K=3 hysteresis to avoid false alarms."

[Click back to work]

**Minute 2-3: The Intelligence Layer (Report Walkthrough)**

[End session, show report]

"Now here's where it gets interesting. This isn't just a simple tracker - it's an intelligence system."

[Point to session report on screen]:

```
Session Report - 10 minutes
├─ Focus ratio: 70%
├─ Distractions detected: 1 event
│  └─ Type: Social media (Twitter)
│  └─ Duration: 3 minutes
│  └─ Detected at: 14:32
└─ Pattern Analysis:
   └─ Screen content: SocialFeed (confidence: 0.92)
   └─ Camera: EyesOffScreen → Focused (returned after alert)
```

"The system knows not just *that* I got distracted, but *how* - it saw the social media feed on my screen and tracked when I looked away from productive work."

**Minute 3-4: The Emotional Intelligence (The Wow Moment)**

[Show emotion analysis timeline if available]:

"But here's the really powerful part. After the session, I can optionally upload the video for emotion analysis."

[Show Hume AI emotion timeline graph]:

```
Emotion Timeline:
Frustration ████░░░░░░░░ (peaks at 14:30, then drops)
Boredom     ░░░░░░██████ (rises during distraction)
Focus       ██████░░░░░░ (high, then drops)
```

"Look at this - my frustration spiked 2 minutes *before* I got distracted. I didn't even realize I was frustrated. The AI caught the pattern: frustration → distraction. That's the trigger.

Over time, Focus Guardian learns these patterns for each person. Maybe for you it's boredom, not frustration. Maybe it's time of day. The system adapts."

**Minute 4-5: The Long-Term Vision & Impact**

"After a week of using this, here's what the system told me:"

[Show weekly insights]:

```
Weekly Patterns:
• You're most vulnerable to distraction at 3-4pm
• Trigger: Frustration peaks before 73% of distractions
• Your average focus bout: 22 minutes
• Recommendation: Schedule 5-minute breaks at 2:55pm daily
```

"This is personalized coaching based on *my actual behavior*, not generic productivity advice.

The technical approach is snapshot-based vision AI - we capture webcam and screen images every 60 seconds, send them to OpenAI's Vision API for classification, then use hysteresis voting to confirm patterns. Post-session, Hume AI provides emotion analysis. It's privacy-conscious: snapshots are analyzed, not continuous video streams."

**The Closing (30 seconds):**

"Focus Guardian doesn't just tell you you're distracted - it understands *why* you get distracted, *when* you're most vulnerable, and *how* to help you build better habits.

For people with ADHD like me, that's life-changing.

**It knows me better than I know myself.**"

[End with product name + tagline on screen]

### Demo Preparation Checklist

**Technical Setup:**
- [ ] Pre-record a backup video demo in case live demo fails
- [ ] Test OpenAI Vision API connectivity and latency
- [ ] Prepare a sample session report with realistic data
- [ ] Have Hume emotion timeline graph ready (can be pre-generated)
- [ ] Test camera permissions on presentation laptop
- [ ] Ensure Twitter/social media is accessible for live demo

**Content Setup:**
- [ ] Prepare presentation slides to "work on" during demo
- [ ] Have Twitter open in another tab for easy switch
- [ ] Practice the 2-3 minute timing for distraction detection
- [ ] Rehearse the emotion timeline explanation (most impactful moment)

**Backup Plans:**
- [ ] If API fails: Use pre-recorded demo video
- [ ] If emotion analysis unavailable: Focus on snapshot detection
- [ ] If timing is off: Have pre-generated alerts ready to trigger

### Judge Q&A Preparation

**Expected Questions:**

Q: "What if I just want to check something quickly? Won't it flag that as distraction?"
A: "Great question! That's why we use K=3 hysteresis - it needs 3 snapshots over 2+ minutes to confirm distraction. Quick checks don't trigger alerts."

Q: "Isn't this expensive with all the API calls?"
A: "We're transparent about costs: ~$2.40 for a 2-hour session at standard quality. Users can adjust frequency to control costs. For hackathon, we're showing the technical feasibility; production could include subscription pricing."

Q: "Privacy concerns - you're uploading camera snapshots?"
A: "Yes, we're honest about this: periodic snapshots go to OpenAI for analysis. Full video stays local. Users control post-session uploads. We chose transparency over misleading 'fully private' claims."

Q: "Why 2-3 minutes latency? Can't you do it faster?"
A: "We could, but we deliberately chose accuracy over speed. Brief glances shouldn't trigger alerts. The 2-3 minute window eliminates false positives and feels supportive, not punitive."

Q: "What makes this better than existing productivity apps?"
A: "Three things: 1) Understands *your* specific patterns, not generic rules, 2) Correlates emotions with behavior - catches triggers, 3) Learns and adapts over time. It's personalized coaching, not just tracking."

### Technical Talking Points

**Architecture Clarity:**
- Snapshot-based pipeline (60s intervals)
- K=3 hysteresis voting for pattern confirmation
- OpenAI Vision API for real-time classification
- Post-session Hume AI for emotion analysis
- Local SQLite storage, optional cloud sync

**AI/ML Innovation:**
- Multi-modal analysis (camera + screen content)
- Temporal pattern recognition (hysteresis state machine)
- Emotion-behavior correlation
- Personalized learning from long-term data

**Production Readiness:**
- Cost model defined ($48-144/month depending on usage)
- Privacy model transparent (snapshot uploads disclosed)
- Cross-platform desktop app (PyInstaller)
- Scalable architecture (edge processing + cloud intelligence)

## Conclusion

The Focus Guardian ADHD Distraction Analysis App is a comprehensive solution that combines snapshot-based cloud vision AI for real-time pattern detection with optional post-session analysis. By addressing distraction at the moment it occurs and learning from each user's patterns, it aims to provide a personalized coach for improving focus. The design balances **cutting-edge tech** (emotion AI, semantic memory) with **practical considerations** (privacy, simplicity, efficiency), making the product both innovative and user-friendly. If successfully implemented, this app could significantly help users with ADHD (and even those without it) to understand their attention habits and foster better work/study routines.

With the above requirements and architecture, the next steps would be prototyping the core detection functionality, user testing for feedback on alerts, and iterating on the model accuracy and UX. Ultimately, Focus Guardian seeks to empower users by **externalizing some of the executive function** - detecting lapses in attention and guiding the user back - thereby augmenting their ability to stay on task and achieve their goals.

[\[1\]](https://link.springer.com/article/10.1007/s44230-025-00099-1) [\[2\]](https://link.springer.com/article/10.1007/s44230-025-00099-1#:~:text=In%20the%20same%20line%2C%20Medghalchi,55) Integrating AI into ADHD Therapy: Insights from ChatGPT-4o and Robotic Assistants | Human-Centric Intelligent Systems

<https://link.springer.com/article/10.1007/s44230-025-00099-1>

[\[3\]](https://dev.hume.ai/intro#:~:text=Hume%E2%80%99s%20state,in%20audio%2C%20video%2C%20and%20images) Welcome to Hume AI | Hume API

<https://dev.hume.ai/intro>

[\[4\]](https://memories.ai/solution#:~:text=solution%20,layer%20makes%20all%20video) [\[5\]](https://memories.ai/solution#:~:text=It%20can%20detect%20unusual%20behavior%2C,layer%20makes%20all%20video) solution - Memories AI

<https://memories.ai/solution>

[\[6\]](https://www.researchgate.net/figure/Edge-AI-Vs-Cloud-AI-Architecture_fig1_383420800#:~:text=low%20latency%20and%20low%20energy,) Edge AI Vs Cloud AI Architecture | Download Scientific Diagram

<https://www.researchgate.net/figure/Edge-AI-Vs-Cloud-AI-Architecture_fig1_383420800>

[\[7\]](https://www.researchgate.net/figure/Edge-devices-and-edge-nodes-in-relation-to-the-cloud_fig1_307902195#:~:text=,) Edge devices and edge nodes in relation to the cloud  | Download Scientific Diagram

<https://www.researchgate.net/figure/Edge-devices-and-edge-nodes-in-relation-to-the-cloud_fig1_307902195>