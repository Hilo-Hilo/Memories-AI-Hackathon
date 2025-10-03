# Memories.ai API Documentation

This document provides a comprehensive overview of the Memories.ai API, combining all available documentation pages into a single resource.

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


---

# Upload image from file

Version: v1.2

Use this API to upload one or multiple images from your local storage.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have created a memories.ai API key.
*   The images must meet the following requirements:
    *   **Formats**: JPEG, PNG, or WebP are supported.
    *   **File size**: Each file must be within the platform’s maximum upload limit.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/upload_img`

    import requestsimport osKEY = "<YOUR_API_KEY>"headers = {"Authorization": "<YOUR_API_KEY>"}files = [    ("files", ("test1.jpg", open(r"test1.png", "rb"), "image/jpg")),    ("files", ("test2.png", open(r"test2.png", "rb"), "image/png"))]data = {    "unique_id": "default",    "datetime_taken": "2025-09-07 22:52:00",    "camera_model": "Canon EOS 5D",    "latitude": "39.9042",    "longitude": "116.4074"}response = requests.post(    "https://api.memories.ai/serve/api/v1/upload_img",    headers=headers,    files=files,    data=data)print("Status Code:", response.status_code)print("Response:", response.text)

Replace the following placeholders:

*   `YOUR_API_KEY`: Your actual memories.ai API key.
*   `files`: Paths to your image files.
*   `unique_id`: A unique identifier for workspace/namespace/user identification.
*   `datetime_taken`: (Optional) Timestamp when the image was taken.
*   `camera_model`: (Optional) Camera used to capture the image.
*   `latitude` & longitude: (Optional) Geo-coordinates of where the photo was taken.

## Request Body[​]()

    files: [binary]unique_id: "<UNIQUE_ID>"datetime_taken: "<YYYY-MM-DD HH:MM:SS>"camera_model: "<MODEL_NAME>"latitude: "<LATITUDE>"longitude: "<LONGITUDE>"

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| files | body | string (binary) | Yes | One or multiple image files to upload |
| unique\_id | body | string | No | Identifier for workspace/namespace/user |
| datetime\_taken | body | string | No | Date and time when the image was captured (format: `YYYY-MM-DD HH:MM:SS`) |
| camera\_model | body | string | No | Camera model metadata |
| latitude | body | string | No | GPS latitude of where the image was captured |
| longitude | body | string | No | GPS longitude of where the image was captured |
| Authorization | header | string | Yes | Authorization API key |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": [    {      "id": "568102998803353601",    },    {      "id": "568102998803353602",    }  ]}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Status code |
| msg | string | Yes | Message |
| data | array | Yes | Array of uploaded image objects |
| » imageNo | string | Yes | Unique image identification number |
| » imageName | string | Yes | Name of the uploaded image |
| » uploadStatus | string | Yes | Status of the image upload |
| » uploadTime | string | Yes | Image upload timestamp |

*   You can upload multiple images in a single request by providing multiple files entries. Metadata fields (datetime\_taken, camera\_model, latitude, longitude) apply to all uploaded images within that request.


---

# Search | Memories.ai

Version: v1.2

Memories.ai stores videos like human memory by pre-indexing uploaded content. When needed, this stored context is retrieved intelligently and automatically, allowing the vision-language model to reason effectively. By integrating all available information, such as visual content, audio, text, and metadata, memories.ai builds a knowledge graph to enable comprehensive, deep understanding of videos.

*   [Search video]() – Perform semantic search across all videos or a specified set to find the most relevant ones

*   Currently, search supports **prompts in English only**.
*   Prompts in other languages (e.g., Chinese, French, Spanish) are not yet supported.


---

# Search from private library

Version: v1.2

Using a natural language query, this API searches through all processed videos & images and ranks the most relevant clips or items within milliseconds. Memories.ai retrieves and ranks results based on visual, audio, or image information in a way similar to human perception. With this API, developers can access the most relevant items from their entire private library.

Searching from `BY_AUDIO`, `BY_VIDEO`, and `BY_IMAGE` is supported. The most relevant clips or items will be retrieved and ranked according to the specified parameters.

*   You have created a memories.ai API key.
*   At least one video/image has been uploaded to memories.ai and is currently in `PARSE` status.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/search`

    import requestsheaders = {"Authorization": "<API_KEY>"}  # API keyjson_body = {    "search_param": "<YOUR_PROMPT>",  # The search query    "search_type": "BY_VIDEO",  # 'BY_AUDIO' or 'BY_VIDEO' or 'BY_IMAGE'    "unique_id": "1",  # optional    "top_k": 3,    "filtering_level": "high"  # low/medium/high}response = requests.post(    "https://api.memories.ai/serve/api/v1/search",    headers=headers,    json=json_body)print(response.json())

Replace `API_KEY` in the code above with your actual API key and `YOUR_PROMPT` with your search query.

## Request Body[​]()

    {  "search_param": "boat in the ocean",  "search_type": "BY_VIDEO",  "unique_id": "1",  "top_k": 3,  "filtering_level": "medium"}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| search\_param | body | string | Yes | Natural language search query |
| search\_type | body | string | Yes | `BY_AUDIO`: search by audio; `BY_VIDEO`: search by video clips; `BY_IMAGE`: search from uploaded images |
| unique\_id | body | string | No | A client-defined identifier to differentiate requests. Default: `default`. |
| top\_k | body | int | No | Maximum number of top results to return. Default: system-defined. |
| filtering\_level | body | string | No | Level of filtering applied to results. Options: `low`, `medium`, `high`. |

    {  "code": "0000",  "msg": "success",  "data": [    {      "videoNo": "VI576925607808602112",      "videoName": "1920447021987282945",      "startTime": "13",      "endTime": "18",      "score": 0.5221236659362116    }  ]}

    {  "code": "0000",  "msg": "success",  "data": {    "item": [      {        "latitude": 39.9042,        "longitude": 116.4074,        "id": "619915496901337088",        "name": "OIX_ZOOM",        "img_url": "https://storage.googleapis.com/.../OIX_ZOOM.jpg?...",        "datetime_taken": "1757285520000",        "camera_model": "Canon EOS 5D"      },      {        "latitude": 39.9042,        "longitude": 116.4074,        "id": "619915496901337089",        "name": "youtube head",        "img_url": "https://storage.googleapis.com/.../youtube%20head.png?...",        "datetime_taken": "1757285520000",        "camera_model": "Canon EOS 5D"      }    ],    "current_page": 0,    "page_size": 20,    "total_count": "5"  }}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Response code |
| msg | string | Yes | Message with response code |
| data | object | Yes | JSON data |
| » videoNo | string | Yes | Video identifier |
| » videoName | string | No | Video name |
| » videoStatus | string | No | Current video processing status |
| » uploadTime | string | No | Upload timestamp (ms) |
| » score | float | Yes | Relevance score of the search result |
| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Paginated search result object |
| » item | array | List of matching image entries |
| »» id | string | Unique image identifier |
| »» name | string | Image name |
| »» img\_url | string | Public URL to access the image |
| »» latitude | float | GPS latitude where the image was taken |
| »» longitude | float | GPS longitude where the image was taken |
| »» datetime\_taken | string | Timestamp when the image was captured (ms) |
| »» camera\_model | string | Camera model used to capture the image |
| current\_page | int | Current page number |
| page\_size | int | Number of results per page |
| total\_count | string | Total number of images matching the query |
| success | boolean | Indicates if the request was successful |
| failed | boolean | Indicates if the request failed |

*   **Use `top_k`:** Limit results to the most relevant items for efficiency.
*   **Filter tuning:** Adjust `filtering_level` to balance recall and precision (`low` = broad, `high` = strict).
*   **Prompt clarity:** Make search queries concise and descriptive for optimal ranking.


---

# Search from public video sources

Version: v1.2

Using a natural language query, this API searches through videos from public video platforms such as TikTok (YouTube and Instagram coming soon). Memories.ai indexes these videos and allows you to search and interact with them. You can specify the platform with the `type` parameter (`TIKTOK`, `YOUTUBE`, `INSTAGRAM`).

Searching by `BY_AUDIO` and `BY_VIDEO` is supported. The most relevant clips will be retrieved from the selected platform.

