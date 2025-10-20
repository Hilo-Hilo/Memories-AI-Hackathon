# Upload API

**Version:** v1.2

The Upload API allows you to upload videos and images to Memories.ai for processing and analysis. Videos can be uploaded from local files, URLs, platform links, or social media sources.

---

## Contents

1. [Upload Video | Memories.ai](#upload-video--memoriesai)
2. [Upload video from file | Memories.ai](#upload-video-from-file--memoriesai)
3. [Upload video from URL | Memories.ai](#upload-video-from-url--memoriesai)
4. [Upload video from platform URL](#upload-video-from-platform-url)
5. [Upload video from platform creator URL | Memories.ai](#upload-video-from-platform-creator-url--memoriesai)
6. [Upload video from hashtag | Memories.ai](#upload-video-from-hashtag--memoriesai)
7. [Upload image from file | Memories.ai](#upload-image-from-file--memoriesai)

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


