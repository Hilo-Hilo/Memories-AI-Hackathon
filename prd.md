# Product Requirements Document: ADHD Distraction Analysis Web App

## Document Information

- **Product Name:** Focus Guardian - ADHD Distraction Analysis Web App
- **Version:** 1.0 (Draft)
- **Date:** October 5, 2025
- **Author:** Product Management Team

## Executive Summary

Focus Guardian is a **desktop application** designed to help individuals with ADHD monitor and reduce distraction episodes in real time. Using a device's camera and microphone, the app detects when a user loses focus or becomes distracted and provides gentle interventions to refocus attention. The system integrates advanced AI services-Hume AI for emotion recognition and Memories AI for long-term behavioral pattern tracking-to personalize feedback and track progress over time. All core processing runs **locally on the user's computer** to ensure minimal setup and protect user privacy, with only high-level analysis results (not raw video/audio) sent to the cloud for storage and pattern analysis. Optional integrations with calendar and email can enrich the app's understanding of the user's schedule and tasks, enabling proactive focus assistance. The ultimate goal is to create an **autonomous digital "coach"** that not only detects distractions but also helps users self-correct and build better focus habits, all through a minimally intrusive, battery-efficient **native desktop application** packaged with PyInstaller for easy distribution.

## Problem Statement

People with ADHD often struggle to maintain focus, especially in unstructured or remote work environments. Moments of distraction-whether daydreaming, fidgeting, or getting pulled into unrelated activities-can significantly reduce productivity and increase frustration. Traditional solutions like site blockers or timers address external distractions but **do not actively monitor the person's attention state**. There is a need for a personalized tool that can **recognize distraction as it happens** through behavioral cues (e.g. gaze aversion, facial expressions, ambient audio) and gently guide the user back on track. Moreover, ADHD individuals benefit from external structure and feedback; however, constant human coaching is impractical. An automated, intelligent assistant that understands the user's goals and patterns could fill this gap. The solution must be privacy-conscious (many users are uncomfortable recording sensitive video/audio to the cloud) and easy to use (minimal setup, simple installation), running as a **native desktop application** on laptops and desktop computers people already use daily.

## Objectives & Success Metrics

**Primary Objectives:**  
1\. **Real-Time Distraction Detection:** Accurately detect episodes of inattention or distraction via webcam video and microphone audio, with low latency.  
2\. **Timely Intervention:** Prompt the user with a subtle alert or cue when a distraction is detected, enabling them to self-correct quickly.  
3\. **Goal Alignment:** Assist the user in staying on task by importing their goals/calendar and breaking down tasks into manageable steps with automated tracking.  
4\. **Personalization:** Adapt to each user over time by storing **semantic and episodic memories** of their behavior (when they get distracted, emotional states, effective interventions) to provide personalized strategies.  
5\. **Emotion-Aware Feedback:** Leverage emotion recognition (via Hume AI) to gauge user frustration, stress, or boredom, and adjust interventions accordingly (e.g. if the user appears frustrated, the app might suggest a short break or a calming technique).  
6\. **Minimize Burden:** Ensure the solution is easy to set up (no complex configuration), runs in a web browser without significant impact on device battery or performance, and keeps all sensitive raw data local to alleviate privacy concerns.

**Success Metrics (KPIs):**  
\- _Detection Accuracy:_ ≥90% of clear distraction events (e.g. user visibly looking away or leaving desk) are correctly identified, with minimal false alerts.  
\- _User Focus Improvement:_ 25% reduction in average daily "off-task" time after 1 month of use (measured by length of detected distraction episodes).  
\- _User Engagement:_ At least 70% of users continue using the app daily after 4 weeks, indicating sustained value.  
\- _Personalization Efficacy:_ >80% of users report that the feedback/interventions feel "helpful and tailored" in post-use surveys.  
\- _Performance:_ The app maintains real-time analysis (video processed at ~15+ FPS) on a typical laptop without exceeding 30% CPU usage on average, and with negligible impact on battery life (target <5% per hour).

## User Personas

**Persona 1 - "The Distracted Student":** _Alex, 20 years old,_ is a university student with ADHD. Alex struggles to stay focused during online lectures and self-study sessions. They often find themselves scrolling social media or staring off into space without realizing it. Alex needs a tool that can **alert them when they drift off-task** and help break study goals into smaller chunks. Privacy is a concern - they prefer not to have their webcam footage sent to cloud servers. Alex would use the app on their laptop while studying at home.

**Persona 2 - "The Busy Professional":** _Jordan, 35 years old,_ is a software developer with ADHD working remotely. Jordan juggles multiple projects and often gets **sidetracked by emails and notifications**. They want an assistant that integrates with their calendar to know what they _should_ be working on, and that can detect if they've gotten distracted (e.g. watching videos or getting up from the desk). Jordan appreciates data-driven insights, so an end-of-day report on when and why distractions happened would be valuable. They need the solution to be lightweight because they run many apps simultaneously and can't afford a performance drag.

## Use Cases & User Stories

- **Real-Time Focus Alert:** _As a user with ADHD, I want the app to alert me immediately when I lose focus (e.g. staring off or looking at my phone) so that I can quickly return to my task._
- **Goal/Task Management:** _As a user, I want to import my tasks or calendar events into the app so it knows what I intend to work on and can remind me of my goal if I get distracted._
- **Personalized Guidance:** _As a user, I want the app to learn my patterns (e.g. I often get distracted in mid-afternoon) and suggest proactive strategies (like scheduling a break or using the Focus mode at those times)._
- **Emotion-Sensitive Response:** _As a user, if I become frustrated or anxious, I want the app to recognize that and respond supportively (for example, not just telling me "get back to work" if I appear very upset, but perhaps suggesting a brief relaxation exercise)._
- **Privacy Assurance:** _As a user, I want to be confident that my video and audio data are not being recorded or sent to someone's server without my consent, so I feel safe using the app continuously._

## Functional Requirements

### FR1. Distraction Detection (Video & Audio)

The system shall **detect distraction episodes in real time** using the user's webcam video and microphone input. Key behaviors to detect include:

