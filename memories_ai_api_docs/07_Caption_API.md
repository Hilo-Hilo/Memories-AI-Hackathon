# Caption API

**Version:** v1.2

The Caption API generates descriptive captions for videos and images, and provides human re-identification capabilities for tracking individuals across video content.

---

## Contents

1. [Caption & Human Re-identification | Memories.ai](#caption-&-human-re-identification--memoriesai)
2. [Video Caption | Memories.ai](#video-caption--memoriesai)
3. [Image Caption | Memories.ai](#image-caption--memoriesai)
4. [Human Re-identification (ReID) | Memories.ai](#human-re-identification-reid--memoriesai)

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