*   You have created a memories.ai API key.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/search_public`

    import requestsheaders = {"Authorization": "<API_KEY>"}  # API keyjson_body = {    "search_param": "<YOUR_PROMPT>",  # The search query    "search_type": "BY_VIDEO",  # \'BY_AUDIO\' or \'BY_VIDEO\'    "type": "TIKTOK",  # \'TIKTOK\' by default, options: \'TIKTOK\', \'YOUTUBE\', \'INSTAGRAM\'    "top_k": 3,    "filtering_level": "high"  # low/medium/high}response = requests.post(    "https://api.memories.ai/serve/api/v1/search_public",    headers=headers,    json=json_body)print(response.json())

Replace `API_KEY` in the code above with your actual API key and `YOUR_PROMPT` with your search query.

## Request Body[​]()

    {  "search_param": "Find sprint race with Usain Bolt",  "search_type": "BY_VIDEO",  "type": "TIKTOK",  "top_k": 3,  "filtering_level": "medium"}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| search\_param | body | string | Yes | Natural language search query |
| search\_type | body | string | Yes | `BY_AUDIO`: search by audio; `BY_VIDEO`: search by video and return clips |
| type | body | string | No | Platform to search. Options: `TIKTOK` (default), `YOUTUBE`, `INSTAGRAM`. |
| top\_k | body | int | No | Maximum number of top results to return. |
| filtering\_level | body | string | No | Level of filtering applied to results. Options: `low`, `medium`, `high`. |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": [    {      "videoNo": "PI-600947902470296459",      "videoName": "They played in their OPPONENTS jerseys?!?",      "startTime": "23",      "endTime": "27",      "score": 0.7350679636001586    }  ]}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Response code |
| msg | string | Yes | Message with response code |
| data | array | Yes | List of search results |
| » videoNo | string | Yes | Video identifier |
| » videoName | string | Yes | Video name/title |
| » startTime | string | No | Start timestamp (seconds) |
| » endTime | string | No | End timestamp (seconds) |
| » score | float | Yes | Relevance score of the search result |

*   **Platform selection:** Use the `type` parameter to specify the desired dataset (TikTok, YouTube, Instagram).
*   **Use `top_k`:** Limit results to the most relevant items for efficiency.
*   **Filter tuning:** Adjust `filtering_level` to balance recall and precision (`low` = broad, `high` = strict).
*   **Prompt clarity:** Make queries concise and descriptive for optimal retrieval.


---

# Search from audio

Version: v1.2

The **Search from Audio** API provides a way to perform accurate text-match searches over audio transcripts stored in the system.  
You can query both **private transcripts** (associated with your account via `search_audio_transcripts`) and **public transcripts** (shared, via `search_public_audio_transcripts`).

These endpoints help you find relevant transcript snippets by keyword or natural language queries, enabling quick navigation within large audio datasets.

*   `https://api.memories.ai`

**POST** `/v1/search_audio_transcripts`

**POST** `/v1/search_public_audio_transcripts`

All requests must include the API key in the `Authorization` header.

    Authorization: <your_key>

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `page` | int | No | Page number (default: 1). |
| `page_size` | int | No | Number of results per page (default: 50, max: 100). |
| `query` | string | Yes | The search string or natural language query. |
| `unique_id` | string | No\* | A client-defined identifier to differentiate requests (private search only). |

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_audio_transcripts"params = {    "page": 1,    "page_size": 100,    "unique_id": "test",    "query": "where is the love"}headers = {  "Authorization": "<your_key>"}response = requests.get(url, headers=headers, params=params)print(response.text)

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_public_audio_transcripts"params = {    "page": 1,    "page_size": 100,    "query": "I don\'t know what is"}headers = {  "Authorization": "<your_key>"}response = requests.get(url, headers=headers, params=params)print(response.text)

The response is returned in JSON format with pagination support.  
Typical fields include:

    {  "results": [    {      "id": "abc123",      "audio_id": "xyz789",      "snippet": "relevant text from transcript...",      "timestamp": "00:05:23"    }  ],  "page": 1,  "page_size": 100,  "total": 250}

| Field | Type | Description |
| --- | --- | --- |
| `results` | array | A list of matching transcript snippets. Each item contains details below. |
| ├─ `id` | string | Unique identifier for the transcript snippet. |
| ├─ `audio_id` | string | Identifier of the audio file the snippet belongs to. |
| ├─ `snippet` | string | Extract of the transcript text relevant to the query. |
| ├─ `timestamp` | string | Timestamp in the audio where the snippet occurs (HH:MM:SS). |
| `page` | int | Current page number of the result set. |
| `page_size` | int | Number of results per page. |
| `total` | int | Total number of results available. |


---

# Search for similar images

Version: v1.2

The **Search Similar Images** API allows you to upload an image and search for visually similar images or videos within the system. Two endpoints are available:

*   **Public Similar Image Search** (`search_public_similar_images`) — compares the uploaded image with public datasets (TikTok, YouTube, Instagram).
*   **Private Similar Image Search** (`search_similar_images`) — compares the uploaded image with your own private library.

*   `https://api.memories.ai`

**POST** `/v1/search_public_similar_images`

**POST** `/v1/search_similar_images`

All requests must include the API key in the `Authorization` header.

    Authorization: <your_key>

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | string | No | The dataset to search against. Options: `TIKTOK`, `YOUTUBE`, `INSTAGRAM`. Default: `TIKTOK`. |
| `file` | file | Yes | The image file to upload and compare. |
| `similarity` | int | No | The threshold (0-1) for filtering out results. |
| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `unique_id` | string | No | A client-defined identifier to differentiate requests. |
| `file` | file | Yes | The image file to upload and compare. |
| `similarity` | int | No | The threshold (0-1) for filtering out results. |

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_public_similar_images"payload = {"type": "","similarity": 0.8}  # default TIKTOK (options: TIKTOK, YOUTUBE, INSTAGRAM)files = [  ("file", ("<IMAGE_NAME.png>", open("<PATH_TO_YOUR_IMAGE.png>","rb"), "image/png"))]headers = {  "Authorization": "<YOUR_API_KEY>"}response = requests.post(url, headers=headers, data=payload, files=files)print(response.text)

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_similar_images"payload = {"unique_id": "test", "similarity": 0.8}files = [  ("file", ("<IMAGE_NAME.png>", open("<PATH_TO_YOUR_IMAGE.png>","rb"), "image/png"))]headers = {  "Authorization": "<YOUR_API_KEY>"}response = requests.post(url, headers=headers, data=payload, files=files)print(response.text)

The response is returned in JSON format. Typical fields include:

    {  "results": [    {      "id": "abc123",      "image_url": "https://cdn.example.com/images/abc123.png",      "similarity_score": 0.92,      "source": "TIKTOK"    }  ],  "total": 50}

| Field | Type | Description |
| --- | --- | --- |
| `results` | array | A list of similar image matches. |
| ├─ `id` | string | Unique identifier of the matched image. |
| ├─ `image_url` | string | URL of the matched image. |
| ├─ `similarity_score` | float | Similarity score (0–1, higher = more similar). |
| ├─ `source` | string | Dataset source (e.g., `TIKTOK`, `YOUTUBE`, `INSTAGRAM`). |
| `total` | int | Total number of matches found. |


---

# Chat | Memories.ai

Version: v1.2

The Video Chat API lets developers build rich, LLM-powered interactions grounded in video content. By supplying one or more `videoNos`, you can enable Memories.ai to analyze, summarize, annotate, or perform complex reasoning across your uploaded videos. Typical use cases include generating highlights, creating chapters, suggesting edits, and providing tailored insights.

To help developers better understand how to interact with the memories.ai Chat API, we’ve provided several example questions. You can refer to the examples below to structure your own prompts and get high-quality responses.

Below are sample questions and responses for testing the memories.ai Chat API. Use them as templates to guide your own queries.

**Q: Summary – Generate summaries of these videos**

**A:**  
Here are the summaries of the videos:  
**Video 1:** This video features the men's 400-meter race, highlighting top athletes like Van Dijk, Matthew Hudson-Smith, Karani James, and LeSean Merritt. Van Dijk wins with a record-breaking time of 43.03, setting a new world record. Karani James and LeSean Merritt secure silver and bronze, respectively. The victory is celebrated as a historic moment for South Africa, with commentators praising Van Dijk's performance and Usain Bolt congratulating him.

**Q: Editing Suggestions – Give me editing suggestions for these videos, from content structure, screenshots, rhythm, and audience experience, in detail**

**A:**  
Here are some editing suggestions for the video:

**Content Structure:**

*   **Opening Hook:** Start with the exciting moment of Van Dijk breaking away from the pack (around 0:03:05). Then rewind to the beginning to build context.
*   **Athlete Introductions:** Condense introductions. Focus on Van Dijk, Karani James, and LeSean Merritt.
*   **Emphasize the Record:** Use graphics to show the previous world record and how Van Dijk surpassed it.
*   **Bolt's Recognition:** Expand on Usain Bolt’s reaction. Include slow-motion replays and sound bites.

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
Here's a breakdown of the video:

**Chapter 1: Introduction (0:00:00 – 0:00:31)**  
Sets the stage for the men's 400m final, teasing the big event.

**Chapter 2: Athlete Spotlight (0:00:31 – 0:02:20)**  
Introduces the runners, their credentials, and what’s at stake.

**Chapter 3: The Race Begins (0:02:20 – 0:03:05)**  
Focus on Van Dijk’s quick start and race dynamics.

**Chapter 4: Van Dijk's Historic Victory (0:03:05 – 0:03:42)**  
Showcases the moment Van Dijk breaks the record.

**Chapter 5: Reactions & Analysis (0:03:42 – 0:04:52)**  
Commentary, reactions, and technical breakdown of the race.

**Chapter 6: The Significance (0:04:52 – 0:06:41)**  
Wrap-up, Bolt’s praise, and the race’s legacy.

