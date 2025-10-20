# Introduction

**Version:** v1.2

Welcome to the Memories.ai API documentation. Memories.ai is a next-generation video understanding platform that enables human-like comprehension of videos through advanced AI and multimodal processing.

---

## Contents

1. [Memories.ai API Documentation](#memoriesai-api-documentation)

---

# API Overview | Memories.ai

Version: v1.2

This section provides an overview and key concepts of the memories.ai API platform:

*   **Two Authentication Methods**:
    
    *   **API Key**: Easily call the memories.ai API using your personal API key, available in your memories.ai account.
    *   **OAuth2 Authentication (O2O)**: A two-step verification process better suited for business use cases that require enhanced security.
*   **REST-Centric Design**:  
    Memories.ai APIs follow REST principles and are compatible with most modern programming languages.
    
*   **Callback Mechanism**:  
    Video processing can take time. To streamline workflow, developers can provide a callback URL. Memories.ai will notify this endpoint once video processing is complete — improving automation and efficiency.
    

The diagram below illustrates the architecture of memories.ai’s backend video processing pipeline:

Encoding refers to the process of transcoding your uploaded video and generating an index for efficient retrieval. It preserves key information from the video and links all your content into a structured knowledge graph. This one-time process optimizes downstream tasks such as semantic search, retrieval, and interaction.

Memories.ai uses a cutting-edge multimodal approach to analyze videos comprehensively. It integrates information from visual, audio, text, and metadata sources to build a richer, more human-like understanding of the content.

When creating your memories.ai API key, you can optionally register a public callback URL (such as a server or test endpoint). This allows your application or server to automatically receive status updates on tasks like video indexing or processing.

To try this feature, you can use tools like [Beeceptor]() to quickly create a temporary test endpoint.
# Quick Start | Memories.ai

Version: v1.2

This guide shows how to use the memories.ai API to build your own personal video management and understanding assistant.

1.  Sign up for your memories.ai account.
2.  Upload your video for encoding.
3.  [search]() highlights from videos!
4.  Start [chatting]() with videos!

The diagram below demonstrates the steps:

You can interact with the platform using any HTTP client to send requests and receive responses.

*   After signing up, navigate to the [API settings]() page to create your personal API key.
*   Videos you upload must meet the following requirements:
    *   **Video and audio formats**: The video must be encoded in a format supported by [FFmpeg]().
    *   **Audio track**: If you intend to use the [audio transcription]() feature, the uploaded video should include an audio track.

*   Use this example Jupyter notebook as a starting point to explore the Memories.ai API and to build your own application. [Example jupyter notebook]()

*   If you encounter an "Exceeding limit" error, please refer to [Rate Limit]() for more information.
# Create your key | Memories.ai

Version: v1.2

This guide walks you through how to access memories.ai APIs securely using your API key.

*   A valid **memories.ai account**
*   An API key (generated after registration)

To use the memories.ai API, you’ll first need to create an account:

1.  Go to the [memories.ai Login Page]().
2.  Sign in using Google to complete your registration.
3.  Follow the developer onboarding steps outlined below.

Once logged in, navigate to the **API Settings** page:

Click the **Create API Key** button:

Store your API key securely. You’ll need to include it in the headers or parameters of all API requests.

> If you prefer, you can continue using the legacy V1.0 authentication method by clicking the **Accredit** button. This method uses a callback URL to obtain a code and exchange it for a token. For more details, refer to the V1.0 authentication guide.
# Memorise.ai API | Memories.ai

© 2025 Memories.ai Platforms, Inc. All Rights Reserved.

Email: [contact@memories.ai]()
# Upload Video | Memories.ai

Version: v1.2

Easily upload your video to Memories.ai. Once uploaded, the video enters Memories.ai’s processing pipeline, where it is analyzed and prepared for further use. You can check the processing status at any time via the API.

You can optionally include a `unique_id` when uploading a video to associate it with a specific **user**, **folder**, **workspace**, or **namespace** in your application.

*   **Purpose**: Enables multi-tenant or organized content management by grouping videos under the same `unique_id`.
*   **Default Behavior**: If omitted, `unique_id` is automatically set to `"default"`.
*   **When to Use**: Recommended if your application has multiple users or logical groupings.  
    If you do not require a namespace-like concept, you can skip this parameter.

Optionally, include a callback URI in your request body to receive automatic status updates—no need to wait around for the results!

*   [Upload from Local File]() – Upload a video directly from your device.
*   [Upload from streaming URL]() – Upload a video using a 【playable link.
*   [Upload from platform URL]() – Upload a video using a [direct video platform url]().
*   [Upload from creator URL]() – Upload a video from a [video platform\'s creator link]().

*   If your video status shows **"FAILED"** shortly after uploading, it is most likely due to an unsupported [video codecs]().
# Search | Memories.ai

Version: v1.2

Memories.ai stores videos like human memory by pre-indexing uploaded content. When needed, this stored context is retrieved intelligently and automatically, allowing the vision-language model to reason effectively. By integrating all available information, such as visual content, audio, text, and metadata, memories.ai builds a knowledge graph to enable comprehensive, deep understanding of videos.

*   [Search video]() – Perform semantic search across all videos or a specified set to find the most relevant ones

*   Currently, search supports **prompts in English only**.
*   Prompts in other languages (e.g., Chinese, French, Spanish) are not yet supported.
# Chat | Memories.ai

Version: v1.2

The Video Chat API lets developers build rich, LLM-powered interactions grounded in video content. By supplying one or more `videoNos`, you can enable Memories.ai to analyze, summarize, annotate, or perform complex reasoning across your uploaded videos. Typical use cases include generating highlights, creating chapters, suggesting edits, and providing tailored insights.

To help developers better understand how to interact with the memories.ai Chat API, we’ve provided several example questions. You can refer to the examples below to structure your own prompts and get high-quality responses.

Below are sample questions and responses for testing the memories.ai Chat API. Use them as templates to guide your own queries.

**Q: Summary – Generate summaries of these videos**

**A:**  
Here are the summaries of the videos:  
**Video 1:** This video features the men\'s 400-meter race, highlighting top athletes like Van Dijk, Matthew Hudson-Smith, Karani James, and LeSean Merritt. Van Dijk wins with a record-breaking time of 43.03, setting a new world record. Karani James and LeSean Merritt secure silver and bronze, respectively. The victory is celebrated as a historic moment for South Africa, with commentators praising Van Dijk\'s performance and Usain Bolt congratulating him.

**Q: Editing Suggestions – Give me editing suggestions for these videos, from content structure, screenshots, rhythm, and audience experience, in detail**

**A:**  
Here are some editing suggestions for the video:

**Content Structure:**

*   **Opening Hook:** Start with the exciting moment of Van Dijk breaking away from the pack (around 0:03:05). Then rewind to the beginning to build context.
*   **Athlete Introductions:** Condense introductions. Focus on Van Dijk, Karani James, and LeSean Merritt.
*   **Emphasize the Record:** Use graphics to show the previous world record and how Van Dijk surpassed it.
*   **Bolt\'s Recognition:** Expand on Usain Bolt’s reaction. Include slow-motion replays and sound bites.

**Screenshots:**

*   **Close-ups:** Show athlete expressions mid-race.
*   **Wide Shots:** Capture the stadium’s atmosphere.
*   **Slow Motion:** Use it for race start and Van Dijk’s final push.
*   **Reactions:** Show crowd and athlete responses.

**Rhythm:**

*   **Build-up:** Increase tempo and cut frequency toward race climax.
*   **Dramatic Pause:** Use silence or slow fade after the record is broken.
*   **Variation:** Alternate between fast-paced and reflective segments.

**Audience Experience:**

*   **Context:** Briefly explain the race’s significance.
*   **Emotion:** Emphasize the joy, disappointment, and energy.
*   **Sound Design:** Layer in crowd noise, footsteps, and finish buzzer.
*   **Call to Action:** End with a prompt for comments or shares.

**Q: Highlights – Find the highlights of these videos and give timestamps**

**A:**  
Here are the highlights of the video:

*   **Athlete Introductions:** 00:00:31–00:00:37, 00:00:50–00:01:26
*   **The Start:** 00:02:31–00:02:35
*   **Van Dijk Takes the Lead:** 00:02:58–00:03:00
*   **Van Dijk Wins & Breaks Record:** 00:03:05–00:03:19
*   **Bolt Congratulates Van Dijk:** 00:06:08–00:06:19
*   **Commentary Moments:** 00:03:34–00:03:42, 00:04:48–00:04:52, 00:05:15–00:05:21, 00:05:58–00:06:06

**Q: Chapterize – Divide these videos into chapters with timestamps and descriptions**

**A:**  
Here\'s a breakdown of the video:

**Chapter 1: Introduction (0:00:00 – 0:00:31)**  
Sets the stage for the men\'s 400m final, teasing the big event.

**Chapter 2: Athlete Spotlight (0:00:31 – 0:02:20)**  
Introduces the runners, their credentials, and what’s at stake.

**Chapter 3: The Race Begins (0:02:20 – 0:03:05)**  
Focus on Van Dijk’s quick start and race dynamics.

**Chapter 4: Van Dijk\'s Historic Victory (0:03:05 – 0:03:42)**  
Showcases the moment Van Dijk breaks the record.

**Chapter 5: Reactions & Analysis (0:03:42 – 0:04:52)**  
Commentary, reactions, and technical breakdown of the race.

**Chapter 6: The Significance (0:04:52 – 0:06:41)**  
Wrap-up, Bolt’s praise, and the race’s legacy.

**Q: Hashtags & Topics – Generate hashtags and titles for these videos**

**A:**

**Suggested Video Titles:**

*   Van Dijk SHATTERS World Record! Unbelievable 400m Olympic Victory
*   History Made: Van Dijk\'s Record-Breaking 400m Run
*   From South Africa to the World: Van Dijk\'s Golden Moment
*   Unstoppable: Van Dijk\'s Dominant 400m Olympic Win
*   Bolt Was Right! Van Dijk’s 400m World Record Performance

**Hashtags:**

`#Olympics` `#Athletics` `#400m` `#WorldRecord` `#VanDijk`  
`#SouthAfrica` `#UsainBolt` `#KaraniJames` `#LeSeanMerritt`  
`#OlympicGames` `#TrackAndField` `#HistoryMade` `#GoldMedal` `#Beijing`

**Q: TikTok – Write titles, descriptions, and tags for TikTok**

**A:**

**Video Title Ideas:**

*   🤯 WORLD RECORD SHATTERED! You won\'t BELIEVE this race!
*   UNSEEN SPEED! 400m Record BROKEN!
*   Bolt KNEW! This runner SHOCKED the world!

**Description:**  
Watch Van Dijk make history in the 400m! This race was INSANE! Usain Bolt saw this coming!

**Tags:**  
`#Olympics` `#TrackAndField` `#Running` `#VanDijk` `#RecordBreaking`  
`#Sports` `#UsainBolt` `#SouthAfrica` `#Viral` `#Inspiration` `#FYP`

**Q: What type of audience is this video suitable for?**

**A:**  
This video is ideal for:

*   Sports fans
*   Track and field followers
*   Olympic history enthusiasts
*   Viewers who enjoy athletic achievement stories
*   Audiences looking for emotional and motivational moments
# Transcription video

Version: v1.2

Transcription API converts visual and autio context of the video into text representations. You could transcribe an uploaded vidoe in two ways:

*   [`VIDEO`](): Transcribing the video\"s visual content into text.
*   [`AUDIO`](): Transcribing the video\"s audio content into text.
    *   `speaker`: Recognizing each speaker in the video.
*   [`Summary`](): Get the summary of the video.
    *   `chapter`: summarize the video along the timeframe.
    *   `topic`: summarize the video by events/topics.

*   You have created a memories.ai API key.
*   At least one video has been uploaded to memories.ai and is currently in the PARSE status.
# Utils | Memories.ai

This page documents utility APIs for managing and retrieving metadata about videos and sessions in the Memories.ai platform. These endpoints are useful for monitoring uploaded assets, organizing session data, and cleaning up unused videos.

*   [List videos]() – List videos under a unique id.
*   [List sessions]() – List chat sessions under a unique id.
*   [Delete videos]() – delete videos under a unique id.
# Caption & Human Re-identification

Version: v1.2

Memories.ai provides advanced APIs to **understand media content**. With these APIs, you can generate captions and summaries for videos and images, while optionally identifying and tracking specific people using **human re-identification (ReID)**.

Once submitted, your media is analyzed asynchronously, and the results (captions, summaries, or detected individuals) are sent back to your application through a callback URL.

*   **Video Caption**  
    Automatically summarize video content and describe scenes. Supports human re-identification to detect people based on reference images.  
    → [Video Caption API]()
    
*   **Image Caption**  
    Generate captions or descriptions from images. Works with both image URLs and file uploads.  
    → [Image Caption API]()
    
*   **Human Re-identification (ReID)**  
    Identify and track specific people in video or image content by providing reference images. This feature is integrated into both Video and Image Caption APIs.  
    → [Human ReID]()
    

You can include a `callback` URL in your requests to receive results automatically when analysis is complete. This removes the need to poll for updates.

*   **Content Understanding**: Summarize long videos or describe images in plain language.
*   **Security & Monitoring**: Detect and re-identify individuals across multiple videos or images.
*   **Accessibility**: Provide captions for visually impaired users or enhance media metadata.

*   **Is Human ReID a separate API?**  
    No. Human ReID is enabled by adding the `persons` parameter in Video or Image Caption requests.
    
*   **Do I need a callback URL?**  
    Yes, results are delivered asynchronously via the `callback` parameter. You must provide a reachable endpoint.
    
*   **What are the media limitations?**
    
    *   Videos: Max size 20 MB, duration 20–300 seconds
    *   Up to 5 person reference images can be included for ReID