- **Visual Inattention:** If the user's gaze or head turns away from the screen for a sustained period (e.g. >5 seconds) or if they appear to be "staring into space" (face oriented but eyes unfocused), the app flags a loss of focus. This can be achieved via facial landmark and head pose tracking. For example, using on-device computer vision, the app monitors if the user's eyes deviate from the screen or if the head is down (possible phone use) or turned away. Techniques like MediaPipe face mesh or similar can track eye gaze and blink rate.
- **Physical Distractors:** Detect if the user leaves their workspace (e.g., no face detected in frame) or engages in unrelated activities. If the webcam sees the user fidgeting excessively (frequent large movements, e.g., rocking in chair) or interacting with objects not related to work (identified by repetitive motions), it may indicate distraction. Prior research shows sensors/cameras can catch cues such as _fidgeting with the chair, moving away from the work area, or playing with objects on the desk as signs of losing focus_[_\[1\]_](https://link.springer.com/article/10.1007/s44230-025-00099-1#:~:text=system%20utilized%20sensors%20strategically%20placed,or%20losing%20focus%20by%20daydreaming). Our app will use similar cues via the webcam feed (and possibly laptop accelerometer if available, for movement).
- **Auditory Distractors:** Using the microphone, the system listens for significant background audio that might distract the user. Examples: sudden loud noises (a TV or music turning on), side conversations, or the user starting to talk to someone else. Basic audio classification can differentiate speech vs. silence vs. music. The app shall detect if the user themselves starts vocalizing unrelated content (e.g., talking on a phone or singing), which could indicate they are off-task. (No speech-to-text transcription is stored locally beyond immediate analysis; the content isn't as important as the fact the user is conversing or not in quiet focus.)
- **Drowsiness/Fatigue:** If video analysis shows signs of drowsiness (e.g. frequent eye closing or yawning), the app flags this since fatigue can lead to distraction or loss of focus. For instance, slow blink rates or nodding off posture can be recognized. This overlaps with distraction detection as an early warning (user is no longer effectively focusing if falling asleep).

When a distraction is detected, the app must timestamp the event and classify it (e.g., "looked away from screen for 10 seconds" or "left desk" or "phone conversation detected"). **No raw video or audio is recorded to disk;** analysis is on-the-fly using streaming data in memory. The detection module will run continuously but efficiently (using lightweight models, throttling frame rate if needed to save battery).

**Alert Mechanism:** Upon detecting a likely distraction that lasts more than a brief threshold (configurable, e.g. >5-10 seconds to avoid false alarms), the app provides feedback. This could be a gentle audio chime or a desktop notification saying "Refocus on task X". The alert should be configurable (some users may prefer a subtle visual nudge vs. a sound). The app should also allow a short grace period; for example, if the user quickly regains focus, an alert might be skipped to avoid annoyance. Additionally, if the user explicitly _pauses_ the monitoring (say they intentionally take a break), alerts are suppressed.

### FR2. Goal Management and Agentic Assistance

The system shall incorporate features of an **intelligent productivity assistant** to help users set goals and stay on track:

- **Task/Calendar Import:** Users can connect their calendar (Google Calendar, Outlook, etc.) or task management tool to the app (optional integration). This allows the app to know the user's schedule and current tasks. For instance, if the user's calendar says "9:00-11:00 Project Work on Report", the app will treat "Report project" as the focus goal during that window. Calendar integration is optional, but when enabled, the app can automatically start a focus session when a calendar event labeled as work/study is active. Similarly, importing tasks (via an API or file) can help the user select a task or goal for an ad-hoc focus session. _(If integration is not set up, the user can manually input or select their current task within the app UI.)_
- **Goal Decomposition:** The app should assist users in breaking down big goals into smaller sub-tasks. For example, if Alex sets a goal "Finish writing essay", the system (optionally using an AI agent) can suggest sub-tasks like "1) Outline the essay, 2) Write introduction, 3) Draft main sections, 4) Proofread final draft". Research indicates that AI (like ChatGPT) can effectively help break tasks into manageable steps and provide real-time feedback[\[2\]](https://link.springer.com/article/10.1007/s44230-025-00099-1#:~:text=In%20the%20same%20line%2C%20Medghalchi,55). The app may utilize a prompt-based approach (leveraging an LLM via API) to decompose a user's goal when asked. These steps can then appear in the UI as a checklist, and the distraction monitoring can track progress (e.g., if a step is expected to take 30 minutes, and the user is on step 1 but repeatedly distracted, the system knows to possibly extend the focus time or suggest splitting further).
- **Agentic Self-Correction:** The assistant should exhibit _agentic behavior_ in helping the user stay on course. This means beyond just alerting, it can take initiative to adjust the plan. For instance, if repeated distractions are detected on a particular task, the system might ask: "Is this task too difficult or causing stress? Should we break it down or schedule a short break?" If a user runs over the allocated time for a task (from calendar or user input), the system might automatically reorganize the schedule (with user permission), pushing meetings or sending a notification that the current task needs more time. This essentially makes the app a smart coach that not only tracks tasks but can suggest corrections: **auto-rescheduling, reminders to return to task after break, or recommending focus techniques** (like the Pomodoro technique if the user is consistently distracted after ~20 minutes).
- **Progress Tracking:** The app will automatically log time spent on each task vs. distracted, giving the user a real-time view of progress. For example, "Writing Report - focused 40 min, distracted 5 min" might be displayed. If integrated with a task manager, the app can mark tasks complete or update progress status once finished (with user confirmation). The user can also manually correct or annotate sessions (e.g., "I was interrupted by a phone call here"). This data feeds into the personal Memory (FR4).

### FR3. Emotion Recognition (Hume AI Integration)

To better understand the context of distractions and the user's state, the app shall integrate **emotion analysis** on the fly. This feature uses **Hume AI's Expression APIs** to interpret facial expressions and vocal tone for emotional cues. Hume AI's models can measure "hundreds of dimensions of human expression" across face and voice[\[3\]](https://dev.hume.ai/intro#:~:text=Hume%E2%80%99s%20state,in%20audio%2C%20video%2C%20and%20images), meaning the app can detect nuanced emotional states like frustration, confusion, boredom, or engagement level.

**Functionality:**  
\- The app will periodically send snapshots of the video (e.g., an image frame every few seconds when the user is active) or short audio snippets to the Hume AI cloud API for analysis. This is done via secure API calls and only when the user has consented (during setup, the user is informed and can toggle emotion sensing on/off). If privacy settings disallow cloud, this feature can be disabled or possibly use a local emotion model (with lower accuracy).  
\- The emotion analysis results (e.g., "high frustration", "bored", "focused", "happy") are used to augment distraction data. For example, if a distraction is detected and the emotion analysis shows rising frustration right before it, the system infers the user might be struggling with the task. It could then recommend a strategy (like "Seems you are getting frustrated; maybe take a 5-minute break or switch to a simpler task and come back later"). If it detects boredom (low engagement expression) leading to distraction, it might suggest making the task more engaging or changing approach.

**Real-Time Adaptation:** Emotional context will also modulate the alerting mechanism. Instead of a one-size-fits-all nudge, the app tailors its tone: e.g., a gentle encouragement if the user looks frustrated ("I know this is tough, but you can do it!") versus a more upbeat refocus prompt if the user simply looks distracted but not upset ("Let's get back on track 👍"). This empathic approach aims to keep the user motivated rather than annoyed. The Hume integration provides the necessary data for this empathy: for instance, detecting **vocal tone** like sighing or muttering can indicate frustration or fatigue, which the app shouldn't ignore in its coaching style.

**Performance Consideration:** Because sending continuous video to an API would be bandwidth-heavy, the app will **throttle and sample** the emotion analysis. For example, it might analyze a face snapshot once every 10 seconds or when a potential distraction event occurs. Hume AI's API supports real-time streaming as well, but for efficiency we may use the batch mode (sending a single frame or short audio clip for inference) to get periodic emotional readouts. All calls to Hume are done via the front-end using Hume's JavaScript/TypeScript SDK (which handles the API communication securely) or via our backend proxy to keep API keys hidden.

### FR4. Semantic & Episodic Memory (Personalization via Memories AI)

The application shall maintain a **long-term memory** of user behavior to enable personalization. This includes recording _episodic data_ (timestamped events like distractions, focus sessions, task completions) and _semantic data_ (general knowledge about user's preferences, patterns, and effective strategies). The integration with **Memories AI** (or a similarly purposed "memory" service) will be used to store and analyze these behavior logs over time:

- **Data Stored:** Only **high-level analytic results** and metadata are stored in the cloud memory. This includes entries like: "10/5/2025 2:30pm - Distracted for 3 minutes (looked away, emotion: bored)" or "10/6/2025 9:00am-10:00am - Focus session on Project X, 2 alerts issued, user stayed on task 85% of time". Raw video or audio is **never stored** in this memory database; the focus is on the _what, when, how long,_ and _possible why_ of distraction events. Additional context such as the task in focus, time of day, and user's emotional state (from FR3) at the time are included to enrich the data.
- **Memories AI Platform:** The Memories AI integration provides a scalable **behavioral data lake** to accumulate these events. Over time, this yields a timeline of the user's focus patterns. The system can run analysis to find patterns - e.g., "The user is frequently distracted in the late afternoon" or "When working on coding tasks, the user rarely gets distracted, but when writing documentation, distractions spike." The platform's semantic layer can help cluster similar episodes or triggers. (If using the Memories.ai service, it might offer built-in analytics for unusual behavior detection or trend analysis[\[4\]](https://memories.ai/solution#:~:text=solution%20,layer%20makes%20all%20video)[\[5\]](https://memories.ai/solution#:~:text=It%20can%20detect%20unusual%20behavior%2C,layer%20makes%20all%20video), which we can leverage for pattern mining).
- **Personalized Insights:** Using the stored data, the app will periodically (say weekly) generate a summary for the user: _e.g., "This week, your average focus duration was 25 minutes, after which you tended to get distracted. Distractions often happened when you were doing Task A, typically around 3 PM. You seemed most focused during 10-12 AM. Compared to last week, you improved your focus time by 15%. Triggers for distraction noted: incoming emails (3 times), phone notifications (2 times)."_ These insights help the user adjust their habits (maybe scheduling tougher work in the morning, or turning off notifications in the afternoon).
- **Adaptive System Behavior:** The app uses the memory data to adjust its own behavior. For example, if it "knows" a user usually struggles on Mondays, it might proactively activate a stricter focus mode on Mondays (with more frequent check-ins). If a user responds poorly to a certain type of alert (e.g., they always dismiss it and remain distracted), the system can try a different approach (perhaps a different alert style or message). Essentially, the app treats past interactions as training data to refine its coaching strategy per individual.

All personal data in this memory is stored securely (likely under the user's account with encryption). If using a third-party service (Memories.ai), we will use their API to store/retrieve data, ensuring compliance with privacy (the data stored is already abstracted, but even so, it should be protected and only accessible to the user). The user may be given controls to view and delete their recorded "memories" at any time, maintaining transparency.

### FR5. Minimal Setup & Desktop Application UX

The product is delivered as a **native desktop application** packaged with PyInstaller - meaning the user can download and install it like any standard application, with **no special hardware or complicated configuration**. Key requirements for the UX and setup include:

- **Onboarding:** The first time user experience will guide the user through granting permissions (camera and microphone access). It will clearly explain why these are needed (e.g., "We use your camera to detect when you get distracted, but **no video is ever sent to the cloud** without your consent"). The onboarding also asks if the user wants to connect their calendar or task manager (optional, can be skipped). If they choose to, a secure OAuth flow to Google, Microsoft, etc., is provided. Similarly, they can opt in/out of emotion analysis (explaining that involves sending data to Hume AI cloud). The goal is to make initial setup doable in minutes. Default settings will work out-of-the-box (e.g., some default alert settings and working hours), which the user can later customize. On macOS, the app will request necessary permissions through system dialogs.
- **UI Design:** The interface will be clean and minimal to avoid being a distraction itself. Likely there will be a **dashboard screen** that shows: current focus session or task, a timer or progress indicator, and maybe an icon indicating monitoring is ON. There may be a small status like "🔵 Focus mode active" or "🟡 Break (monitoring paused)". When an alert triggers, it might display as a system notification or small overlay window rather than a jarring popup. The color scheme and visuals should be calming (avoiding bright reds or alarming designs, as the aim is supportive). Battery and CPU efficiency considerations mean using native UI frameworks (CustomTkinter, PyQt, or Tkinter) with minimal animations and efficient rendering.
- **Cross-Platform Support:** The desktop application will support macOS, Windows, and Linux through PyInstaller packaging. The primary use case is desktop/laptop computers where users typically do their focus work. Each platform will have a native installer (DMG for macOS, MSI/EXE for Windows, AppImage/DEB for Linux). Platform-specific features (like system tray integration or native notifications) will be implemented using conditional imports and platform detection.
- **Battery/CPU Optimizations:** The app will implement numerous optimizations to remain lightweight:
- Utilizing **optimized Python libraries** for video processing to leverage native performance. Critical algorithms (face landmark detection via MediaPipe, eye gaze estimation) run as compiled C++ extensions through libraries like OpenCV and MediaPipe, achieving real-time performance without excessive CPU usage.
- Adaptive frame rate processing: if the app detects high CPU or battery drain, it can reduce how often it samples video frames (e.g., processing 1 frame per second when idle, ramping up to 5 fps during active focus sessions). Many distraction cues don't require 30fps full motion analysis - a lower frequency can suffice to catch most issues, thereby saving power.
- Use of Threading: all heavy computations (video frame analysis, emotion API calls) will run in background threads using Python's threading or multiprocessing modules, so the UI thread remains free and the application stays responsive.
- Graceful degradation: On older devices that cannot handle local video analysis well, the app could detect this and offer an alternative (such as more reliance on cloud analysis, if the user permits, or limiting features like turning off emotion analysis).
- **Security & Privacy UX:** Clearly communicate privacy features in the UI. For example, have an indicator when video is being analyzed (like a small camera icon that the user can click to see "Video is being processed locally. No footage is stored."). Also allow users to easily pause or stop monitoring at any time (maybe a big "Pause" button), giving them control. This transparency will build trust, which is crucial for an app that has access to camera/mic continuously.

### FR6. Optional Integrations (Calendar, Email, etc.)

While not core to the MVP, the system may support additional integrations to enhance functionality:

- **Calendar Integration:** (Optional) As described in FR2, connecting a calendar helps the app contextualize the user's focus sessions. In addition to import, if given write access, the app could automatically create calendar entries for focus sessions or distraction logs (e.g., log "Focus Session - 45 min" on the calendar for self-tracking). This integration should use standard APIs (Google Calendar API, Microsoft Graph for Outlook) and adhere to least privilege (only reading events and writing focus logs if user enables that feature). The PRD treats this as an enhancement: it's highly useful but the app should still function without it (user manually inputs their current goal).
- **Email Integration:** (Optional) An idea is to integrate with email (e.g., Gmail or Outlook) to both manage distractions and gather context. For example, the app could detect when the user alt-tabs to check email during a focus session and count that as a distraction (this would require a browser extension or desktop app to monitor active window, which is out of scope for a pure web app - possibly an extension in future). On the other hand, email could be a source of tasks: the app might parse flagged emails or to-dos from email content to suggest tasks to focus on. Due to complexity, email integration is considered a future enhancement and would need careful privacy handling (accessing email content might be sensitive).
- **Other Productivity Tools:** (Future Consideration) Integration with project management tools (Trello, Asana, etc.) or note-taking apps could deepen the system's knowledge of what the user should be doing. These are beyond the current scope but can be kept in mind for extensibility. The architecture should allow adding new integrations without major overhaul (perhaps via plugin-like modules that feed the goal/task system).

**Note:** Both calendar and email integrations require user authentication into third-party services and should use industry-standard OAuth flows. They are optional - the app's core loop (monitor distraction, alert user, log data) does not depend on them. If not connected, the user can manually specify their focus periods or rely on default work hour settings.

## Non-Functional Requirements (NFRs)

- **NFR1: Privacy & Data Security:** The system shall ensure that **no raw video or audio data is transmitted or stored outside the user's local device** (unless explicitly enabled by the user for features like Hume emotion analysis). All cloud-stored data will be limited to processed results and metadata. Data in transit to cloud (e.g., emotion analysis calls, result uploads) must be encrypted (HTTPS). In storage (databases), user data must be encrypted at rest. The user will have unique access to their data (protected by account login). We will comply with relevant privacy laws (e.g., GDPR) giving users rights to their data (export, deletion).
- **NFR2: Performance:** The distraction detection should run in real-time with minimal lag. The UI feedback loop (from distraction event to user alert) should occur within 1-2 seconds at most. The app should be optimized to use <500MB RAM and keep CPU usage low (target <30% on a typical 4-core CPU during active analysis). It should not noticeably slow down other applications. To maintain system health, if the app detects it is using too many resources (via performance APIs), it may auto-throttle or warn the user.
- **NFR3: Battery Efficiency:** Especially for laptop users on battery, the app should be thrifty. Utilizing device resources like GPU for video processing can be more power-efficient than pegging CPU. OpenCV and MediaPipe can leverage GPU acceleration when available. The app shall avoid continuous high-resolution processing; for example, analyzing a downsampled video stream (e.g., 320x240 px frames) is often sufficient for face detection and significantly reduces CPU load. If available, the app can make use of any OS-level optimizations or platform-specific ML accelerators (like CoreML on macOS, DirectML on Windows). The aim is that running the app for an hour uses only a small percentage of battery - achieving this will likely require tuning and possibly dynamic adjustment of processing intensity.
- **NFR4: Compatibility:** The desktop app must be compatible with modern operating systems (macOS 10.14+, Windows 10+, Ubuntu 20.04+). It should degrade gracefully if certain features aren't available. For instance, if GPU acceleration isn't available, the app might use CPU-only processing (with a possible hit to performance, but still functional). The app will detect platform capabilities at startup and adjust processing accordingly.
- **NFR5: Reliability:** The system should handle long-running sessions (e.g., 8+ hours of monitoring) without memory leaks or crashes. It should also be resilient to internet connectivity issues: since most core features run locally, the app can function offline or with intermittent connectivity, simply queuing any cloud uploads until the connection restores. The user interface should clearly show if cloud features (like fetching personalization data or syncing with calendar) are temporarily unavailable due to offline status, but local monitoring continues unaffected.
- **NFR6: Security:** Follow best practices for desktop application security. All libraries used for the app should be well-audited to prevent vulnerabilities, especially since we are dealing with camera/mic. Store sensitive data (API keys, session recordings) using encrypted storage. The backend APIs will authenticate requests (the user will likely log in to the app, possibly using OAuth or our own account system, to tie their data to them). The system must also ensure that no one else can access the user's data - e.g., memory data is scoped per user account with proper auth checks. The PyInstaller bundle will be code-signed on macOS and Windows to ensure authenticity.
- **NFR7: Usability:** The app's interventions must be supportive, not punitive or overly distracting themselves. We will follow UX guidelines for assistive tech - for example, allow the user to adjust alert frequency or turn off certain types of nudges. The user retains ultimate control (they can snooze the assistant if needed). The interface will be simple to navigate, with clear terminology (avoid technical jargon in user-facing text). We will gather some user feedback in testing to ensure the prompts and summaries are actually helpful and not guilt-inducing.
- **NFR8: Extensibility:** The architecture should allow adding new detection methods or integrations. For example, if later we want to incorporate keystroke or mouse activity as additional signals of distraction, the system's modular design should accommodate plugging in another module (using libraries like pynput for cross-platform input monitoring). Similarly, if alternative emotion recognition or memory services are to be supported, it should be relatively easy to swap those in (abstract the API calls behind interfaces).

## Technical Architecture

_System architecture diagram illustrating key components and data flows._ The desktop application handles real-time video/audio capture and on-device analysis, only sending minimal results to the cloud. The optional cloud backend stores AI analysis results and patterns (Memories AI), and integrates optional services like calendar or email. External APIs (Hume AI) are used for specialized analysis (emotion), with privacy safeguards in place. All core functionality works completely offline with local SQLite storage.

### Desktop Application (Local)

The desktop application is the centerpiece, running all real-time processes locally on the user's computer:

- **Video/Audio Capture Module:** Utilizes OpenCV (cv2.VideoCapture) to access webcam streams and libraries like sounddevice or pyaudio for microphone input. Video frames are fed into the processing pipeline as NumPy arrays for analysis. Audio is primarily monitored for amplitude and classification (not full transcript); audio processing libraries can extract frequency data or detect speech segments. We will not continuously record or send this raw media during realtime analysis, it's processed on-the-fly in memory. For post-session analysis, recordings are saved locally as MP4 files.
- **Distraction Analysis Module:** This contains the core algorithms running in background threads. Sub-components include:
- _Face & Eye Tracker:_ Uses MediaPipe FaceMesh (Python) to track the user's face orientation and eye gaze. The pre-trained model provides 3D face landmarks from which we compute metrics like "looking off-screen angle" or eye openness (for drowsiness). This runs every X milliseconds on the video frames in a dedicated thread.
- _Pose/Posture Detector:_ Optionally uses MediaPipe's BlazePose model for upper-body posture tracking (e.g., to detect if user slumped or left the chair frame). This is an enhancement feature for ergonomic posture feedback, though our main focus is attention - posture is secondary.
- _Audio Monitor:_ Listens to the mic input using sounddevice or pyaudio with NumPy/SciPy for FFT analysis to detect speech vs silence or sudden noise. We might integrate a simple machine learning model for classifying audio segments if needed, or simply use heuristics (e.g., volume spikes, presence of non-silent periods when the user is supposed to be quietly working).

This module in real-time decides if a "distraction event" is happening. It likely runs a small state machine or buffer (to avoid reacting to split-second changes). For example: if gaze is off-screen continuously for >5 seconds, trigger event; if user leaves frame for >10 seconds, trigger event, etc.

- **Emotion Analysis Integration:** If enabled, the application will interface with Hume AI. API calls are made directly from the desktop app using the Hume Python SDK or requests library. When we want an emotion reading, the app will capture a still image (or short audio clip) and send it via an HTTPS request to Hume's Expression API endpoint. The response (an emotion feature vector or labeled emotions) is parsed and fed into the personalization logic and possibly immediate feedback logic. API keys are stored securely in the local configuration file with encryption. _(These calls are infrequent and only initiated based on need.)_
- **User Interface & Control:** The application uses a Python GUI framework (CustomTkinter, PyQt, or Tkinter) to render the dashboard, status, and handle user interactions (like pausing monitoring, acknowledging alerts, viewing reports). The UI communicates with the background analysis via threading events and queues. For example, the analysis thread might post messages like {event: "distracted", type:"look-away", timestamp: ...} to a queue which the UI thread receives to display a notification. Conversely, if the user clicks "dismiss alert" or "pause", the UI signals the analysis thread to halt or adjust thresholds. The UI also handles login and integration authorizations (OAuth flows via system browser).
- **Local Data Storage:** All data is stored locally using SQLite for structured data (sessions, events, KPIs) and the filesystem for recordings (MP4 files). The database schema matches the session_report.json structure with tables for segments, distractions, expressions, and recommendations. Settings and user preferences are stored in JSON configuration files. Session recordings are organized in timestamped directories. All data remains on-device unless the user explicitly enables cloud sync features.
- **Screen Capture Module:** For comprehensive distraction analysis, the app can optionally capture screen content using libraries like mss (for screenshots) or python-mss for efficient screen recording. This allows detection of which applications the user is using (browser, IDE, video player) and whether they've switched to distracting content. Screen capture runs in a separate thread and can be toggled on/off by the user.
- **Recording Module:** For post-session analysis, the app can record both webcam and screen to local MP4 files using OpenCV's VideoWriter or ffmpeg-python. Recordings include configurable quality presets (Low/Standard/High) to balance file size and detail. After a session ends, these recordings can optionally be uploaded to Memories.ai or Hume for detailed cloud-based analysis.

### Cloud Backend

The backend component serves primarily as a secure data store and integration point, **not for real-time processing**. Its responsibilities:

- **REST/GraphQL API:** The backend exposes endpoints for the client to: authenticate the user, fetch or update user profile/settings, and upload analysis results (distraction events, session summaries). For instance, when the client has a distraction event ready to log, it calls POST /api/events with the JSON payload (timestamp, type, duration, emotion summary, etc.). Similarly, there might be an endpoint GET /api/dashboard for the client to retrieve aggregated stats or weekly reports. These APIs require the user's auth token and all communication is over HTTPS.
- **Authentication & User Management:** Users will likely create an account (or log in via Google/OAuth). The backend manages these accounts and links them to stored data. Authentication tokens (JWT or session cookies) are issued to the client. We'll enforce auth on data endpoints so one user cannot access another's data.
- **Database:** A scalable cloud database stores the **analysis results and patterns**. This can be a relational DB or a combination of a time-series DB and a vector store. For structured events (timestamp, type, etc.), a relational or time-series database is appropriate. For more complex semantic data (perhaps embeddings of context or patterns for personalization), we might use a vector database. Given the likely scale (each user might generate a few dozen events a day), the data volume is not huge; even a SQLite or lightweight DB per user could suffice initially, but we'll opt for a multi-tenant DB for simplicity. The **Memories AI** integration might mean we use their platform as the database: e.g., calling a Memories.ai API to store each event. They tout a "multimodal data lake with a single semantic layer"[\[5\]](https://memories.ai/solution#:~:text=It%20can%20detect%20unusual%20behavior%2C,layer%20makes%20all%20video) which could offer built-in analysis capabilities (like querying for similar past events or detecting unusual patterns[\[4\]](https://memories.ai/solution#:~:text=solution%20,layer%20makes%20all%20video)). If that service is used, our backend would act as a bridge to it. Alternatively, we implement our own analytics. This decision can be made based on the hackathon context and available resources.
- **Analytics & Pattern Analysis:** Either via the Memories AI platform or our own batch jobs, the backend will analyze accumulated data to extract patterns. This could run periodically (e.g., a daily cron job that crunches the latest data and updates a user's profile with new insights). Example: calculating the user's average focus duration, identifying peak distraction times, or training a simple model to predict when a user is likely to get distracted next. These results are then available to send to the client (e.g., in the weekly report or live adaptation). If using Memories.ai, some of this may be offloaded to their API which might provide analytics out of the box (their marketing implies capabilities like detecting unusual behavior or summarizing video content, which might extend to summarizing our event streams).
- **Integration Services:** The backend also handles any heavy lifting for optional integrations:
- For calendar sync, if the user grants permission, the backend could fetch upcoming events and send them to the client or directly incorporate them into the schedule logic. (This avoids putting sensitive API keys or secrets in the client. The client would just request "import calendar" and the backend, having stored refresh tokens from OAuth, fetches events from Google Calendar API and returns them.)
- For email or other integrations, similarly, the backend can fetch or listen for data (though real-time email distraction detection would require continuous client monitoring as noted earlier, so likely only offline analysis like summarizing tasks from emails).
- These integration modules ensure that third-party API calls and keys are secured on server side, and only necessary info is passed to the client.
- **WebSockets (Notifications):** While the client is mostly pulling data or handling things itself, the backend could use WebSockets or Server-Sent Events to push certain updates. For example, if a user's friend or coach is viewing their session remotely (if we implement a co-watcher), the backend could relay events. Or if we schedule server-side analytics (like an AI periodically analyzing behavior and generating a suggestion), it could push a notification to the client ("New insight available!"). This is not mandatory for MVP but we design the system to allow real-time server->client messages if needed.
- **Scalability:** Since most compute is client-side, the backend load is relatively modest (mostly handling data storage and some processing of stored data). This makes it easy to scale: we can host on a cloud function or small server for the hackathon MVP. If user base grows, we scale the database and perhaps add caching for analytics results. The architecture inherently offloads heavy computation to the edge (browser), aligning with modern edge computing practices (perform ML at the data source to reduce cloud burden[\[6\]](https://www.researchgate.net/figure/Edge-AI-Vs-Cloud-AI-Architecture_fig1_383420800#:~:text=low%20latency%20and%20low%20energy,)). This also improves scalability because adding users doesn't linearly increase server CPU costs, mainly storage and some periodic jobs.

### Tech Stack Considerations

To fulfill the above, we propose the following technologies, chosen for **minimal complexity** and desktop-focused efficiency:

- **Desktop Application:**
- **GUI Framework:** _CustomTkinter_ or _PyQt6_ for building the modern UI. CustomTkinter provides a clean, modern look with dark mode support and is simpler than PyQt. PyQt6 offers more advanced features and native platform integration. Both support cross-platform deployment. For rapid prototyping, CustomTkinter is preferred; for production-grade polish, PyQt6.
- **Media/ML Libraries:** Use _MediaPipe_ (Python) for face/pose tracking - highly optimized C++ implementations with Python bindings. _OpenCV_ (cv2) for video capture and general image processing. These libraries provide near-native performance and are battle-tested for real-time CV applications.
- **Audio Processing:** _sounddevice_ or _pyaudio_ for microphone capture, _NumPy/SciPy_ for FFT analysis and audio feature extraction. These provide efficient audio stream handling with minimal overhead.
- **Threading:** Python's _threading_ module for concurrent operations (UI thread, video analysis thread, audio monitoring thread, recording thread). For CPU-intensive tasks, consider _multiprocessing_ to bypass the GIL, though threading is often sufficient given MediaPipe's efficiency.
- **Screen Capture:** _mss_ (Python MSS) for fast screen grabbing across platforms, or _python-mss_ for screen recording. These libraries provide hardware-accelerated screenshot capture.
- **Recording:** _OpenCV VideoWriter_ or _ffmpeg-python_ for encoding webcam and screen to MP4 files. Support for H.264 codec with configurable bitrate/quality presets.
- **Back-End (Optional Cloud Features):**
- **Language & Framework:** _Python_ with FastAPI for the optional API server (if implementing cloud sync features). FastAPI has excellent async support and auto-generated API docs. Can easily interface with OAuth providers and external APIs (Hume, Memories).
- **Database:** _SQLite_ for local storage (embedded, zero-configuration, perfect for desktop apps). For cloud sync, optionally use _PostgreSQL_ for server-side storage. SQLite schema will match the session_report.json structure with proper indexes for queries.
- **Memories AI**: If we integrate this service, the desktop app will call their API directly using _requests_ library. Upload session recordings (MP4) via their video upload endpoints, then query their Chat API for structured analysis. This is an optional feature users can enable.
- **Hume AI:** Call Hume's Expression API directly from the desktop app using their Python SDK or _requests_. API keys stored in encrypted local config. Calls are made periodically (not continuously) to analyze emotional state from webcam frames or audio samples.
- **Packaging & Distribution:**
- _PyInstaller_ for creating standalone executables. Bundle all Python dependencies, MediaPipe models, and assets into a single distributable.
- Platform-specific installers: _create-dmg_ for macOS DMG files, _Inno Setup_ or _WiX_ for Windows MSI/EXE installers, _AppImage_ or _fpm_ for Linux packages.
- Code signing: macOS (Apple Developer Certificate), Windows (Authenticode certificate) for security and trust.
- **Edge Processing Philosophy:** The design heavily leans on **edge (on-device) AI**. Modern laptops can handle surprising amounts of ML locally. By running MediaPipe models on-device, we bypass network latency and protect data. MediaPipe models are highly optimized (quantized, compiled) to run in <100MB memory with minimal compute. This approach means most computations happen where the data is produced (the user's machine) rather than shipping all data to cloud.

We do remain cognizant that some users' devices might be underpowered. For them, one could offer a setting "Use Cloud Processing" where session recordings are uploaded to cloud services (Memories.ai/Hume) for analysis instead of attempting local emotion/pattern analysis. This is optional and defaults to off for privacy.

## Trade-Off Analysis: Local vs Cloud Processing

One of the core architectural decisions is how much to process locally on the desktop vs. send to cloud. We have chosen a **local-first approach** for distraction detection and only send minimal results to cloud when users opt-in. Below is an analysis of this trade-off:

- **Privacy:** Processing video/audio locally means the user's face, environment, and personal moments are not continuously uploaded. This is a huge privacy win and likely critical for user acceptance (many users would not use an app that streams their webcam all day to a server). In our design, the cloud only sees abstracted events or session recordings if explicitly uploaded. If we went cloud-first (streaming video to analyze on server), we'd introduce significant privacy concerns and require heavy security measures to protect that stream. Local processing thus keeps sensitive data on-device by default, aligning with data sovereignty principles.
- **Bandwidth:** Continuous video streaming is bandwidth intensive (a 720p video at even 15fps can be hundreds of MBs per hour). Many users have limited or metered connections. Our local processing sends only tiny data (a few bytes per event, occasional API calls for emotion). This is hugely efficient. Even the periodic Hume API image calls are maybe a few KB each. So local-first avoids saturating the network. It also enables offline use; the core detection doesn't depend on internet. In contrast, a cloud approach would break if internet drops.
- **Latency:** For real-time feedback, local processing is faster. There's near-zero network latency; detection happens in milliseconds on device. If we had to send each frame to cloud and wait for a response, even a 100ms network delay could make feedback sluggish, or worse if connection is slow. Local ensures immediate responsiveness (alerts within 1-2s vs possibly 3-5s or more round-trip for cloud). Low latency is crucial for interrupting distractions effectively.
- **Device Performance:** On the flip side, doing everything locally consumes the user's CPU/GPU, which could heat up their device or slow other tasks. Cloud processing would offload work from the user's device. For some users on old hardware, local heavy computing might not be feasible. However, given continuous video streaming out is also heavy on the system (encoding video and network I/O also use CPU and battery), the difference may not be that stark. It is known that moving lots of data (like constantly moving frames between CPU, network, memory) is very energy-intensive - over 60% of mobile device energy can be spent just on data movement for tasks like video processing[\[7\]](https://www.researchgate.net/figure/Edge-devices-and-edge-nodes-in-relation-to-the-cloud_fig1_307902195#:~:text=,). So avoiding that by keeping data local can actually **save energy**. We also mitigate performance issues by optimizing our models and using efficient libraries like MediaPipe.
- **Development Complexity:** Implementing on-device ML with Python is straightforward using mature libraries (MediaPipe, OpenCV, scikit-learn). By contrast, using cloud would require building and maintaining server infrastructure with GPU support. Since one of our goals is minimal complexity and cost, we avoid building a full server-side computer vision pipeline. Modern Python ML libraries provide pre-trained models and high-level APIs. Also, at scale, cloud processing would cost more (running possibly GPU instances for each user's stream), whereas leveraging the user's device is cost-free for us and scales naturally with user base. For a hackathon project and beyond, this is a simpler deployment story (no need to maintain heavy server infrastructure).
- **Quality of Analysis:** In theory, cloud could host larger, more accurate models than what can run on-device. There is a trade-off in model size. However, the chosen tasks (face detection, gaze, etc.) can be done well with lightweight models like MediaPipe. And with hardware advances, on-device capabilities are growing. If extremely fine-grained analysis was needed (like detailed emotion recognition beyond Hume's scope, or complex scene understanding), cloud might outperform. But our focus is narrow (user's face & voice cues), which is feasible on device with high accuracy. Additionally, by not compressing and streaming video, we avoid any network-induced quality loss or delay that could degrade analysis quality.

In summary, the chosen hybrid approach (local analysis, optional cloud storage of results) maximizes privacy and responsiveness, while minimizing cloud costs. The **only cloud processing** we intentionally use is the specialized emotion AI (Hume) and long-term pattern analysis (Memories.ai), both of which are optional features users can enable. If in the future on-device emotion recognition becomes viable (via a small model), we could move that local too.

We will provide a user option: if they prefer, they could enable cloud features where session recordings are uploaded to Memories.ai/Hume for detailed analysis (perhaps if their device struggles with local processing or they want deeper insights). But the default will always prioritize local processing. This aligns with an "edge AI" philosophy - bring the model to the data, not data to the model[\[6\]](https://www.researchgate.net/figure/Edge-AI-Vs-Cloud-AI-Architecture_fig1_383420800#:~:text=low%20latency%20and%20low%20energy,).

## System Architecture Diagram

_(Refer to the figure above for a visual overview.)_ In the diagram, the left side represents the **Desktop Application** and its components (GUI, local ML modules, integrations), while the right side shows the **Optional Cloud Backend** and external services. The data flow is as follows:

- Video/Audio streams are processed locally by the distraction detection engine. If an event is detected, it's immediately fed back to the user via the UI (alert) and stored in local SQLite database.
- The desktop app optionally sends **analysis results** or **session recordings** to the backend (dashed arrow - optional feature). This includes distraction events and focus session summaries, or MP4 recordings for post-processing. The backend receives and stores these in the database (and/or forwards to Memories AI service for storage and further pattern computation). The backend never receives raw media unless user explicitly uploads recordings.
- The desktop app optionally communicates with **Hume AI** (dashed arrow - optional feature) for emotion analysis, sending minimal data (frames or audio snippets) and receiving emotion insights. These insights are used locally and stored in the SQLite database with session events. Hume AI is an external cloud API specialized for this task[\[3\]](https://dev.hume.ai/intro#:~:text=Hume%E2%80%99s%20state,in%20audio%2C%20video%2C%20and%20images).
- The app or backend integrates with **Calendar/Email APIs** (dashed arrows - optional) as needed. For example, on user request or at session start, the app might pull the user's calendar events to understand what the current focus context is. Similarly, if we implement email parsing for tasks, the app would fetch emails and extract task info. These are optional flows.
- The backend may also connect to **Memories AI** service (dashed arrow "Pattern Storage" - optional), if we leverage that platform to store and analyze session recordings. The desktop app uploads MP4 files to Memories.ai, which returns structured analysis via their Chat API. Alternatively, local SQLite DB and local analytics fulfill this role. In either case, this component is about long-term memory and pattern mining.
- Finally, the backend can send aggregated results back to the desktop app (e.g., when the user opens a weekly report view and has cloud sync enabled). In practice, most user-facing alerts and reports are generated locally using SQLite queries; backend-originating messages are only relevant if cloud sync is enabled.

The architecture is modular: one could replace Hume AI with another emotion engine, or plug in additional sensors (like a smartwatch for heart rate to detect stress) into the desktop app, without overhauling the whole system. The clean separation ensures that the **desktop application is doing real-time interactive work**, while the **optional backend does storage, synchronization, and heavy analysis offline**. This division minimizes latency and maximizes privacy.

## Risks & Open Issues

- **Accuracy vs. False Alarms:** Tuning the distraction detection to be sensitive enough but not overly sensitive will be challenging. If the app misidentifies normal behavior (e.g., briefly glancing at notes or looking away in thought) as a distraction too often, users will get annoyed and may quit using it. We will need to refine algorithms and possibly allow user calibration (maybe an initial calibration session to learn what "focused" looks like for that user, or adjustable sensitivity sliders). Using proven models (like eye gaze tracking) should help, but individual differences exist. We might mitigate this by starting with conservative alerts (only alert on clear-cut cases) and then gradually getting more proactive as trust is built.
- **User Comfort and Consent:** Having a camera watch you can itself _feel_ distracting or intrusive for some. Even though we handle privacy well, some users might be uncomfortable knowing they are being recorded (even locally). Clear communication and the ability to **turn off the camera at any time** is essential. We also ensure that if camera is off, the app gracefully degrades (perhaps just doing audio-based limited monitoring or only tracking tasks without live feedback). User workshops or testing could inform how to make the experience more comfortable (maybe using avatars or animations to indicate the AI "coach" presence instead of a feeling of being surveilled).
- **Integration Complexity:** Calendar and email integrations, if enabled, have to handle various user contexts and errors (auth tokens expiring, conflicting events, etc.). Since these are optional, it's acceptable if initially they are somewhat basic (e.g., only Google Calendar supported in MVP). We note the risk that these can consume development time without being core to the prototype; hence they are scoped as stretch goals.
- **Performance on Different Devices:** There's variability in user hardware. On a high-end PC, everything might run smoothly, but on an older laptop or a budget tablet, real-time video analysis could lag. We plan to test on a range of devices and provide settings to reduce load. If necessary, we may use a simpler detection method for low-end devices (e.g., just detect face presence and large movements, skipping fine gaze tracking). Ensuring wide compatibility is a risk but manageable with feature scaling.
- **Third-Party Dependency Reliability:** Our solution relies on Hume AI and possibly Memories AI. If these services have downtime or change their API, it could affect our app. To mitigate, we will implement graceful fallbacks - e.g., if Hume is unreachable, the app continues without emotion input (and maybe informs the user that emotion features are temporarily unavailable). For Memories AI, if not using it, we can rely on our own DB. Essentially, the core loop doesn't break if those services fail; only some enhanced features do. We also should consider cost: Hume API calls might incur cost per request, which could become expensive if done too frequently. We will limit usage to stay within a free tier or a predictable budget.

Insert the following into your PRD. Do not rewrite prior sections; splice these where indicated.

# 1) Architecture split (replace "Technical Architecture" header)

## Runtime Topology

- **Realtime (Edge, in-browser only):**
  - Inputs: webcam frames; optional screen frames (via getDisplayMedia).
  - Ops: image-only inference for posture, activity, and screen-content classification. No LLM/VLM calls. No cloud I/O.
  - Outputs: timestamped event stream (focus/distract, posture state, active app class), in-memory + IndexedDB ring buffer; optional low-freq thumbnails for local audit only.
- **Post-Processing (End-of-session, cloud):**
  - Inputs: two MP4s saved locally-cam.mp4 (user) and screen.mp4 (display)-default 480p, configurable bitrate.
  - Upload targets: **Memories.ai** (primary) + **Hume AI** (expression timeline).
  - Ops: Memories Chat API runs LLM/VLM over the two videos to extract structured session summaries; Hume produces expression tracks.
  - Outputs: normalized JSON report (schema below) persisted in backend DB; links to Memories objects; expression timeline merged.

## Data Flow Summary

- **Session start:** user grants camera; optional screen share; choose quality profile.
- **Realtime loop:** CV-only metrics at 1-5 Hz; UI nudges; ring buffer retention; zero network.
- **Session end:** stop capture; finalize two MP4s; upload; trigger post-processing jobs; generate report; sync to dashboard.

# 2) Realtime module (new subsection under "Functional Requirements")

## FR1a. Realtime CV Pipeline (Edge)

- **Frame cadence:** 1-5 Hz webcam; 0.2-1 Hz screen snapshot; both downscaled to target (default 480p, min 256p).
- **Posture:** MediaPipe BlazeFace/FaceMesh + head-pose; optional BlazePose upper-body. States: {neutral, slouch, head-down, head-away, out-of-frame, micro-sleep}.
- **Activity:** heuristics on motion vectors + face/eye features; classify {focused, reading, typing-like, phone-likely, talking, absent}.
- **Screen content (image classification, not OCR):** window archetypes via lightweight CNN (e.g., ONNX Runtime Web): {IDE/docs/terminal/slides/video/short-video/social/feed/chat/games/unknown}.
- **Fusion:** hysteresis state machine with debounce (≥5 s) to reduce false positives; emits focus_event and distract_event with reason codes.
- **Edge budgets:** CPU avg <30%; memory <300 MB; auto-throttle frame rate on perf drop.

## FR1b. Realtime Storage & Privacy

- No raw frames leave device.
- Ring buffer: last N thumbnails (default N=0; off by default).
- IndexedDB: transient event stream; auto-purge after upload.
- Controls: Pause, Sensitivity slider, Screen-capture toggle.

# 3) Post-processing pipeline (new subsection under "Functional Requirements")

## FR7. End-of-Session Upload & Jobs

- **Recording:** two local files-cam.mp4, screen.mp4; container MP4/H.264; default 480p@15fps; VBR target 300-800 kbps (config: Low/Std/High).
- **Upload order:** (1) Memories.ai objects {cam, screen}; (2) Hume video expression analysis on cam.
- **Jobs:**
  - **Memories Chat API Prompt:** "Given cam and screen, segment the work session; infer task phases, app classes, distraction intervals, triggers, break taxonomy; extract step-level actions; output in schema v1.2."
  - **Hume Expressions:** derive time-series for valence, arousal, stress, frustration; resample to 1 Hz; align to segments.
  - **Merger:** join on timestamps; compute per-segment KPIs; persist session_report.json.

## FR7a. Structured Output Schema (v1.2)

{

"session_id": "uuid",

"meta": { "started_at": "iso", "ended_at": "iso", "profile": "Low|Std|High" },

"segments": \[

{

"t0":"s","t1":"s","label":"Focus|Break|Admin|Setup",

"task_hypothesis":"string",

"apps":\[{"class":"IDE|Docs|Browser|Video|Social|Chat|Slides|Terminal|Unknown","share":0.0}\],

"distractions":\[{"t0":"s","t1":"s","type":"LookAway|Phone|Video|Social|Chat|Noise","evidence":"string"}\],

"posture":{"mode":"Neutral|Slouch|HeadAway|Down|Absent","pct":0.0},

"expressions":{"frustration_mean":0.0,"valence_mean":0.0,"arousal_mean":0.0}

}

\],

"kpis":{

"focus_ratio":0.0,"avg_focus_bout_min":0.0,"num_alerts":0,

"top_triggers":\["Video","Phone","HeadAway"\],"peak_distraction_hour":"15:00-16:00"

},

"recommendations":\[{"type":"BreakSchedule|AppBlock|TaskSplit|Ergonomics","msg":"string"}\],

"artifacts":{"memories_urls":{"cam":"url","screen":"url"},"hume_job_id":"string"}

}

# 4) UX changes (append to "Minimal Setup & Web-Based UX")

- **Quality presets:** Low (256p/10fps/200 kbps), Standard (480p/15fps/500 kbps), High (720p/15fps/1000 kbps).
- **Screen capture scope:** full screen or single window; default: single window.
- **Session end modal:** show file sizes estimate; toggle "Upload now / Defer"; show privacy note ("raw video stored locally until upload; deleted after successful processing if 'Auto-delete' is on").
- **Reports tab:** render session_report.json timeline; filters by segment, trigger, posture; export CSV/JSON.

# 5) Tech stack deltas (append to "Tech Stack Considerations")

- **Recording:** MediaRecorder for MP4/H.264; mux webcam and display into separate streams; fallback WebM/VP9 in Safari → transcode client-side via FFmpeg.wasm if needed (batch, post-session).
- **Realtime CV:** MediaPipe FaceMesh/BlazePose via TF.js or ONNX Runtime Web; head-pose (PnP on landmarks) via OpenCV.js; small CNN for screen archetypes (~3-5M params, int8).
- **Post-proc calls:**
  - **Memories.ai:** Upload two assets; invoke Chat API with schema prompt; poll job; fetch JSON.
  - **Hume:** Video expression endpoint; poll; fetch 1 Hz tracks.
- **Backend:** thin Node/Express proxy for API keys + webhook receivers; Postgres for session_report storage; signed URLs to artifacts; no raw media retention after confirm.
- **Workers:** Web Workers for realtime CV; background fetch() with keepalive for uploads.

# 6) Privacy, retention, and bandwidth (new subsection under "Non-Functional Requirements")

- **Default retention:** raw cam.mp4 and screen.mp4 deleted after successful upload + report merge; retention window configurable (0, 24h, 7d).
- **Local-only mode:** skip uploads; produce local report using cached embeddings/thumbnails only; disables Hume and Memories features.
- **Bandwidth caps:** hard cap per session (e.g., 300 MB) with adaptive transcode before upload; warn user if projected size exceeds cap.
- **Auditability:** user can preview clips tied to flagged distraction intervals before upload.

# 7) Evals and ablations (map to rubric; add under "Objectives & Success Metrics" or separate "Evals")

- **Latency eval:** alert time (event→nudge) p95 < 1.5 s.
- **Accuracy eval:** posture confusion matrix; screen archetype F1 ≥ 0.85 on held-out clip set.
- **Ablation:** disable posture; measure Δfocus_ratio; disable screen archetype; measure Δfalse-positives; show charts in README.
- **Load test:** 2-hour session on mid-tier laptop; CPU mean <30%, dropped-frame rate <10%.
- **Cost awareness:** per session API cost target <\$0.05 at Std profile (Memories + Hume), with sampling gates.

# 8) Agentic behavior hooks (append under "Goal Management and Agentic Assistance")

- **Realtime hooks:** if distract_event count ≥ N in 20 min, auto-suggest micro-break; if screen:video appears during focus, prompt to switch back; if posture "Slouch/HeadDown" >60% of last 10 min and frustration↑, suggest posture reset + 2-min reset.
- **Post-proc hooks:** recommendations generated from session_report.kpis + rules; offer one-click plan (Pomodoro length, blocklist suggestion, break slots).

# 9) API contracts (new appendix)

### POST /api/session/start

- Body: { quality:"Low|Std|High", screen:true|false }
- Resp: { session_id }

### POST /api/session/end

- Body: { session_id, metrics:{…} }
- Side effects: initiate uploads; return job ids.

### POST /api/upload

- Multipart: cam.mp4, screen.mp4, session_id
- Resp: { memories_ids:{cam,screen} }

### POST /api/process

- Body: { session_id, memories_ids, hume_job_id? }
- Resp: { report_url, status }

### GET /api/report/:session_id

- Resp: session_report.json

# 10) Sequence diagrams (textual; add as appendix)

**Realtime**

User -> WebApp: Start session

WebApp -> Camera/Screen: getUserMedia/getDisplayMedia

WebApp (Worker): CV loop (posture/activity/screen-class) @ 1-5 Hz

Worker -> UI: events (focus/distract) with reasons

UI -> User: nudges (debounced)

**Post-processing**

User -> WebApp: End session

WebApp: finalize cam.mp4 + screen.mp4

WebApp -> Backend: upload(cam, screen)

Backend -> Memories.ai: store assets

Backend -> Hume: submit cam.mp4 for expressions

Backend: poll jobs, merge outputs -> session_report.json

Backend -> WebApp: report ready

# 11) Risks deltas (append to "Risks & Open Issues")

- **Recording compatibility:** MP4/H.264 availability varies by browser; include WebM fallback + optional client-side transcode.
- **Upload size/time:** long sessions produce large files; enforce caps, chunked uploads, resumable transport; expose ETA.
- **Memories/Hume quotas:** enforce sampling and profile presets; backoff on 429; queue jobs.
- **LLM hallucination in post-proc:** constrain with strict schema; add validation; surface "confidence" per field.

# 12) README/demo checklist (for "Completeness & Reliability")

- One-command setup (pnpm + env template).
- Demo script: 10-min session; end; show report.
- Evals notebook: latency, CPU, F1, ablations.
- Privacy doc: data paths, toggles, retention table.

This integration preserves your original privacy stance, meets hackathon rubric criteria (architecture clarity, autonomy, memory, affect, evals), and bounds complexity by pushing LLM/VLM to post-processing while keeping realtime edge CV lightweight.

## Conclusion

The Focus Guardian ADHD Distraction Analysis App is a comprehensive solution that combines real-time on-device AI with cloud-assisted long-term analysis. By addressing distraction at the moment it occurs and learning from each user's patterns, it aims to provide a personalized coach for improving focus. The design balances **cutting-edge tech** (emotion AI, semantic memory) with **practical considerations** (privacy, simplicity, efficiency), making the product both innovative and user-friendly. If successfully implemented, this app could significantly help users with ADHD (and even those without it) to understand their attention habits and foster better work/study routines.

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