# Utils API

**Version:** v1.2

The Utils API provides utility functions for managing your videos, sessions, and tasks. These endpoints help you list, retrieve, delete, and monitor your content and operations.

---

## Contents

1. [List Videos | Memories.ai](#list-videos--memoriesai)
2. [List Videos | Memories.ai](#list-videos--memoriesai)
3. [List Chat Sessions | Memories.ai](#list-chat-sessions--memoriesai)
4. [Delete Videos | Memories.ai](#delete-videos--memoriesai)
5. [Get Session Detail | Memories.ai](#get-session-detail--memoriesai)
6. [Get Public Video Details | Memories.ai](#get-public-video-details--memoriesai)
7. [Get Task Status | Memories.ai](#get-task-status--memoriesai)
8. [List Images | Memories.ai](#list-images--memoriesai)
9. [Get Private Video Details | Memories.ai](#get-private-video-details--memoriesai)
10. [Download Video | Memories.ai](#download-video--memoriesai)

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