**Q: Hashtags & Topics – Generate hashtags and titles for these videos**

**A:**

**Suggested Video Titles:**

*   Van Dijk SHATTERS World Record! Unbelievable 400m Olympic Victory
*   History Made: Van Dijk's Record-Breaking 400m Run
*   From South Africa to the World: Van Dijk's Golden Moment
*   Unstoppable: Van Dijk's Dominant 400m Olympic Win
*   Bolt Was Right! Van Dijk’s 400m World Record Performance

**Hashtags:**

`#Olympics` `#Athletics` `#400m` `#WorldRecord` `#VanDijk`  
`#SouthAfrica` `#UsainBolt` `#KaraniJames` `#LeSeanMerritt`  
`#OlympicGames` `#TrackAndField` `#HistoryMade` `#GoldMedal` `#Beijing`

**Q: TikTok – Write titles, descriptions, and tags for TikTok**

**A:**

**Video Title Ideas:**

*   🤯 WORLD RECORD SHATTERED! You won't BELIEVE this race!
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


---

# Video Chat | Memories.ai

Version: v1.2

By providing the `videoNos`, developers can ask the Memories.ai to analyze, summarize, annotate, or perform other reasoning tasks across all uploaded videos. This API also supports streaming responses to reduce latency during generation.

*   You have created a memories.ai API key.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   The video is currently in the `PARSE` status.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/chat`

**POST** `/serve/api/v1/chat_stream`

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",    "Accept": "text/event-stream"}payload = {    "video_nos": ["<VIDEO_ID_1>", "<VIDEO_ID_2>"],  # List of video IDs to chat about    "prompt": "Summarize the emotional moments in these videos",  # User query    "session_id": "<SESSION_ID>",  # Chat session ID    "unique_id": "<UNIQUE_ID>",}response = requests.post(    "https://api.memories.ai/serve/api/v1/chat_stream",    headers=headers,    json=payload,    stream=True)if response.status_code != 200:    print(response.status_code)    print(response.text)else:    try:        for line in response.iter_lines(decode_unicode=True):            if line:                print(line)                if line.strip().lower() == \'data:"done"\':                    print("\n")                    break                if line.startswith("data:"):                    print(line.replace("data:", "").strip(), end="", flush=True)    except Exception as e:        print(str(e))

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",}payload = {    "video_nos": ["<VIDEO_ID_1>", "<VIDEO_ID_2>"],  # List of video IDs to chat about    "prompt": "Summarize the emotional moments in these videos",  # User query    "session_id": "<SESSION_ID>",  # Chat session ID    "unique_id": "<UNIQUE_ID>",}response = requests.post(    "https://api.memories.ai/serve/api/v1/chat",    headers=headers,    json=payload,    stream=False)if response.status_code != 200:    print(response.status_code)    print(response.text)else:    try:        for line in response.iter_lines(decode_unicode=True):            if line:                print(line)                if line.strip().lower() == \'data:"done"\':                    print("\n")                    break                if line.startswith("data:"):                    print(line.replace("data:", "").strip(), end="", flush=True)    except Exception as e:        print(str(e))

## Request Body[​]()

    {  "videoNos": [    "string"  ],  "prompt": "string",  "session_id": "123456",  "unique_id": "default",}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| Accept | header | string | No | `text/event-stream` for streaming mode |
| video\_nos | body | \[string\] | Yes | list of video numbers |
| prompt | body | string | Yes | natural language prompt |
| session\_id | body | int | No | ID of the chat session |
| unique\_id | body | string | No | `default` by default |

🧠 Thinking Message

    {    "type": "thinking",    "title": "Based on selected videos, fetch detailed information",     "content": "Okay, the user wants a \"Video summary.\" I\'ve been given some selected videos and need to fetch their detailed information to understand their content. This means I need to go",    "sessionId": "606120397607260160"}

🔁 Reference Message (ref)

    {	"type": "ref",	"sessionId": "606143186439766016",	"ref": [{		"video": {			"duration": "10",			"video_no": "VI606140356924534784",			"video_name": "test_video_gz_visual_understanding_fuse_s9_video_fuse_4_video_fuse_4"		},		"refItems": [{			"videoNo": "VI606140356924534784",			"startTime": 23,			"type": "keyframe"		}		{			"videoNo": "VI606140356924534784",			"startTime": 30,			"type": "visual_ts",			"endTime": 36,			"text": "A close-up view shows a collection of items on a concrete surface. To the left, two brown, round objects resembling small barrels or planters are visible. One has a blue lid or insert. Next to them, a black corrugated pipe is partially visible, along with a red flexible tube and a yellow pole with a red tip. A grey, textured wall or fence dominates the right side of the frame, with wooden planks visible at the top right."		},{			"videoNo": "VI606140356924534784",			"startTime": 30,			"type": "audio_ts",			"endTime": 36,			"text": "A close-up view shows a collection of items on a concrete surface. To the left, two brown, round objects resembling small barrels or planters are visible. One has a blue lid or insert. Next to them, a black corrugated pipe is partially visible, along with a red flexible tube and a yellow pole with a red tip. A grey, textured wall or fence dominates the right side of the frame, with wooden planks visible at the top right."		}]	}]}

💬 Content Message

    {  "type": "content",  "role": "assistant",  "content": "A\" shape, is suggested to be inspired by Eiffel\'s past",  "sessionId": "606122521255088128"}

✅ Response End Example Success Response (Status Code: 200)

    {  "code": "SUCCESS",  "data": "Done"}

⚠️ Error End Conditions Any final response where "data" is not "Done" is considered an error. Common examples include: "data": "Error" "data": "No videos found for the provided video numbers." "data": "user don\'t login" "data": "Video is not parsed:"

Status code **200**

    {  "code": "SUCCESS",  "data": "Done"}

| Name | Type | Required | Restriction | Description |
| --- | --- | --- | --- | --- |
| code | string | true | none | Response code |
| data | object or string | true | none | JSON data. `"Done"` on success; error message string or structured data otherwise |
| type | string | true | enum | Type of message, e.g., `"thinking"`, `"ref"`, `"content"` |
| title | string | false | none | Title of the thinking message (used when `type` is `"thinking"`) |
| content | string | false | none | Text content of the message (used in `"thinking"` or `"content"` types) |
| sessionId | string | true | UUID/ID | ID of the current session |
| role | string | false | enum | Role of the responder; currently used with `"assistant"` |
| ref | array | false | none | List of reference objects containing video and timestamp-based metadata |
| video | object | true | nested | Video metadata (only when `type` is `"ref"`) |
| video\_no | string | true | none | Unique video identifier |
| video\_name | string | true | none | Name of the video |
| duration | string or number | true | seconds | Duration of the video |
| refItems | array | true | none | Reference annotations such as `keyframe`, `visual_ts`, `audio_ts` |
| videoNo | string | true | none | Video identifier in `refItems` (redundant with `video_no`) |
| startTime | number | true | seconds | Start timestamp of the referenced segment |
| endTime | optional | seconds | End timestamp (if applicable, e.g., for `visual_ts` or `audio_ts`) |
| text | string | optional | none | Transcribed or described content of the referenced segment |


---

# Video Marketer

Version: v1.2

We have indexed over **1 million** TikTok videos for you to explore our **Large Visual Memory Model** and **Agentic QA System**.  
With this API, you can chat directly with insights from the entire 1-million-video dataset—no need to manually select videos beforehand!

1.  You could use "@xxx" or "#xxx" to filter out videos from a certain creator or hashtag when querying videos in the video marketer public vidoe pool. E.g. "What does @theshowlorios recently talk about?"

*   You have created a memories.ai API key.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/marketer_chat`

**POST** `/serve/api/v1/marketer_chat_stream`

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",}payload = {    "prompt": "What does nike recently post?",  # User query    "session_id": "",  # Chat session ID    "unique_id": '1' # unique id for user/workspace/namespace management}response = requests.post(    "https://api.memories.ai/serve/api/v1/marketer_chat",    headers=headers,    json=payload,    stream=False)print(response.status_code)print(response.json())

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",    "Accept": "text/event-stream"}payload = {    "prompt": "What does nike recently post?",  # User query    "session_id": "",  # Chat session ID, Optional    "unique_id": '<UNIQUE_ID>' # Optional    "type": "TIKTOK", # 'TIKTOK' by default}response = requests.post(    "https://api.memories.ai/serve/api/v1/marketer_chat_stream",    headers=headers,    json=payload,    stream=True)if response.status_code != 200:    print(response.status_code)    print(response.text)else:    try:        full_chunks = []        for line in response.iter_lines(decode_unicode=True):            if not line:                continue            lower = line.strip().lower()            if lower in ('data:"done"', "data:[done]", "data:done", "[done]", "done"):                print("\n")                break            if line.startswith("data:"):                data = line.replace("data:", "", 1).strip()                text_piece = None                try:                    obj = json.loads(data)                    if isinstance(obj, dict):                        for k in ("content", "text", "delta", "message"):                            if isinstance(obj.get(k), str):                                text_piece = obj[k]                                break                except Exception:                    pass                if text_piece is None:                    text_piece = data                print(text_piece, end="", flush=True)                full_chunks.append(text_piece)        final_text = "".join(full_chunks)        print("\n=== FINAL ===")        print(final_text)    except Exception as e:        print(str(e))

## Request Body[​]()

    {  "prompt": "What does nike recently post?",  "session_id": "",  "unique_id": "default",  "type": "TIKTOK",}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| Accept | header | string | No | `text/event-stream` for streaming mode |
| prompt | body | string | Yes | natural language prompt |
| session\_id | body | int | No | ID of the chat session |
| unique\_id | body | string | No | `default` by default |
| type | body | string | No | `TIKTOK` by default, `YOUTUBE`, `INSTAGRAM` |

    {  "code": "0000",  "msg": "success",  "data": {    "role": "ASSISTANT",    "content": "Opening scene: a quiet, tactile tease. Nike posted a low-key, high-significance image — two embossed logos on a dark-brown textured surface — the familiar Nike swoosh sitting to the left of the SKIMS wordmark. No captioned hashtags. The piece reads like a whisper of a collaboration rather than a full reveal.\n\nQuick facts\n- Creator: @nike  \n- Hashtags: None  \n- view count: 1,000,000  \n- like count: 59,500  \n- share count: 9,226  \n- comment count: 146\n\nWhat the post shows (what we can say with confidence)\n- Visual: embossed Nike swoosh + SKIMS logo on a dark-brown, textured material (leather-like feel).  \n- Intent: a branding-focused image that documents/announces the co-presence of both logos — effectively a teaser of a Nike × SKIMS item or capsule.  \n- Tone: minimal, premium, deliberate — designed to spark recognition and speculation rather than provide product details.\n\nEngagement and comparative context\n- Strong reach: 1M views and ~59.5K likes indicate the post cut through the noise.  \n- Share-heavy reaction: 9.2K shares with only 146 comments suggests users are forwarding/speculating more than debating — classic teaser behavior that drives earned distribution.  \n- Relative performance: the Nike post sits in the mid-to-high engagement band when compared to creator posts in this set:\n  - @pappiiq (outfit + pickups): 1,700,000 views, 115,800 likes, 1,329 shares, 700 comments — high likes and comments, lower share rate (community engagement + product show-and-tell).  \n  - @camfant (reposts reaction): 1,100,000 views, 187,400 likes, 14,300 shares, 719 comments — extremely high likes and shares (viral creator energy).  \n  Nike’s post trades off raw likes for a higher share-to-comment ratio, signaling effective intrigue and social forwarding.\n\nBroader trend signals (what this post means in context)\n- Collaboration momentum: The explicit co-branding with SKIMS signals Nike is continuing the strategy of curated partnerships with lifestyle/fashion brands to access a premium/aesthetic audience.  \n- Premium/material emphasis: The embossed logos on a textured brown surface read as a leather/upscale-material treatment — suggesting footwear, accessories, or elevated apparel rather than basic activewear.  \n- Ecosystem amplification: Nike’s logo also appears organically in creator content in this dataset (@pappiiq wearing Nike Tech pants; two @camfant clips showing Nike-branded shirts). That organic visibility plus an official brand tease creates a two-pronged approach: corporate teaser + creator-led lifestyle exposure.\n\nMarketing implications & recommended next moves\n- Teaser works — but follow up quickly: convert intrigue into product pages or hyped drops within a short window (48–72 hours) to capture share-driven interest before speculation cools.  \n- Use creators strategically: amplify the reveal via creators already wearing Nike in authentic contexts (e.g., @pappiiq’s fit and pickups) to translate buzz into purchase intent.  \n- Reveal product cues gradually: if the item is premium (leather/boot/sneaker), follow-up content should show texture, silhouette, and lifestyle shots — that matches the initial tactile cue.  \n- Encourage discussion: respond or post a follow-up that invites user questions or polls to convert shares into comments and richer audience signals.\n\nLimitations / unknowns\n- No explicit product details (name, category, release date, pricing) are visible. The material hints leather/upscale, but the post does not confirm product type.  \n- No hashtags or caption clues to indicate campaign timing or collaborators beyond SKIMS branding.\n\nBottom line\nNike’s recent post reads as a targeted teaser for a Nike × SKIMS touchpoint — minimal but effective. It’s generating shares and reach, signaling a premium collaboration and creating an opening to leverage creator partnerships already showing Nike product in lifestyle content. To capitalize fully, a timely, detail-rich follow-up and creator amplification will translate intrigue into conversions.",    "thinkings": [      {        "title": "Break down the analysis request",        "content": "The user is asking for recent posts from Nike. To answer this effectively, the first step is to determine what \"recently\" means in this context. It's likely referring to their social media presence or official annou...12938 bytes truncated...


---

# Chat with personal media entities

Version: v1.2

The **Chat Personal** APIs provide an interface for conversational queries.  
Two modes are supported:

*   **Streaming Mode (`chat_personal_stream`)** — responses are returned incrementally using Server-Sent Events (SSE).
*   **Standard Mode (`chat_personal`)** — responses are returned as a single JSON object.

*   `https://api.memories.ai`

**POST** `/v1/chat_personal_stream`

## **POST** `/v1/chat_personal`[​]()

All requests must include the API key in the `Authorization` header.

    Authorization: <YOUR_API__KEY>

| Header | Required | Value | Description |
| --- | --- | --- | --- |
| `Authorization` | Yes | `Bearer sk-<api_key>` | API key for authentication. |
| `Content-Type` | Yes | `application/json` | Request body format. |
| `Accept` | Yes | `text/event-stream` | Indicates the client expects a stream (SSE). |

## Request Body[​]()

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `session_id` | string | No | The chat session ID. Empty string will create a new session. |
| `prompt` | string | Yes | The user prompt (text to send to the chat model). |
| `unique_id` | string | No | A client-defined identifier to differentiate requests. |

**Example Body:**

    {  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"}

    import requestsimport jsonurl = "https://api.memories.ai/serve/api/v1/chat_personal_stream"payload = json.dumps({  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"})headers = {  'Authorization': 'sk-test',  'Content-Type': 'application/json',  'Accept': 'text/event-stream'}with requests.post(url, headers=headers, data=payload) as resp:    resp.raise_for_status()    for line in resp.iter_lines(decode_unicode=True):        if line:            print(line)

    import requestsimport jsonurl = "https://api.memories.ai/serve/api/v1/chat_personal"payload = json.dumps({  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"})headers = {  'Authorization': 'sk-test',  'Content-Type': 'application/json'}response = requests.post(url, headers=headers, data=payload)print(response.text)

The response is a stream of text events delivered as Server-Sent Events (SSE). Each line contains a chunk of the generated response until the stream ends.

    data: {"token": "This is ..."}data: {"token": "..."}data: [DONE]

    {  "session_id": "sess_12345",  "response": "This is...",  "metadata": {}}

| Field | Type | Description |
| --- | --- | --- |
| `token` | string | A chunk of text generated by the model. |
| `[DONE]` | marker | Indicates the end of the stream. |
| Field | Type | Description |
| --- | --- | --- |
| `session_id` | string | Identifier for the chat session. |
| `response` | string | The generated chat response. |
| `metadata` | object | Additional response metadata (may include search info). |


---

# Transcription video

Version: v1.2

Transcription API converts visual and autio context of the video into text representations. You could transcribe an uploaded vidoe in two ways:

*   [`VIDEO`](): Transcribing the video\'s visual content into text.
*   [`AUDIO`](): Transcribing the video\'s audio content into text.
    *   `speaker`: Recognizing each speaker in the video.
*   [`Summary`](): Get the summary of the video.
    *   `chapter`: summarize the video along the timeframe.
    *   `topic`: summarize the video by events/topics.

*   You have created a memories.ai API key.
*   At least one video has been uploaded to memories.ai and is currently in the PARSE status.

# Prerequisites

*   You have created a memories.ai API key.
*   At least one video has been uploaded to memories.ai and is currently in the PARSE status.


---

# Get Video Transcription

Version: v1.2

Use this API to retrieve the transcription result for a video you have uploaded.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/get_video_transcription`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {  "video_no": "<VIDEO_ID>",   "unique_id": "<UNIQUE_ID>"}response = requests.get("https://api.memories.ai/serve/api/v1/get_video_transcription", headers=headers, params=params)print("Status:", response.status_code)try:    print("Video Transcription Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| video\_no | query | string | Yes | Unique video number returned after upload |
| Authorization | header | string | Yes | Your API key for authentication |
| unique\_id | body | string | No | `default` by default |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "VI606041694843813888",     "transcriptions": [      {        "index": 0,         "content": "Under a rocky overhang, three people are washing clothes in a shallow stream. Two individuals are seated on the pebbled ground, tending to laundry in basins, while a third person stands in the water further downstream. To the left, an open doorway reveals a room with a fireplace and a person tending to the fire. The background shows a misty, mountainous landscape with trees.",         "startTime": "0",         "endTime": "8"      }    ]  },   "success": true, "failed": false}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » transcription | list of objects | List of transcription segments |
| »» start | float | Segment start time in seconds |
| »» end | float | Segment end time in seconds |
| »» text | string | Transcribed speech content for that time segment |

*   Ensure the video has finished processing (status: `PARSE`) before calling this API.


---

# Generate Video Summary

Version: v1.2

Use this API to generate a structured summary of a video, either in the form of **chapters** or **topics**.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   You have a valid memories.ai API key.
*   The video must be successfully parsed and transcribed.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/generate_summary`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {    "video_no": "<VIDEO_ID>",    "type": "<TYPE>",    "unique_id": "<UNIQUE_ID>"}response = requests.get("https://api.memories.ai/serve/api/v1/generate_summary", headers=headers, params=params)print("Status:", response.status_code)try:    print("Summary Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| video\_no | query | string | Yes | Unique video number returned after upload |
| type | query | string | Yes | Type of summary to generate. Accepted values: `CHAPTER`, `TOPIC` |
| Authorization | header | string | Yes | Your API key for authentication |
| unique\_id | body | string | No | `default` by default |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "summary": "The video seems to capture a family in a parking lot, possibly dealing with a minor emergency or preparing to leave. The audio consists of fragmented speech, mainly a child\'s voice repeating \"Mommy, you\'re going to go,\" suggesting a departure or concern. The visual content shows the family approaching their car with shopping bags and a red backpack. There is no clear indication of what\'s happening, so it\'s hard to say definitively what the video is about without additional context.",    "items": [      {        "description": "A woman, a boy, and another woman are walking towards a parked car in a parking lot. They are carrying shopping bags. The car doors are open.",        "title": "Arrival at the Car",        "start": "0"      },      {        "description": "The boy is looking at his phone near the open car door. One of the women is bending down, seemingly interacting with something on the ground near the car.",        "title": "Phone and Interaction on the Ground",        "start": "10"      },      {        "description": "Close-up view reveals objects on a concrete surface, including brown planters, a black pipe, a red tool, and a yellow broom or mop handle.",        "title": "Close-up of Objects on the Ground",        "start": "30"      }    ]  },  "success": true,  "failed": false}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » summary\_type | string | The requested summary type (`CHAPTER` or `TOPIC`) |
| » summary | list of objects | List of structured summary segments |
| »» title | string | Title of the segment |
| »» start | float | Segment start time in seconds |
| »» end | float | Segment end time in seconds |
| »» description | string | Natural language description of the segment content |

*   Use `type=CHAPTER` for scene-based structural breakdown.
*   Use `type=TOPIC` for semantic grouping of related content.
*   Ensure the video has finished processing (status: `PARSE`) before calling this API.


---

# Get Audio Transcription from a public video

Version: v1.2

Use this API to retrieve the transcription result specifically from the audio track of a video from public video sources.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/get_public_audio_transcription`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {"video_no": "PI-594031499251159058"}response = requests.get("https://api.memories.ai/serve/api/v1/get_public_audio_transcription", headers=headers, params=params)print("Status:", response.status_code)try:    print("Audio Transcription Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | Your API key for authentication |
| video\_no | query | string | Yes | Unique video number |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "PI-594031499251159058",    "transcriptions": [      {        "index": 0,        "content": "I just got back from my friend's vintage liquidation sale.",        "startTime": "0",        "endTime": "3"      },      {        "index": 1,        "content": "Somehow I came back with two bags full of stuff.",        "startTime": "3",        "endTime": "7"      },      {        "index": 2,        "content": "Fully intended just to browse.",        "startTime": "7",        "endTime": "9"      }      ...    ]  }}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » transcriptions | list of objects | List of transcription segments from the audio track |
| »» startTime | float | Segment start time in seconds |
| »» endTime | float | Segment end time in seconds |
| »» content | string | Transcribed speech content for that time segment |
| »» index | int | id of segment |

*   This endpoint returns only the transcription derived from the **audio track**.


---

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


---

# List Videos | Memories.ai

Version: v1.2

Use this API to retrieve a paginated list of videos that have been uploaded to the platform. You can optionally filter the results by video name, video ID, folder, or processing status.

*   You have uploaded videos to the platform using the [Upload API]().
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/list_videos`

    import requestsheaders = {"Authorization": "<API_KEY>"}json_body = {    "page": 1,    "size": 200,    "video_name": "<VIDEO_NAME>",    "video_no": "<VIDEO_ID>",    "unique_id": "<UNIQUE_ID>",    "status": "<STATUS>",}response = requests.post("https://api.memories.ai/serve/api/v1/list_videos", headers=headers, json=json_body)print(response.json())

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| page | query | int | No | Page number for pagination (default: 1) |
| size | query | int | No | Number of results per page (default: 20) |
| video\_name | query | string | No | Filter by partial or exact video name |
| video\_no | query | string | No | Filter by unique video ID |
| status | query | string | No | Filter by video status (must match internal `VideoStatus` enum) |
| Authorization | header | string | Yes | Your API key for authentication |
| unique\_id | body | string | No | `default` by default |

    {  "code": "0000",  "msg": "success",  "data": {    "videos": [      {        "duration": "12",        "size": "3284512",        "status": "PARSE",        "cause": "null",        "video_no": "VI606404158946574336",        "video_name": "182082-867762198_tiny",        "create_time": "1754037217992"      },      {        "duration": "61",        "size": "5324808",        "status": "PARSE",        "cause": "null",        "video_no": "VI606402870447996928",        "video_name": "test_video_gz_visual_understanding_s36_gun_6_special_gun_6",        "create_time": "1754036910783"      },      {        "duration": "44",        "size": "3583477",        "status": "PARSE",        "cause": "null",        "video_no": "VI606401846039576576",        "video_name": "ssstik.io_@evarose.cosplay_1747479033469",        "create_time": "1754036666561"      }    ],    "current_page": 1,    "page_size": 200,    "total_count": "3"  },  "success": true,  "failed": false}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Paginated video metadata |
| » videos | list of objects | List of video entries |
| »» duration | string | Length of the video in seconds |
| »» size | string | File size in bytes |
| »» status | string | Processing status (e.g., `PARSE`, `UNPARSE`, `FAILED`) |
| »» cause | string | Reason for failure if status is failed (or `"null"`) |
| »» video\_no | string | Unique video identifier |
| »» video\_name | string | Name of the video |
| »» create\_time | string | Upload timestamp (Unix milliseconds format) |
| » current\_page | int | Current page number |
| » page\_size | int | Number of videos per page |
| » total\_count | string | Total number of videos matching the query |
| success | boolean | Indicates if the request was successful |
| failed | boolean | Indicates if the request failed |

*   Combine filters for more specific search results (e.g., by `folder_id` and `status`).
*   Use this API to find `video_no` values for downstream processing or retrieval tasks.


---

# Delete Videos | Memories.ai

Version: v1.2

To free up cloud storage or remove unused videos from the memories.ai database, developers can call this API to delete all raw and derived data associated with the specified `videoNos` in the request. Once the API call is successfully completed, no data related to the deleted videos will be retained.

*   You have created a memories.ai API key.

*   `https://api.memories.ai`

**POST** `serve/api/v1/delete_videos`  
**Rate limit**: Maximum 100 videos per request.

    import requestsheaders = {"Authorization": "<API_KEY>"}  # API key# List of video IDs to deletedata = ["VI1234567890", "VI0987654321"]params = {"unique_id": <UNIQUE_ID>}response = requests.post(    "https://api.memories.ai/serve/api/v1/delete_videos",    headers=headers,    json=data,    params=params)print(response.json())

## Request Body[​]()

    ["VI1234567890", "VI0987654321"]

    {  "unique_id": "<UNIQUE_ID>"}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | Authorization API key |
| data | body | string | Yes | List of video numbers to delete |
| unique\_id | body | string | No | `default` by default |

Status code **200**

    {  "code": "0000",   "msg": "success",   "data": null,   "success": true,   "failed": false}

| Status code | Message | Description |
| --- | --- | --- |
| 200 | [OK]() | The request was successful and the videos have been deleted. |

Status code **200**

| Name | Type | Required | Restriction | Description |
| --- | --- | --- | --- | --- |
| code | string | true | none | Response status code |
| msg | string | true | none | Message for the response |


---

# Get Public Video Details

Version: v1.2

Use this API to retrieve the details & metadata of a video from public video sources.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/get_public_video_detail`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {"video_no": "PI-603068775285264430"}response = requests.get("https://api.memories.ai/serve/api/v1/get_public_video_detail", headers=headers, params=params)print("Status:", response.status_code)try:    print("Audio Transcription Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | Your API key for authentication |
| video\_no | query | string | Yes | Unique video number |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "duration": "13",    "status": "PARSE",    "video_no": "PI-603068775285264430",    "video_name": "24 HOURS WOLVES FANS. 🐺 #nba #minnesota #timberwolves ",    "create_time": "1753242002121",    "video_url": "https://www.tiktok.com/player/v1/7434361641896103211",    "like_count": "1460",    "share_count": "6",    "comment_count": "29",    "view_count": "14200",    "collect_count": "50",    "blogger_id": "timberwolves",    "text_language": "en",    "music_name": "original sound",    "hash_tag": "#nba#minnesota#timberwolves",    "publish_time": "1730947213"  }}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » video\_no | string | The unique video ID |
| » video\_name | string | Title of the video |
| » duration | string | Length of the video in seconds |
| » create\_time | string | Timestamp of indexing the video |
| » video\_url | string | Original URL of the video |
| » blogger\_id | string | ID of the video creator/poster |
| » status | string | Indexing status of the video |
| » like\_count | string | Number of likes on the video |
| » share\_count | string | Number of times the video was shared |
| » comment\_count | string | Number of comments on the video |
| » view\_count | string | Number of views on the video |
| » collect\_count | string | Number of times the video was collected |
| » text\_language | string | Language of the video’s text content |
| » music\_name | string | Name of the background music/sound |
| » hash\_tag | string | Hashtags associated with the video |
| » publish\_time | string | Timestamp when the video was published |


---

# Download Video

Version: v1.2

The **Download Video** API returns the raw video file for a given `video_no` in your private library. Successful downloads return a binary stream (`application/octet-stream`). If the response is JSON, it indicates that the download did not succeed (e.g., the video is not ready, not found, or the request is invalid).

*   `https://api.memories.ai`

**POST** `/serve/api/v1/download`

> Full URL: `https://api.memories.ai/serve/api/v1/download`

Include your API key in the `Authorization` header.

    Authorization: <YOUR_API_KEY>

**Content-Type:** `application/json`

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `video_no` | string | Yes | The unique identifier of the video to download (e.g., `VI625239098370850816`). |
| `unique_id` | string | No | A client-defined identifier to scope the request. Default: `default`. |

    import requestsheaders = {"Authorization": "sk-test"}payload = {    "unique_id": "test",    "video_no": "VI625239098370850816"}url = "https://api.memories.ai/serve/api/v1/download"# stream=True enables chunked downloadresp = requests.post(url, json=payload, headers=headers, stream=True)print("Status:", resp.status_code)content_type = resp.headers.get("Content-Type", "")if "application/json" in content_type.lower():    # JSON means the download did not succeed; inspect the error payload    print(resp.json())else:    # Binary stream (video)    with open("video.mp4", "wb") as f:        for chunk in resp.iter_content(chunk_size=8192):            if chunk:                f.write(chunk)    print("Download complete")

    curl -X POST "https://api.memories.ai/serve/api/v1/download"   -H "Authorization: sk-test"   -H "Content-Type: application/json"   -d \'{"video_no":"VI625239098370850816","unique_id":"test"}\'   --output video.mp4

> If the server returns JSON (e.g., an error), `curl` will save that JSON into `video.mp4`. If you want to handle errors separately, omit `--output` first to inspect the response.

On success, the server returns the **video file as a binary stream**:

*   **Status:** `200`
*   **Content-Type:** `application/octet-stream`
*   **Body:** Binary content of the video

If the download cannot be fulfilled, a JSON payload is returned instead of the binary stream. Example:

    {  "code": "0001",  "msg": "video not found",  "data": null,  "failed": true,  "success": false}

Common scenarios:

*   **Rate limit**: API calling frequency has reached rate limit. Try again later.
*   **Not found**: Invalid `video_no` or does not exist within the specified `unique_id` scope.

| Code | Meaning | Notes |
| --- | --- | --- |
| 0000 | OK | Returns binary video stream on success |
| 0001 | Video not found | No video find from `video_no` |
| 0429 | Rate limit reached | Request has exceeded the limit. |

*   **Stream downloads**: Always use `stream=True` (Python) to avoid loading the entire file into memory.
*   **File name**: Choose your own output filename (e.g., `video.mp4`). The API does not enforce a specific name.
*   **Scopes**: If you organize content by `unique_id`, include it for correct scoping.


---

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


---

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


---

# Video Caption | Memories.ai

Version: v1.2

Use this API to analyze video content and automatically generate captions or summaries. It also supports **human re-identification (ReID)** by matching people in the video against reference images you provide.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have acquired for special memories.ai API key, as this API is not provided for general API key.
*   You have provide a callback URL, as the repsonse is contained in POST request to it.
*   The videos must meet the following requirements:
    *   **File size**: Maximum 20 MB
    *   **Duration**: Between 20–300 seconds
    *   **Optional ReID**: Up to 5 reference person images can be provided

*   `https://security.memories.ai`

*   **POST** `/v1/understand/upload` – Upload video by URL
*   **POST** `/v1/understand/uploadFile` – Upload video by local file (multipart form)

    import requests, jsonurl = "https://security.memories.ai/v1/understand/upload"headers = {"Authorization": "<API_KEY>"}json_body = {    "video_url": "https://example.com/test_video.mp4",    "user_prompt": "Summarize the video content and identify key persons",    "system_prompt": "You are a video understanding system that analyzes content and detects persons.",    "callback": "https://yourserver.com/callback",    "thinking": False}response = requests.post(url, headers=headers, json=json_body)print(response.json())

Replace the following placeholders:

*   `API_KEY`: Your actual memories.ai API key.
*   `video_url`: Publicly accessible video URL (if using URL method).
*   `callback`: A publicly accessible endpoint to receive analysis results.
*   `persons`: Optional list of people to re-identify in the video.

    import requests, jsonurl = "https://security.memories.ai/v1/understand/uploadFile"headers = {"Authorization": "<API_KEY>"}# JSON request bodydata = {    "user_prompt": "Summarize the video content and identify key persons",    "system_prompt": "You are a video understanding system that summarizes video content.",    "callback": "https://yourserver.com/callback",}files = [    ("req", ("req.json", json.dumps(data), "application/json")),    ("files", ("video.mp4", open("video.mp4", "rb"), "video/mp4")),]response = requests.post(url, files=files, headers=headers)print(response.json())

When processing is complete, results will be sent asynchronously to the `callback` URL you provide.

    {  "status": 0,  "task_id": "8e03075a-2230-4e67-98d4-ba53f37c807a",  "data": {    "text": "A man enters the room and greets two colleagues. Alice is identified by the reference image.",    "token": {      "input": 123,      "output": 456,      "total": 579    }  }}

The callback request body includes:

*   **status**: `0` = success, `-1` = failure
*   **task\_id**: Unique task identifier
*   **data.text**: Generated caption or summary text
*   **data.token**: Token usage statistics (input/output/total)

## Request Body (URL Method)[​]()

    video_url: "<VIDEO_URL>"user_prompt: "<USER_PROMPT>"system_prompt: "<SYSTEM_PROMPT>"callback: "<CALLBACK_URL>"persons:   - name: "<NAME>"    url: "<IMAGE_URL>"thinking: false

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| video\_url | body | string | No | Public video URL (use local file method if not provided) |
| user\_prompt | body | string | Yes | Instruction for video analysis |
| system\_prompt | body | string | Yes | Role/context for the analysis system |
| callback | body | string | Yes | Callback URL for asynchronous results |
| persons | body | array | No | Person descriptors for human re-identification |
| thinking | body | boolean | No | Enable/disable reasoning mode |
| Authorization | header | string | Yes | Your API key |

Status code **200**

    {  "code": 0,  "msg": "success",  "data": {    "task_id": "xxx"  }}

| Name | Type | Description |
| --- | --- | --- |
| code | int | Status code (`0` for success, `-1` for failure) |
| msg | string | Message text |
| data | object | Response data |
| » task\_id | string | Unique task ID for tracking |

**Note:** The `callback` field must be provided and reachable. The final captioning or analysis result is only delivered asynchronously.


---

# Human Re-identification (ReID)

Version: v1.2

Use this feature to identify and track specific people in videos or images. The API compares provided reference images against the media being analyzed and tags any detected matches.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have acquired for special memories.ai API key, as this API is not provided for general API key.
*   Reference images should be clear and high-quality to maximize accuracy.
*   A maximum of **5 reference images** can be provided per request.

*   `https://security.memories.ai`

*   **POST** `/v1/understand/upload` – Upload image by URL
*   **POST** `/v1/understand/uploadFile` – Upload image by local file (multipart form)

Human re-identification is not a standalone endpoint. Instead, it is integrated as part of the **Video Caption** and **Image Caption** APIs.  
You add a `persons` parameter to the request body with details of each individual you want to track.

    import requests, jsonurl = "https://security.memories.ai/v1/understand/upload"headers = {"Authorization": "<API_KEY>"}json_body = {    "video_url": "https://example.com/test_video.mp4",    "user_prompt": "Summarize the video and identify known persons.",    "system_prompt": "You are a video understanding system that can detect and identify people.",    "callback": "https://yourserver.com/callback",    "persons": [        {"name": "Alice", "url": "https://example.com/alice.jpg"},        {"name": "Bob", "url": "https://example.com/bob.jpg"}    ]}response = requests.post(url, headers=headers, json=json_body)print(response.json())

    import requests, jsonurl = "https://security.memories.ai/v1/understand/uploadFile"headers = {"Authorization": "<API_KEY>"}data = {    "user_prompt": "Identify if Alice appears in this image.",    "system_prompt": "You are an image analysis system with human re-identification capabilities.",    "thinking": False}files = [    ("req", ("req.json", json.dumps(data), "application/json")),    ("files", ("video.mp4", open("video.mp4", "rb"), "video/mp4")),    ("file", ("test_image.png", open("test_image.png", "rb"), "image/png")),    ("file", ("alice.png", open("alice.png", "rb"), "image/png"))]response = requests.post(url, files=files, headers=headers)print(response.json())

## Request Body (ReID Parameter)[​]()

    persons:   - name: "Alice"    url: "https://example.com/alice.jpg"  - name: "Bob"    url: "https://example.com/bob.jpg"

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| persons | body | array | No | List of person descriptors (name + reference image URL or file) |
| » name | body | string | Yes | Person’s name or identifier |
| » url | body | string | No | Reference image URL (if file not uploaded) |
| file | body | binary | No | Reference image file (if URL not provided) |

If `persons` are provided, the result will indicate whether those individuals were detected.

    {  "status": 0,  "task_id": "a1b2c3d4e5",  "data": {    "text": "Bob and Alice are both present in the video. Alice enters first, followed by Bob.",    "token": {      "input": 210,      "output": 92,      "total": 302    }  }}

| Name | Type | Description |
| --- | --- | --- |
| status | int | `0` = success, `-1` = failure |
| task\_id | string | Unique task identifier |
| data | object | Response data |
| » text | string | Generated caption including detected person matches |
| » token | object | Token usage details |

**Note:** Human ReID is always used in conjunction with Video or Image Caption APIs. It cannot be called independently.


---

# Pricing and Free Trial Policy

Version: v1.2

Memories.ai API is built to help developers seamlessly integrate powerful **AI video understanding** and **interactive features**. To help you get started quickly, we offer a **100 free credit**, allowing you to **explore the core capabilities of the API with zero barriers**.

*   Every newly registered user receives 100 credits.
*   The free credit can be used across all memories.ai API endpoints, with no limitations.
*   No credit card is required to start using the platform.

*   Once your 100 credits are exhausted\*\*, your API access will be paused. You’ll need to recharge your account to continue using the service.
    
*   After recharging, your usage will be billed according to the standard API pricing.  
    For full details, visit our [Pricing]() page.
    

*   Log in to your memories.ai account and navigate to the **API Usage** page to view your current balance and recharge options.
    
*   After recharging, your balance will be updated automatically, and you can continue using the API without interruption.
    

*   **100 free trial credits** — get started instantly, no credit card required.
*   **Flexible pay-as-you-go pricing** — scale as you grow, without hidden costs.
*   **Advanced video understanding capabilities** — empower your applications with state-of-the-art AI.

| Service Component | Unit Description | Price | Rate Limit |
| --- | --- | --- | --- |
| 1\. Index to search | Per 1,000 minutes | Free | 1 QPS (Max 2 hours) |
| 2\. Index to chat | Per 1,000 minutes | Free | 1 QPS |
| 2.1 Video Transcription | Per 1,000 queries | Free | 5 QPS |
| 2.2 Audio Transcription | Per 1,000 queries | Free | 5 QPS |
| 2.3 Update Video Transcription | Per 1,000 queries | Free | 5 QPS |
| 3\. Search | Per 1,000 search queries | Free | 10 QPS |
| 4\. Storage | Per 10 GB per month | Free | N/A (Max 10 GB) |
| 5\. Video Creator(TBD) | Per 1,000 minutes input | Free | 1 QPM |
| 6.1 Video Marketer | Per 1,000 minutes scraped | Free | N/A (Max 100 minutes) |
| 6.2 Video Marketer | Per 1 query | Free | 1 QPS |
| 6.3 Video Chat | Per 1 query | Free | 1 QPS |
| 7\. Creator Insight(TBD) | Per Creator | Free | 1 QPS |
| 8\. Video Scriptor | Per minute | Free | 3 episodes (Max 5 minutes each) |
| Service Component | Unit Description | Price |
| --- | --- | --- |
| 1\. Index to search | Per 1,000 minutes | $0.5 |
| 2\. Index to chat | Per 1,000 minutes | $5 |
| 2.1 Video Transcription | Per 1,000 queries | $0.1 |
| 2.2 Audio Transcription | Per 1,000 queries | $0.1 |
| 2.3 Update Video Transcription | Per 1,000 seconds | ~$0.1 (exact price will based on token usage) |
| 3\. Search | Per 1,000 search queries | $0.1 |
| 4\. Storage | Per 10 GB per month | $0.3 / month |
| 5\. Video Creator(TBD) | Per 1,000 minutes input | $92 |
| 6.1 Video Marketer | Per 1,000 minutes scraped | $40 |
| 6.2 Video Marketer | Per 1M tokens | $1.6 |
| 6.3 Video Chat | Per 1M tokens | $0.3 |
| 7\. Creator Insight(TBD) | Per Creator | $0.6 |
| 8\. Video Scriptor | Per minute | $0.6 |
| 9\. Video Download | Per GB | $0.12 |


---

# Rate Limits | Memories.ai

Version: v1.2

Rate limiting helps ensure optimal performance and smooth operation for all users by allocating resources efficiently.

The following are the throttling limits for each interface, defined by per-minute and daily (24-hour) usage caps:

| Interface | Query Per Second/Minute |
| --- | --- |
| Upload from local/streaming url | 1 QPS |
| Upload from platform/creator url | 1 QPM |
| Search | 10 QPS |
| Chat | 1 QPS |
| Video Marketer | 1 QPS |
| Video Transcription | 5 QPS |
| Audio Transcription | 5 QPS |
| Summary | 5 QPS |
| List Videos | 5 QPS |
| List Sessions | 5 QPS |
| Delete Videos | 5 QPS |
| Download Videos | 12 QPM |
| Caption Videos | 1 QPS |
| Caption Images | 5 QPS |
| Human Reid | 1 QPS |

If you exceed a rate limit, the API will return a `0429` error response. For example:

    {  "code": "0429",  "msg": "Request has exceeded the limit."}

Each newly registered user receives 100 API credit. Once this credit is used up, your service will be paused. To continue using the API, simply recharge your account — service will automatically resume upon successful payment.


---

# Upload video from file

Version: v1.2

Use this API to upload your file from your local storage.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have created a memories.ai API key.
*   The videos must meet the following requirements to ensure a successful encoding process:
    *   **Video and audio formats**: The video files must be encoded in `h264`, `h265`, `vp9`, or `hevc`.
    *   **Audio track**: If you intend to use the [audio transcription]() feature, the video you are uploading must contain an audio track.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/upload`

    import osimport requests  headers = {"Authorization": "<API_KEY>"}  # API key  file_path = "<VIDEO_FILE_PATH>"# Video file details  files = {      "file": (os.path.basename(file_path), open(file_path, 'rb'), "video/mp4")  }  # Optional callback URL for task status notifications  data = {"callback": "<YOUR_CALLBACK_URI>", "unique_id": "<UNIQUE_ID>"} # Optionalresponse = requests.post(      "https://api.memories.ai/serve/api/v1/upload",      files=files,      data=data,      headers=headers  )  print(response.json())   

Replace the following placeholders:

*   `API_KEY`: Your actual memories.ai API key.
*   `VIDEO_FILE_PATH`: Full path to your video file.
*   `YOUR_CALLBACK_URI`: A publicly accessible URL where memories.ai can send video status updates.
*   `UNIQUE_ID`: a unique id for workspace/namespace/user identification

If you provide a callBackUri, memories.ai will send a POST request to it once the video has been uploaded or parsed.

    {  "videoNo": "VI554046065381212160",  "status": "PARSE"}

The callback request body includes the following fields:

*   **videoNo**: The unique video number.
*   **status**: The processing status of the video.

The **status** field can have one of the following values:

*   `"PARSE"` – The video is being processed.
*   `"UNPARSE"` – The video has not been processed.
*   `"FAIL"` – The video processing failed.

## Request Body[​]()

    file: ""unique_id: "<UNIQUE_ID"callback: "<CALLBACK_URL>"

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| callback | query | string | No | Callback URI to notify on successful parsing |
| Authorization | header | string | Yes | Authorization API key |
| file | body | string (binary) | Yes | Video file to upload |
| unique\_id | body | string | No | `default` by default |
| datetime\_taken | body | string | No | Date and time when the image was captured (format: `YYYY-MM-DD HH:MM:SS`) |
| camera\_model | body | string | No | Camera model metadata |
| latitude | body | string | No | GPS latitude of where the image was captured |
| longitude | body | string | No | GPS longitude of where the image was captured |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "VI568102998803353600",    "videoName": "1be6a69f3c6e49bf986235d68807ab1f",    "videoStatus": "UNPARSE",    "uploadTime": "1744905509814"  }}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Status code |
| msg | string | Yes | Message |
| data | object | Yes | Data object |
| » videoNo | string | Yes | Video identification number |
| » videoName | string | Yes | Name of the video |
| » videoStatus | string | Yes | Status of the video |
| » uploadTime | string | Yes | Video upload timestamp |

**Note: The callBackUri field will actively notify you of the task status after the video upload is complete and the parsing task is finished.**


---

# Upload video from URL

Version: v1.2

Use this API to upload your file from a direct streamable url. Example:

    http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have created a memories.ai API key.
*   The videos from url must meet the following requirements to ensure a successful encoding process:
    *   **Video and audio formats**: The video files must be encoded in `h264`, `h265`, `vp9`, or `hevc`.
    *   **Audio track**: If you intend to use the [audio transcription]() feature, the video you are uploading must contain an audio track.
*   The url must be a direct download link to the video file. This URL can be accessed via a GET request to download or stream the video content. No authentication is required (unless otherwise noted).

*   `https://api.memories.ai`

**POST** `/serve/api/v1/upload_url`

    import requests  headers = {"Authorization": "<API_KEY>"}  # API key  # Video file details  data = {      "url": "<URL>",    "callback": "<YOUR_CALLBACK_URI>", # Optional    "unique_id": "<UNIQUE ID>",}  response = requests.post(      "https://api.memories.ai/serve/api/v1/upload_url",      data=data,      headers=headers  )  print(response.json())   

Replace the following placeholders:

*   `API_KEY`: Your actual memories.ai API key.
*   `URL`: URL to your video.
*   `YOUR_CALLBACK_URI`: A publicly accessible URL where memories.ai can send video status updates.
*   `UNIQUE_ID`: a unique id for workspace/namespace/user identification

If you provide a callBackUri, memories.ai will send a POST request to it once the video has been uploaded or parsed.

    {  "videoNo": "VI554046065381212160",  "status": "PARSE"}

The callback request body includes the following fields:

*   **videoNo**: The unique video number.
*   **status**: The processing status of the video.

The **status** field can have one of the following values:

*   `"PARSE"` – The video is being processed.
*   `"UNPARSE"` – The video has not been processed.
*   `"FAIL"` – The video processing failed.

## Request Body[​]()

    {  "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",  "callback": "test.beeceptor.com",  "unique_id": "default",}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| callback | query | string | No | Callback URI to notify on successful parsing |
| Authorization | header | string | Yes | Authorization API key |
| url | body | string | Yes | URL of the video |
| unique\_id | body | string | No | `default` by default |
| datetime\_taken | body | string | No | Date and time when the image was captured (format: `YYYY-MM-DD HH:MM:SS`) |
| camera\_model | body | string | No | Camera model metadata |
| latitude | body | string | No | GPS latitude of where the image was captured |
| longitude | body | string | No | GPS longitude of where the image was captured |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "VI568102998803353600",    "videoName": "1be6a69f3c6e49bf986235d68807ab1f",    "videoStatus": "UNPARSE",    "uploadTime": "1744905509814"  }}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Status code |
| msg | string | Yes | Message |
| data | object | Yes | Data object |
| » videoNo | string | Yes | Video identification number |
| » videoName | string | Yes | Name of the video |
| » videoStatus | string | Yes | Status of the video |
| » uploadTime | string | Yes | Video upload timestamp |

**Note: The callBackUri field will actively notify you of the task status after the video upload is complete and the parsing task is finished.**


---

# Upload video from platform URL

Version: v1.2

Memories.ai supports uploading a video from a video platform. Currently we support any url from [TikTok](), [Youtube]() and [Instagram]()(Facebook, Twitter coming soon). When calling this API, we will first download the data from that url and then index it into Memories.ai system.

Example:

    Tiktok: https://www.tiktok.com/@cutshall73/video/7543017294226558221Instagram: https://www.instagram.com/p/DNu8_Fs4mSd/Youtube: https://www.youtube.com/shorts/T2ThsydNQaM

This page describes **two upload APIs**:

*   **Using URLs from the same platform when batching in a single request**: When submitting video\_urls in an API request, please make sure they are from the same platform. The API will auto-parse and check the URLs before indexing the videos from the request.
    
*   **Private Library Upload** – Add videos to your personal library for use with [Video Chat]().
    
*   **Public Library Upload** – Contribute videos to the shared library for use with [Video Marketer]().
    
*   **Youtube** - Youtube videos that are long might be slow to be indexed because of scraper capacity.
    

*   Videos in the **private library** can be deleted at any time.
*   Videos in the **public library** are permanent and **cannot be deleted**.
*   Once a video (`video_url`) is uploaded to one library, uploading the same video to the other is **free of charge**.
*   Videos in the **public library** are visible to all Memories.ai users and are **searchable and queryable** by everyone. Thank you for your contribution!
*   If a video is scraped again, **only metadata is updated**—no extra download, storage, or indexing cost will be incurred.
*   Youtube scraper is a bit slower and we will keep improveing it! Please contact us if you have any technical problems!

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have created a memories.ai API key.
*   The url must be a proper URL that directs users to a video post page.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/scraper_url`

**POST** `/serve/api/v1/scraper_url_public`

    import requests  headers = {"Authorization": "<API_KEY>"}  # API key  # Video url details  payload={  "video_urls": ["https://www.tiktok.com/@cutshall73/video/7543017294226558221","https://www.tiktok.com/@abcnews/video/7543794552365124919"],  "unique_id": "default",  "callback_url": "<CALLBACK_URL>",  "quality": 1080, # the final resolution will be <= 1080 based on the provided source, default 720} response = requests.post(      "https://api.memories.ai/serve/api/v1/scraper_url",      json=payload,      headers=headers  )  print(response.json())   

    import requestsheaders = {    "Authorization": "<API_KEY>",  # API key}payload = {    "video_urls": [        "https://www.tiktok.com/@cutshall73/video/7543017294226558221",        "https://www.tiktok.com/@abcnews/video/7543794552365124919"    ],    "callback_url": "<CALLBACK_URL>",    "quality": 1080, # the final resolution will be <= 1080 based on the provided source, default 720}resp = requests.post(    "https://api.memories.ai/serve/api/v1/scraper_url_public",    json=payload,    headers=headers,    timeout=60)print(resp.json())

Replace the following placeholders:

*   `API_KEY`: Your actual memories.ai API key.
*   `CALLBACK_URL`: A publicly accessible URL where memories.ai can send video status updates.

If you provide a callback URL,, memories.ai will send a POST request to it once the scraping task has finished and indexing has begun. After that, you can use videos from callback message or use [`get_task_status`]() to retrieve video\_ids that were scraped, and [`list_videos`]() to check the status of those video\_ids.

    {    "taskId": "4b2d85ea-8b61-4689-96c3-75d907140242_84f9d9b4b6e5940b67e67e2d17ef1f97",     "status": "SUCCEEDED"}

The callback request body includes the following fields:

*   **videoNo**: The unique video number.
*   **status**: The processing status of the video.

The **status** field can have one of the following values:

*   `"SUCCEEDED"` – The task is successfully created.
*   `"FAILED"` – The task is not created.

## Request Body[​]()

    {  "video_urls": ["https://www.tiktok.com/@cutshall73/video/7543017294226558221","https://www.tiktok.com/@abcnews/video/7543794552365124919"],  "callback": "test.beeceptor.com",  "unique_id": "default", // only needed when uploading to private library  "quality": 1080, // the final resolution will be <= 1080 based on the provided source, default 720}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| **Authorization** | header | string | Yes | API key, e.g. `Authorization: <API_KEY>` |
| **video\_urls** | body | array of string | Yes | List of video URLs to scrape |
| **unique\_id** | body | string | No | Correlation id; defaults to `"default"` (only used when uploading to private library) |
| **callback\_url** | body | string (URL) | No | Callback URI to notify on successful parsing |
| **quality** | body | int | No | resolution of the scraped video based on the provided source (1080 if source has 1080p, otherwise 720, or 480, or 260); 720 if no value is passed; this parameter is only effective when youtube URL is provided; for other platform, the video will be scraped at original resolution |

Status code **200**

    {    "code": "0000",     "msg": "success",     "data": {        "taskId": "31b0fccb-d6f9-4135-922d-1e8828499812_84f9d9b4b6e5940b67e67e2d17ef1f97"    },     "failed": false,     "success": true}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Status code |
| msg | string | Yes | Message |
| data | object | Yes | Data object |
| » taskId | string | Yes | Unique identifier of the uploading task |
| failed | boolean | Yes | Indicates whether the request failed |
| success | boolean | Yes | Indicates whether the request succeeded |

*   Data indexing is performed **asynchronously**. When indexing is complete, Memories.ai will send a notification to the `callback_url` you provided.
*   You can also use the `task_id` to [check the task status]().
    *   If the `"video_ids"` field in the response is an empty list `[]`, the system is still downloading the video(s) from the platform.
    *   If the `"video_ids"` field contains one or more IDs (e.g., `"PI-603068775285264430"`), the video(s) have been downloaded and are currently being indexed.


---

